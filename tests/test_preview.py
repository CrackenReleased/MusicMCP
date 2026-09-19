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
            with urllib.request.urlopen(req, timeout=3.0) as resp:
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
            with urllib.request.urlopen(req, timeout=3.0) as resp:
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


if __name__ == "__main__":
    unittest.main()
