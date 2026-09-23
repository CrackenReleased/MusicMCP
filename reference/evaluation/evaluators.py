"""Evaluation Provider Implementations: Deterministic Conformance Evaluator and TypeSafe Jev Adapter.

Adheres strictly to Python 3.11+ standard library only: os, time, math, typing.
Enforces BYOK credential handling, secret redaction, and strict authority boundaries.
"""
import math
import json
import os
import time
from typing import Any, Mapping

from reference.core import Note

from reference.evaluation.contract import (
    EvaluationProvenance,
    EvaluationProvider,
    EvaluationRequest,
    EvaluationResult,
    EvaluationStatus,
    EvaluationType,
    ProbabilityDistribution,
)

JEV_PROVIDER_NAME = "typesafe_jev"
DETERMINISTIC_PROVIDER_NAME = "deterministic_conformance"


def _finite_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _context_problem(request):
    """Check rule-specific evidence before any default or comparison is applied."""
    question, ctx = request.question.lower(), request.context
    notes = lambda value: isinstance(value, (tuple, list)) and all(isinstance(n, Note) for n in value)
    strings = lambda value: isinstance(value, (tuple, list, set, frozenset)) and all(_text(v) for v in value)
    onset = lambda value: _finite_number(value) and value >= 0
    checks = None
    if "locked melody modified" in question or "locked scope modified" in question:
        checks = {"locked_phrase": notes, "candidate_phrase": notes}
    elif "identified as generated" in question or "provenance preserved" in question:
        checks = {"origin": lambda value: isinstance(value, str) and value in ("human", "generated", "interpreted")}
    elif "possess authority" in question or "authorized operation" in question:
        checks = {"actor_operations": strings, "actor_scopes": strings, "operation": _text, "scope": _text}
    if checks is not None and request.evaluation_type != EvaluationType.BOOLEAN:
        return EvaluationStatus.CAPABILITY_UNAVAILABLE, "This named rule requires BOOLEAN evaluation."
    if checks is None and request.evaluation_type == EvaluationType.ALIGNMENT:
        def events(value):
            return isinstance(value, Mapping) and all(
                _text(key) and isinstance(event, (tuple, list)) and len(event) == 2
                and _text(event[0]) and onset(event[1]) for key, event in value.items())
        checks = {"observed_pitch": _text, "observed_onset": onset, "score_events": events}
    for key, valid in (checks or {}).items():
        if key not in ctx or ctx[key] is None:
            return EvaluationStatus.UNRESOLVED, f"Missing evidence: {key}. Supply this field before evaluating."
        if not valid(ctx[key]):
            return EvaluationStatus.ERROR, f"Malformed evidence: {key}. Check the evaluation contract."
    if request.evaluation_type == EvaluationType.ALIGNMENT and checks:
        if any(c != "unresolved" and c not in ctx["score_events"] for c in request.candidates) or not any(
            c != "unresolved" and c in ctx["score_events"] for c in request.candidates
        ):
            return EvaluationStatus.UNRESOLVED, "Missing score_events evidence for candidate comparison."
    return None


def _validated_response(request, response):
    """One response boundary shared by injected clients and HTTP providers."""
    if not isinstance(response, Mapping):
        raise ValueError("Provider response must be an object.")
    if response.get("status", "SUCCESS") != "SUCCESS":
        raise ValueError("Provider did not report a successful evaluation.")
    decision = response.get("decision")
    kind = request.evaluation_type
    if kind == EvaluationType.BOOLEAN:
        valid = type(decision) is bool
    elif kind == EvaluationType.SCORE:
        valid = _finite_number(decision) and 0 <= decision <= 1
    else:
        valid = isinstance(decision, str) and decision in request.candidates
    if not valid:
        raise ValueError("Provider decision must match the requested type, candidates, and score range.")
    calibrated = response.get("calibrated", False)
    if type(calibrated) is not bool:
        raise ValueError("Provider calibrated field must be Boolean.")
    raw_probabilities = response.get("probabilities")
    probabilities = None
    if raw_probabilities is not None:
        probabilities = ProbabilityDistribution(raw_probabilities, calibrated=calibrated)
        allowed = {"true", "false"} if kind == EvaluationType.BOOLEAN else set(request.candidates)
        if kind == EvaluationType.SCORE or not set(raw_probabilities).issubset(allowed):
            raise ValueError("Provider probability keys do not match the requested outcomes.")
    explanation = response.get("explanation", "Provider evaluation completed.")
    uncertainty = response.get("uncertainty", "LOW")
    if not isinstance(explanation, str):
        raise ValueError("Provider explanation must be text.")
    if not isinstance(uncertainty, str) or uncertainty not in ("LOW", "MEDIUM", "HIGH", "AMBIGUOUS", "UNRESOLVED"):
        raise ValueError("Provider uncertainty must use a supported label.")
    status = EvaluationStatus.SUCCESS
    if kind == EvaluationType.ALIGNMENT and decision == "unresolved":
        uncertainty = "UNRESOLVED"
    if uncertainty in ("AMBIGUOUS", "UNRESOLVED"):
        status = EvaluationStatus(uncertainty)
    return decision, probabilities, explanation, uncertainty, status


