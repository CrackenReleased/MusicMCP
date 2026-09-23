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

    def test_live_transport_constructs_request_and_preserves_provider_result(self):
        import json
        from io import BytesIO
        from unittest.mock import patch
        req = EvaluationRequest(question="Which pitch?", evaluation_type=EvaluationType.CHOICE,
                                candidates=("A4", "Bb4"), context={"scope": "melody"})
        response = {"decision": "Bb4", "probabilities": {"A4": 0.2, "Bb4": 0.8},
                    "calibrated": False, "uncertainty": "MEDIUM", "explanation": "Measured response"}
        adapter = TypeSafeJevAdapter(api_key="synthetic-test-key", endpoint="https://provider.invalid/evaluate")
        with patch("urllib.request.urlopen", return_value=BytesIO(json.dumps(response).encode())) as transport:
            result = adapter.evaluate(req)
        transport.assert_called_once()
        outgoing = transport.call_args.args[0]
        self.assertEqual(outgoing.get_method(), "POST")
        self.assertEqual(outgoing.full_url, "https://provider.invalid/evaluate")
        self.assertEqual(outgoing.get_header("Authorization"), "Bearer synthetic-test-key")
        self.assertEqual(json.loads(outgoing.data), {"question": req.question, "type": req.evaluation_type.value,
                         "candidates": list(req.candidates), "context": req.context, "model": "jev-fast"})
        self.assertEqual(result.status, EvaluationStatus.SUCCESS)
        self.assertEqual(result.request_id, req.request_id)
        self.assertEqual(result.decision, "Bb4")
        self.assertEqual(result.uncertainty, "MEDIUM")
        self.assertEqual(result.probabilities.probabilities, response["probabilities"])
        self.assertFalse(result.probabilities.calibrated)

    def test_unsupported_questions_never_invent_a_judgment(self):
        for kind in (EvaluationType.BOOLEAN, EvaluationType.CHOICE, EvaluationType.SCORE):
            with self.subTest(kind=kind):
                req = EvaluationRequest(question="Which interpretation is most expressive?",
                                        evaluation_type=kind, candidates=("first", "second"))
                result = self.det_evaluator.evaluate(req)
                self.assertEqual(result.status, EvaluationStatus.CAPABILITY_UNAVAILABLE)
                self.assertIsNone(result.decision)
                self.assertIsNone(result.probabilities)
                self.assertEqual(result.uncertainty, "UNRESOLVED")

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
        ws, (session,) = create_workspace([Grant("composer-joel", {"melody"}, {"confirm"})])
        evidence = ws.add_evidence(b"confirmed evidence", "audio/wav")
        observation = ws.observe(evidence.id, "take", producer=self.producer)
        proposal = ws.propose(observation.id, "melody", self.melody, "intended", "HIGH", "interpreted", producer=self.producer)
        # Evaluators receive only a request, never the host session.
        session.confirm(proposal.id, 0, "human confirmation")
        initial_state = ws.snapshot()

        req = EvaluationRequest(
            question="Is melody in range?",
            evaluation_type=EvaluationType.BOOLEAN,
            context={"scope": "melody"},
        )
        res = self.det_evaluator.evaluate(req)

        # Exercise each outcome against an already confirmed snapshot.
        self.assertEqual(res.status, EvaluationStatus.CAPABILITY_UNAVAILABLE)
        from types import SimpleNamespace
        outcomes = [
            self.det_evaluator.evaluate(EvaluationRequest("Was locked melody modified?", EvaluationType.BOOLEAN)),
            self.det_evaluator.evaluate(EvaluationRequest("Was locked melody modified?", EvaluationType.BOOLEAN,
                                                        context={"locked_phrase": self.melody, "candidate_phrase": self.melody})),
        ]
        for payload in ({"decision": False}, {"decision": "invalid"}, {"decision": True, "uncertainty": "AMBIGUOUS"}):
            adapter = TypeSafeJevAdapter(api_key="test-only", mock_client=SimpleNamespace(evaluate=lambda _, p=payload: p))
            outcomes.append(adapter.evaluate(req))
        self.assertEqual({r.status for r in outcomes}, {EvaluationStatus.SUCCESS, EvaluationStatus.ERROR,
                                                       EvaluationStatus.UNRESOLVED, EvaluationStatus.AMBIGUOUS})
        self.assertEqual(ws.snapshot(), initial_state)


    def test_typesafe_jev_adapter_live_invalid_key_does_not_fabricate_success(self):
        # Synthetic invalid credentials must not fabricate SUCCESS or calibrated probabilities
        adapter = TypeSafeJevAdapter(api_key="ts_invalid_synthetic_key_xyz", endpoint="http://127.0.0.1:9")
        req = EvaluationRequest(
            question="Which pitch was intended?",
            evaluation_type=EvaluationType.CHOICE,
            candidates=("F#4", "F4"),
        )
        from unittest.mock import patch
        with patch("urllib.request.urlopen", side_effect=OSError("provider unavailable")) as transport:
            res = adapter.evaluate(req)
        transport.assert_called_once()
        self.assertIn("provider unavailable", res.explanation)

        # Invariant: Must report ERROR, never fabricate SUCCESS with calibrated probabilities
        self.assertNotEqual(res.status, EvaluationStatus.SUCCESS)
        self.assertEqual(res.status, EvaluationStatus.ERROR)
        self.assertIsNone(res.probabilities)
        self.assertIsNone(res.decision)
        self.assertEqual(res.uncertainty, "UNRESOLVED")
        self.assertIn("TypeSafe Jev adapter error", res.explanation)
        self.assertNotIn("ts_invalid_synthetic_key_xyz", res.explanation)


