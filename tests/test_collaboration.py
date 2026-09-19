"""Conformance tests for the Scoped Multi-Role Collaboration Silo."""
from fractions import Fraction
import unittest

from reference.collaboration import (
    CollaborationError,
    CollaborationManager,
    Role,
)
from reference.core import (
    MusicError,
    LockConstraint,
    Note,
    Producer,
    phrase,
)


class TestCollaboration(unittest.TestCase):
    def setUp(self):
        self.mgr = CollaborationManager()
        self.producer = Producer("test-producer", "0.1.01")

        # Register primary scope ownerships
        self.mgr.register_owner("lead_melody", "composer-joel", Role.COMPOSER, "Thematic vocal lead")
        self.mgr.register_owner("harmony_voices", "composer-joel", Role.COMPOSER, "Vocal harmony")
        self.mgr.register_owner("rhythm_section", "arranger-sarah", Role.ARRANGER, "Bass and groove")

        # Actors with their broad granted capabilities in the workspace
        actors = [
            ("composer-joel", {"lead_melody", "harmony_voices", "rhythm_section"}, {"confirm", "correct", "restore"}),
            ("arranger-sarah", {"lead_melody", "harmony_voices", "rhythm_section"}, {"confirm", "correct", "restore"}),
            ("performer-david", {"lead_melody"}, {"confirm"}),
        ]
        self.ws, self.sessions = self.mgr.build_workspace(actors)

        # Base audio evidence and proposal fixture
        ev = self.ws.add_evidence(b"RIFF....WAVE audio take", "audio/wav")
        obs = self.ws.observe(ev.id, "Lead take performance", producer=self.producer)
        self.lead_notes = phrase([Note("C4", Fraction(1, 1)), Note("E4", Fraction(1, 1)), Note("G4", Fraction(2, 1))])
        self.lead_prop = self.ws.propose(obs.id, "lead_melody", self.lead_notes, "intended", "HIGH", "interpreted", producer=self.producer)

    def test_owner_can_confirm_and_correct(self):
        # Composer owns lead_melody and can confirm
        sess_composer = self.sessions["composer-joel"]
        rev1 = sess_composer.confirm(self.lead_prop.id, 0, "Composer approved lead melody")
        self.assertEqual(rev1.number, 1)
        self.assertEqual(rev1.actor, "composer-joel")

    def test_non_owner_blocked_without_delegation(self):
        # Arranger Sarah does not own lead_melody and has no delegation
        sess_arranger = self.sessions["arranger-sarah"]
        with self.assertRaises(MusicError) as ctx:
            sess_arranger.confirm(self.lead_prop.id, 0, "Arranger tries to unilaterally accept lead take")
        self.assertIn("POLICY_BLOCKED", ctx.exception.diagnostic.code)

    def test_delegation_allows_mutation(self):
        # Composer delegates harmony_voices to Arranger Sarah
        grant = self.mgr.delegate(
            delegator="composer-joel",
            delegatee="arranger-sarah",
            scope="harmony_voices",
            operations={"confirm", "correct"},
            reason="Sarah arranges backing vocal harmony",
        )
        self.assertTrue(grant.active)

        # Propose harmony
        ev = self.ws.add_evidence(b"harmony audio bytes", "audio/wav")
        obs = self.ws.observe(ev.id, "Harmony take", producer=self.producer)
        h_notes = phrase([Note("E4", Fraction(1, 1)), Note("G4", Fraction(1, 1)), Note("C5", Fraction(2, 1))])
        h_prop = self.ws.propose(obs.id, "harmony_voices", h_notes, "intended", "HIGH", "interpreted", producer=self.producer)

        # Arranger Sarah can now confirm harmony_voices under active delegation
        sess_arranger = self.sessions["arranger-sarah"]
        rev1 = sess_arranger.confirm(h_prop.id, 0, "Arranger confirms harmony under delegation")
        self.assertEqual(rev1.number, 1)
        self.assertEqual(rev1.actor, "arranger-sarah")
        self.assertEqual(rev1.scope, "harmony_voices")

    def test_revocation_immediately_blocks_subsequent_mutations(self):
        # Composer delegates and then revokes
        grant = self.mgr.delegate("composer-joel", "arranger-sarah", "harmony_voices", {"confirm", "correct"}, "Temporary")
        self.mgr.revoke("composer-joel", grant.id, "Delegation finished")

        # Sarah tries to confirm
        ev = self.ws.add_evidence(b"audio", "audio/wav")
        obs = self.ws.observe(ev.id, "Take", producer=self.producer)
        h_prop = self.ws.propose(obs.id, "harmony_voices", self.lead_notes, "intended", "HIGH", "interpreted", producer=self.producer)

        sess_arranger = self.sessions["arranger-sarah"]
        with self.assertRaises(MusicError) as ctx:
            sess_arranger.confirm(h_prop.id, 0, "Sarah tries to confirm after revocation")
        self.assertIn("POLICY_BLOCKED", ctx.exception.diagnostic.code)

    def test_cannot_delegate_unowned_scope(self):
        # Arranger Sarah cannot delegate lead_melody because she does not own it
        with self.assertRaises(MusicError) as ctx:
            self.mgr.delegate("arranger-sarah", "performer-david", "lead_melody", {"confirm"}, "Illegitimate delegation")
        self.assertIn("NOT_SCOPE_OWNER", ctx.exception.diagnostic.code)


if __name__ == "__main__":
    unittest.main()