class DeterministicConformanceEvaluator(EvaluationProvider):
    """Zero-dependency local evaluator for atomic conformance and score alignment rules."""

    @property
    def name(self) -> str:
        return DETERMINISTIC_PROVIDER_NAME

    @property
    def version(self) -> str:
        return "0.1.01"

    def capabilities(self) -> dict[str, bool]:
        return {
            "boolean_evaluation": True,
            "choice_evaluation": False,
            "score_evaluation": False,
            "alignment_evaluation": True,
            "offline_only": True,
            "incremental_compatible": True,
        }

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        start_time = time.time()
        q_lower = request.question.lower()
        ctx = request.context
        problem = _context_problem(request)
        if problem:
            status, explanation = problem
            return EvaluationResult(request.request_id, EvaluationProvenance(self.name, "rule-input-check"),
                                    status, None, uncertainty="UNRESOLVED", explanation=explanation)

        # 1. Atomic Conformance: "Was locked melody modified?"
        if "locked melody modified" in q_lower or "locked scope modified" in q_lower:
            orig = ctx.get("locked_phrase")
            cand = ctx.get("candidate_phrase")
            is_modified = orig != cand
            latency = (time.time() - start_time) * 1000.0
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(self.name, "rule-locked-diff", latency_ms=latency),
                status=EvaluationStatus.SUCCESS,
                decision=is_modified,
                explanation=f"Locked phrase comparison: modified={is_modified}.",
            )

        # 2. Atomic Conformance: "Was generated material identified as generated?"
        if "identified as generated" in q_lower or "provenance preserved" in q_lower:
            origin = ctx.get("origin")
            is_gen = (origin == "generated")
            latency = (time.time() - start_time) * 1000.0
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(self.name, "rule-origin-check", latency_ms=latency),
                status=EvaluationStatus.SUCCESS,
                decision=is_gen,
                explanation=f"Origin check: recorded origin='{origin}', matches generated={is_gen}.",
            )

        # 3. Atomic Conformance: "Did requested operation possess authority?"
        if "possess authority" in q_lower or "authorized operation" in q_lower:
            actor_ops = set(ctx["actor_operations"])
            target_op = ctx.get("operation")
            actor_scopes = set(ctx["actor_scopes"])
            target_scope = ctx.get("scope")
            has_auth = (target_op in actor_ops) and (target_scope in actor_scopes)
            latency = (time.time() - start_time) * 1000.0
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(self.name, "rule-authority-check", latency_ms=latency),
                status=EvaluationStatus.SUCCESS,
                decision=has_auth,
                explanation=f"Authority matrix check: op in {actor_ops}, scope in {actor_scopes} -> {has_auth}.",
            )

        # 4. Atomic Alignment: Which candidate score event corresponds to observed onset?
        if request.evaluation_type == EvaluationType.ALIGNMENT:
            obs_pitch = ctx.get("observed_pitch")
            obs_onset = ctx["observed_onset"]
            score_events = ctx["score_events"]  # Map of event_id to (pitch, onset)

            best_candidate = "unresolved"
            best_score = float("inf")

            for cand_id in request.candidates:
                if cand_id in score_events:
                    cand_pitch, cand_onset = score_events[cand_id]
                    # Score based on pitch match and onset difference
                    pitch_match = (cand_pitch == obs_pitch)
                    onset_diff = abs(cand_onset - obs_onset)
                    cost = (0.0 if pitch_match else 10.0) + onset_diff
                    if cost < best_score:
                        best_score = cost
                        best_candidate = cand_id

            latency = (time.time() - start_time) * 1000.0
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(self.name, "rule-score-alignment", latency_ms=latency),
                status=EvaluationStatus.SUCCESS if best_candidate != "unresolved" else EvaluationStatus.AMBIGUOUS,
                decision=best_candidate,
                uncertainty="LOW" if best_score < 0.2 else "MEDIUM",
                explanation=f"Aligned to '{best_candidate}' with cost {best_score:.3f}.",
            )

        # No implemented rule can justify an arbitrary judgment.
        latency = (time.time() - start_time) * 1000.0
        return EvaluationResult(
            request_id=request.request_id,
            provenance=EvaluationProvenance(self.name, "rule-unavailable", latency_ms=latency),
            status=EvaluationStatus.CAPABILITY_UNAVAILABLE,
            decision=None,
            uncertainty="UNRESOLVED",
            explanation="No deterministic rule supports this evaluation question; no judgment was made.",
        )


