"""Conformance tests for the Host-Held Interactive Review Shell / CLI."""
from fractions import Fraction
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reference.cli import main, parse_notes_string
from reference.core import Note, phrase
from tests.audio_fixtures import make_wav


class TestCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.project_path = self.dir_path / "test_proj.musicmcp"
        self.wav_path = self.dir_path / "test_audio.wav"

        # Generate a test WAV file with A4 (440 Hz) for 1.0s
        self.wav_bytes = make_wav([(440.0, 1.0)], sample_rate=16000)
        self.wav_path.write_bytes(self.wav_bytes)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_notes_string(self):
        # Test comma-separated
        p1 = parse_notes_string("C4 1, E4 1/2, G4 1/2, rest 1")
        self.assertEqual(len(p1), 4)
        self.assertEqual(p1[0], Note("C4", Fraction(1, 1)))
        self.assertEqual(p1[1], Note("E4", Fraction(1, 2)))
        self.assertEqual(p1[3], Note("rest", Fraction(1, 1)))

        # Test space-separated pairs
        p2 = parse_notes_string("D4 2 A4 1")
        self.assertEqual(len(p2), 2)
        self.assertEqual(p2[0], Note("D4", Fraction(2, 1)))
        self.assertEqual(p2[1], Note("A4", Fraction(1, 1)))

        # Invalid formats
        with self.assertRaises(ValueError):
            parse_notes_string("C4 1 E4")
        with self.assertRaises(ValueError):
            parse_notes_string("C4 not_a_fraction")

    def test_full_cli_lifecycle(self):
        # 1. init
        ret = main(["init", str(self.project_path), "--artist", "composer-joel", "--scopes", "melody,harmony"])
        self.assertEqual(ret, 0)
        self.assertTrue(self.project_path.exists())

        # 2. info
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main(["info", str(self.project_path)])
            self.assertEqual(ret, 0)
            self.assertIn("Integrity Valid:     True", mock_out.getvalue())

        # 3. inspect-audio
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main(["inspect-audio", str(self.wav_path)])
            self.assertEqual(ret, 0)
            out = mock_out.getvalue()
            self.assertIn("10-Band Acoustic Spectrum", out)
            self.assertIn("Monophonic Pitch Analysis", out)

        # 4. propose-audio
        ret = main(["propose-audio", str(self.project_path), str(self.wav_path), "--scope", "melody"])
        self.assertEqual(ret, 0)

        # 5. review with confirm action
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main(["review", str(self.project_path), "--action", "confirm", "--reason", "Artist confirmed A4 note"])
            self.assertEqual(ret, 0)
            self.assertIn("Confirmed and published Revision 1", mock_out.getvalue())

        # 6. review with correct action (Revision 2)
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main([
                "review",
                str(self.project_path),
                "--action",
                "correct",
                "--notes",
                "A4 1, C5 1, E5 2",
                "--reason",
                "Corrected to full chord arpeggio",
            ])
            self.assertEqual(ret, 0)
            self.assertIn("Corrected and published Revision 2", mock_out.getvalue())

        # 7. history
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main(["history", str(self.project_path)])
            self.assertEqual(ret, 0)
            hist = mock_out.getvalue()
            self.assertIn("Rev   1", hist)
            self.assertIn("Rev   2", hist)

        # 8. export to MusicXML
        xml_out = self.dir_path / "exported.xml"
        ret = main(["export", str(self.project_path), "--scope", "melody", "--format", "musicxml", "--out", str(xml_out)])
        self.assertEqual(ret, 0)
        self.assertTrue(xml_out.exists())
        self.assertIn("<score-partwise", xml_out.read_text(encoding="utf-8"))

        # 9. export to MIDI
        midi_out = self.dir_path / "exported.mid"
        ret = main(["export", str(self.project_path), "--scope", "melody", "--format", "midi", "--out", str(midi_out)])
        self.assertEqual(ret, 0)
        self.assertTrue(midi_out.exists())
        self.assertTrue(midi_out.read_bytes().startswith(b"MThd"))

        # 10. import MIDI as proposal with immediate confirmation
        ret = main(["import", str(self.project_path), "--file", str(midi_out), "--scope", "harmony", "--confirm"])
        self.assertEqual(ret, 0)

        # 11. restore revision 1 as revision 4
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = main(["restore", str(self.project_path), "--revision", "1", "--reason", "Restored initial A4 take"])
            self.assertEqual(ret, 0)
            self.assertIn("Restored Revision 1 as new Revision 4", mock_out.getvalue())


if __name__ == "__main__":
    unittest.main()
