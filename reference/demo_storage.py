"""Demonstration of Durable Evidence & Revision Storage for Music MCP."""
from fractions import Fraction
from pathlib import Path
import tempfile

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.storage.sqlite_store import SqliteStorageEngine


def run_storage_demo():
    print("=== Music MCP Durable Storage Demonstration ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "demo_project.musicmcp"
        producer = Producer("demo-producer", "0.1.01")

        # Step 1: Initialize Workspace and record musical state
        print("\n1. Initializing in-memory Workspace with constraints and evidence...")
        ws, (sess,) = create_workspace(
            [Grant("artist-joel", {"melody"}, {"confirm", "correct", "restore"})],
            constraints=(LockConstraint("backing", "artist-joel", "lead vocal integrity"),),
        )

        # Retain raw audio evidence
        synthetic_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        ev = ws.add_evidence(synthetic_wav, "audio/wav")
        obs = ws.observe(ev.id, "Vocal take A (acoustic mic)", producer=producer)
        print(f"   Stored raw evidence {ev.id[:12]}... ({len(ev.data)} bytes, SHA-256: {ev.sha256[:16]}...)")

        # Machine proposes melodic phrase
        p_notes = phrase([
            Note("C4", Fraction(1, 1)),
            Note("E4", Fraction(1, 1)),
            Note("G4", Fraction(2, 1)),
        ])
        prop = ws.propose(obs.id, "melody", p_notes, "intended", "HIGH", "interpreted", producer=producer)
        print(f"   Recorded proposal {prop.id[:12]}... (notes: {[n.pitch for n in p_notes]})")

        # Host-held human authority confirms Revision 1
        rev1 = sess.confirm(prop.id, 0, "Artist approved initial melodic transcription")
        print(f"   [AUTHORITY] Published Revision {rev1.number} (scope: {rev1.scope})")

        # Step 2: Persist state to durable SQLite storage
        print(f"\n2. Persisting Workspace to durable SQLite file: {db_path.name}...")
        report = SqliteStorageEngine.save_workspace(ws, db_path)
        print(f"   [OK] Saved successfully: {report.evidence_count} evidence, {report.revision_count} revision(s).")

        # Step 3: Verify cryptographic integrity of storage on disk
        print("\n3. Auditing disk storage integrity...")
        integ = SqliteStorageEngine.verify_integrity(db_path)
        assert integ.valid, f"Storage integrity failed: {integ.errors}"
        print(f"   [OK] Database passed PRAGMA and SHA-256 integrity checks (valid: {integ.valid})")

        # Step 4: Discard in-memory workspace and restore from disk
        print("\n4. Discarding in-memory Workspace and restoring fresh instance from disk...")
        del ws, sess  # Discard in-memory objects completely
        ws_restored, (sess_restored,) = SqliteStorageEngine.load_workspace(db_path)

        restored_phrase = [r for r in ws_restored.snapshot().phrases if r.scope == "melody"][0].notes
        print(f"   Restored phrase: {[f'{n.pitch} ({n.duration})' for n in restored_phrase]}")
        assert restored_phrase == p_notes, "Restored phrase does not match original!"
        print("   [OK] Restored state matches original with 100% mathematical fidelity.")

        # Step 5: Continue lifecycle on restored workspace
        print("\n5. Executing human correction (Revision 2) on restored workspace...")
        corrected_notes = phrase([
            Note("C4", Fraction(1, 1)),
            Note("E4", Fraction(1, 1)),
            Note("G4", Fraction(1, 1)),
            Note("C5", Fraction(1, 1)),
        ])
        rev2 = sess_restored.correct(prop.id, corrected_notes, 1, "Added high C5 resolving note")
        print(f"   [AUTHORITY] Published Revision {rev2.number} on restored workspace (notes: {[n.pitch for n in corrected_notes]})")

        # Resave and verify
        SqliteStorageEngine.save_workspace(ws_restored, db_path)
        integ2 = SqliteStorageEngine.verify_integrity(db_path)
        assert integ2.valid and integ2.revisions_count == 2
        print("   [OK] Revision 2 saved and verified in durable storage.")

    print("\n=== Durable Storage Demonstration Verified Successfully ===")


if __name__ == "__main__":
    run_storage_demo()
