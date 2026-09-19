"""Conformance tests for durable SQLite evidence and revision storage."""
from fractions import Fraction
from pathlib import Path
import sqlite3
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
