"""Foundational attribution and uncertainty regression coverage."""
from dataclasses import FrozenInstanceError
from fractions import Fraction
import unittest

import reference.core as core


class ProvenanceConformance(unittest.TestCase):
    def test_missing_producer_is_rejected_instead_of_retaining_unattributed_analysis(self):
        workspace, _ = core.create_workspace([])
        evidence = workspace.add_evidence(b'performance', 'audio/wav')
        with self.assertRaises(core.MusicError) as context:
            workspace.observe(evidence.id, 'Unattributed observation')
        self.assertEqual(context.exception.diagnostic.code, 'MUSICMCP-CORE-VALIDATION_FAILED')
        self.assertEqual(workspace.snapshot().revision, 0)

    def test_observer_and_interpreter_provenance_survive_correction_and_restore(self):
        observer = core.Producer('fixture.observer', '1.2.3')
        interpreter = core.Producer('fixture.interpreter', '4.5.6')
        workspace, (human,) = core.create_workspace([
            core.Grant('musician', {'phrase'}, {'confirm', 'correct', 'restore'})])
        evidence = workspace.add_evidence(b'performance', 'audio/wav')
        observed = workspace.observe(evidence.id, 'Observed pitch', producer=observer)
        generated = workspace.propose(observed.id, 'phrase', [core.Note('A4', Fraction(1))],
                                      'intended', 'LOW', 'generated', producer=interpreter)
        human.confirm(generated.id, 0, 'Accept this generated suggestion')
        human.correct(generated.id, [core.Note('B4', Fraction(1))], 1, 'Correct the pitch')
        restored = human.restore(1, 2, 'Restore generated phrase')
        self.assertEqual(restored.origin, 'generated')
        self.assertEqual(workspace.proposal(restored.proposal_id).producer, interpreter)
        self.assertEqual(workspace.observation(restored.observation_id).producer, observer)
        self.assertEqual(workspace.evidence(restored.evidence_id), evidence)
        with self.assertRaises(FrozenInstanceError):
            generated.producer.version = 'forged'

    def test_invalid_producer_is_rejected_at_both_ingestion_boundaries(self):
        workspace, _ = core.create_workspace([])
        evidence = workspace.add_evidence(b'x', 'audio/wav')
        observed = workspace.observe(evidence.id, 'Observed', producer=core.Producer('analyzer', '1'))
        for invalid in (None, '', {'identity': 'analyzer', 'version': '1'}, True):
            for action in (
                lambda: workspace.observe(evidence.id, 'Observed', producer=invalid),
                lambda: workspace.propose(observed.id, 'phrase', [core.Note('A4', Fraction(1))],
                                          'intended', 'HIGH', 'interpreted', producer=invalid)):
                with self.subTest(invalid=invalid), self.assertRaises(core.MusicError) as context:
                    action()
                self.assertEqual(context.exception.diagnostic.code, 'MUSICMCP-CORE-VALIDATION_FAILED')
        for identity, version in (('', '1'), ('a', ''), ('a', True), ('x' * 129, '1')):
            with self.assertRaises(core.MusicError):
                core.Producer(identity, version)

    def test_constraint_origin_and_reason_are_immutable_and_retained_in_history(self):
        lock = core.LockConstraint('melody', 'composer:alice', 'Keep the original melody untouched')
        supplied = [lock]
        workspace, (human,) = core.create_workspace([
            core.Grant('arranger', {'melody', 'harmony'}, {'confirm', 'correct', 'restore'})], constraints=supplied)
        supplied.clear()
        evidence = workspace.add_evidence(b'x', 'audio/wav')
        producer = core.Producer('fixture', '1')
        observed = workspace.observe(evidence.id, 'Observed', producer=producer)
        proposals = [workspace.propose(observed.id, scope, [core.Note('A4', Fraction(1))],
                                      'intended', 'HIGH', 'interpreted', producer=producer)
                     for scope in ('melody', 'harmony')]
        for action in (lambda: human.confirm(proposals[0].id, 0, 'Change melody'),
                       lambda: human.correct(proposals[0].id, proposals[0].notes, 0, 'Correct melody')):
            with self.assertRaises(core.MusicError) as context:
                action()
            self.assertEqual(context.exception.diagnostic.code, 'MUSICMCP-CORE-CONSTRAINT_CONFLICT')
        revision = human.confirm(proposals[1].id, 0, 'Accept harmony')
        restored = human.restore(1, 1, 'Restore harmony')
        self.assertEqual(revision.constraints, (lock,))
        self.assertEqual(restored.constraints, (lock,))
        with self.assertRaises(FrozenInstanceError):
            lock.reason = 'Discard history'

    def test_malformed_or_conflicting_constraints_fail_at_host_setup(self):
        lock = core.LockConstraint('melody', 'composer', 'Preserve')
        for constraints in (['melody'], [lock, lock], 'melody', [None]):
            with self.subTest(constraints=constraints), self.assertRaises(core.MusicError):
                core.create_workspace([], constraints=constraints)
        for fields in (('', 'composer', 'Preserve'), ('melody', '', 'Preserve'), ('melody', 'composer', '')):
            with self.assertRaises(core.MusicError):
                core.LockConstraint(*fields)

    def test_every_uncertainty_state_remains_provisional_until_human_action(self):
        workspace, (human,) = core.create_workspace([core.Grant('musician', {'phrase'}, {'confirm'})])
        producer = core.Producer('fixture', '1')
        evidence = workspace.add_evidence(b'x', 'audio/wav')
        observed = workspace.observe(evidence.id, 'Observed', producer=producer)
        for label in sorted(core.UNCERTAINTY):
            proposal = workspace.propose(observed.id, 'phrase', [core.Note('A4', Fraction(1))],
                                         'intended', label, 'interpreted', producer=producer)
            self.assertEqual(workspace.snapshot().revision, 0)
            self.assertEqual(workspace.preview(proposal.id).uncertainty, label)
        human.confirm(proposal.id, 0, 'Explicit human choice despite uncertainty')
        self.assertEqual(workspace.snapshot().revision, 1)


if __name__ == '__main__':
    unittest.main()
