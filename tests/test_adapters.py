"""Conformance and round-trip tests for MusicXML and MIDI adapters."""
from fractions import Fraction
import unittest

from reference.adapters.midi import midi_to_phrase, phrase_to_midi
from reference.adapters.musicxml import musicxml_to_phrase, phrase_to_musicxml
from reference.core import MusicError, Note, phrase


class FormatAdaptersConformance(unittest.TestCase):
    def setUp(self):
        self.sample_notes = phrase([
            Note('C4', Fraction(1, 1)),      # Quarter note
            Note('rest', Fraction(1, 2)),    # Eighth rest
            Note('G4', Fraction(1, 2)),      # Eighth note
            Note('C#5', Fraction(2, 1)),     # Half note
        ])

    def test_musicxml_export_and_loss_disclosure(self):
        xml_str, report = phrase_to_musicxml(self.sample_notes, tempo_bpm=120)
        
        self.assertIn('<?xml', xml_str)
        self.assertIn('<score-partwise', xml_str)
        self.assertIn('<step>C</step>', xml_str)
        self.assertIn('<octave>4</octave>', xml_str)
        self.assertTrue('<rest/>' in xml_str or '<rest />' in xml_str)
        self.assertIn('<step>C</step>', xml_str)
        self.assertIn('<alter>1</alter>', xml_str)

        self.assertEqual(report.format, 'musicxml')
        self.assertEqual(report.direction, 'export')
        self.assertEqual(report.notes_processed, 4)
        self.assertGreater(len(report.disclosed_losses), 0)

    def test_musicxml_round_trip_fidelity(self):
        xml_str, _ = phrase_to_musicxml(self.sample_notes, tempo_bpm=120)
        parsed_phrase, report = musicxml_to_phrase(xml_str)

        self.assertEqual(len(parsed_phrase), len(self.sample_notes))
        for orig, parsed in zip(self.sample_notes, parsed_phrase):
            self.assertEqual(orig.pitch, parsed.pitch)
            self.assertEqual(orig.duration, parsed.duration)

    def test_midi_export_and_loss_disclosure(self):
        midi_bytes, report = phrase_to_midi(self.sample_notes, tempo_bpm=120)

        # Standard MIDI header verification
        self.assertTrue(midi_bytes.startswith(b'MThd'))
        self.assertIn(b'MTrk', midi_bytes)
        self.assertEqual(report.format, 'midi')
        self.assertEqual(report.direction, 'export')
        self.assertEqual(report.notes_processed, 4)
        self.assertGreater(len(report.disclosed_losses), 0)

    def test_midi_round_trip_fidelity(self):
        midi_bytes, _ = phrase_to_midi(self.sample_notes, tempo_bpm=120)
        parsed_phrase, report = midi_to_phrase(midi_bytes)

        self.assertEqual(len(parsed_phrase), len(self.sample_notes))
        for orig, parsed in zip(self.sample_notes, parsed_phrase):
            self.assertEqual(orig.pitch, parsed.pitch)
            self.assertEqual(orig.duration, parsed.duration)

    def test_malformed_inputs_rejected_safely(self):
        with self.assertRaises(MusicError) as xml_ctx:
            musicxml_to_phrase(b'<invalid-xml>incomplete')
        self.assertEqual(xml_ctx.exception.diagnostic.code, 'MUSICMCP-MUSICXML-MALFORMED_XML')

        with self.assertRaises(MusicError) as midi_ctx:
            midi_to_phrase(b'not-a-midi-file-header')
        self.assertEqual(midi_ctx.exception.diagnostic.code, 'MUSICMCP-MIDI-INVALID_HEADER')


if __name__ == '__main__':
    unittest.main()
