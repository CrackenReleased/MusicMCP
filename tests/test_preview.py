"""Conformance and security tests for Visualizer Preview Silo."""
from fractions import Fraction
import io
import json
import math
import struct
import unittest
import urllib.request
import urllib.error
import wave

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.preview.server import (
    PreviewServer,
    serialize_music_obj,
)


def make_clean_sine_wav(frequency=440.0, duration=0.25, sample_rate=44100):
    num_samples = int(sample_rate * duration)
    frames = bytearray()
    for i in range(num_samples):
        val = int(16000 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        frames.extend(struct.pack('<h', val))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)
    return buf.getvalue()


class TestPreviewServer(unittest.TestCase):
    def setUp(self):
        self.producer = Producer("test-preview-producer", "0.1.01")
        self.melody_grant = Grant("composer-joel", {"melody", "harmony"}, {"confirm", "correct", "restore"})
        self.ws, (self.sess,) = create_workspace(
            [self.melody_grant],
            constraints=[LockConstraint("lead_voice", "composer-joel", "Melody locked for production")],
        )

        # Ingest test evidence and proposal
        wav_data = make_clean_sine_wav(440.0, 0.25, 44100)
        self.evidence = self.ws.add_evidence(wav_data, "audio/wav")
        self.obs = self.ws.observe(self.evidence.id, "Test vocal melody", producer=self.producer)
        self.initial_notes = (Note("A4", Fraction(1, 1)), Note("C5", Fraction(1, 1)))
        self.proposal = self.ws.propose(
            self.obs.id,
            scope="melody",
            notes=self.initial_notes,
            mode="intended",
            uncertainty="LOW",
            origin="interpreted",
            producer=self.producer,
        )

        # Spin up test server on ephemeral port (port=0)
        self.server = PreviewServer(self.ws, self.sess, host="127.0.0.1", port=0)
        self.server.start(background=True)

    def tearDown(self):
        self.server.stop()

    def _get(self, path: str) -> tuple[int, dict | str]:
        url = f"{self.server.url}{path}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return resp.status, json.loads(data.decode("utf-8"))
                return resp.status, data.decode("utf-8")
        except urllib.error.HTTPError as err:
            data = err.read()
            return err.code, json.loads(data.decode("utf-8"))

    def _post(self, path: str, body: dict) -> tuple[int, dict]:
        url = f"{self.server.url}{path}"
        raw = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=raw, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def test_security_boundary_rejects_external_hosts(self):
        with self.assertRaises(ValueError):
            PreviewServer(self.ws, self.sess, host="0.0.0.0", port=8765)
        with self.assertRaises(ValueError):
            PreviewServer(self.ws, self.sess, host="192.168.1.100", port=8765)

    def test_get_root_serves_html(self):
        status, content = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Music MCP Visualizer", content)
        self.assertIn("Authority Review Deck", content)

    def test_get_project_status(self):
        status, body = self._get("/api/project")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["revision"], 0)
        self.assertEqual(len(body["locks"]), 1)
        self.assertEqual(body["locks"][0]["scope"], "lead_voice")
        self.assertTrue(body["capabilities"]["human_confirmation"])

    def test_get_proposals_and_spectrum(self):
        # 1. Check proposals endpoint
        status, p_body = self._get("/api/proposals")
        self.assertEqual(status, 200)
        self.assertTrue(p_body["ok"])
        self.assertEqual(len(p_body["proposals"]), 1)
        self.assertEqual(p_body["proposals"][0]["id"], self.proposal.id)
        self.assertEqual(p_body["proposals"][0]["uncertainty"], "LOW")

        # 2. Check spectrum endpoint
        status, s_body = self._get(f"/api/spectrum?evidence_id={self.evidence.id}")
        self.assertEqual(status, 200)
        self.assertTrue(s_body["ok"])
        self.assertIn("report", s_body)
        rep = s_body["report"]
        self.assertEqual(rep["sample_rate"], 44100)
        self.assertIn("bass", rep["band_energies"])
        self.assertIn("extended_ultrasonic", rep["band_energies"])
        self.assertTrue(rep["clean_musical_signal"])

    def test_post_confirm_publishes_revision(self):
        status, body = self._post("/api/confirm", {
            "proposal_id": self.proposal.id,
            "expected_revision": 0,
            "reason": "Musician verified A4 pitch in melody line",
        })
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        rev = body["revision"]
        self.assertEqual(rev["number"], 1)
        self.assertEqual(rev["actor"], "composer-joel")
        self.assertEqual(rev["operation"], "confirm")
        self.assertEqual(rev["origin"], "interpreted")
        self.assertEqual(len(rev["notes"]), 2)
        self.assertEqual(rev["notes"][0]["pitch"], "A4")

        # Verify state in workspace
        self.assertEqual(self.ws.snapshot().revision, 1)

    def test_post_correct_publishes_human_revision(self):
        # Confirm proposal first
        self._post("/api/confirm", {
            "proposal_id": self.proposal.id,
            "expected_revision": 0,
            "reason": "Initial confirm",
        })

        # Submit human correction
        status, body = self._post("/api/correct", {
            "proposal_id": self.proposal.id,
            "notes": "D4 1, F4 1/2, A4 1/2",
            "expected_revision": 1,
            "reason": "Human artist corrected melody notes",
        })
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        rev = body["revision"]
        self.assertEqual(rev["number"], 2)
        self.assertEqual(rev["operation"], "correct")
        self.assertEqual(rev["origin"], "human")
        self.assertEqual(len(rev["notes"]), 3)
        self.assertEqual(rev["notes"][0]["pitch"], "D4")

        self.assertEqual(self.ws.snapshot().revision, 2)

    def test_post_restore_publishes_restored_revision(self):
        # Rev 1
        self._post("/api/confirm", {"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "R1"})
        # Rev 2
        self._post("/api/correct", {"proposal_id": self.proposal.id, "notes": "C4 1", "expected_revision": 1, "reason": "R2"})

        # Restore Rev 1
        status, body = self._post("/api/restore", {
            "revision_number": 1,
            "expected_revision": 2,
            "reason": "Musician reverted to initial interpretation",
        })
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        rev = body["revision"]
        self.assertEqual(rev["number"], 3)
        self.assertEqual(rev["operation"], "restore")
        self.assertEqual(rev["restored_from"], 1)
        self.assertEqual(rev["notes"][0]["pitch"], "A4")

        self.assertEqual(self.ws.snapshot().revision, 3)

    def test_propose_alternative_retains_generated_origin(self):
        # Publish melody first
        self._post("/api/confirm", {"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "Base melody"})

        # Request generated alternative for harmony scope
        status, body = self._post("/api/propose_alternative", {
            "source_scope": "melody",
            "target_scope": "harmony",
            "alt_type": "HARMONY_THIRD_ABOVE",
            "requested_by": "composer-joel",
            "reason": "Add backing vocal harmony",
        })
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        prop = body["proposal"]
        self.assertEqual(prop["scope"], "harmony")
        self.assertEqual(prop["origin"], "generated")
        # Diatonic 3rd above A4 is C5; C5 is E5
        self.assertEqual(prop["notes"][0]["pitch"], "C5")
        self.assertEqual(prop["notes"][1]["pitch"], "E5")

        # Confirm the generated alternative
        status, c_body = self._post("/api/confirm", {
            "proposal_id": prop["id"],
            "expected_revision": 1,
            "reason": "Accepted generated 3rd harmony",
        })
        self.assertEqual(status, 200)
        self.assertTrue(c_body["ok"])
        # Provenance Invariant: Acceptance must retain origin='generated'
        self.assertEqual(c_body["revision"]["origin"], "generated")
        self.assertEqual(c_body["revision"]["scope"], "harmony")

    def test_revision_conflict_returns_409(self):
        status, body = self._post("/api/confirm", {
            "proposal_id": self.proposal.id,
            "expected_revision": 999,  # Stale revision
            "reason": "Will conflict",
        })
        self.assertEqual(status, 409)
        self.assertFalse(body["ok"])
        self.assertIn("REVISION_CONFLICT", body["error"]["code"])

    def test_unauthorized_scope_returns_403(self):
        # Ingest proposal in unauthorized scope 'drums'
        obs = self.ws.observe(self.evidence.id, "Drums", producer=self.producer)
        p_drums = self.ws.propose(
            obs.id,
            scope="drums",
            notes=(Note("C4", Fraction(1, 1)),),
            mode="intended",
            uncertainty="LOW",
            origin="interpreted",
            producer=self.producer,
        )

        status, body = self._post("/api/confirm", {
            "proposal_id": p_drums.id,
            "expected_revision": 0,
            "reason": "Attempting unauthorized scope",
        })
        self.assertEqual(status, 403)
        self.assertFalse(body["ok"])
        self.assertIn("UNAUTHORIZED", body["error"]["code"])


    def test_api_upload_endpoint_ingests_and_analyzes_audio(self):
        import base64
        wav_data = make_clean_sine_wav(440.0, 0.25, 44100)
        b64_str = base64.b64encode(wav_data).decode("utf-8")
        status, body = self._post("/api/upload", {"wav_base64": b64_str, "scope": "melody", "tempo": 120})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("proposal", body)
        self.assertEqual(body["proposal"]["scope"], "melody")
        self.assertIn("report", body)

    def test_failed_upload_does_not_retain_partial_evidence(self):
        import base64
        before = (len(self.ws._evidence), len(self.ws._observations), len(self.ws._proposals))
        status, body = self._post("/api/upload", {
            "wav_base64": base64.b64encode(b"not a WAV").decode("ascii"),
            "scope": "melody",
        })
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])
        self.assertEqual(
            (len(self.ws._evidence), len(self.ws._observations), len(self.ws._proposals)), before
        )

    def test_failed_alternative_save_does_not_retain_partial_observation(self):
        from unittest.mock import Mock
        self._post("/api/confirm", {"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "Base melody"})
        before = (len(self.ws._observations), len(self.ws._proposals))
        self.server.persist = Mock(side_effect=OSError("save failed"))
        status, body = self._post("/api/propose_alternative", {
            "source_scope": "melody",
            "target_scope": "harmony",
            "alt_type": "HARMONY_THIRD_ABOVE",
            "requested_by": "composer-joel",
            "reason": "Preview only",
        })
        self.assertEqual(status, 500)
        self.assertFalse(body["ok"])
        self.assertEqual((len(self.ws._observations), len(self.ws._proposals)), before)



    def test_preview_server_auto_persists_to_sqlite_project_on_disk(self):
        from pathlib import Path
        import tempfile
        from reference.core import create_workspace, Grant
        from reference.storage.sqlite_store import SqliteStorageEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            proj_path = Path(tmpdir) / "test_persist.musicmcp"
            ws_disk, (sess_disk,) = create_workspace([Grant("composer-joel", {"melody"}, {"confirm", "correct", "restore"})])

            # Create evidence and proposal in project
            ev = ws_disk.add_evidence(b"dummy", "audio/wav")
            obs = ws_disk.observe(ev.id, "Test obs", producer=self.producer)
            prop = ws_disk.propose(obs.id, "melody", (Note("C4", Fraction(1)),), mode="intended", uncertainty="HIGH", origin="interpreted", producer=self.producer)
            SqliteStorageEngine.save_workspace(ws_disk, proj_path)

            # Start preview server bound to this sqlite project file
            srv = PreviewServer(ws_disk, (sess_disk,), port=0, project_path=proj_path)
            srv.start(background=True)
            try:
                # POST /api/confirm
                req = urllib.request.Request(
                    f"{srv.url}/api/confirm",
                    data=json.dumps({"proposal_id": prop.id, "expected_revision": 0, "reason": "Disk test"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(data["ok"])
            finally:
                srv.stop()

            # Verify persisted state on disk
            ws_reloaded, _ = SqliteStorageEngine.load_workspace(proj_path)
            snap = ws_reloaded.snapshot()
            self.assertEqual(snap.revision, 1)
            self.assertEqual(len(snap.phrases), 1)
            self.assertEqual(snap.phrases[0].notes[0].pitch, "C4")

    def test_security_boundary_rejects_foreign_origin(self):
        url = f"{self.server.url}/api/confirm"
        raw = json.dumps({"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "Attack"}).encode("utf-8")
        req = urllib.request.Request(url, data=raw, headers={
            "Content-Type": "application/json",
            "Origin": "http://evil-attacker.com",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as err:
            status = err.code
            body = json.loads(err.read().decode("utf-8"))
            self.assertEqual(status, 403)
            self.assertIn("SECURITY_VIOLATION", body["error"]["code"])
        self.assertEqual(status, 403)

    def test_security_boundary_rejects_foreign_host(self):
        url = f"{self.server.url}/api/confirm"
        raw = json.dumps({"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "Attack"}).encode("utf-8")
        req = urllib.request.Request(url, data=raw, headers={
            "Content-Type": "application/json",
            "Host": "evil-attacker.com",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as err:
            status = err.code
            body = json.loads(err.read().decode("utf-8"))
            self.assertEqual(status, 403)
            self.assertIn("SECURITY_VIOLATION", body["error"]["code"])
        self.assertEqual(status, 403)

    def test_security_boundary_rejects_untyped_or_text_plain_post(self):
        url = f"{self.server.url}/api/confirm"
        raw = json.dumps({"proposal_id": self.proposal.id, "expected_revision": 0, "reason": "Attack"}).encode("utf-8")
        req = urllib.request.Request(url, data=raw, headers={
            "Content-Type": "text/plain",
        })
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as err:
            status = err.code
            body = json.loads(err.read().decode("utf-8"))
            self.assertEqual(status, 403)
            self.assertIn("SECURITY_VIOLATION", body["error"]["code"])
        self.assertEqual(status, 403)

    def test_persistence_failure_rolls_back_memory_to_preserve_disk_consistency(self):
        from unittest.mock import patch
        import tempfile
        from pathlib import Path
        from reference.core import create_workspace, Grant
        from reference.storage.sqlite_store import SqliteStorageEngine, StorageError

        with tempfile.TemporaryDirectory() as tmpdir:
            proj_path = Path(tmpdir) / "fail_test.musicmcp"
            ws, (sess,) = create_workspace([Grant("composer-joel", {"melody"}, {"confirm", "correct", "restore"})])
            ev = ws.add_evidence(b"riff", "audio/wav")
            obs = ws.observe(ev.id, "take", producer=self.producer)
            prop = ws.propose(obs.id, "melody", (Note("C4", Fraction(1)),), mode="intended", uncertainty="HIGH", origin="interpreted", producer=self.producer)
            SqliteStorageEngine.save_workspace(ws, proj_path)

            srv = PreviewServer(ws, (sess,), port=0, project_path=proj_path)
            srv.start(background=True)
            try:
                # Mock SqliteStorageEngine.save_workspace to simulate disk write failure
                with patch("reference.storage.sqlite_store.SqliteStorageEngine.save_workspace", side_effect=IOError("Simulated disk write failure")):
                    url = f"{srv.url}/api/confirm"
                    raw = json.dumps({"proposal_id": prop.id, "expected_revision": 0, "reason": "Fail test"}).encode("utf-8")
                    req = urllib.request.Request(url, data=raw, headers={"Content-Type": "application/json"})
                    try:
                        with urllib.request.urlopen(req) as resp:
                            status = resp.status
                    except urllib.error.HTTPError as err:
                        status = err.code

                    self.assertEqual(status, 500)
                    # Crucial Invariant: workspace memory MUST NOT be left ahead of disk!
                    self.assertEqual(srv.workspace.snapshot().revision, 0)
                    self.assertEqual(len(srv.workspace.snapshot().history), 0)
            finally:
                srv.stop()


    def test_preview_html_escapes_model_controlled_proposal_fields(self):
        # Invariant: untrusted model/proposal text must NOT be interpolated as unescaped HTML
        status, body = self._get("/")
        self.assertEqual(status, 200)
        html = body if isinstance(body, str) else ""
        self.assertIn("function escapeHtml", html)
        self.assertIn("escapeHtml(prop.scope)", html)
        self.assertIn("escapeHtml(p.scope)", html)
        self.assertIn("escapeHtml(rev.scope)", html)
        self.assertNotIn("Scope: ${prop.scope}", html)

    def test_preview_html_preserves_correction_drafts_across_polling(self):
        # Invariant: Polling refresh must NOT wipe active user draft or force-reset selected proposal
        status, body = self._get("/")
        self.assertEqual(status, 200)
        html = body if isinstance(body, str) else ""
        self.assertIn("currentSelectedProposalId", html)
        self.assertIn("isDraftDirty", html)
        self.assertIn("fromPoll", html)
        self.assertNotIn("if (cachedProposals.length > 0) {\n          selectProposal(cachedProposals[0].id);\n        }", html)


class TestPreviewRecovery(unittest.TestCase):
    """Recovery checks use mocked handlers and never start servers or write files."""

    def setUp(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from reference.preview.server import PreviewRequestHandler
        self.policy = lambda candidate: True
        self.validator = lambda candidate: True
        self.grant = Grant("restricted-host", {"melody"}, {"confirm"})
        self.ws, self.sessions = create_workspace([self.grant], policy=self.policy, validator=self.validator)
        self.preview = PreviewServer(self.ws, self.sessions, project_path="unused-review.musicmcp")
        self.handler = object.__new__(PreviewRequestHandler)
        self.handler.server = SimpleNamespace(preview=self.preview)
        self.handler.send_json = Mock()
        self.preview.persist = Mock(side_effect=OSError("write failed"))
        exists = patch("pathlib.Path.exists", return_value=True)
        exists.start()
        self.addCleanup(exists.stop)

    def test_recovery_retains_host_policy_validator_and_grant_override(self):
        from unittest.mock import patch
        from reference.storage.sqlite_store import SqliteStorageEngine
        recovered, sessions = create_workspace([self.grant], policy=self.policy, validator=self.validator)
        with patch.object(SqliteStorageEngine, "load_workspace", return_value=(recovered, sessions)) as load:
            self.handler._execute_mutation(lambda: self.ws.add_evidence(b"pending", "audio/wav"), lambda _: {"ok": True})
        self.assertEqual(load.call_args.kwargs["grants"], (self.grant,))
        self.assertIs(load.call_args.kwargs["policy"], self.policy)
        self.assertIs(load.call_args.kwargs["validator"], self.validator)
        error = self.handler.send_json.call_args.args[0]["error"]
        self.assertTrue(error["state_safe"])
        self.assertEqual(error["recovery"], "reloaded")

    def test_failed_reconciliation_reports_unknown_and_blocks_following_writes(self):
        from unittest.mock import Mock, patch
        from reference.storage.sqlite_store import SqliteStorageEngine
        before = self.ws.snapshot()
        with patch.object(SqliteStorageEngine, "load_workspace", side_effect=OSError("cannot read")):
            self.handler._execute_mutation(lambda: self.ws.add_evidence(b"pending", "audio/wav"), lambda _: {"ok": True})
        self.assertEqual(self.ws.snapshot(), before)
        self.assertEqual(self.ws._evidence, {})
        error = self.handler.send_json.call_args.args[0]["error"]
        self.assertIsNone(error["state_safe"])
        self.assertIsNone(error["authoritative_state_modified"])
        self.assertEqual(error["recovery"], "failed")
        following = Mock()
        self.handler._execute_mutation(following, lambda _: {"ok": True})
        following.assert_not_called()
        self.assertIn("RECOVERY_REQUIRED", self.handler.send_json.call_args.args[0]["error"]["code"])

    def test_mutation_failure_removes_partial_ingestion_without_persisting(self):
        def partial_ingestion():
            self.ws.add_evidence(b"partial", "audio/wav")
            raise ValueError("analysis failed")
        self.handler._execute_mutation(partial_ingestion, lambda _: {"ok": True})
        self.assertEqual(self.ws._evidence, {})
        self.preview.persist.assert_not_called()

    def test_recovery_does_not_add_sessions_held_outside_preview(self):
        from unittest.mock import patch
        from reference.storage.sqlite_store import SqliteStorageEngine
        extra = Grant("other-host", {"harmony"}, {"correct"})
        ws, sessions = create_workspace([self.grant, extra])
        self.preview.workspace = ws
        self.preview.sessions = sessions[:1]
        recovered, recovered_sessions = create_workspace([self.grant])
        with patch.object(SqliteStorageEngine, "load_workspace", return_value=(recovered, recovered_sessions)) as load:
            self.handler._execute_mutation(lambda: None, lambda _: {"ok": True})
        self.assertEqual(load.call_args.kwargs["grants"], (self.grant,))

    def test_requests_cannot_interleave_mutation_and_persistence(self):
        from threading import Event, Thread
        from types import SimpleNamespace
        from unittest.mock import Mock
        from reference.preview.server import PreviewRequestHandler
        entered_persist, release_persist, second_mutation = Event(), Event(), Event()
        other = object.__new__(PreviewRequestHandler)
        other.server = SimpleNamespace(preview=self.preview)
        other.send_json = Mock()
        def persist():
            entered_persist.set()
            if not release_persist.wait(2):
                raise RuntimeError("test barrier timed out")
        self.preview.persist = persist
        first = Thread(target=lambda: self.handler._execute_mutation(lambda: None, lambda _: {"ok": True}))
        second = Thread(target=lambda: other._execute_mutation(second_mutation.set, lambda _: {"ok": True}))
        first.start()
        try:
            self.assertTrue(entered_persist.wait(2))
            second.start()
            self.assertFalse(second_mutation.wait(0.1), "Another request mutated while persistence was pending")
        finally:
            release_persist.set()
            first.join(2)
            if second.ident is not None:
                second.join(2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_mutation.is_set())


class TestCorrectionEditor(unittest.TestCase):
    def test_editor_uses_confirmed_notes_and_preserves_new_drafts(self):
        import shutil
        import subprocess
        from pathlib import Path
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is required for the browser-script regression")
        html = Path(__file__).parents[1] / "reference/preview/static/index.html"
        script = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const elements = new Map();
function el(id) {
  if (id.startsWith('canvas-')) return canvas;
  if (!elements.has(id)) elements.set(id, {value:'',textContent:'',innerText:'',innerHTML:'',
    classList:{add(){},remove(){}},addEventListener(){}});
  return elements.get(id);
}
const drawnY = [];
const drawingContext = {clearRect(){},beginPath(){},moveTo(x,y){drawnY.push(y)},lineTo(x,y){drawnY.push(y)},
  stroke(){},fill(){},save(){},restore(){},translate(x,y){drawnY.push(y)},rotate(){},ellipse(){},fillText(t,x,y){drawnY.push(y)}};
const canvas = {width:600,height:120,style:{},getContext(){return drawingContext}};
let project = {ok:true,revision:0,locks:[],phrases:[],history:[]};
const proposal = {id:'p1',scope:'melody',notes:[{pitch:'C4',duration:'1'}],origin:'interpreted'};
let proposals = [proposal];
const context = {console,drawnY,canvas,document:{getElementById:el,querySelectorAll:()=>[],activeElement:null},
  window:{addEventListener(){}},setTimeout(){},clearTimeout(){},setInterval(){},
  fetch:async (url, options)=>({json:async()=>{
    if(url==='/api/project') return project;
    if(url==='/api/proposals') return {ok:true,proposals};
    if(url==='/api/correct') {
      const rev = {number:2,scope:'melody',proposal_id:'p1',notes:[{pitch:'E4',duration:'2'}],actor:'qa',reason:'qa'};
      project = {...project,revision:2,phrases:[rev],history:[rev]};
      return {ok:true,revision:rev};
    }
    return {ok:false};
  }})};
vm.createContext(context);
const source = fs.readFileSync(process.argv[1],'utf8').split('<script>')[1].split('</script>')[0].replace(/\r\n/g,'\n');
vm.runInContext(source.replace('    refreshAll();\n    setInterval(refreshAll, 5000);',''),context);
context.assert=assert;
(async()=>{
await vm.runInContext(`(async()=>{
  showToast=()=>{};
  await fetchProject(); await fetchProposals();
  const input=document.getElementById('correct-notes-input');
  assert.equal(input.value,'C4 1');
  assert.equal(document.getElementById('prop-count-badge').innerText,'1 Pending · 0 Reviewed');
  input.value='E4 2'; isDraftDirty=true;
  await handleCorrect();
})()`,context);
await new Promise(resolve=>setImmediate(resolve));
await vm.runInContext(`(async()=>{
  const input=document.getElementById('correct-notes-input');
  assert.equal(input.value,'E4 2','save must not reload original proposal');
  assert.equal(document.getElementById('prop-count-badge').innerText,'0 Pending · 1 Reviewed');
  assert.match(document.getElementById('proposals-container').innerHTML,/Reviewed/);
  assert.match(document.getElementById('correction-source').textContent,/revision 2/i);
  await fetchProposals(); selectProposal('p1');
  assert.equal(input.value,'E4 2','reselection must use confirmed notes');
  input.value='G4 3'; isDraftDirty=true;
  await refreshAll(); selectProposal('p1');
  assert.equal(input.value,'G4 3','poll and same-card click must preserve draft');
  isDraftDirty=false; currentSelectedProposalId=null;
  await refreshAll();
  assert.equal(input.value,'E4 2','fresh selection must reload confirmed notes');
  cachedProposals.push({id:'p2',scope:'melody',notes:[{pitch:'A4',duration:'1'}]});
  selectProposal('p2');
  assert.equal(input.value,'A4 1','different proposal must retain its own interpretation');
  assert.match(document.getElementById('correction-source').textContent,/original proposal/i);
})()`,context);
// A different current phrase must not make previously reviewed proposals pending again.
project = {...project,phrases:[]};
proposals = [proposal,{id:'p2',scope:'melody',notes:[{pitch:'A4',duration:'1'}],origin:'generated'}];
await vm.runInContext(`(async()=>{
  await refreshAll();
  drawnY.length=0; canvas.height=120; canvas.style.height='130px';
  drawStaff(canvas,[{pitch:'C#8',duration_float:1},{pitch:'C3',duration_float:1}]);
  assert.ok(drawnY.every(y=>y>=0 && y<=canvas.height),'staff drawing clipped: ' + drawnY.filter(y=>y<0 || y>canvas.height));
  assert.ok(canvas.height>120,'extreme pitches must expand the backing canvas');
  assert.equal(canvas.style.height,canvas.height+'px','visible canvas height must match backing bitmap');
  assert.equal(document.getElementById('prop-count-badge').innerText,'1 Pending · 1 Reviewed');
  assert.equal(cachedProposals.length,2,'reviewed provenance must remain accessible');
  assert.match(document.getElementById('proposals-container').innerHTML,/card-p1/);
  assert.match(document.getElementById('proposals-container').innerHTML,/card-p2/);
})()`,context);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run([node, "-e", script, str(html)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
