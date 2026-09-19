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

from reference.core import (
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
    return Note(pitch=d["pitch"], duration=Fraction(d["num"], d["den"]))


def notes_to_json(notes: tuple[Note, ...]) -> str:
    return json.dumps([note_to_dict(n) for n in notes], separators=(",", ":"))


def json_to_notes(s: str) -> tuple[Note, ...]:
    raw_list = json.loads(s)
    return phrase([dict_to_note(item) for item in raw_list])


def constraint_to_dict(c: LockConstraint) -> dict:
    return {"scope": c.scope, "origin": c.origin, "reason": c.reason}


def dict_to_constraint(d: dict) -> LockConstraint:
    return LockConstraint(scope=d["scope"], origin=d["origin"], reason=d["reason"])


class SqliteStorageEngine:
    """Provides atomic persistence and verification for Music MCP workspaces."""

    @staticmethod
    def _init_db(conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        with conn:
            conn.executescript("""
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
                    actor TEXT PRIMARY KEY,
                    scopes_json TEXT NOT NULL,
                    operations_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS constraints (
                    scope TEXT PRIMARY KEY,
                    origin TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
            """)

    @classmethod
    def save_workspace(cls, workspace: Workspace, path: str | Path) -> StorageReport:
        """Persists the complete state of a workspace into an atomic SQLite file."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(target_path))
        try:
            cls._init_db(conn)

            # Introspect internal workspace structures
            with workspace._lock:
                evidence_items = list(workspace._evidence.values())
                observation_items = list(workspace._observations.values())
                proposal_items = list(workspace._proposals.values())
                grant_items = list(set(workspace._grants.values()))
                constraint_items = list(workspace._constraints)
                snapshot = workspace._state

            now_iso = datetime.now(timezone.utc).isoformat()

            with conn:
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
            conn.close()

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
            # 1. Load constraints
            cur = conn.cursor()
            cur.execute("SELECT scope, origin, reason FROM constraints ORDER BY scope;")
            constraints = tuple(LockConstraint(scope=r[0], origin=r[1], reason=r[2]) for r in cur.fetchall())

            # 2. Load grants
            resolved_grants = []
            if grants is not None:
                resolved_grants = list(grants)
            else:
                cur.execute("SELECT actor, scopes_json, operations_json FROM grants ORDER BY actor;")
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

            return IntegrityReport(
                valid=len(errors) == 0,
                schema_version=schema_ver,
                evidence_count=len(ev_rows),
                revisions_count=len(rev_rows),
                errors=tuple(errors),
            )
        finally:
            conn.close()
