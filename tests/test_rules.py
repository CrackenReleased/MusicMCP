"""Conformance tests for Constraint-Aware Arranging and Musical Rules Engine."""
from fractions import Fraction
import unittest

from reference.core import (
    Grant,
    MusicError,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.rules import (
    RuleSeverity,
    RulesEngine,
    Ruleset,
    STANDARD_VOCAL_RANGES,
    midi_to_pitch,
    pitch_to_midi,
    transpose_phrase,
)


class TestRules(unittest.TestCase):
    def setUp(self):
        self.producer = Producer("rules-test-producer", "0.1.01")

    def test_pitch_to_midi_and_back(self):
        self.assertEqual(pitch_to_midi("C4"), 60)
        self.assertEqual(pitch_to_midi("A4"), 69)
        self.assertEqual(pitch_to_midi("C5"), 72)
        self.assertEqual(pitch_to_midi("rest"), None)

        self.assertEqual(midi_to_pitch(60), "C4")
        self.assertEqual(midi_to_pitch(69), "A4")
        self.assertEqual(midi_to_pitch(72), "C5")

    def test_transposition_preserves_phrase_relationships(self):
        original = phrase([
            Note("C4", Fraction(1, 1)),
            Note("E4", Fraction(1, 1)),
            Note("G4", Fraction(2, 1)),
            Note("rest", Fraction(1, 1)),
        ])

        # Transpose up by a major second (+2 semitones) -> D4, F#4, A4, rest
        transposed = transpose_phrase(original, semitones=2)
        expected = phrase([
            Note("D4", Fraction(1, 1)),
            Note("F#4", Fraction(1, 1)),
            Note("A4", Fraction(2, 1)),
            Note("rest", Fraction(1, 1)),
        ])
        self.assertEqual(transposed, expected)

        # Transpose down by a minor third (-3 semitones) -> A3, C#4, E4, rest
        transposed_down = transpose_phrase(original, semitones=-3)
        expected_down = phrase([
            Note("A3", Fraction(1, 1)),
            Note("C#4", Fraction(1, 1)),
            Note("E4", Fraction(2, 1)),
            Note("rest", Fraction(1, 1)),
        ])
        self.assertEqual(transposed_down, expected_down)

    def test_vocal_range_blocking_violation(self):
        # Create an Alto ruleset (F3 to D5)
        alto_rules = Ruleset(
            name="alto-range",
            version="0.1.01",
            author="lead-arranger",
            vocal_range=STANDARD_VOCAL_RANGES["ALTO"],
        )
        engine = RulesEngine(alto_rules)

        # In-range Alto phrase (A3 to C5) -> Valid
        good_phrase = phrase([Note("A3", Fraction(1, 1)), Note("C5", Fraction(1, 1))])
        report_good = engine.evaluate_phrase(good_phrase)
        self.assertTrue(report_good.valid)
        self.assertEqual(len(report_good.blocking_violations), 0)

        # Out-of-range Soprano high G5 (MIDI 79, above Alto max 74) -> Blocking
        bad_phrase = phrase([Note("A3", Fraction(1, 1)), Note("G5", Fraction(1, 1))])
        report_bad = engine.evaluate_phrase(bad_phrase)
        self.assertFalse(report_bad.valid)
        self.assertEqual(len(report_bad.blocking_violations), 1)
        self.assertEqual(report_bad.blocking_violations[0].rule_name, "VOCAL_RANGE_EXCEEDED")
        self.assertEqual(report_bad.blocking_violations[0].severity, RuleSeverity.BLOCKING)

    def test_tessitura_warning_violation(self):
        # Create a Soprano ruleset (tessitura E4 to G5)
        soprano_rules = Ruleset(
            name="soprano-range",
            version="0.1.01",
            author="lead-arranger",
            vocal_range=STANDARD_VOCAL_RANGES["SOPRANO"],
        )
        engine = RulesEngine(soprano_rules)

        # C4 is within absolute range (60-84) but outside comfortable tessitura (64-79) -> Warning
        tessitura_phrase = phrase([Note("C4", Fraction(1, 1)), Note("G4", Fraction(1, 1))])
        report = engine.evaluate_phrase(tessitura_phrase)
        self.assertTrue(report.valid)  # Still valid because tessitura is WARNING by default
        self.assertEqual(len(report.warning_violations), 1)
        self.assertEqual(report.warning_violations[0].rule_name, "TESSITURA_OVERFLOW")
        self.assertEqual(report.warning_violations[0].severity, RuleSeverity.WARNING)

    def test_workspace_validator_blocks_commit_on_range_violation(self):
        # Wire RulesEngine.check_candidate directly into Workspace._validator
        bass_rules = Ruleset(
            name="bass-range",
            version="0.1.01",
            author="lead-arranger",
            vocal_range=STANDARD_VOCAL_RANGES["BASS"],  # E2 (40) to E4 (64)
        )
        engine = RulesEngine(bass_rules)

        ws, (sess,) = create_workspace(
            [Grant("lead-artist", {"bass_line"}, {"confirm", "correct", "restore"})],
            validator=engine.check_candidate,
        )

        ev = ws.add_evidence(b"bass audio take", "audio/wav")
        obs = ws.observe(ev.id, "Bass performance", producer=self.producer)

        # High A4 (69) exceeds Bass range max E4 (64)
        out_of_range_notes = phrase([Note("A4", Fraction(1, 1))])
        prop = ws.propose(obs.id, "bass_line", out_of_range_notes, "intended", "HIGH", "interpreted", producer=self.producer)

        # Commit must fail post-validation with VALIDATION_FAILED
        with self.assertRaises(MusicError) as ctx:
            sess.confirm(prop.id, 0, "Artist tries to confirm out-of-range bass pitch")
        self.assertIn("VALIDATION_FAILED", ctx.exception.diagnostic.code)
        self.assertEqual(ws.snapshot().revision, 0)


if __name__ == "__main__":
    unittest.main()
