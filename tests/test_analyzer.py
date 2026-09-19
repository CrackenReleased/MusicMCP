"""Conformance tests for the monophonic audio analyzer silo."""
from fractions import Fraction
import unittest

from reference.analyzer import (
    ANALYZER_PRODUCER,
    analyze_monophonic_wav,
    freq_to_pitch,
    ingest_and_propose,
    quantize_duration
)
from reference.core import (
    Grant,
    MusicError,
    Note,
    create_workspace
)
from tests.audio_fixtures import (
    make_silence_wav,
    make_stereo_wav,
    make_vibrato_wav,
    make_wav
)


class MonophonicAnalyzerConformance(unittest.TestCase):
    def test_freq_to_pitch_mapping(self):
        pitch, cents = freq_to_pitch(440.0)
        self.assertEqual(pitch, 'A4')
        self.assertAlmostEqual(cents, 0.0, places=1)

        pitch_c4, cents_c4 = freq_to_pitch(261.63)
        self.assertEqual(pitch_c4, 'C4')
        self.assertLess(abs(cents_c4), 1.0)

        pitch_rest, _ = freq_to_pitch(0.0)
        self.assertEqual(pitch_rest, 'rest')

    def test_quantize_duration_grid(self):
        # 120 BPM: 0.5s = 1 quarter, 0.25s = 1/2 quarter (eighth note)
        self.assertEqual(quantize_duration(0.5, 120), Fraction(1, 1))
        self.assertEqual(quantize_duration(0.25, 120), Fraction(1, 2))
        self.assertEqual(quantize_duration(1.0, 120), Fraction(2, 1))
        self.assertEqual(quantize_duration(0.0, 120), Fraction(1, 16))

    def test_clean_monophonic_wav_extracted_accurately(self):
        # A4 (440Hz, 0.4s) -> C5 (523.25Hz, 0.4s)
        audio = make_wav([(440.0, 0.4), (523.25, 0.4)])
        result = analyze_monophonic_wav(audio, tempo_bpm=120)

        pitches = [n.pitch for n in result.notes if n.pitch != 'rest']
        self.assertIn('A4', pitches)
        self.assertIn('C5', pitches)
        self.assertEqual(result.producer, ANALYZER_PRODUCER)
        self.assertIn(result.uncertainty, ('HIGH', 'MEDIUM'))
        self.assertGreater(result.duration_seconds, 0.7)

    def test_vibrato_audio_triggers_ambiguous_or_medium_uncertainty(self):
        # 440Hz with 55 cents vibrato at 5Hz
        audio = make_vibrato_wav(base_freq=440.0, duration=0.8, vib_rate=5.0, vib_cents=55.0)
        result = analyze_monophonic_wav(audio, tempo_bpm=120)

        self.assertIn(result.uncertainty, ('AMBIGUOUS', 'MEDIUM'))
        self.assertEqual(result.producer, ANALYZER_PRODUCER)

    def test_silence_audio_classified_as_insufficient_evidence(self):
        audio = make_silence_wav(duration=0.5)
        result = analyze_monophonic_wav(audio, tempo_bpm=120)

        self.assertEqual(result.uncertainty, 'INSUFFICIENT_EVIDENCE')
        for note in result.notes:
            self.assertEqual(note.pitch, 'rest')

    def test_invalid_and_unsupported_inputs_rejected_cleanly(self):
        # 1. Non-WAV junk
        with self.assertRaises(MusicError) as ctx:
            analyze_monophonic_wav(b'NOT_A_WAV_HEADER_DATA_STREAM_TOO_SHORT')
        self.assertEqual(ctx.exception.diagnostic.code, 'MUSICMCP-ANALYZER-INPUT_INVALID')

        # 2. Stereo WAV rejected
        stereo_wav = make_stereo_wav(duration=0.2)
        with self.assertRaises(MusicError) as ctx:
            analyze_monophonic_wav(stereo_wav)
        self.assertEqual(ctx.exception.diagnostic.code, 'MUSICMCP-ANALYZER-CHANNEL_UNSUPPORTED')

        # 3. Empty payload (valid header, 0 samples)
        empty_wav = make_wav([])
        with self.assertRaises(MusicError) as ctx:
            analyze_monophonic_wav(empty_wav)
        self.assertEqual(ctx.exception.diagnostic.code, 'MUSICMCP-ANALYZER-EMPTY_PAYLOAD')

    def test_ingest_and_propose_preserves_uncommitted_core_state(self):
        grant = Grant('test-host', frozenset({'melody'}), frozenset({'confirm', 'correct', 'restore'}))
        workspace, (session,) = create_workspace([grant])

        audio = make_wav([(440.0, 0.5)])
        ev = workspace.add_evidence(audio, 'audio/wav')
        self.assertEqual(workspace.snapshot().revision, 0)

        obs, prop = ingest_and_propose(workspace, ev.id, 'melody', tempo_bpm=120)

        # Observation checks
        self.assertEqual(obs.evidence_id, ev.id)
        self.assertEqual(obs.producer, ANALYZER_PRODUCER)

        # Proposal checks
        self.assertEqual(prop.observation_id, obs.id)
        self.assertEqual(prop.producer, ANALYZER_PRODUCER)
        self.assertEqual(prop.mode, 'intended')
        self.assertEqual(prop.origin, 'interpreted')
        self.assertIn(prop.uncertainty, ('HIGH', 'MEDIUM'))
        self.assertTrue(len(prop.notes) >= 1)

        # State is STILL UNCOMMITTED (revision 0)
        self.assertEqual(workspace.snapshot().revision, 0)
        self.assertEqual(workspace.snapshot().phrases, ())

    def test_human_correction_survives_subsequent_reanalysis(self):
        grant = Grant('test-host', frozenset({'melody'}), frozenset({'confirm', 'correct', 'restore'}))
        workspace, (session,) = create_workspace([grant])

        # Step 1: Ingest performance audio
        audio = make_wav([(440.0, 0.5)])
        ev = workspace.add_evidence(audio, 'audio/wav')
        obs, prop = ingest_and_propose(workspace, ev.id, 'melody', tempo_bpm=120)

        # Step 2: Human corrects intent through host session
        human_notes = [Note('A4', Fraction(1, 1))]
        rev1 = session.correct(prop.id, human_notes, expected_revision=0,
                               reason='Performer intended a full quarter note A4.')
        self.assertEqual(rev1.origin, 'human')
        self.assertEqual(workspace.snapshot().revision, 1)

        # Step 3: Re-analysis or competing proposal arrives
        audio2 = make_wav([(440.0, 0.25), (493.88, 0.25)])
        ev2 = workspace.add_evidence(audio2, 'audio/wav')
        obs2, prop2 = ingest_and_propose(workspace, ev2.id, 'melody', tempo_bpm=120)

        # Authoritative state is STILL human correction at revision 1
        snapshot = workspace.snapshot()
        self.assertEqual(snapshot.revision, 1)
        self.assertEqual(snapshot.phrases[0].origin, 'human')
        self.assertEqual(snapshot.phrases[0].notes, tuple(human_notes))


if __name__ == '__main__':
    unittest.main()