class TypeSafeJevAdapter(EvaluationProvider):
    """Bring-Your-Own-Key (BYOK) adapter for TypeSafe Jev structured evaluations.

    Requires TYPESAFE_API_KEY environment variable. If absent, gracefully returns
    status=CAPABILITY_UNAVAILABLE without corrupting core state or crashing.
    """

    def __init__(self, api_key: str | None = None, model: str = "jev-fast", mock_client: Any = None, endpoint: str | None = None):
        self._api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        self._model = model
        self._mock_client = mock_client
        self._endpoint = endpoint or os.environ.get("TYPESAFE_API_ENDPOINT", "https://api.typesafe.ai/v1/evaluate")

    @property
    def name(self) -> str:
        return JEV_PROVIDER_NAME

    @property
    def version(self) -> str:
        return "0.1.01"

    def capabilities(self) -> dict[str, bool]:
        configured = bool(self._api_key or self._mock_client)
        return {
            "boolean_evaluation": configured,
            "choice_evaluation": configured,
            "score_evaluation": configured,
            "alignment_evaluation": configured,
            "credentials_configured": configured,
            "low_latency_inference": True,
            "probability_distributions": True,
        }

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        start_time = time.time()

        # Secret Redaction Invariant: Never allow API key to leak into explanation or diagnostics
        if not self._api_key and not self._mock_client:
            latency = (time.time() - start_time) * 1000.0
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(
                    provider=self.name,
                    model=self._model,
                    latency_ms=latency,
                    credentials_configured=False,
                ),
                status=EvaluationStatus.CAPABILITY_UNAVAILABLE,
                decision=None,
                uncertainty="UNRESOLVED",
                explanation="TypeSafe credentials (TYPESAFE_API_KEY) not configured in environment. Core state unaffected.",
            )

        # Mock or external execution
        try:
            if self._mock_client:
                res = self._mock_client.evaluate(request)
            else:
                # Live Jev HTTP/REST execution
                # Enforces authentic provider communication; never fabricates provider results
                import urllib.request
                import urllib.error

                payload = json.dumps({
                    "question": request.question,
                    "type": request.evaluation_type.value,
                    "candidates": list(request.candidates),
                    "context": request.context,
                    "model": self._model,
                }).encode("utf-8")

                req_http = urllib.request.Request(
                    self._endpoint,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "MusicMCP-Evaluation-Silo/0.1.01",
                    },
                    method="POST",
                )

                with urllib.request.urlopen(req_http, timeout=5.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))

            decision, probabilities, explanation, uncertainty, status = _validated_response(request, res)

            latency = (time.time() - start_time) * 1000.0

            # Verify secret redaction
            if self._api_key and self._api_key in explanation:
                explanation = explanation.replace(self._api_key, "[REDACTED_SECRET]")

            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(
                    provider=self.name,
                    model=self._model,
                    latency_ms=latency,
                    credentials_configured=True,
                ),
                status=status,
                decision=decision,
                probabilities=probabilities,
                uncertainty=uncertainty,
                explanation=explanation,
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            err_msg = str(e)
            if self._api_key and self._api_key in err_msg:
                err_msg = err_msg.replace(self._api_key, "[REDACTED_SECRET]")
            return EvaluationResult(
                request_id=request.request_id,
                provenance=EvaluationProvenance(
                    provider=self.name,
                    model=self._model,
                    latency_ms=latency,
                    credentials_configured=True,
                ),
                status=EvaluationStatus.ERROR,
                decision=None,
                probabilities=None,
                uncertainty="UNRESOLVED",
                explanation=f"TypeSafe Jev adapter error: {err_msg}",
            )
