"""Demonstration of Host-Held Interactive Review Shell & CLI for Music MCP."""
from pathlib import Path
import tempfile

from reference.cli import main
from tests.audio_fixtures import make_wav


def run_cli_demo():
    print("=== Music MCP Host CLI & Review Shell Demonstration ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        proj_file = temp_path / "demo.musicmcp"
        wav_file = temp_path / "lead_take.wav"

        # 1. Synthesize a clean 440 Hz (A4) performance WAV
        print("\n1. Synthesizing test audio evidence (A4 440 Hz sine)...")
        wav_file.write_bytes(make_wav([(440.0, 1.0)], sample_rate=16000))
        print(f"   Created WAV fixture: {wav_file.name} ({wav_file.stat().st_size} bytes)")

        # 2. CLI: init project
        print(f"\n2. Initializing new project via CLI: {proj_file.name}...")
        main(["init", str(proj_file), "--artist", "artist-joel", "--scopes", "lead_vocal,backing"])

        # 3. CLI: inspect-audio
        print(f"\n3. Running non-mutating audio inspection on {wav_file.name}...")
        main(["inspect-audio", str(wav_file)])

        # 4. CLI: propose-audio
        print(f"\n4. Ingesting audio evidence and proposing notes into scope 'lead_vocal'...")
        main(["propose-audio", str(proj_file), str(wav_file), "--scope", "lead_vocal"])

        # 5. CLI: review and confirm
        print(f"\n5. Human authority review: confirming machine proposal...")
        main(["review", str(proj_file), "--action", "confirm", "--reason", "Artist confirmed initial pitch extraction"])

        # 6. CLI: review and correct (Revision 2)
        print(f"\n6. Human authority review: correcting phrase with expressive resolution...")
        main([
            "review",
            str(proj_file),
            "--action",
            "correct",
            "--notes",
            "A4 1, C5 1, E5 1, A5 1",
            "--reason",
            "Artist added arpeggiated ascent to high A5",
        ])

        # 7. CLI: export to MusicXML with loss disclosure
        xml_out = temp_path / "lead_vocal.musicxml"
        print(f"\n7. Exporting published phrase to MusicXML...")
        main(["export", str(proj_file), "--scope", "lead_vocal", "--format", "musicxml", "--out", str(xml_out)])

        # 8. CLI: export to Standard MIDI File
        mid_out = temp_path / "lead_vocal.mid"
        print(f"\n8. Exporting published phrase to Standard MIDI File...")
        main(["export", str(proj_file), "--scope", "lead_vocal", "--format", "midi", "--out", str(mid_out)])

        # 9. CLI: display revision history
        print(f"\n9. Inspecting immutable revision history...")
        main(["history", str(proj_file)])

    print("\n=== Host CLI & Review Shell Demonstration Verified Successfully ===")


if __name__ == "__main__":
    run_cli_demo()
