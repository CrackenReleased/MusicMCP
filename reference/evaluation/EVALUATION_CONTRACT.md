# Evaluation Contract: Provider-Neutral Structured Evaluation & Interpretation

**Contract Version:** 0.1.01  
**Module:** `reference.evaluation`  
**Status:** Reference Evaluation Silo  

---

## 1. Purpose and Architectural Boundary

In accordance with Founding Directive §1 and the Jev Evaluation Architecture Addendum:
**External evaluation must remain optional. Models propose; human intent governs.**

This contract defines a provider-neutral boundary for structured musical judgments, atomic conformance evaluations, and incremental interpretation. It accommodates deterministic algorithms, local models, and optional specialized evaluators (such as TypeSafe Jev) without permitting any single provider to become a structural dependency.

> **The Governing Architectural Test**: If any external evaluator disappears tomorrow, only its silo disappears; core authoritative state, revisions, and operations remain completely unaffected.

---

## 2. Invariants

1. **Provider-Neutral Primitives**:
   Core evaluation requests are phrased in provider-independent semantics (`BOOLEAN`, `CHOICE`, `SCORE`, `ALIGNMENT`). Evaluators never impose vendor-specific primitives on MusicMCP core.
2. **Atomic Judgments**:
   Evaluations are decomposed into small, focused questions (e.g. *"Was locked melody modified?"*, *"Which candidate score event corresponds to the observed onset?"*) rather than monolithic evaluation prompts.
3. **Strict Interpretation vs. Mutation Barrier**:
   Evaluators supply judgments, interpretations, and probability distributions. Evaluators **never possess `AuthoritySession` tokens** and cannot directly mutate Authoritative Musical State.
4. **Mandatory Evaluation Provenance**:
   Every evaluation result records provider identity, model/version, timestamp, latency, question context, and whether the evaluation was advisory or action-gating.
5. **No Fake Precision**:
   Fabricated confidence metrics are prohibited. Structured qualitative uncertainty (`LOW`, `MEDIUM`, `HIGH`, `AMBIGUOUS`, `UNRESOLVED`) remains authoritative. Numerical probabilities are permitted only with provider provenance and task calibration.
6. **Graceful Degradation & BYOK**:
   External evaluators are Bring-Your-Own-Key (BYOK, e.g. `TYPESAFE_API_KEY`). If credentials are absent or the provider is unreachable, the system degrades gracefully with `CAPABILITY_UNAVAILABLE`. Core state remains 100% safe.
7. **Incremental Evidence Compatibility**:
   Evidence structures support bounded temporal windows (`EvidenceWindow`, `DetectedEvent`) for future live-listening, score alignment, and performance tracking without imposing batch-only constraints.

---

## 3. Data Structures Specification

### `EvaluationType` (Enum)
- `BOOLEAN`: Yes/No atomic judgment.
- `CHOICE`: Selection among discrete candidate strings (e.g. pitch candidates, alignment targets).
- `SCORE`: Normalized metric assessment ($0.0 \dots 1.0$).
- `ALIGNMENT`: Association of observed event to candidate score events or `unresolved`.

### `EvaluationRequest` (Dataclass)
- `request_id`: Unique UUID string.
- `evaluation_type`: `EvaluationType`.
- `question`: Concise textual question.
- `candidates`: Tuple of discrete candidate options (for `CHOICE` or `ALIGNMENT`).
- `context`: Dictionary of musical context (e.g. active scope, revision, evidence reference).

### `ProbabilityDistribution` (Dataclass)
- `probabilities`: Mapping of candidate string to float probability ($\sum p \approx 1.0$).
- `calibrated`: Boolean indicating whether values have been calibrated for the task.

### `EvaluationProvenance` (Dataclass)
- `provider`: Provider identifier (e.g. `"deterministic"`, `"typesafe_jev"`, `"local_model"`).
- `model`: Model version or engine identity.
- `timestamp`: ISO timestamp string.
- `latency_ms`: Float execution latency in milliseconds.
- `credentials_configured`: Boolean indicating whether provider credentials were used.

### `EvaluationResult` (Dataclass)
- `request_id`: Echoes request ID.
- `provenance`: `EvaluationProvenance`.
- `status`: Result status (`SUCCESS`, `CAPABILITY_UNAVAILABLE`, `AMBIGUOUS`, `UNRESOLVED`, `ERROR`).
- `decision`: Selected candidate, boolean value, or float score.
- `probabilities`: Optional `ProbabilityDistribution`.
- `uncertainty`: Qualitative uncertainty rating (`LOW`, `MEDIUM`, `HIGH`, `AMBIGUOUS`, `UNRESOLVED`).
- `explanation`: Traceable natural language justification.

---

## 4. Diagnostics Mapping

| Condition | Diagnostic Code | Severity | State Safe | Action |
|---|---|---|---|---|
| Credentials not configured | `MUSICMCP-EVALUATION-UNAVAILABLE` | DEGRADED | `True` | Configure provider credentials via environment or use deterministic evaluator. |
| Provider network/API error | `MUSICMCP-EVALUATION-FAILED` | DEGRADED | `True` | Review provider connectivity; core state safe. |
| Malformed evaluation input | `MUSICMCP-EVALUATION-INVALID` | ERROR | `True` | Verify request adheres to Evaluation Contract. |
