"""Visualizer Preview Server and Local Human Review Engine for Music MCP.

Adheres strictly to Python 3.11+ standard library only: http.server, json, urllib, socket, threading.
Binds strictly to loopback (127.0.0.1) enforcing local security boundaries.
Provides interactive inspection of 10-band acoustic spectrum, anomalies, phrases, and authority mutations.
"""
from dataclasses import asdict, is_dataclass
from fractions import Fraction
import http.server
import json
from pathlib import Path
import re
import socket
import socketserver
import threading
import traceback
from typing import Any, Sequence
from urllib.parse import parse_qs, urlparse

from reference.alternatives import (
    AlternativeGenerator,
    AlternativeRequest,
    AlternativeType,
)
from reference.cli import parse_notes_string
from reference.core import (
    AuthoritySession,
    Diagnostic,
    LockConstraint,
    MusicError,
    Note,
    Producer,
    Proposal,
    Revision,
    Workspace,
    phrase,
)
from reference.spectrum import (
    AcousticResonance,
    BAND_LIMITS,
    HarmonicPeak,
    SpectralAnomaly,
    SpectrumReport,
    watch_audio_bytes,
)

STATIC_DIR = Path(__file__).parent / "static"
PREVIEW_PRODUCER = Producer("host-visualizer-preview", "0.1.01")


def serialize_music_obj(obj: Any) -> Any:
    """Helper to cleanly serialize core domain dataclasses with Fractions to JSON."""
    if isinstance(obj, Fraction):
        return str(obj)
    if isinstance(obj, Note):
        return {
            "pitch": obj.pitch,
            "duration": str(obj.duration),
            "duration_float": float(obj.duration),
        }
    if isinstance(obj, LockConstraint):
        return {
            "scope": obj.scope,
            "origin": obj.origin,
            "reason": obj.reason,
        }
    if isinstance(obj, Revision):
        return {
            "number": obj.number,
            "parent": obj.parent,
            "actor": obj.actor,
            "operation": obj.operation,
            "scope": obj.scope,
            "notes": [serialize_music_obj(n) for n in obj.notes],
            "proposal_id": obj.proposal_id,
            "observation_id": obj.observation_id,
            "evidence_id": obj.evidence_id,
            "origin": obj.origin,
            "reason": obj.reason,
            "restored_from": obj.restored_from,
        }
    if isinstance(obj, Proposal):
        return {
            "id": obj.id,
            "observation_id": obj.observation_id,
            "evidence_id": obj.evidence_id,
            "scope": obj.scope,
            "notes": [serialize_music_obj(n) for n in obj.notes],
            "mode": obj.mode,
            "uncertainty": obj.uncertainty,
            "origin": obj.origin,
            "producer": {"identity": obj.producer.identity, "version": obj.producer.version},
        }
    if isinstance(obj, SpectralAnomaly):
        return {
            "kind": obj.kind,
            "severity": obj.severity,
            "magnitude": round(obj.magnitude, 4),
            "frequency_hz": round(obj.frequency_hz, 2) if obj.frequency_hz is not None else None,
            "description": obj.description,
        }
    if isinstance(obj, HarmonicPeak):
        return {
            "harmonic_number": obj.harmonic_number,
            "frequency_hz": round(obj.frequency_hz, 1),
            "magnitude": round(obj.magnitude, 5),
            "relative_db": round(obj.relative_db, 1),
        }
    if isinstance(obj, AcousticResonance):
        return {
            "fundamental_hz": round(obj.fundamental_hz, 1) if obj.fundamental_hz is not None else None,
            "harmonics": [serialize_music_obj(h) for h in obj.harmonics],
            "sympathetic_octaves_present": obj.sympathetic_octaves_present,
            "natural_harmonics_present": obj.natural_harmonics_present,
            "room_resonances": [round(r, 1) for r in obj.room_resonances],
            "description": obj.description,
        }
    if isinstance(obj, SpectrumReport):
        return {
            "duration_seconds": round(obj.duration_seconds, 3),
            "sample_rate": obj.sample_rate,
            "nyquist_hz": round(obj.nyquist_hz, 1),
            "peak_amplitude": round(obj.peak_amplitude, 4),
            "rms_amplitude": round(obj.rms_amplitude, 4),
            "dc_offset": round(obj.dc_offset, 6),
            "snr_db": round(obj.snr_db, 2),
            "band_energies": {k: round(v, 6) for k, v in obj.band_energies.items()},
            "anomalies": [serialize_music_obj(a) for a in obj.anomalies],
            "clean_musical_signal": obj.clean_musical_signal,
            "summary": obj.summary,
            "resonance": serialize_music_obj(obj.resonance) if obj.resonance else None,
        }
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, (tuple, list, set, frozenset)):
        return [serialize_music_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: serialize_music_obj(v) for k, v in obj.items()}
    return obj


class PreviewRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for Music MCP Visualizer and Local Authority Review."""

    @property
    def preview(self) -> "PreviewServer":
        return self.server.preview  # type: ignore

    def log_message(self, format, *args):
        pass

    def _check_security(self) -> bool:
        """Enforce strict localhost security boundary, host validation, and origin checks."""
        client_ip = self.client_address[0]
        if client_ip not in ("127.0.0.1", "::1", "localhost"):
            self.send_error_json(
                code="SECURITY_VIOLATION",
                message=f"Access denied from non-local client address '{client_ip}'.",
                action="Access the visualizer exclusively from the local host machine.",
                operation="security_check",
                scope="preview",
                status=403,
            )
            return False

        # Host header validation: strictly localhost / 127.0.0.1 / ::1
        host_header = self.headers.get("Host", "")
        host_name = host_header.split(":")[0].strip("[]")
        if not host_name or host_name not in ("127.0.0.1", "localhost", "::1"):
            self.send_error_json(
                code="SECURITY_VIOLATION",
                message=f"Access denied: invalid or foreign Host header '{host_header}'.",
                action="Access the visualizer exclusively using localhost or 127.0.0.1.",
                operation="security_check",
                scope="preview",
                status=403,
            )
            return False

        # Origin header validation: reject any non-local cross-origin request
        origin = self.headers.get("Origin")
        if origin:
            parsed_origin = urlparse(origin)
            origin_host = (parsed_origin.hostname or "").strip("[]")
            if origin_host not in ("127.0.0.1", "localhost", "::1"):
                self.send_error_json(
                    code="SECURITY_VIOLATION",
                    message=f"Access denied: foreign Origin '{origin}' is forbidden.",
                    action="Submit requests exclusively from the local visualizer deck.",
                    operation="security_check",
                    scope="preview",
                    status=403,
                )
                return False

        # Sec-Fetch-Site validation: cross-site requests are strictly rejected
        sec_fetch_site = self.headers.get("Sec-Fetch-Site")
        if sec_fetch_site == "cross-site":
            self.send_error_json(
                code="SECURITY_VIOLATION",
                message="Access denied: cross-site requests are forbidden.",
                action="Access the visualizer exclusively from the local interface.",
                operation="security_check",
                scope="preview",
                status=403,
            )
            return False

        # Content-Type validation on mutating POST requests (prevents simple form CSRF)
        if self.command == "POST":
            content_type = self.headers.get("Content-Type", "").split(";")[0].strip()
            if content_type != "application/json":
                self.send_error_json(
                    code="SECURITY_VIOLATION",
                    message=f"Mutating requests require Content-Type 'application/json', got '{content_type}'.",
                    action="Submit requests with Content-Type: application/json.",
                    operation="security_check",
                    scope="preview",
                    status=403,
                )
                return False

        return True

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(
        self,
        code: str,
        message: str,
        action: str = "Review error details and retry.",
        operation: str = "preview",
        scope: str = "preview",
        status: int = 400,
        **state_details,
    ):
        data = {
            "ok": False,
            "error": {
                "code": f"MUSICMCP-PREVIEW-{code}" if not code.startswith("MUSICMCP-") else code,
                "message": message,
                "action": action,
                "operation": operation,
                "scope": scope,
                **state_details,
            },
        }
        self.send_json(data, status=status)

    def read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0 or length > 1024 * 1024:
                self.send_error_json("INVALID_REQUEST", "Expected JSON request body <= 1MB.", status=400)
                return None
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            self.send_error_json("INVALID_JSON", f"Failed to parse JSON body: {e}", status=400)
            return None

    def _execute_mutation(self, mutation_fn, success_data_fn):
        """Serialize the complete mutation, publication, and recovery boundary."""
        with self.preview._mutation_lock:
            if self.preview._recovery_required:
                self.send_error_json("RECOVERY_REQUIRED", "Writes are blocked because disk recovery could not be verified.",
                                     action="Reopen the project after resolving the storage failure.", status=503,
                                     state_safe=None, authoritative_state_modified=None, recovery="failed")
                return
            self._execute_mutation_locked(mutation_fn, success_data_fn)

    def _execute_mutation_locked(self, mutation_fn, success_data_fn):
        ws = self.preview.workspace
        with ws._lock:
            prev_state = ws._state
            prev_evidence = dict(ws._evidence)
            prev_observations = dict(ws._observations)
            prev_proposals = dict(ws._proposals)
            # Restore only authority actually held by this host, not other sessions.
            grants = tuple(ws._grants[session._token] for session in self.preview.sessions)

        def restore_memory():
            with ws._lock:
                ws._state = prev_state
                ws._evidence = prev_evidence
                ws._observations = prev_observations
                ws._proposals = prev_proposals

        try:
            result = mutation_fn()
        except MusicError as err:
            restore_memory()
            status = 409 if "REVISION_CONFLICT" in err.diagnostic.code else 400
            self.send_error_json(err.diagnostic.code, err.diagnostic.message, err.diagnostic.next_action,
                                 err.diagnostic.operation, err.diagnostic.scope, status=status)
            return
        except Exception as e:
            restore_memory()
            self.send_error_json("TRANSACTION_FAILED", f"Mutation failed: {e}", status=400)
            return

        # Attempt persistence
        try:
            self.preview.persist()
        except Exception as e:
            restore_memory()
            recovered = False
            if self.preview.project_path:
                try:
                    from reference.storage.sqlite_store import SqliteStorageEngine
                    reloaded_ws, reloaded_sessions = SqliteStorageEngine.load_workspace(
                        self.preview.project_path, grants=grants, policy=ws._policy, validator=ws._validator)
                    self.preview.workspace = reloaded_ws
                    self.preview.sessions = reloaded_sessions
                    recovered = True
                except Exception:
                    self.preview._recovery_required = True
            else:
                self.preview._recovery_required = True

            self.send_error_json(
                code="PERSISTENCE_FAILED",
                message=(f"Persistence failed: {e}. " +
                         ("Reloaded verified disk state; review it before making another change." if recovered else
                          "Pre-mutation memory restored, but disk state could not be verified. Further writes are blocked.")),
                action="Review the recovered project." if recovered else "Resolve the storage failure and reopen the project.",
                operation="persist",
                scope="storage",
                status=500,
                state_safe=True if recovered else None,
                authoritative_state_modified=(self.preview.workspace.snapshot() != prev_state) if recovered else None,
                recovery="reloaded" if recovered else "failed",
                rollback="memory_restored",
                transaction="reconciled_from_disk" if recovered else "unknown",
            )
            return

        self.send_json(success_data_fn(result))

    def find_session_for(self, scope: str, operation: str) -> AuthoritySession | None:
        """Finds a host authority session possessing the required scope and operation."""
        for sess in self.preview.sessions:
            grant = self.preview.workspace._grants.get(sess._token)
            if grant and scope in grant.scopes and operation in grant.operations:
                return sess
        return None

    def do_GET(self):
        try:
            with self.preview._mutation_lock:
                self._handle_GET()
        except Exception as e:
            traceback.print_exc()
            self.send_error_json("INTERNAL_ERROR", f"Internal server error: {e}", status=500)

    def _handle_GET(self):
        if not self._check_security():
            return

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                html = index_path.read_bytes()
            else:
                html = b"<html><body><h1>Music MCP Visualizer</h1><p>Static index missing.</p></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if path == "/api/project":
            snap = self.preview.workspace.snapshot()
            data = {
                "ok": True,
                "revision": snap.revision,
                "phrases": [serialize_music_obj(p) for p in snap.phrases],
                "history": [serialize_music_obj(h) for h in snap.history],
                "locks": [serialize_music_obj(c) for c in self.preview.workspace._constraints],
                "capabilities": dict(self.preview.workspace.capabilities()),
            }
            self.send_json(data)
            return

        if path == "/api/proposals":
            scope_filter = query.get("scope", [None])[0]
            with self.preview.workspace._lock:
                props = list(self.preview.workspace._proposals.values())
            if scope_filter:
                props = [p for p in props if p.scope == scope_filter]
            self.send_json({"ok": True, "proposals": [serialize_music_obj(p) for p in props]})
            return

        if path == "/api/spectrum":
            evidence_id = query.get("evidence_id", [None])[0]
            if not evidence_id:
                self.send_error_json("MISSING_PARAMETER", "Query parameter 'evidence_id' is required.", status=400)
                return
            try:
                ev = self.preview.workspace.evidence(evidence_id)
            except MusicError as err:
                self.send_error_json(err.diagnostic.code, err.diagnostic.message, err.diagnostic.next_action, status=404)
                return

            try:
                report = watch_audio_bytes(ev.data)
            except MusicError as err:
                self.send_error_json(err.diagnostic.code, err.diagnostic.message, err.diagnostic.next_action, status=400)
                return
            except Exception as e:
                self.send_error_json("SPECTRUM_FAILED", f"Spectrum inspection failed: {e}", status=400)
                return

            self.send_json({"ok": True, "evidence_id": evidence_id, "report": serialize_music_obj(report)})
            return

        if path == "/api/alternatives":
            scope = query.get("scope", ["melody"])[0]
            alt_type_str = query.get("type", ["HARMONY_THIRD_ABOVE"])[0]
            try:
                alt_type = AlternativeType[alt_type_str]
            except KeyError:
                self.send_error_json("INVALID_PARAMETER", f"Unknown alternative type '{alt_type_str}'.", status=400)
                return

            snap = self.preview.workspace.snapshot()
            target_phrase = next((p for p in snap.phrases if p.scope == scope), None)
            if not target_phrase:
                self.send_error_json("NOT_FOUND", f"No active phrase found for scope '{scope}'.", status=404)
                return

            req = AlternativeRequest(
                requested_by="preview-user",
                source_scope=scope,
                target_scope="preview_target",
                alt_type=alt_type,
                reason="Interactive visualizer preview generation",
            )
            alt = AlternativeGenerator.generate(req, target_phrase.notes)
            self.send_json({
                "ok": True,
                "source_scope": scope,
                "alt_type": alt_type_str,
                "notes": [serialize_music_obj(n) for n in alt.notes],
            })
            return

        self.send_error_json("ENDPOINT_NOT_FOUND", f"Unknown GET endpoint '{path}'.", status=404)

    def do_POST(self):
        try:
            # Acquire before resolving a workspace/session into a mutation closure.
            with self.preview._mutation_lock:
                self._handle_POST()
        except Exception as e:
            traceback.print_exc()
            self.send_error_json("INTERNAL_ERROR", f"Internal server error: {e}", status=500)

    def _handle_POST(self):
        if not self._check_security():
            return

        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()
        if body is None:
            return

        if path == "/api/confirm":
            prop_id = body.get("proposal_id")
            exp_rev = body.get("expected_revision")
            reason = body.get("reason", "Authorized confirmation via Visualizer Deck")

            if not prop_id or exp_rev is None:
                self.send_error_json("MISSING_FIELDS", "Fields 'proposal_id' and 'expected_revision' are required.")
                return

            try:
                proposal = self.preview.workspace.proposal(prop_id)
            except MusicError as err:
                self.send_error_json(err.diagnostic.code, err.diagnostic.message, err.diagnostic.next_action, status=404)
                return

            session = self.find_session_for(proposal.scope, "confirm")
            if not session:
                self.send_error_json(
                    "MUSICMCP-CORE-UNAUTHORIZED",
                    f"No host authority session possesses 'confirm' permission for scope '{proposal.scope}'.",
                    action="Assign appropriate host grant and retry.",
                    operation="confirm",
                    scope=proposal.scope,
                    status=403,
                )
                return

            self._execute_mutation(
                lambda: session.confirm(prop_id, exp_rev, reason),
                lambda rev: {"ok": True, "revision": serialize_music_obj(rev)}
            )
            return

        if path == "/api/correct":
            prop_id = body.get("proposal_id")
            notes_raw = body.get("notes")
            exp_rev = body.get("expected_revision")
            reason = body.get("reason", "Authorized correction via Visualizer Deck")

            if not prop_id or not notes_raw or exp_rev is None:
                self.send_error_json("MISSING_FIELDS", "Fields 'proposal_id' and 'notes' and 'expected_revision' are required.")
                return

            try:
                proposal = self.preview.workspace.proposal(prop_id)
            except MusicError as err:
                self.send_error_json(err.diagnostic.code, err.diagnostic.message, err.diagnostic.next_action, status=404)
                return

            session = self.find_session_for(proposal.scope, "correct")
            if not session:
                self.send_error_json(
                    "MUSICMCP-CORE-UNAUTHORIZED",
                    f"No host authority session possesses 'correct' permission for scope '{proposal.scope}'.",
                    action="Assign appropriate host grant and retry.",
                    operation="correct",
                    scope=proposal.scope,
                    status=403,
                )
                return

            try:
                if isinstance(notes_raw, str):
                    corrected_phrase = parse_notes_string(notes_raw)
                elif isinstance(notes_raw, list):
                    corrected_phrase = phrase([
                        Note(item["pitch"], Fraction(item["duration"])) for item in notes_raw
                    ])
                else:
                    self.send_error_json("VALIDATION_FAILED", "Notes must be a string or array of note objects.")
                    return
            except Exception as e:
                self.send_error_json("VALIDATION_FAILED", f"Failed to parse notes: {e}")
                return

            self._execute_mutation(
                lambda: session.correct(prop_id, corrected_phrase, exp_rev, reason),
                lambda rev: {"ok": True, "revision": serialize_music_obj(rev)}
            )
            return

        if path == "/api/restore":
            rev_num = body.get("revision_number")
            exp_rev = body.get("expected_revision")
            reason = body.get("reason", "Authorized restore via Visualizer Deck")

            if rev_num is None or exp_rev is None:
                self.send_error_json("MISSING_FIELDS", "Fields 'revision_number' and 'expected_revision' are required.")
                return

            snap = self.preview.workspace.snapshot()
            if rev_num <= 0 or rev_num > len(snap.history):
                self.send_error_json("NOT_FOUND", f"Historical revision {rev_num} does not exist.", status=404)
                return

            target_rev = snap.history[rev_num - 1]
            session = self.find_session_for(target_rev.scope, "restore")
            if not session:
                self.send_error_json(
                    "MUSICMCP-CORE-UNAUTHORIZED",
                    f"No host authority session possesses 'restore' permission for scope '{target_rev.scope}'.",
                    action="Assign appropriate host grant and retry.",
                    operation="restore",
                    scope=target_rev.scope,
                    status=403,
                )
                return

            self._execute_mutation(
                lambda: session.restore(rev_num, exp_rev, reason),
                lambda rev: {"ok": True, "revision": serialize_music_obj(rev)}
            )
            return

        if path == "/api/propose_alternative":
            source_scope = body.get("source_scope", "melody")
            target_scope = body.get("target_scope", "harmony")
            alt_type_str = body.get("alt_type", "HARMONY_THIRD_ABOVE")
            requested_by = body.get("requested_by", "preview-user")
            reason = body.get("reason", f"Requested {alt_type_str} alternative")

            try:
                alt_type = AlternativeType[alt_type_str]
            except KeyError:
                self.send_error_json("INVALID_PARAMETER", f"Unknown alternative type '{alt_type_str}'.")
                return

            snap = self.preview.workspace.snapshot()
            source_phrase = next((p for p in snap.phrases if p.scope == source_scope), None)
            if not source_phrase:
                self.send_error_json("NOT_FOUND", f"No active phrase found for scope '{source_scope}'.", status=404)
                return

            req = AlternativeRequest(
                requested_by=requested_by,
                source_scope=source_scope,
                target_scope=target_scope,
                alt_type=alt_type,
                reason=reason,
            )
            alt = AlternativeGenerator.generate(req, source_phrase.notes)

            def propose_alternative():
                obs = self.preview.workspace.observe(
                    source_phrase.evidence_id,
                    f"Generated alternative {alt_type.value} from scope '{source_scope}'",
                    producer=PREVIEW_PRODUCER,
                )
                return self.preview.workspace.propose(
                    obs.id,
                    scope=target_scope,
                    notes=alt.notes,
                    mode="intended",
                    uncertainty="LOW",
                    origin="generated",
                    producer=PREVIEW_PRODUCER,
                )

            self._execute_mutation(
                propose_alternative,
                lambda prop: {"ok": True, "proposal": serialize_music_obj(prop)}
            )
            return

        if path == "/api/upload":
            wav_base64 = body.get("wav_base64")
            scope = body.get("scope", "melody")
            tempo = int(body.get("tempo", 120))
            if not wav_base64:
                self.send_error_json("INVALID_INPUT", "Missing 'wav_base64' payload in upload request.", status=400)
                return

            import base64
            try:
                wav_bytes = base64.b64decode(wav_base64)
            except Exception as e:
                self.send_error_json("INVALID_BASE64", f"Failed to decode base64 WAV audio: {e}", status=400)
                return

            def ingest_upload():
                from reference.analyzer import ingest_and_propose
                evidence = self.preview.workspace.add_evidence(wav_bytes, "audio/wav")
                obs, prop = ingest_and_propose(self.preview.workspace, evidence.id, scope, tempo_bpm=tempo)
                report = watch_audio_bytes(wav_bytes)
                return prop, report, obs.id, evidence.id

            self._execute_mutation(
                ingest_upload,
                lambda res: {
                    "ok": True,
                    "evidence_id": res[3],
                    "observation_id": res[2],
                    "proposal": serialize_music_obj(res[0]),
                    "report": serialize_music_obj(res[1]),
                }
            )
            return

        self.send_error_json("ENDPOINT_NOT_FOUND", f"Unknown POST endpoint '{path}'.", status=404)


class ThreadedPreviewServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, preview_server: "PreviewServer"):
        super().__init__(server_address, RequestHandlerClass)
        self.preview = preview_server


class PreviewServer:
    """Local visualizer HTTP preview server holding host authority sessions."""

    def __init__(
        self,
        workspace: Workspace,
        sessions: Sequence[AuthoritySession] | AuthoritySession,
        host: str = "127.0.0.1",
        port: int = 8765,
        project_path: Path | str | None = None,
    ):
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(
                f"PreviewServer security boundary strictly forbids binding to external host '{host}'. "
                "Only localhost loopback interfaces are authorized."
            )
        self.workspace = workspace
        self._mutation_lock = threading.RLock()
        self._recovery_required = False
        self.sessions = (sessions,) if isinstance(sessions, AuthoritySession) else tuple(sessions)
        self.host = host
        self.requested_port = port
        self.project_path = Path(project_path) if project_path else None
        self.server: ThreadedPreviewServer | None = None
        self.thread: threading.Thread | None = None

    def persist(self):
        """Persists workspace mutations to SQLite storage if project_path is defined."""
        if self.project_path:
            from reference.storage.sqlite_store import SqliteStorageEngine
            SqliteStorageEngine.save_workspace(self.workspace, self.project_path)

    @property
    def port(self) -> int:
        if self.server:
            return self.server.server_address[1]
        return self.requested_port

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, background: bool = True):
        """Starts the local preview HTTP server."""
        self.server = ThreadedPreviewServer((self.host, self.requested_port), PreviewRequestHandler, self)

        if background:
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
        else:
            self.server.serve_forever()

    def stop(self):
        """Shuts down and terminates the preview HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.thread = None

    def __enter__(self):
        self.start(background=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

if __name__ == "__main__":
    import sys
    from reference.core import Grant, create_workspace
    project_arg = sys.argv[1] if len(sys.argv) > 1 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    if project_arg and Path(project_arg).exists():
        from reference.storage.sqlite_store import SqliteStorageEngine
        ws, sessions = SqliteStorageEngine.load_workspace(Path(project_arg))
        print(f"Loaded project: {project_arg}")
        server = PreviewServer(ws, sessions, port=port, project_path=Path(project_arg))
    else:
        ws, (sess,) = create_workspace([Grant("composer-joel", {"melody", "harmony", "bass"}, {"confirm", "correct", "restore"})])
        sessions = (sess,)
        print("Created in-memory session for composer-joel")
        server = PreviewServer(ws, sessions, port=port)
    print(f"=== Music MCP Visualizer Deck serving at http://127.0.0.1:{port} ===")
    print("Press Ctrl+C to stop.")
    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nShutting down preview server...")
        server.stop()
