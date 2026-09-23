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
   External evaluators are Bring-Your-Own-Key (BYOK, e.g. `TYPESAFE_API_KEY`). Absent credentials return `CAPABILITY_UNAVAILABLE`; attempted provider requests that fail return `ERROR`. Neither outcome authorizes a core mutation.
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


## 5. Implemented evaluation limits

The deterministic evaluator implements the named Boolean conformance rules and score-event alignment. It does not implement arbitrary musical choice or numeric score judgments; those capabilities are reported false. A question with no implemented rule returns `CAPABILITY_UNAVAILABLE`, `decision=None`, no probabilities, and `UNRESOLVED` uncertainty. Candidate order is never evidence for a fallback decision.

The TypeSafe adapter constructs a JSON POST and parses the provider response. Transport regression tests intercept HTTP to verify serialization and response preservation; they do not certify the configured endpoint, provider schema, model availability, or calibration against a live service. A connection failure is tested separately from missing credentials so an internal serialization error cannot masquerade as verified network error handling.


## 6. Required evidence and response validation (milestone 1)

Request construction rejects unknown evaluation types, non-mapping context, empty/non-text questions, and non-sequence, empty-string or duplicate candidate entries with ValueError. CHOICE and ALIGNMENT still require candidates. This validates the request envelope; it does not claim arbitrary nested musical context is valid.

Named deterministic rules require BOOLEAN requests. Required fields are:

| Rule | Required evidence | Accepted representation |
| --- | --- | --- |
| Locked phrase comparison | locked_phrase, candidate_phrase | Lists/tuples of core Note objects; empty phrases are valid evidence. |
| Generated-origin check | origin | human, generated, or interpreted. |
| Authority membership check | actor_operations, actor_scopes, operation, scope | Collections of non-empty strings and non-empty target strings; explicitly empty grant collections are valid and produce a negative judgment. |
| Alignment | observed_pitch, observed_onset, score_events | Non-empty pitch text, finite nonnegative numeric onset (not Boolean), mapping of event IDs to pitch/onset pairs. Every candidate except the reserved unresolved option needs event evidence. |

A missing or null field returns UNRESOLVED with no decision; a present malformed field returns ERROR with no decision. Missing candidate event evidence also returns UNRESOLVED. A named Boolean rule requested with a different result type is unavailable. No automatic False or zero-onset substitute is used. These checks validate evidence shape, not recording accuracy, identity authentication, or musicological truth.

Injected clients and HTTP results share one validator. Decisions must be strict Booleans, listed candidate strings, or finite numeric scores in [0, 1] (Booleans do not count as scores). Null/missing decisions, invalid explanation types and unknown uncertainty labels fail with ERROR. An explicitly non-success provider status is surfaced as an adapter ERROR rather than promoted to success. A listed ALIGNMENT decision of unresolved yields UNRESOLVED; explicit AMBIGUOUS/UNRESOLVED uncertainty likewise prevents SUCCESS. Valid False and score zero are retained.

Probability distributions must be non-empty mappings with non-empty string keys, finite values in [0, 1], and a total within 1e-6 of one. This tightens the earlier 0.95–1.05 tolerance. Candidate distributions may cover a subset of requested candidates; omitted candidates carry no assigned mass. BOOLEAN distributions use true/false string keys. SCORE does not accept candidate probabilities. Wrong keys, empty distributions and invalid calibration types are errors. Calibration defaults to false on both transport paths; an explicit true value is a recorded provider claim, not independent verification of calibration.

Regression ownership: tests/test_evaluation.py::TestEvaluationValidation and the confirmed-state test. All statuses remain advisory; no host authority is granted by validation. No live provider compatibility, external calibration or musical accuracy certification is implied.
