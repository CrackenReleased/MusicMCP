"""Conformance tests for durable SQLite evidence and revision storage."""
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.storage.sqlite_store import (
    SqliteStorageEngine,
    StorageError,
)


class TestSqliteStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "project.musicmcp"
        self.producer = Producer("test-producer", "0.1.01")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self):
        # 1. Create workspace with constraints, evidence, observations, proposals, and revisions
        ws, (sess,) = create_workspace(
            [Grant("lead-artist", {"melody"}, {"confirm", "correct", "restore"})],
            constraints=(LockConstraint("backing", "lead-artist", "protected backing track"),),
        )

        # Add evidence
        ev = ws.add_evidence(b"RIFF....WAVEfmt test audio data", "audio/wav")
        obs = ws.observe(ev.id, "Lead vocal take 1", producer=self.producer)

        # Propose notes
        n1 = Note("C4", Fraction(1, 1))
        n2 = Note("E4", Fraction(1, 2))
        n3 = Note("G4", Fraction(1, 2))
        notes = phrase([n1, n2, n3])
        prop = ws.propose(obs.id, "melody", notes, "intended", "HIGH", "interpreted", producer=self.producer)

        # Acquire session and confirm revision 1
        rev1 = sess.confirm(prop.id, 0, "lead artist approves take 1 transcription")
        self.assertEqual(rev1.number, 1)

        # Correct to revision 2
        n_corrected = phrase([Note("C4", Fraction(1, 1)), Note("E4", Fraction(1, 1)), Note("G4", Fraction(2, 1))])
        rev2 = sess.correct(prop.id, n_corrected, 1, "lengthened final note")
        self.assertEqual(rev2.number, 2)

        # 2. Save to SQLite
        report = SqliteStorageEngine.save_workspace(ws, self.db_path)
        self.assertEqual(report.evidence_count, 1)
        self.assertEqual(report.observation_count, 1)
        self.assertEqual(report.proposal_count, 1)
        self.assertEqual(report.revision_count, 2)
        self.assertEqual(report.grant_count, 1)
        self.assertEqual(report.constraint_count, 1)
        self.assertTrue(report.sha256_verified)

        # 3. Verify integrity of saved database
        integ = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertTrue(integ.valid)
        self.assertEqual(integ.errors, ())
        self.assertEqual(integ.revisions_count, 2)

        # 4. Load into fresh workspace
        ws_loaded, (sess_loaded,) = SqliteStorageEngine.load_workspace(self.db_path)
        snap = ws_loaded.snapshot()
        self.assertEqual(snap.revision, 2)
        self.assertEqual(len(snap.history), 2)
        self.assertEqual(len(snap.phrases), 1)

        loaded_phrase = [r for r in ws_loaded.snapshot().phrases if r.scope == "melody"][0].notes
        self.assertEqual(loaded_phrase, n_corrected)

        # 5. Verify that authority sessions continue to function correctly on restored workspace
        # Restore revision 1 as revision 3
        rev3 = sess_loaded.restore(1, 2, "revert to original shorter rhythm")
        self.assertEqual(rev3.number, 3)
        self.assertEqual(rev3.notes, notes)
        self.assertEqual([r for r in ws_loaded.snapshot().phrases if r.scope == "melody"][0].notes, notes)

    def test_detect_corrupted_evidence(self):
        ws, _ = create_workspace([])
        ev = ws.add_evidence(b"unaltered raw audio evidence bytes", "audio/wav")
        obs = ws.observe(ev.id, "Guitar riff", producer=self.producer)
        SqliteStorageEngine.save_workspace(ws, self.db_path)

        # Corrupt evidence directly in SQLite
        conn = sqlite3.connect(str(self.db_path))
        with conn:
            conn.execute("UPDATE evidence SET data = ? WHERE id = ?", (b"tampered evil bytes", ev.id))
        conn.close()

        # Audit should report corruption
        integ = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertFalse(integ.valid)
        self.assertTrue(any("SHA-256 mismatch" in err for err in integ.errors))

        # Loading should fail closed
        with self.assertRaises(StorageError) as ctx:
            SqliteStorageEngine.load_workspace(self.db_path)
        self.assertIn("EVIDENCE_CORRUPTED", ctx.exception.diagnostic.code)

    def test_corrupt_project_file_rejects_dangling_observation(self):
        ws, (session,) = create_workspace([Grant("artist", {"melody"}, {"confirm"})])
        evidence = ws.add_evidence(b"source audio", "audio/wav")
        observation = ws.observe(evidence.id, "take", producer=self.producer)
        proposal = ws.propose(observation.id, "melody", (Note("C4", Fraction(1)),),
                              "intended", "LOW", "interpreted", producer=self.producer)
        session.confirm(proposal.id, 0, "accept")
        SqliteStorageEngine.save_workspace(ws, self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("UPDATE observations SET evidence_id=? WHERE id=?", ("missing-evidence", observation.id))
            conn.commit()
        finally:
            conn.close()

        report = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertFalse(report.valid)
        self.assertTrue(any("Observation" in error and "missing evidence" in error for error in report.errors))
        with self.assertRaises(StorageError) as caught:
            SqliteStorageEngine.load_workspace(self.db_path)
        self.assertIn("INTEGRITY_FAILURE", caught.exception.diagnostic.code)

    def test_terminated_writer_preserves_last_committed_revision(self):
        ws, (session,) = create_workspace([Grant("artist", {"melody"}, {"confirm", "correct"})])
        evidence = ws.add_evidence(b"source audio", "audio/wav")
        observation = ws.observe(evidence.id, "take", producer=self.producer)
        proposal = ws.propose(observation.id, "melody", (Note("C4", Fraction(1)),),
                              "intended", "LOW", "interpreted", producer=self.producer)
        session.confirm(proposal.id, 0, "accepted")
        SqliteStorageEngine.save_workspace(ws, self.db_path)
        original_token = ws._storage_token

        child = """
import sqlite3
import sys
import time
from unittest.mock import patch
from fractions import Fraction
from reference.core import Note
from reference.storage.sqlite_store import SqliteStorageEngine

workspace, (session,) = SqliteStorageEngine.load_workspace(sys.argv[1])
session.correct(sys.argv[2], (Note('D4', Fraction(1)),), 1, 'interrupted correction')
real_connect = sqlite3.connect

class PauseBeforeCommit(sqlite3.Connection):
    def commit(self):
        print('READY_TO_COMMIT', flush=True)
        time.sleep(60)
        return super().commit()

with patch('reference.storage.sqlite_store.sqlite3.connect',
           side_effect=lambda path: real_connect(path, factory=PauseBeforeCommit)):
    SqliteStorageEngine.save_workspace(workspace, sys.argv[1])
"""
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", child, str(self.db_path), proposal.id],
            cwd=Path(__file__).parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        reader = ThreadPoolExecutor(max_workers=1)
        try:
            ready = reader.submit(process.stdout.readline).result(timeout=10)
            self.assertEqual(ready.strip(), "READY_TO_COMMIT")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            reader.shutdown(wait=True)
            process.stdout.close()
            process.stderr.close()

        report = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertTrue(report.valid, report.errors)
        reopened, _ = SqliteStorageEngine.load_workspace(self.db_path)
        self.assertEqual(reopened.snapshot().revision, 1)
        self.assertEqual(reopened.snapshot().history[0].notes, (Note("C4", Fraction(1)),))
        self.assertEqual(len(reopened._evidence), 1)
        self.assertEqual(reopened._storage_token, original_token)

    def test_detect_broken_revision_chain(self):
        ws, (sess,) = create_workspace([Grant("editor", {"lead"}, {"confirm", "correct", "restore"})])
        ev = ws.add_evidence(b"audio", "audio/wav")
        obs = ws.observe(ev.id, "Test", producer=self.producer)
        p = ws.propose(obs.id, "lead", phrase([Note("C4", Fraction(1, 1))]), "intended", "HIGH", "interpreted", producer=self.producer)
        sess.confirm(p.id, 0, "initial")

        SqliteStorageEngine.save_workspace(ws, self.db_path)

        # Tamper with revision parent
        conn = sqlite3.connect(str(self.db_path))
        with conn:
            conn.execute("UPDATE revisions SET parent = 999 WHERE number = 1")
        conn.close()

        integ = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertFalse(integ.valid)
        self.assertTrue(any("parent mismatch" in err for err in integ.errors))

    def test_nonexistent_storage_file_fails_closed(self):
        missing_path = Path(self.temp_dir.name) / "does_not_exist.musicmcp"
        integ = SqliteStorageEngine.verify_integrity(missing_path)
        self.assertFalse(integ.valid)
        self.assertTrue(any("File not found" in err for err in integ.errors))

        with self.assertRaises(StorageError) as ctx:
            SqliteStorageEngine.load_workspace(missing_path)
        self.assertIn("NOT_FOUND", ctx.exception.diagnostic.code)

    def test_unsupported_schema_version(self):
        ws, _ = create_workspace([])
        SqliteStorageEngine.save_workspace(ws, self.db_path)

        # Change schema version
        conn = sqlite3.connect(str(self.db_path))
        with conn:
            conn.execute("UPDATE schema_meta SET value = '9.9.9' WHERE key = 'schema_version'")
        conn.close()

        integ = SqliteStorageEngine.verify_integrity(self.db_path)
        self.assertFalse(integ.valid)
        self.assertTrue(any("Unsupported schema version" in err for err in integ.errors))


class TestStorageSafety(unittest.TestCase):
    """Storage regressions run wholly in memory without host test artifacts."""

    def setUp(self):
        class MemoryConnection(sqlite3.Connection):
            def close(self):
                pass
        self.conn = sqlite3.connect(":memory:", factory=MemoryConnection)
        self.addCleanup(lambda: sqlite3.Connection.close(self.conn))
        for patcher in (
            patch("reference.storage.sqlite_store.sqlite3.connect", return_value=self.conn),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.mkdir"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.path = Path("memory-review.musicmcp")
        self.ws, (self.session,) = create_workspace([
            Grant("artist", {"melody"}, {"confirm", "correct", "restore"})
        ])
        ev = self.ws.add_evidence(b"original evidence", "audio/wav")
        obs = self.ws.observe(ev.id, "take", producer=Producer("test", "1"))
        self.prop = self.ws.propose(obs.id, "melody", (Note("C4", Fraction(1)),),
                                    "intended", "HIGH", "interpreted", producer=Producer("test", "1"))
        self.session.confirm(self.prop.id, 0, "initial")
        SqliteStorageEngine.save_workspace(self.ws, self.path)

    def test_corrupt_record_relationships_fail_audit_and_load(self):
        other_evidence = self.ws.add_evidence(b"unrelated evidence", "audio/wav")
        other_observation = self.ws.observe(other_evidence.id, "other take", producer=Producer("test", "1"))
        self.session.restore(1, 1, "return to approved phrase")
        SqliteStorageEngine.save_workspace(self.ws, self.path)
        self.conn.execute("PRAGMA foreign_keys=OFF")  # Simulate an externally corrupted file.

        cases = (
            ("observation without evidence", "observations", "evidence_id", "id=?", (self.prop.observation_id,), "missing-evidence", "Observation"),
            ("proposal without observation", "proposals", "observation_id", "id=?", (self.prop.id,), "missing-observation", "Proposal"),
            ("proposal evidence mismatch", "proposals", "evidence_id", "id=?", (self.prop.id,), other_evidence.id, "Proposal"),
            ("revision without proposal", "revisions", "proposal_id", "number=?", (1,), "missing-proposal", "Revision"),
            ("revision observation mismatch", "revisions", "observation_id", "number=?", (1,), other_observation.id, "Revision"),
            ("revision evidence mismatch", "revisions", "evidence_id", "number=?", (1,), other_evidence.id, "Revision"),
            ("revision scope mismatch", "revisions", "scope", "number=?", (1,), "unrelated", "Revision"),
            ("restore references future revision", "revisions", "restored_from", "number=?", (2,), 99, "Revision"),
            ("proposal origin invalid", "proposals", "origin", "id=?", (self.prop.id,), "human", "Proposal"),
            ("confirm origin mismatch", "revisions", "origin", "number=?", (1,), "human", "Revision"),
            ("confirm notes mismatch", "revisions", "notes_json", "number=?", (1,), '[{"pitch":"D4","num":1,"den":1}]', "Revision"),
            ("restore notes mismatch", "revisions", "notes_json", "number=?", (2,), '[{"pitch":"D4","num":1,"den":1}]', "Revision"),
            ("restore origin mismatch", "revisions", "origin", "number=?", (2,), "human", "Revision"),
            ("confirm has restore source", "revisions", "restored_from", "number=?", (1,), 1, "Revision"),
            ("malformed proposal notes", "proposals", "notes_json", "id=?", (self.prop.id,), "not-json", "Proposal"),
            ("unexpected proposal note field", "proposals", "notes_json", "id=?", (self.prop.id,), '[{"pitch":"C4","num":1,"den":1,"velocity":64}]', "Proposal"),
            ("malformed revision notes", "revisions", "notes_json", "number=?", (1,), "not-json", "Revision"),
            ("boolean note numerator", "revisions", "notes_json", "number=?", (1,), '[{"pitch":"C4","num":true,"den":1}]', "Revision"),
            ("invalid note duration", "revisions", "notes_json", "number=?", (1,), '[{"pitch":"C4","num":1,"den":0}]', "Revision"),
            ("malformed revision constraints", "revisions", "constraints_json", "number=?", (1,), "not-json", "Revision"),
            ("invalid constraint collection", "revisions", "constraints_json", "number=?", (1,), "{}", "Revision"),
            ("unexpected constraint field", "revisions", "constraints_json", "number=?", (1,), '[{"scope":"melody","origin":"artist","reason":"old","extra":1}]', "Revision"),
        )
        for name, table, column, where, keys, corrupt_value, label in cases:
            with self.subTest(name=name):
                original = self.conn.execute(f"SELECT {column} FROM {table} WHERE {where}", keys).fetchone()[0]
                try:
                    self.conn.execute(f"UPDATE {table} SET {column}=? WHERE {where}", (corrupt_value, *keys))
                    self.conn.commit()
                    report = SqliteStorageEngine.verify_integrity(self.path)
                    self.assertFalse(report.valid, name)
                    self.assertTrue(any(label in error for error in report.errors), report.errors)
                    with self.assertRaises(StorageError) as caught:
                        SqliteStorageEngine.load_workspace(self.path)
                    self.assertIn("INTEGRITY_FAILURE", caught.exception.diagnostic.code)
                    self.assertIn(label, caught.exception.diagnostic.message)
                finally:
                    self.conn.execute(f"UPDATE {table} SET {column}=? WHERE {where}", (original, *keys))
                    self.conn.commit()

        clean_report = SqliteStorageEngine.verify_integrity(self.path)
        self.assertTrue(clean_report.valid, clean_report.errors)
        loaded, _ = SqliteStorageEngine.load_workspace(self.path)
        self.assertEqual(loaded.snapshot().history, self.ws.snapshot().history)

    def test_stale_authoritative_save_preserves_first_writer(self):
        a, (sa,) = SqliteStorageEngine.load_workspace(self.path)
        b, (sb,) = SqliteStorageEngine.load_workspace(self.path)
        sa.correct(self.prop.id, (Note("D4", Fraction(1)),), 1, "first editor")
        SqliteStorageEngine.save_workspace(a, self.path)
        sb.correct(self.prop.id, (Note("E4", Fraction(1)),), 1, "stale editor")
        with self.assertRaises(StorageError):
            SqliteStorageEngine.save_workspace(b, self.path)
        loaded, _ = SqliteStorageEngine.load_workspace(self.path)
        self.assertEqual(loaded.snapshot().history[-1].reason, "first editor")

    def test_stale_nonrevision_save_is_rejected(self):
        a, _ = SqliteStorageEngine.load_workspace(self.path)
        b, _ = SqliteStorageEngine.load_workspace(self.path)
        a.add_evidence(b"new evidence", "audio/wav")
        SqliteStorageEngine.save_workspace(a, self.path)
        with self.assertRaises(StorageError):
            SqliteStorageEngine.save_workspace(b, self.path)

    def test_failed_force_save_preserves_complete_database(self):
        before = list(self.conn.iterdump())
        token = self.ws._storage_token
        with patch("reference.storage.sqlite_store.notes_to_json", side_effect=RuntimeError("serialization failed")):
            with self.assertRaises(RuntimeError):
                SqliteStorageEngine.save_workspace(self.ws, self.path, force=True)
        self.assertEqual(list(self.conn.iterdump()), before)
        self.assertEqual(self.ws._storage_token, token)

    def test_rejected_save_preserves_legacy_grants_schema_and_rows(self):
        with self.conn:
            self.conn.execute("ALTER TABLE grants RENAME TO grants_current")
            self.conn.execute("CREATE TABLE grants (actor TEXT PRIMARY KEY, scopes_json TEXT NOT NULL, operations_json TEXT NOT NULL)")
            self.conn.execute("INSERT INTO grants SELECT actor, scopes_json, operations_json FROM grants_current")
            self.conn.execute("DROP TABLE grants_current")
        before = list(self.conn.iterdump())
        stale, _ = create_workspace([])
        with self.assertRaises(StorageError):
            SqliteStorageEngine.save_workspace(stale, self.path)
        self.assertEqual(list(self.conn.iterdump()), before)

    def test_save_rejects_unsupported_schema_without_changes(self):
        with self.conn:
            self.conn.execute("UPDATE schema_meta SET value='9.9.9' WHERE key='schema_version'")
        before = list(self.conn.iterdump())
        with self.assertRaises(StorageError):
            SqliteStorageEngine.save_workspace(self.ws, self.path)
        self.assertEqual(list(self.conn.iterdump()), before)

    def test_force_init_replaces_all_content(self):
        from reference.cli import main
        self.assertEqual(main(["init", str(self.path), "--force", "--artist", "new artist"]), 0)
        loaded, sessions = SqliteStorageEngine.load_workspace(self.path)
        self.assertEqual(loaded.snapshot().revision, 0)
        self.assertEqual(loaded.snapshot().history, ())
        self.assertEqual(loaded._evidence, {})
        self.assertEqual(loaded._observations, {})
        self.assertEqual(loaded._proposals, {})
        self.assertEqual(len(sessions), 1)
        self.assertEqual(next(iter(loaded._grants.values())).actor, "new artist")

    def test_load_rejects_unsupported_schema(self):
        with self.conn:
            self.conn.execute("UPDATE schema_meta SET value='9.9.9' WHERE key='schema_version'")
        with self.assertRaises(StorageError):
            SqliteStorageEngine.load_workspace(self.path)

    def test_load_rejects_invalid_parent(self):
        with self.conn:
            self.conn.execute("UPDATE revisions SET parent=999 WHERE number=1")
        with self.assertRaises(StorageError):
            SqliteStorageEngine.load_workspace(self.path)

    def test_separate_grants_same_actor_round_trip_without_broadening(self):
        loaded, _ = SqliteStorageEngine.load_workspace(self.path, grants=[
            Grant("same", {"melody"}, {"confirm"}),
            Grant("same", {"harmony"}, {"correct"}),
        ])
        SqliteStorageEngine.save_workspace(loaded, self.path)
        restored, sessions = SqliteStorageEngine.load_workspace(self.path)
        self.assertEqual(set(restored._grants.values()), set(loaded._grants.values()))
        self.assertEqual(len(sessions), 2)
        for session in sessions:
            with self.assertRaises(Exception) as caught:
                session.correct(self.prop.id, (Note("D4", Fraction(1)),), 1, "forbidden")
            self.assertIn("UNAUTHORIZED", caught.exception.diagnostic.code)


class TestConcurrentStorage(unittest.TestCase):
    def test_competing_save_cannot_overwrite_after_conflict_check(self):
        # Two independent connections, interleaved at the old check/write gap.
        from uuid import uuid4
        real_connect = sqlite3.connect
        uri = "file:" + uuid4().hex + "?mode=memory&cache=shared"
        keeper = real_connect(uri, uri=True)
        self.addCleanup(keeper.close)
        callback = []
        outcomes = []

        class Cursor(sqlite3.Cursor):
            def execute(self, sql, parameters=()):
                self.checking_history = sql.startswith("SELECT number, parent, actor")
                return super().execute(sql, parameters)

            def fetchall(self):
                rows = super().fetchall()
                if self.checking_history and callback:
                    callback.pop()()
                return rows

        class Connection(sqlite3.Connection):
            def cursor(self):
                return super().cursor(factory=Cursor)

        def connect(*args, **kwargs):
            return real_connect(uri, uri=True, timeout=0, factory=Connection)

        with patch("reference.storage.sqlite_store.sqlite3.connect", side_effect=connect), \
             patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.mkdir"):
            path = "concurrent-memory.musicmcp"
            initial, _ = create_workspace([])
            SqliteStorageEngine.save_workspace(initial, path)
            first, _ = SqliteStorageEngine.load_workspace(path)
            second, _ = SqliteStorageEngine.load_workspace(path)
            first.add_evidence(b"first", "audio/wav")
            second.add_evidence(b"second", "audio/wav")

            def competing_save():
                try:
                    SqliteStorageEngine.save_workspace(second, path)
                    outcomes.append("saved")
                except (StorageError, sqlite3.OperationalError):
                    outcomes.append("rejected")

            callback.append(competing_save)
            SqliteStorageEngine.save_workspace(first, path)
            self.assertEqual(outcomes, ["rejected"])
            loaded, _ = SqliteStorageEngine.load_workspace(path)
            self.assertEqual([ev.data for ev in loaded._evidence.values()], [b"first"])


if __name__ == "__main__":
    unittest.main()