class TestEvaluationValidation(unittest.TestCase):
    def setUp(self):
        self.rules = [
            ("Was locked melody modified?", EvaluationType.BOOLEAN,
             {"locked_phrase": (Note("C4", Fraction(1)),), "candidate_phrase": ()}),
            ("Was generated material identified as generated?", EvaluationType.BOOLEAN, {"origin": "human"}),
            ("Did requested operation possess authority?", EvaluationType.BOOLEAN,
             {"actor_operations": (), "actor_scopes": (), "operation": "confirm", "scope": "melody"}),
            ("Align observed onset", EvaluationType.ALIGNMENT,
             {"observed_pitch": "C4", "observed_onset": 0.0, "score_events": {"event": ("C4", 0.0)}}),
        ]
        self.evaluator = DeterministicConformanceEvaluator()

    def test_missing_each_required_field_is_unresolved(self):
        for question, kind, context in self.rules:
            for key in context:
                for absent in (True, False):
                    with self.subTest(question=question, key=key, absent=absent):
                        partial = dict(context)
                        if absent:
                            del partial[key]
                        else:
                            partial[key] = None
                        result = self.evaluator.evaluate(EvaluationRequest(question, kind, ("event",), partial))
                        self.assertEqual(result.status, EvaluationStatus.UNRESOLVED)
                        self.assertIsNone(result.decision)
                        self.assertIn(key, result.explanation)

    def test_malformed_rule_inputs_return_error(self):
        cases = [(0, "locked_phrase", "C4"), (1, "origin", "unknown"),
                 (2, "actor_operations", "confirm"), (2, "scope", []),
                 (3, "observed_onset", float("nan")), (3, "observed_onset", True),
                 (3, "score_events", {"event": ("C4", float("inf"))})]
        for index, key, value in cases:
            question, kind, context = self.rules[index]
            with self.subTest(key=key, value=value):
                result = self.evaluator.evaluate(EvaluationRequest(question, kind, ("event",), {**context, key: value}))
                self.assertEqual(result.status, EvaluationStatus.ERROR)
                self.assertIsNone(result.decision)

    def test_alignment_without_candidate_evidence_is_unresolved(self):
        question, kind, context = self.rules[-1]
        result = self.evaluator.evaluate(EvaluationRequest(question, kind, ("event",), {**context, "score_events": {}}))
        self.assertEqual(result.status, EvaluationStatus.UNRESOLVED)
        self.assertIsNone(result.decision)

    def test_valid_empty_grants_and_zero_onset_are_evidence(self):
        for question, kind, context in self.rules:
            result = self.evaluator.evaluate(EvaluationRequest(question, kind, ("event",), context))
            self.assertEqual(result.status, EvaluationStatus.SUCCESS)
        question, _, context = self.rules[0]
        result = self.evaluator.evaluate(EvaluationRequest(question, EvaluationType.SCORE, context=context))
        self.assertEqual(result.status, EvaluationStatus.CAPABILITY_UNAVAILABLE)

    def _provider_result(self, kind, payload, http):
        import json
        from io import BytesIO
        from types import SimpleNamespace
        from unittest.mock import patch
        request = EvaluationRequest("Evaluate evidence", kind, ("a", "b", "unresolved"))
        if http:
            with patch("urllib.request.urlopen", return_value=BytesIO(json.dumps(payload).encode())):
                return TypeSafeJevAdapter(api_key="test-only").evaluate(request)
        return TypeSafeJevAdapter(api_key="test-only", mock_client=SimpleNamespace(evaluate=lambda _: payload)).evaluate(request)

    def test_malformed_provider_results_rejected_on_both_paths(self):
        cases = [(EvaluationType.BOOLEAN, {"decision": value}) for value in (None, 0, "false")]
        cases += [(EvaluationType.CHOICE, {"decision": "outside"}),
                  (EvaluationType.ALIGNMENT, {"decision": 1})]
        cases += [(EvaluationType.SCORE, {"decision": value}) for value in (True, -0.1, 1.1, float("nan"), float("inf"))]
        cases += [(EvaluationType.CHOICE, payload) for payload in (
            {}, [], {"decision": "a", "probabilities": {}},
            {"decision": "a", "probabilities": {"a": -0.2, "b": 1.2}},
            {"decision": "a", "probabilities": {"outside": 1.0}},
            {"decision": "a", "calibrated": "true"},
            {"decision": "a", "uncertainty": "CERTAIN"},
            {"decision": "a", "explanation": []},
            {"decision": "a", "status": "ERROR"},
        )]
        for http in (False, True):
            for kind, payload in cases:
                with self.subTest(http=http, kind=kind, payload=payload):
                    result = self._provider_result(kind, payload, http)
                    self.assertEqual(result.status, EvaluationStatus.ERROR)
                    self.assertIsNone(result.decision)
                    self.assertIsNone(result.probabilities)

    def test_valid_negative_zero_and_unresolved_results(self):
        for http in (False, True):
            for kind, decision in ((EvaluationType.BOOLEAN, False), (EvaluationType.SCORE, 0),
                                   (EvaluationType.CHOICE, "b"), (EvaluationType.ALIGNMENT, "unresolved")):
                with self.subTest(http=http, kind=kind):
                    result = self._provider_result(kind, {"decision": decision}, http)
                    expected = EvaluationStatus.UNRESOLVED if decision == "unresolved" else EvaluationStatus.SUCCESS
                    self.assertEqual(result.status, expected)
                    self.assertEqual(result.decision, decision)
            result = self._provider_result(EvaluationType.CHOICE, {"decision": "a", "probabilities": {"a": 1.0}}, http)
            self.assertFalse(result.probabilities.calibrated)

    def test_probability_values_are_finite_bounded_and_normalized(self):
        for values in ({"a": -0.2, "b": 1.2}, {"a": True}, {"a": 0.96}, {"a": float("nan")}, {}):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    ProbabilityDistribution(values)

    def test_request_rejects_invalid_types_and_candidates(self):
        for overrides in ({"evaluation_type": "BOOLEAN"}, {"context": []}, {"candidates": ("a", "a")},
                          {"candidates": "abc"}, {"candidates": ("",)}, {"question": 3}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    EvaluationRequest(**{"question": "Evaluate", "evaluation_type": EvaluationType.CHOICE,
                                         "candidates": ("a",), **overrides})


if __name__ == "__main__":
    unittest.main()
