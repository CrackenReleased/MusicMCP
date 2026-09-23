"""SQLite-backed durable evidence and revision storage for Music MCP.

Adheres strictly to Python 3.11+ standard library only: sqlite3, hashlib, json, fractions.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Callable
from uuid import uuid4

from reference.core import (
    UNCERTAINTY,
    AuthoritySession,
    Diagnostic,
    Evidence,
    Grant,
    LockConstraint,
    MusicError,
    Note,
    Observation,
    Producer,
    Proposal,
    Revision,
    Snapshot,
    Workspace,
    phrase,
)

SCHEMA_VERSION = "0.1.01"


@dataclass(frozen=True)
class StorageReport:
    path: str
    evidence_count: int
    observation_count: int
    proposal_count: int
    revision_count: int
    grant_count: int
    constraint_count: int
    sha256_verified: bool


@dataclass(frozen=True)
class IntegrityReport:
    valid: bool
    schema_version: str
    evidence_count: int
    revisions_count: int
    errors: tuple[str, ...]


class StorageError(MusicError):
    pass


def _storage_fail(code: str, message: str, action: str = "Check storage integrity and parameters."):
    raise StorageError(
        Diagnostic(
            code=f"MUSICMCP-STORAGE-{code}",
            message=message,
            next_action=action,
            operation="storage",
            scope="storage",
            trace_id="storage_trace",
            module="storage",
        )
    )


def note_to_dict(note: Note) -> dict:
    return {
        "pitch": note.pitch,
        "num": note.duration.numerator,
        "den": note.duration.denominator,
    }


def dict_to_note(d: dict) -> Note:
    if type(d) is not dict or set(d) != {"pitch", "num", "den"}:
        raise ValueError("Stored note fields must match the note schema exactly.")
    if type(d["num"]) is not int or type(d["den"]) is not int:
        raise ValueError("Stored note duration must use integer numerator and denominator.")
    return Note(pitch=d["pitch"], duration=Fraction(d["num"], d["den"]))


def notes_to_json(notes: tuple[Note, ...]) -> str:
    return json.dumps([note_to_dict(n) for n in notes], separators=(",", ":"))


def json_to_notes(s: str) -> tuple[Note, ...]:
    raw_list = json.loads(s)
    return phrase([dict_to_note(item) for item in raw_list])


def constraint_to_dict(c: LockConstraint) -> dict:
    return {"scope": c.scope, "origin": c.origin, "reason": c.reason}


def dict_to_constraint(d: dict) -> LockConstraint:
    if type(d) is not dict or set(d) != {"scope", "origin", "reason"}:
        raise ValueError("Stored constraint fields must match the constraint schema exactly.")
    return LockConstraint(scope=d["scope"], origin=d["origin"], reason=d["reason"])


class SqliteStorageEngine:
    """Provides atomic persistence and verification for Music MCP workspaces."""

    @staticmethod
    def _init_db(conn: sqlite3.Connection) -> None:
        # All DDL belongs to the caller's transaction; executescript would commit it.
        row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='grants'").fetchone()
        legacy_grants = bool(row and "id INTEGER PRIMARY KEY" not in row[0])
        if legacy_grants:
            conn.execute("ALTER TABLE grants RENAME TO grants_legacy")
        schema_sql = """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    media_type TEXT NOT NULL,
                    sha256 TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    evidence_id TEXT NOT NULL REFERENCES evidence(id),
                    description TEXT NOT NULL,
                    producer_identity TEXT NOT NULL,
                    producer_version TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL REFERENCES observations(id),
                    evidence_id TEXT NOT NULL REFERENCES evidence(id),
                    scope TEXT NOT NULL,
                    notes_json TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    uncertainty TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    producer_identity TEXT NOT NULL,
                    producer_version TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS revisions (
                    number INTEGER PRIMARY KEY,
                    parent INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    notes_json TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    observation_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    restored_from INTEGER,
                    constraints_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS grants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    scopes_json TEXT NOT NULL,
                    operations_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS constraints (
                    scope TEXT PRIMARY KEY,
                    origin TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
            """
        for statement in schema_sql.split(";"):
            if statement.strip():
                conn.execute(statement)
        if legacy_grants:
            conn.execute("INSERT INTO grants (actor, scopes_json, operations_json) SELECT actor, scopes_json, operations_json FROM grants_legacy")
            conn.execute("DROP TABLE grants_legacy")


    @classmethod
    def save_workspace(cls, workspace: Workspace, path: str | Path, force: bool = False) -> StorageReport:
        """Persists the complete state of a workspace into an atomic SQLite file."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with workspace._lock:
            return cls._save_locked(workspace, target_path, force)

    @classmethod
    def _save_locked(cls, workspace: Workspace, target_path: Path, force: bool) -> StorageReport:
        conn = sqlite3.connect(str(target_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_meta'").fetchone():
                row = conn.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
                if not force and (not row or row[0] != SCHEMA_VERSION):
                    _storage_fail("UNSUPPORTED_SCHEMA", "Target storage schema is unsupported; save rejected.")
            cls._init_db(conn)

            # Introspect internal workspace structures
            with workspace._lock:
                evidence_items = list(workspace._evidence.values())
                observation_items = list(workspace._observations.values())
                proposal_items = list(workspace._proposals.values())
                grant_items = list(workspace._grants.values())
                constraint_items = list(workspace._constraints)
                snapshot = workspace._state

            cur = conn.cursor()
            if force:
                conn.execute("DELETE FROM revisions;")
                conn.execute("DELETE FROM proposals;")
                conn.execute("DELETE FROM observations;")
                conn.execute("DELETE FROM evidence;")
                conn.execute("DELETE FROM constraints;")
                conn.execute("DELETE FROM grants;")
                conn.execute("DELETE FROM schema_meta;")
            else:
                # 1. State Token / Concurrent Modification Check
                cur.execute("SELECT value FROM schema_meta WHERE key = 'state_token';")
                row = cur.fetchone()
                current_db_token = row[0] if row else None

                loaded_token = getattr(workspace, "_storage_token", None)
                if current_db_token is not None:
                    if loaded_token is None:
                        _storage_fail(
                            "CONCURRENT_MODIFICATION",
                            "Target storage file already contains an active workspace. Use force=True to re-initialize or load the workspace first.",
                            action="Load the existing workspace before saving, or specify force=True."
                        )
                    elif current_db_token != loaded_token:
                        _storage_fail(
                            "CONCURRENT_MODIFICATION",
                            f"Database has been modified by another process (stored token {current_db_token} != loaded {loaded_token}).",
                            action="Reload workspace from disk before saving changes."
                        )

                # 2. Stored Revision Conflict Check
                cur.execute("SELECT number, parent, actor, operation, scope, notes_json, reason FROM revisions ORDER BY number ASC;")
                db_rev_rows = cur.fetchall()
                if db_rev_rows:
                    db_max_rev = db_rev_rows[-1][0]
                    if db_max_rev > len(snapshot.history):
                        _storage_fail(
                            "REVISION_CONFLICT",
                            f"Database contains revision {db_max_rev}, but workspace history only has {len(snapshot.history)}.",
                            action="Reload the latest project state from disk."
                        )
                    for r_row in db_rev_rows:
                        r_num = r_row[0]
                        hist_rev = snapshot.history[r_num - 1]
                        if hist_rev.number != r_num or hist_rev.parent != r_row[1] or hist_rev.scope != r_row[4] or hist_rev.reason != r_row[6]:
                            _storage_fail(
                                "REVISION_CONFLICT",
                                f"Revision {r_num} on disk ('{r_row[6]}') conflicts with workspace revision {r_num} ('{hist_rev.reason}').",
                                action="Resolve revision divergence before saving."
                            )

            now_iso = datetime.now(timezone.utc).isoformat()
            new_token = uuid4().hex

            # Update metadata
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("schema_version", SCHEMA_VERSION),
            )
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("format_id", "musicmcp-sqlite"),
            )
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("updated_at", now_iso),
            )
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("state_token", new_token),
            )

            # Save constraints
            conn.execute("DELETE FROM constraints;")
            for c in constraint_items:
                conn.execute(
                    "INSERT INTO constraints (scope, origin, reason) VALUES (?, ?, ?)",
                    (c.scope, c.origin, c.reason),
                )

            # Save grants
            conn.execute("DELETE FROM grants;")
            for g in grant_items:
                conn.execute(
                    "INSERT INTO grants (actor, scopes_json, operations_json) VALUES (?, ?, ?)",
                    (g.actor, json.dumps(sorted(g.scopes)), json.dumps(sorted(g.operations))),
                )

            # Save evidence
            for ev in evidence_items:
                digest = hashlib.sha256(ev.data).hexdigest()
                if digest != ev.sha256:
                    _storage_fail("EVIDENCE_CORRUPTED", f"Evidence {ev.id} SHA-256 mismatch before save.")
                conn.execute(
                    "INSERT OR REPLACE INTO evidence (id, data, media_type, sha256) VALUES (?, ?, ?, ?)",
                    (ev.id, ev.data, ev.media_type, digest),
                )

            # Save observations
            for obs in observation_items:
                conn.execute(
                    """INSERT OR REPLACE INTO observations
                       (id, evidence_id, description, producer_identity, producer_version)
                       VALUES (?, ?, ?, ?, ?)""",
                    (obs.id, obs.evidence_id, obs.description, obs.producer.identity, obs.producer.version),
                )

            # Save proposals
            for prop in proposal_items:
                conn.execute(
                    """INSERT OR REPLACE INTO proposals
                       (id, observation_id, evidence_id, scope, notes_json, mode, uncertainty, origin, producer_identity, producer_version)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        prop.id,
                        prop.observation_id,
                        prop.evidence_id,
                        prop.scope,
                        notes_to_json(prop.notes),
                        prop.mode,
                        prop.uncertainty,
                        prop.origin,
                        prop.producer.identity,
                        prop.producer.version,
                    ),
                )

            # Save revisions (from snapshot.history)
            for rev in snapshot.history:
                c_json = json.dumps([constraint_to_dict(c) for c in rev.constraints], separators=(",", ":"))
                conn.execute(
                    """INSERT OR REPLACE INTO revisions
                       (number, parent, actor, operation, scope, notes_json, proposal_id, observation_id, evidence_id, origin, reason, restored_from, constraints_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        rev.number,
                        rev.parent,
                        rev.actor,
                        rev.operation,
                        rev.scope,
                        notes_to_json(rev.notes),
                        rev.proposal_id,
                        rev.observation_id,
                        rev.evidence_id,
                        rev.origin,
                        rev.reason,
                        rev.restored_from,
                        c_json,
                    ),
                )

            conn.commit()
            workspace._storage_token = new_token
            return StorageReport(
                path=str(target_path),
                evidence_count=len(evidence_items),
                observation_count=len(observation_items),
                proposal_count=len(proposal_items),
                revision_count=len(snapshot.history),
                grant_count=len(grant_items),
                constraint_count=len(constraint_items),
                sha256_verified=True,
            )
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    @staticmethod
    def _record_errors(conn: sqlite3.Connection) -> list[str]:
        """Validate the stored causal chain before it becomes a live workspace."""
        errors: list[str] = []
        evidence_ids = {row[0] for row in conn.execute("SELECT id FROM evidence")}
        observations = {
            row[0]: row for row in conn.execute(
                "SELECT id, evidence_id, producer_identity, producer_version FROM observations"
            )
        }
        for obs_id, (_, evidence_id, identity, version) in observations.items():
            if evidence_id not in evidence_ids:
                errors.append(f"Observation {obs_id} references missing evidence {evidence_id}.")
            try:
                Producer(identity, version)
            except Exception:
                errors.append(f"Observation {obs_id} has invalid producer attribution.")

        proposals = {
            row[0]: row for row in conn.execute(
                "SELECT id, observation_id, evidence_id, scope, notes_json, mode, "
                "uncertainty, origin, producer_identity, producer_version FROM proposals"
            )
        }
        proposal_notes: dict[str, tuple[Note, ...]] = {}
        for prop_id, row in proposals.items():
            _, obs_id, evidence_id, scope, notes_json, mode, uncertainty, origin, identity, version = row
            observation = observations.get(obs_id)
            if observation is None:
                errors.append(f"Proposal {prop_id} references missing observation {obs_id}.")
            if evidence_id not in evidence_ids:
                errors.append(f"Proposal {prop_id} references missing evidence {evidence_id}.")
            if observation is not None and evidence_id != observation[1]:
                errors.append(f"Proposal {prop_id} evidence disagrees with observation {obs_id}.")
            if (type(scope) is not str or not scope.strip() or mode not in ("intended", "literal")
                    or uncertainty not in UNCERTAINTY or origin not in ("interpreted", "generated")):
                errors.append(f"Proposal {prop_id} has invalid scope, mode, uncertainty, or origin.")
            try:
                Producer(identity, version)
            except Exception:
                errors.append(f"Proposal {prop_id} has invalid producer attribution.")
            try:
                proposal_notes[prop_id] = json_to_notes(notes_json)
            except Exception:
                errors.append(f"Proposal {prop_id} has invalid notes_json.")

        revisions = {
            row[0]: row for row in conn.execute(
                "SELECT number, proposal_id, observation_id, evidence_id, scope, operation, "
                "notes_json, origin, restored_from, constraints_json, actor FROM revisions"
            )
        }
        revision_notes: dict[int, tuple[Note, ...]] = {}
        for number, row in revisions.items():
            _, prop_id, obs_id, evidence_id, scope, operation, notes_json, origin, restored_from, constraints_json, actor = row
            proposal = proposals.get(prop_id)
            if proposal is None:
                errors.append(f"Revision {number} references missing proposal {prop_id}.")
            else:
                if obs_id != proposal[1] or evidence_id != proposal[2] or scope != proposal[3]:
                    errors.append(f"Revision {number} lineage or scope disagrees with proposal {prop_id}.")
            if obs_id not in observations:
                errors.append(f"Revision {number} references missing observation {obs_id}.")
            if evidence_id not in evidence_ids:
                errors.append(f"Revision {number} references missing evidence {evidence_id}.")
            if type(actor) is not str or not actor.strip():
                errors.append(f"Revision {number} has no attributable actor.")
            try:
                revision_notes[number] = json_to_notes(notes_json)
            except Exception:
                errors.append(f"Revision {number} has invalid notes_json.")
            try:
                raw_constraints = json.loads(constraints_json)
                if type(raw_constraints) is not list:
                    raise ValueError("Expected a constraint list")
                tuple(dict_to_constraint(item) for item in raw_constraints)
            except Exception:
                errors.append(f"Revision {number} has invalid constraints_json.")

            if operation == "confirm":
                if proposal is not None and origin != proposal[7]:
                    errors.append(f"Revision {number} confirm origin disagrees with proposal {prop_id}.")
                if prop_id in proposal_notes and number in revision_notes and revision_notes[number] != proposal_notes[prop_id]:
                    errors.append(f"Revision {number} confirmed notes disagree with proposal {prop_id}.")
            elif operation == "correct":
                if origin != "human":
                    errors.append(f"Revision {number} correction lacks human origin.")
            elif operation != "restore":
                errors.append(f"Revision {number} has unsupported operation {operation}.")

            if operation == "restore":
                source = revisions.get(restored_from) if type(restored_from) is int else None
                if source is None or restored_from >= number:
                    errors.append(f"Revision {number} has invalid restored_from reference {restored_from}.")
                else:
                    if (source[1], source[2], source[3], source[4]) != (prop_id, obs_id, evidence_id, scope):
                        errors.append(f"Revision {number} restore lineage disagrees with revision {restored_from}.")
                    if origin != source[7]:
                        errors.append(f"Revision {number} restore origin disagrees with revision {restored_from}.")
                    if number in revision_notes and restored_from in revision_notes and revision_notes[number] != revision_notes[restored_from]:
                        errors.append(f"Revision {number} restored notes disagree with revision {restored_from}.")
            elif restored_from is not None:
                errors.append(f"Revision {number} has unexpected restored_from reference {restored_from}.")
        return errors

    @classmethod
    def load_workspace(
        cls,
        path: str | Path,
        grants: tuple[Grant, ...] | list[Grant] | None = None,
        policy: Callable | None = None,
        validator: Callable | None = None,
    ) -> tuple[Workspace, tuple[AuthoritySession, ...]]:
        """Loads and restores a Workspace and its AuthoritySessions from an atomic SQLite database file."""
        target_path = Path(path)
        if not target_path.exists():
            _storage_fail("NOT_FOUND", f"Storage file does not exist: {target_path}")

        conn = sqlite3.connect(str(target_path))
        try:
            conn.execute("BEGIN")
            cur = conn.cursor()

            # 0. Check schema version
            cur.execute("SELECT value FROM schema_meta WHERE key = 'schema_version';")
            row = cur.fetchone()
            schema_ver = row[0] if row else "missing"
            if schema_ver != SCHEMA_VERSION:
                _storage_fail("UNSUPPORTED_SCHEMA", f"Unsupported schema version: {schema_ver} (expected {SCHEMA_VERSION}).")
            record_errors = cls._record_errors(conn)
            if record_errors:
                _storage_fail(
                    "INTEGRITY_FAILURE",
                    f"Stored project records are inconsistent: {record_errors[0]}",
                    "Inspect the project file; restore a known-good copy rather than repairing provenance silently.",
                )

            # 1. Load constraints
            cur.execute("SELECT scope, origin, reason FROM constraints ORDER BY scope;")
            constraints = tuple(LockConstraint(scope=r[0], origin=r[1], reason=r[2]) for r in cur.fetchall())

            # 2. Load grants
            resolved_grants = []
            if grants is not None:
                resolved_grants = list(grants)
            else:
                cur.execute("SELECT actor, scopes_json, operations_json FROM grants ORDER BY rowid;")
                for row in cur.fetchall():
                    actor = row[0]
                    scopes = frozenset(json.loads(row[1]))
                    ops = frozenset(json.loads(row[2]))
                    resolved_grants.append(Grant(actor=actor, scopes=scopes, operations=ops))

            # Reconstruct workspace and sessions
            workspace = Workspace(constraints=constraints, policy=policy, validator=validator)
            sessions = []
            for grant in resolved_grants:
                token = object()
                workspace._grants[token] = grant
                sessions.append(AuthoritySession(workspace, token))

            # Attach storage state token to workspace
            cur.execute("SELECT value FROM schema_meta WHERE key = 'state_token';")
            st_row = cur.fetchone()
            workspace._storage_token = st_row[0] if st_row else None

            # 3. Load evidence
            cur.execute("SELECT id, data, media_type, sha256 FROM evidence;")
            evidence_map = {}
            for row in cur.fetchall():
                ev_id, data, media_type, recorded_sha = row[0], row[1], row[2], row[3]
                calculated_sha = hashlib.sha256(data).hexdigest()
                if calculated_sha != recorded_sha:
                    _storage_fail("EVIDENCE_CORRUPTED", f"Evidence {ev_id} failed SHA-256 integrity check on load.")
                evidence_map[ev_id] = Evidence(id=ev_id, data=data, media_type=media_type, sha256=recorded_sha)

            # 4. Load observations
            cur.execute("SELECT id, evidence_id, description, producer_identity, producer_version FROM observations;")
            obs_map = {}
            for row in cur.fetchall():
                obs_id, ev_id, desc, p_id, p_ver = row[0], row[1], row[2], row[3], row[4]
                obs_map[obs_id] = Observation(
                    id=obs_id,
                    evidence_id=ev_id,
                    description=desc,
                    producer=Producer(identity=p_id, version=p_ver),
                )

            # 5. Load proposals
            cur.execute("""SELECT id, observation_id, evidence_id, scope, notes_json,
                                  mode, uncertainty, origin, producer_identity, producer_version
                           FROM proposals;""")
            prop_map = {}
            for row in cur.fetchall():
                p_id, o_id, e_id, scope, n_json, mode, unc, origin, prod_id, prod_ver = (
                    row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]
                )
                prop_map[p_id] = Proposal(
                    id=p_id,
                    observation_id=o_id,
                    evidence_id=e_id,
                    scope=scope,
                    notes=json_to_notes(n_json),
                    mode=mode,
                    uncertainty=unc,
                    origin=origin,
                    producer=Producer(identity=prod_id, version=prod_ver),
                )

            # 6. Load revisions and rebuild snapshot history
            cur.execute("""SELECT number, parent, actor, operation, scope, notes_json,
                                  proposal_id, observation_id, evidence_id, origin, reason,
                                  restored_from, constraints_json
                           FROM revisions ORDER BY number ASC;""")
            history = []
            phrases_by_scope = {}
            expected_next = 1
            for row in cur.fetchall():
                num, parent, actor, op, scope, n_json, prop_id, o_id, ev_id, origin, reason, rest_from, c_json = (
                    row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]
                )
                if num != expected_next:
                    _storage_fail("REVISION_CHAIN_BROKEN", f"Expected revision {expected_next}, got {num}.")
                if parent != expected_next - 1:
                    _storage_fail("REVISION_CHAIN_BROKEN", f"Revision {num} parent mismatch: expected {expected_next - 1}, got {parent}.")
                expected_next += 1

                c_list = [dict_to_constraint(item) for item in json.loads(c_json)]
                rev = Revision(
                    number=num,
                    parent=parent,
                    actor=actor,
                    operation=op,
                    scope=scope,
                    notes=json_to_notes(n_json),
                    proposal_id=prop_id,
                    observation_id=o_id,
                    evidence_id=ev_id,
                    origin=origin,
                    reason=reason,
                    restored_from=rest_from,
                    constraints=tuple(c_list),
                )
                history.append(rev)
                phrases_by_scope[scope] = rev

            # Populate internal workspace structures
            with workspace._lock:
                workspace._evidence.update(evidence_map)
                workspace._observations.update(obs_map)
                workspace._proposals.update(prop_map)
                workspace._state = Snapshot(
                    revision=len(history),
                    phrases=tuple(phrases_by_scope.values()),
                    history=tuple(history),
                )

            return workspace, tuple(sessions)
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()

    @classmethod
    def verify_integrity(cls, path: str | Path) -> IntegrityReport:
        """Audits database schema, evidence SHA-256 hashes, and revision continuity."""
        target_path = Path(path)
        if not target_path.exists():
            return IntegrityReport(
                valid=False,
                schema_version="unknown",
                evidence_count=0,
                revisions_count=0,
                errors=(f"File not found: {target_path}",),
            )

        errors = []
        conn = sqlite3.connect(str(target_path))
        try:
            conn.execute("BEGIN")
            # Check SQLite integrity
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchall()
            if not res or res[0][0] != "ok":
                errors.append(f"SQLite PRAGMA integrity_check failed: {res}")

            # Check schema version
            cur.execute("SELECT value FROM schema_meta WHERE key = 'schema_version';")
            row = cur.fetchone()
            schema_ver = row[0] if row else "missing"
            if schema_ver != SCHEMA_VERSION:
                errors.append(f"Unsupported schema version: {schema_ver} (expected {SCHEMA_VERSION})")

            # Check evidence hashes
            cur.execute("SELECT id, data, sha256 FROM evidence;")
            ev_rows = cur.fetchall()
            for r in ev_rows:
                calc_sha = hashlib.sha256(r[1]).hexdigest()
                if calc_sha != r[2]:
                    errors.append(f"Evidence {r[0]} SHA-256 mismatch (recorded {r[2]}, computed {calc_sha})")

            # Check revision continuity
            cur.execute("SELECT number, parent FROM revisions ORDER BY number ASC;")
            rev_rows = cur.fetchall()
            prev_num = 0
            for r in rev_rows:
                if r[0] != prev_num + 1:
                    errors.append(f"Revision sequence jump: expected {prev_num + 1}, found {r[0]}")
                if r[1] != prev_num:
                    errors.append(f"Revision {r[0]} parent mismatch: expected {prev_num}, found {r[1]}")
                prev_num = r[0]

            errors.extend(cls._record_errors(conn))

            return IntegrityReport(
                valid=len(errors) == 0,
                schema_version=schema_ver,
                evidence_count=len(ev_rows),
                revisions_count=len(rev_rows),
                errors=tuple(errors),
            )
        finally:
            if conn.in_transaction:
                conn.rollback()
            conn.close()
