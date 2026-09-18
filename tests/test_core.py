"""Adversarial checks for the experimental reference contract (not audio accuracy)."""
import unittest
from dataclasses import FrozenInstanceError
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor

from reference.core import Grant, LockConstraint, MusicError, Note, Producer, create_workspace

PRODUCER = Producer('supplied-test-fixture', '1')


class CoreConformance(unittest.TestCase):
    def setup_workspace(self, **kwargs):
        self.workspace, (self.human,) = create_workspace(
            [Grant('musician', {'phrase-1'}, {'confirm', 'correct', 'restore'})], **kwargs)
        self.evidence = self.workspace.add_evidence(b'original performance bytes', 'audio/wav')
        self.observation = self.workspace.observe(self.evidence.id, 'Pitch drift; two rhythmic interpretations.', producer=PRODUCER)
        self.notes = (Note('A4', Fraction(1, 2)), Note('B4', Fraction(1, 2)))
        self.proposal = self.workspace.propose(self.observation.id, 'phrase-1', self.notes,
                                               'intended', 'AMBIGUOUS', 'interpreted', producer=PRODUCER)

    def reject(self, code, action):
        before = self.workspace.snapshot()
        with self.assertRaises(MusicError) as context:
            action()
        diagnostic = context.exception.diagnostic
        self.assertEqual(diagnostic.code, 'MUSICMCP-CORE-' + code)
        self.assertFalse(diagnostic.authoritative_state_modified)
        self.assertTrue(diagnostic.state_safe)
        self.assertEqual(diagnostic.rollback, 'not_required')
        self.assertTrue(diagnostic.trace_id)
        self.assertTrue(diagnostic.next_action)
        self.assertEqual(self.workspace.snapshot(), before)

    def test_evidence_and_competing_interpretations_never_establish_authority(self):
        self.setup_workspace()
        alternative = self.workspace.propose(self.observation.id, 'phrase-1',
            (Note('Ab4', Fraction(1)),), 'literal', 'UNRESOLVED', 'interpreted', producer=PRODUCER)
        self.assertNotEqual(alternative.id, self.proposal.id)
        self.assertEqual(self.workspace.preview(self.proposal.id).notes, self.notes)
        self.assertEqual(self.workspace.snapshot().revision, 0)
        self.assertEqual(self.workspace.evidence(self.evidence.id).data, b'original performance bytes')

    def test_confirm_correct_and_restore_preserve_lineage(self):
        self.setup_workspace()
        original = self.human.confirm(self.proposal.id, 0, 'Accept this phrase')
        correction = self.human.correct(self.proposal.id, (Note('C5', Fraction(1)),), 1,
                                        'Straight note, not the inferred rhythm')
        self.assertEqual(correction.origin, 'human')
        self.assertEqual(correction.evidence_id, self.evidence.id)
        self.workspace.propose(self.observation.id, 'phrase-1', self.notes,
                               'intended', 'HIGH', 'interpreted', producer=PRODUCER)
        self.assertEqual(self.workspace.snapshot().phrases[0].notes, correction.notes)
        restored = self.human.restore(original.number, 2, 'Restore first accepted phrase')
        self.assertEqual(restored.notes, self.notes)
        self.assertEqual(restored.origin, 'interpreted')
        self.assertEqual(restored.restored_from, 1)
        self.assertEqual(len(self.workspace.snapshot().history), 3)

    def test_generated_acceptance_does_not_become_human_authorship(self):
        self.setup_workspace()
        generated = self.workspace.propose(self.observation.id, 'phrase-1', self.notes,
                                           'intended', 'UNRESOLVED', 'generated', producer=PRODUCER)
        revision = self.human.confirm(generated.id, 0, 'Accept generated suggestion')
        self.assertEqual(revision.origin, 'generated')
        self.assertEqual(revision.actor, 'musician')

    def test_lock_rejects_confirm_and_correct(self):
        self.setup_workspace(constraints=[LockConstraint('phrase-1', 'test-composer', 'Keep melody unchanged')])
        self.reject('CONSTRAINT_CONFLICT', lambda: self.human.confirm(self.proposal.id, 0, 'Accept'))
        self.reject('CONSTRAINT_CONFLICT', lambda: self.human.correct(self.proposal.id, self.notes, 0, 'Correct'))

    def test_scope_and_operation_authority_do_not_expand(self):
        self.setup_workspace()
        other = self.workspace.propose(self.observation.id, 'other', self.notes,
                                       'intended', 'HIGH', 'interpreted', producer=PRODUCER)
        self.reject('UNAUTHORIZED', lambda: self.human.confirm(other.id, 0, 'Accept'))
        workspace, (session,) = create_workspace([Grant('reader', {'phrase-1'}, set())])
        evidence = workspace.add_evidence(b'x', 'audio/wav')
        observation = workspace.observe(evidence.id, 'Observed', producer=PRODUCER)
        proposal = workspace.propose(observation.id, 'phrase-1', self.notes, 'intended', 'HIGH', 'interpreted', producer=PRODUCER)
        self.workspace = workspace
        self.reject('UNAUTHORIZED', lambda: session.confirm(proposal.id, 0, 'Accept'))

    def test_stale_and_boolean_revision_are_rejected(self):
        self.setup_workspace()
        self.human.confirm(self.proposal.id, 0, 'Accept')
        self.reject('REVISION_CONFLICT', lambda: self.human.confirm(self.proposal.id, 0, 'Replay'))
        self.reject('VALIDATION_FAILED', lambda: self.human.confirm(self.proposal.id, True, 'Bypass'))

    def test_failed_policy_and_post_validation_leave_no_partial_revision(self):
        def crash(_):
            raise RuntimeError('private provider detail')
        for callback, value, code in [('policy', lambda _: False, 'POLICY_BLOCKED'),
                                     ('policy', crash, 'POLICY_UNAVAILABLE'),
                                     ('policy', lambda _: 'yes', 'POLICY_UNAVAILABLE'),
                                     ('validator', crash, 'TRANSACTION_FAILED'),
                                     ('validator', lambda _: False, 'VALIDATION_FAILED')]:
            with self.subTest(callback=callback, code=code):
                self.setup_workspace(**{callback: value})
                self.reject(code, lambda: self.human.confirm(self.proposal.id, 0, 'Accept'))
                self.assertEqual(self.workspace.evidence(self.evidence.id), self.evidence)

    def test_mutable_inputs_and_return_values_cannot_mutate_state(self):
        self.setup_workspace()
        supplied = list(self.notes)
        proposal = self.workspace.propose(self.observation.id, 'phrase-1', supplied, 'intended', 'HIGH', 'interpreted', producer=PRODUCER)
        supplied.clear()
        revision = self.human.confirm(proposal.id, 0, 'Accept')
        self.assertEqual(revision.notes, self.notes)
        with self.assertRaises(FrozenInstanceError):
            revision.origin = 'human'
        self.assertIsInstance(self.workspace.snapshot().history, tuple)

    def test_unknown_and_malformed_input_fail_closed(self):
        self.setup_workspace()
        self.reject('NOT_FOUND', lambda: self.human.confirm('invented', 0, 'Accept'))
        self.reject('NOT_FOUND', lambda: self.human.restore(99, 0, 'Restore'))
        self.reject('VALIDATION_FAILED', lambda: self.human.correct(self.proposal.id, (), 0, 'Empty'))
        self.reject('VALIDATION_FAILED', lambda: self.workspace.propose(self.observation.id, 'phrase-1',
            self.notes, 'intended', 0.9137, 'human', producer=PRODUCER))
        for pitch, duration in [('H4', Fraction(1)), ('A4', Fraction(0)), ('A4', 1.5)]:
            with self.subTest(pitch=pitch, duration=duration):
                self.reject('VALIDATION_FAILED', lambda: Note(pitch, duration))

    def test_concurrent_confirmations_have_one_winner(self):
        self.setup_workspace()
        def apply(_):
            try:
                self.human.confirm(self.proposal.id, 0, 'Concurrent accept')
                return 'success'
            except MusicError as error:
                return error.diagnostic.code
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(apply, range(2)))
        self.assertEqual(outcomes.count('success'), 1)
        self.assertEqual(outcomes.count('MUSICMCP-CORE-REVISION_CONFLICT'), 1)
        self.assertEqual(len(self.workspace.snapshot().history), 1)

    def test_reentrant_callback_cannot_publish_nested_changes(self):
        def reenter(_):
            self.human.confirm(self.proposal.id, 0, 'Nested write')
            return True
        self.setup_workspace(validator=reenter)
        self.reject('TRANSACTION_FAILED', lambda: self.human.confirm(self.proposal.id, 0, 'Outer write'))

    def test_capabilities_do_not_claim_transcription_or_mcp(self):
        self.setup_workspace()
        capabilities = dict(self.workspace.capabilities())
        self.assertTrue(capabilities['human_confirmation'])
        for absent in ('transcription', 'mcp_transport', 'durable_storage', 'musicxml'):
            self.assertFalse(capabilities[absent])

    def test_rejected_writes_report_attempted_operation_and_known_scope(self):
        self.setup_workspace()
        for operation, action in [
                ('correct', lambda: self.human.correct(self.proposal.id, [], 0, 'Correct')),
                ('confirm', lambda: self.human.confirm(self.proposal.id, True, 'Accept'))]:
            with self.subTest(operation=operation):
                with self.assertRaises(MusicError) as context:
                    action()
                self.assertEqual(context.exception.diagnostic.operation, operation)
                self.assertEqual(context.exception.diagnostic.scope, 'phrase-1')
        with self.assertRaises(MusicError) as context:
            self.human.confirm('missing', 0, 'Accept')
        self.assertEqual(context.exception.diagnostic.operation, 'confirm')
        self.assertEqual(context.exception.diagnostic.scope, 'workspace')

    def test_capacity_failure_preserves_history_and_diagnostic_context(self):
        self.setup_workspace()
        for expected in range(1024):
            self.human.confirm(self.proposal.id, expected, 'Explicit acceptance')
        self.reject('CAPACITY_EXCEEDED', lambda: self.human.confirm(self.proposal.id, 1024, 'One too many'))
        with self.assertRaises(MusicError) as context:
            self.human.restore(1, 1024, 'Restore beyond capacity')
        self.assertEqual(context.exception.diagnostic.operation, 'restore')
        self.assertEqual(context.exception.diagnostic.scope, 'phrase-1')

    def test_restore_checks_current_policy_and_preserves_unrelated_scope(self):
        blocked = [False]
        workspace, (human, limited) = create_workspace([
            Grant('musician', {'a', 'b'}, {'confirm', 'restore'}),
            Grant('other', {'b'}, {'restore'})], policy=lambda _: not blocked[0])
        self.workspace = workspace
        source = workspace.add_evidence(b'x', 'audio/wav')
        observation = workspace.observe(source.id, 'Supplied interpretation', producer=PRODUCER)
        proposals = [workspace.propose(observation.id, scope, (Note('A4', Fraction(1)),),
                                      'intended', 'HIGH', 'interpreted', producer=PRODUCER) for scope in ('a', 'b')]
        human.confirm(proposals[0].id, 0, 'Accept a')
        b = human.confirm(proposals[1].id, 1, 'Accept b')
        self.reject('UNAUTHORIZED', lambda: limited.restore(1, 2, 'Cannot reach a'))
        blocked[0] = True
        self.reject('POLICY_BLOCKED', lambda: human.restore(1, 2, 'Policy now denies'))
        blocked[0] = False
        human.restore(1, 2, 'Restore a')
        self.assertEqual(workspace.snapshot().phrases[1], b)

    def test_evidence_capacity_rejects_without_evicting_originals(self):
        self.setup_workspace()
        for _ in range(127):
            self.workspace.add_evidence(b'x', 'audio/wav')
        self.reject('CAPACITY_EXCEEDED', lambda: self.workspace.add_evidence(b'excess', 'audio/wav'))
        self.assertEqual(self.workspace.evidence(self.evidence.id), self.evidence)

    def test_read_and_proposal_errors_keep_public_operation(self):
        self.setup_workspace()
        for operation, action in [
                ('evidence', lambda: self.workspace.evidence('missing')),
                ('observation', lambda: self.workspace.observation('missing')),
                ('proposal', lambda: self.workspace.proposal('missing')),
                ('preview', lambda: self.workspace.preview('missing')),
                ('add_evidence', lambda: self.workspace.add_evidence(b'', 'audio/wav')),
                ('observe', lambda: self.workspace.observe('missing', 'Observation', producer=PRODUCER)),
                ('propose', lambda: self.workspace.propose('missing', 'phrase-1', self.notes,
                                                          'intended', 'HIGH', 'interpreted', producer=PRODUCER))]:
            with self.subTest(operation=operation):
                with self.assertRaises(MusicError) as context:
                    action()
                self.assertEqual(context.exception.diagnostic.operation, operation)


if __name__ == '__main__':
    unittest.main()
