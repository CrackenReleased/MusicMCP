"""Conformance tests for Requested Generated Alternatives Silo."""
from fractions import Fraction
import unittest

from reference.alternatives import (
    AlternativeGenerator,
    AlternativeRequest,
    AlternativeType,
)
from reference.core import (
    Grant,
    Note,
    Producer,
    create_workspace,
    phrase,
)


class TestAlternatives(unittest.TestCase):
    def setUp(self):
        self.producer = Producer("test-producer", "0.1.01")
        self.ws, (self.sess,) = create_workspace(
            [Grant("lead-composer", {"melody", "harmony", "bass"}, {"confirm", "correct", "restore"})]
        )

        ev = self.ws.add_evidence(b"RIFF....melody audio", "audio/wav")
        self.obs = self.ws.observe(ev.id, "Composer lead theme", producer=self.producer)

        # C4 (1), D4 (1), E4 (2)
        self.melody = phrase([
            Note("C4", Fraction(1, 1)),
            Note("D4", Fraction(1, 1)),
            Note("E4", Fraction(2, 1)),
        ])

    def test_explicit_request_produces_harmony_third_above(self):
        req = AlternativeRequest(
            requested_by="lead-composer",
            source_scope="melody",
            target_scope="harmony",
            alt_type=AlternativeType.HARMONY_THIRD_ABOVE,
            reason="Explore vocal harmony for chorus",
        )

        alt = AlternativeGenerator.generate(req, self.melody)
        self.assertEqual(alt.request, req)
        self.assertEqual(len(alt.notes), 3)

        # Diatonic 3rd above C4 is E4; D4 is F4; E4 is G4
        expected = phrase([
            Note("E4", Fraction(1, 1)),
            Note("F4", Fraction(1, 1)),
            Note("G4", Fraction(2, 1)),
        ])
        self.assertEqual(alt.notes, expected)

    def test_generated_proposal_retains_generated_origin_when_published(self):
        # Invariant: Accepting a generated alternative MUST NEVER turn its origin into 'human'
        req = AlternativeRequest(
            requested_by="lead-composer",
            source_scope="melody",
            target_scope="harmony",
            alt_type=AlternativeType.HARMONY_THIRD_BELOW,
            reason="Lower vocal harmony",
        )
        alt = AlternativeGenerator.generate(req, self.melody)

        # Propose into workspace
        prop = AlternativeGenerator.propose_into_workspace(self.ws, self.obs.id, alt)
        self.assertEqual(prop.origin, "generated")

        # Human confirms proposal
        rev = self.sess.confirm(prop.id, 0, "Composer accepts machine-proposed lower harmony")
        self.assertEqual(rev.number, 1)
        self.assertEqual(rev.actor, "lead-composer")
        self.assertEqual(rev.scope, "harmony")

        # Provenance guarantee: Origin must remain 'generated'
        self.assertEqual(rev.origin, "generated")
        self.assertEqual(self.ws.snapshot().history[0].origin, "generated")

    def test_root_bass_pedal_generation(self):
        req = AlternativeRequest(
            requested_by="lead-composer",
            source_scope="melody",
            target_scope="bass",
            alt_type=AlternativeType.ROOT_BASS_PEDAL,
            reason="Anchor bassline",
        )
        alt = AlternativeGenerator.generate(req, self.melody)
        # Total duration = 1 + 1 + 2 = 4 quarters
        self.assertEqual(len(alt.notes), 1)
        self.assertEqual(alt.notes[0], Note("C2", Fraction(4, 1)))

    def test_cadence_resolution_generation(self):
        req = AlternativeRequest(
            requested_by="lead-composer",
            source_scope="melody",
            target_scope="melody",
            alt_type=AlternativeType.CADENCE_RESOLUTION,
            reason="Resolve final tone to tonic",
        )
        alt = AlternativeGenerator.generate(req, self.melody)
        self.assertEqual(len(alt.notes), 3)
        # Final note should resolve to C4 with duration 2
        self.assertEqual(alt.notes[2], Note("C4", Fraction(2, 1)))


if __name__ == "__main__":
    unittest.main()
