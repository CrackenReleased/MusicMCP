"""Conformance tests for Provider-Neutral Evaluation Silo and TypeSafe Jev Adapter."""
from fractions import Fraction
import os
import unittest

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.evaluation import (
    DetectedEvent,
    DeterministicConformanceEvaluator,
    EvaluationProvenance,
    EvaluationRequest,
    EvaluationResult,
    EvaluationStatus,
    EvaluationType,
    EvidenceWindow,
    ProbabilityDistribution,
    TypeSafeJevAdapter,
)


class TestEvaluationSilo(unittest.TestCase):
    def setUp(self):
        self.producer = Producer("test-eval-producer", "0.1.01")
        self.melody = phrase([Note("C4", Fraction(1, 1)), Note("E4", Fraction(1, 1))])
        self.det_evaluator = DeterministicConformanceEvaluator()

    def test_provider_neutral_contract_primitives(self):
        req = EvaluationRequest(
            question="Which pitch was intended?",
            evaluation_type=EvaluationType.CHOICE,
            candidates=("F#4", "F4", "G4"),
            context={"onset": 12.8},
        )
        self.assertEqual(req.evaluation_type, EvaluationType.CHOICE)
        self.assertEqual(len(req.candidates), 3)

        probs = ProbabilityDistribution({"F#4": 0.80, "F4": 0.15, "G4": 0.05}, calibrated=True)
        self.assertTrue(probs.calibrated)
        self.assertAlmostEqual(sum(probs.probabilities.values()), 1.0)

        # Invalid probability distribution not summing to 1.0 raises ValueError
        with self.assertRaises(ValueError):
            ProbabilityDistribution({"A": 0.2, "B": 0.3})

    def test_deterministic_evaluator_locked_melody_check(self):
        # 1. Unmodified candidate
        req_clean = EvaluationRequest(
            question="Was locked melody modified?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"locked_phrase": self.melody, "candidate_phrase": self.melody},
        )
        res_clean = self.det_evaluator.evaluate(req_clean)
        self.assertEqual(res_clean.status, EvaluationStatus.SUCCESS)
        self.assertFalse(res_clean.decision)

        # 2. Modified candidate
        altered_melody = phrase([Note("C4", Fraction(1, 1)), Note("F4", Fraction(1, 1))])
        req_altered = EvaluationRequest(
            question="Was locked melody modified?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"locked_phrase": self.melody, "candidate_phrase": altered_melody},
        )
        res_altered = self.det_evaluator.evaluate(req_altered)
        self.assertTrue(res_altered.decision)

    def test_deterministic_evaluator_origin_provenance_check(self):
        # Verifies generated origin check
        req_gen = EvaluationRequest(
            question="Was generated material identified as generated?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"origin": "generated"},
        )
        res_gen = self.det_evaluator.evaluate(req_gen)
        self.assertTrue(res_gen.decision)

        req_human = EvaluationRequest(
            question="Was generated material identified as generated?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"origin": "human"},
        )
        res_human = self.det_evaluator.evaluate(req_human)
        self.assertFalse(res_human.decision)

    def test_deterministic_evaluator_authority_check(self):
        # Verifies actor authority check
        req_auth = EvaluationRequest(
            question="Did requested operation possess authority?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={
                "actor_operations": ("confirm",),
                "actor_scopes": ("melody",),
                "operation": "confirm",
                "scope": "melody",
            },
        )
        self.assertTrue(self.det_evaluator.evaluate(req_auth).decision)

        req_unauth = EvaluationRequest(
            question="Did requested operation possess authority?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={
                "actor_operations": ("confirm",),
                "actor_scopes": ("melody",),
                "operation": "correct",  # Not granted
                "scope": "melody",
            },
        )
        self.assertFalse(self.det_evaluator.evaluate(req_unauth).decision)

    def test_incremental_evidence_window_and_score_alignment(self):
        # Bounded temporal window for live score following
        event = DetectedEvent(
            event_id="obs-847",
            onset_seconds=12.842,
            duration_seconds=0.487,
            pitch_candidates=(("F#4", "high"), ("F4", "low")),
        )
        window = EvidenceWindow(
            source_id="live-mic-01",
            start_seconds=12.0,
            end_seconds=14.0,
            detected_events=(event,),
            score_context={"measure": 18},
        )
        self.assertEqual(len(window.detected_events), 1)

        req_align = EvaluationRequest(
            question="Which candidate score event corresponds to observed onset?",
            evaluation_type=EvaluationType.ALIGNMENT,
            candidates=("m18.voice1.event3", "m18.voice1.event4", "unresolved"),
            context={
                "observed_pitch": "F#4",
                "observed_onset": event.onset_seconds,
                "score_events": {
                    "m18.voice1.event3": ("F#4", 12.80),
                    "m18.voice1.event4": ("G4", 13.50),
                },
            },
        )
        res_align = self.det_evaluator.evaluate(req_align)
        self.assertEqual(res_align.decision, "m18.voice1.event3")
        self.assertEqual(res_align.uncertainty, "LOW")

    def test_typesafe_jev_adapter_graceful_degradation_without_key(self):
        # Ensure environment has no key
        old_key = os.environ.pop("TYPESAFE_API_KEY", None)
        try:
            adapter = TypeSafeJevAdapter()
            self.assertFalse(adapter.capabilities()["credentials_configured"])

            req = EvaluationRequest(
                question="Evaluate pitch candidate",
                evaluation_type=EvaluationType.CHOICE,
                candidates=("A4", "Bb4"),
            )
            res = adapter.evaluate(req)

            # Invariant: Must return CAPABILITY_UNAVAILABLE without crashing or modifying core
            self.assertEqual(res.status, EvaluationStatus.CAPABILITY_UNAVAILABLE)
            self.assertIn("not configured", res.explanation)
            self.assertFalse(res.provenance.credentials_configured)
        finally:
            if old_key:
                os.environ["TYPESAFE_API_KEY"] = old_key

    def test_typesafe_jev_adapter_secret_redaction_and_mock_execution(self):
        fake_secret = "ts_live_secret_key_12345"
        mock_client = type("MockJev", (), {
            "evaluate": lambda self, req: {
                "decision": "F#4",
                "probabilities": {"F#4": 0.88, "F4": 0.12},
                "explanation": f"Jev with key {fake_secret} resolved F#4 as best match.",
            }
        })()

        adapter = TypeSafeJevAdapter(api_key=fake_secret, mock_client=mock_client)
        req = EvaluationRequest(
            question="Which pitch was intended?",
            evaluation_type=EvaluationType.CHOICE,
            candidates=("F#4", "F4"),
        )
        res = adapter.evaluate(req)

        self.assertEqual(res.status, EvaluationStatus.SUCCESS)
        self.assertEqual(res.decision, "F#4")
        self.assertIsNotNone(res.probabilities)
        self.assertEqual(res.probabilities.probabilities["F#4"], 0.88)
        self.assertTrue(res.provenance.credentials_configured)

        # Invariant: Secret key MUST be redacted from explanation
        self.assertNotIn(fake_secret, res.explanation)
        self.assertIn("[REDACTED_SECRET]", res.explanation)

    def test_evaluator_cannot_mutate_authoritative_state(self):
        # Verifies that evaluators do not possess AuthoritySession and cannot change Workspace revision
        ws, _ = create_workspace([Grant("composer-joel", {"melody"}, {"confirm"})])
        initial_rev = ws.snapshot().revision

        req = EvaluationRequest(
            question="Is melody in range?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"scope": "melody"},
        )
        res = self.det_evaluator.evaluate(req)

        # Invariant: Authoritative state MUST remain completely unaffected by evaluation
        self.assertEqual(ws.snapshot().revision, initial_rev)


if __name__ == "__main__":
    unittest.main()
