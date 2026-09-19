# MusicMCP Architectural Addendum

## Optional Structured Evaluation, TypeSafe Jev, and Low-Latency Musical Interpretation

**Status:** Founding architectural addendum\
**Audience:** Local coding agents, maintainers, reviewers, and future
contributors\
**Applies to:** MusicMCP architecture, conformance testing,
evidence/interpretation contracts, optional evaluation providers, and
future live musical workflows

------------------------------------------------------------------------

# 1. Purpose

This addendum records an architectural direction discovered after the
initial MusicMCP foundation was established.

The project has identified a potentially valuable class of external
systems that can perform fast, structured judgments over supplied state.
TypeSafe AI's **Jev** is the first concrete system being evaluated for
this role.

Jev is **not** being adopted as a required dependency.

Jev is **not** being granted authority over MusicMCP.

Jev is **not** the definition of MusicMCP's evaluation semantics.

Instead, this addendum establishes provider-neutral architecture that
may allow Jev, ordinary coding agents, frontier models, specialized
music models, deterministic algorithms, local models, or future systems
to perform compatible evaluation and interpretation work.

The goal is to gain the advantages of systems such as Jev without
allowing any one provider to become a structural dependency.

The governing architectural test remains:

> If the provider disappears tomorrow, only its silo should disappear.

------------------------------------------------------------------------

# 2. Existing Constitutional Principles Still Govern

Nothing in this addendum overrides the founding principles of MusicMCP.

> **The musician stays the artist. The machine does the notation,
> calculation, and clerical work.**

> **Human intent is authoritative. Machine inference is provisional.
> Machine creation is identifiable. Machine modification is
> authorized.**

> **No model directly controls authoritative musical state.**

> **Every consequential change is attributable, constrained,
> inspectable, and reversible.**

> **Failure must be contained. Dependencies must be replaceable. Errors
> must be explainable. Behavior must be documented.**

------------------------------------------------------------------------

# 3. External Evaluation Must Remain Optional

MusicMCP MUST NOT require TypeSafe, Jev, or an equivalent hosted
evaluator for core operation, authoritative-state integrity,
compatibility, deterministic transformations, provenance, revision
history, rollback, or ordinary conformance testing.

A MusicMCP implementation without TypeSafe credentials MUST remain
valid.

Absence of an optional provider should degrade locally:

``` text
provider: typesafe_jev
status: CAPABILITY_UNAVAILABLE
reason: credentials_not_configured
core_state: unaffected
```

Provider failure must not become core failure.

------------------------------------------------------------------------

# 4. Do Not Build "Jev Semantics"

Define provider-neutral semantics first.

Do not create core interfaces named after Jev unless they live strictly
inside the Jev adapter.

Prefer concepts such as:

``` text
EvaluationProvider
EvaluationRequest
EvaluationResult
ChoiceEvaluation
BooleanEvaluation
ScoreEvaluation
ProbabilityDistribution
EvaluationProvenance
```

The core contract defines what MusicMCP needs. An adapter translates
that contract into provider-specific requests.

------------------------------------------------------------------------

# 5. Evaluation Provider Boundary

``` text
                   MUSICMCP
                      |
             EVALUATION CONTRACT
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
  TypeSafe/Jev    Agent/LLM      Deterministic
    Adapter        Adapter        Evaluator
       |              |              |
       +--------------+--------------+
                      |
                      v
             NORMALIZED RESULT
```

Future providers may include Jev, Codex or another frontier agent, local
open-source models, specialized music models, deterministic algorithms,
evaluator ensembles, and systems that do not yet exist.

No provider receives special architectural authority because it is
faster or currently performs better.

------------------------------------------------------------------------

# 6. First Use: Accelerated Conformance Evaluation

A strong initial use case is the MusicMCP conformance suite.

Where deterministic testing alone is insufficient, conformance
requirements should be decomposable into small, explicit,
provider-neutral judgments such as:

``` text
Did this operation modify locked melody?
Was machine-generated material identified as generated?
Was provenance preserved?
Does the user-facing error agree with the technical diagnostic?
Was ambiguity preserved rather than silently resolved?
Does the result imply authority the actor did not possess?
Was a lossy conversion disclosed?
Did the operation make an artistic change beyond granted permission?
```

These evaluations must be specified independently of Jev.

A sufficiently capable agent should be able to execute the same semantic
test. A human reviewer should be able to understand it. A specialized
provider may execute it faster.

> **Any Jev-accelerated conformance test MUST have a
> provider-independent semantic definition.**

If removing the Jev adapter causes the meaning of a test to disappear,
the architecture is wrong.

------------------------------------------------------------------------

# 7. Atomic Evaluation Design

Prefer small judgments over giant prompts.

Bad:

``` text
Review this entire operation and decide whether it is correct,
safe, authorized, musically valid, and architecturally compliant.
```

Better:

``` text
Was locked melody modified?
Was generated material identified?
Did the requested operation possess authority to modify pitch?
Does the human-facing message state that authoritative state changed?
Does the technical diagnostic indicate that authoritative state changed?
```

Compose those results in deterministic MusicMCP code.

The evaluator supplies judgments. MusicMCP owns the policy that
determines what those judgments mean.

------------------------------------------------------------------------

# 8. Probability and Confidence

The prohibition against fake precision remains valid.

MusicMCP MUST NOT fabricate numerical confidence, require every provider
to return it, or treat an unexplained value such as `confidence: 0.9137`
as inherently meaningful.

An evaluator MAY return probability distributions or confidence metrics
when:

1.  the provider defines their semantics;
2.  provenance is preserved;
3.  provider/model identity is recorded;
4.  thresholds are calibrated for the MusicMCP task rather than copied
    blindly;
5.  authoritative state does not depend upon an unexplained number;
6.  uncertainty can still be represented without numerical confidence.

Conceptually:

``` yaml
interpretation:
  status: ambiguous
  candidates: [A4, Ab4]

  structured_uncertainty:
    evidence_quality: high
    interpretive_ambiguity: moderate
    review_required: true

  optional_evaluations:
    - provider: typesafe_jev
      provider_model: jev-latest
      evaluation_type: choice
      probabilities:
        A4: ...
        Ab4: ...
      confidence: ...
```

Deleting `optional_evaluations` MUST NOT invalidate the underlying
MusicMCP state.

------------------------------------------------------------------------

# 9. Evaluation Provenance Is Mandatory

Any externally produced evaluation that influences behavior MUST be
attributable.

Preserve enough information to answer:

-   Which provider produced it?
-   Which provider model/version was used when available?
-   What evaluation contract/version was used?
-   What state or state reference was evaluated?
-   What questions were asked?
-   What result was returned?
-   What probability/confidence information was returned?
-   When was it evaluated?
-   Was it advisory or action-gating?
-   Did a human subsequently confirm or override it?
-   Did another evaluator disagree?

Do not silently flatten provider output into authoritative truth.

------------------------------------------------------------------------

# 10. Multiple Evaluators May Disagree

The architecture MUST permit disagreement.

``` text
Evidence
   |
   +--> Jev ------------------+
   |                          |
   +--> Specialized Model ----+--> Interpretation Comparison
   |                          |
   +--> Local Model ----------+
                              |
                              v
                         MusicMCP Core
```

Disagreement is information. Do not establish model supremacy by
default.

Possible normalized outcomes include:

``` text
CONSENSUS
DISAGREEMENT
AMBIGUOUS
INSUFFICIENT_EVIDENCE
REVIEW_REQUIRED
```

------------------------------------------------------------------------

# 11. Second Use: Low-Latency Musical Interpretation

A potentially important future capability is low-latency interpretation
of live or incrementally received musical evidence.

This addendum does NOT authorize implementation of a complete live
transcription system immediately.

It DOES require that early evidence and interpretation contracts avoid
unnecessarily making such a system impossible.

Do not design transcription exclusively around:

``` text
complete WAV file
    ->
opaque batch transcription
    ->
complete finished score
```

The architecture SHOULD permit incremental musical evidence.

------------------------------------------------------------------------

# 12. Raw Audio Is Not the Evaluator's Responsibility by Default

A structured evaluator such as Jev should not be assumed to perform
signal processing.

Preferred separation:

``` text
MICROPHONE / INSTRUMENT / AUDIO FILE
                 |
                 v
         AUDIO ANALYSIS SILO
                 |
                 v
       NORMALIZED MUSIC EVIDENCE
                 |
                 v
    MUSICAL INTERPRETATION PROVIDER
                 |
                 v
       NORMALIZED INTERPRETATION
                 |
                 v
           MUSICMCP CORE
                 |
       AUTHORITY / CONSTRAINTS
                 |
                 v
          PROPOSED NOTATION
                 |
                 v
       AUTHORIZED STATE CHANGE
                 |
                 v
             ENGRAVING
```

Signal processing asks what appears to have physically occurred.

Interpretation asks what musical meaning most plausibly explains the
evidence in context.

Authority asks what the system may do with that interpretation.

Keep them distinct.

------------------------------------------------------------------------

# 13. Example Incremental Evidence

A future audio-analysis silo might produce bounded evidence such as:

``` yaml
evidence_window:
  source_id: performance-001
  window:
    start_seconds: 12.400
    end_seconds: 13.100

  detected_events:
    - event_id: observed-847
      onset_seconds: 12.842
      duration_seconds: 0.487
      pitch_candidates:
        - pitch: F#4
          evidence_strength: high
        - pitch: F4
          evidence_strength: low
        - pitch: G4
          evidence_strength: low

  score_context:
    previous_measure: 17
    current_measure: 18
    next_measure: 19

  current_alignment_candidates:
    - m18.voice1.event3
    - m18.voice1.event4
    - m18.voice2.event2
    - new_event
    - unresolved
```

This is illustrative only. Do NOT adopt it as a final schema without
review.

------------------------------------------------------------------------

# 14. Example Atomic Musical Evaluations

## Score alignment

``` text
Which candidate score event most plausibly corresponds to the observed onset?

m18.voice1.event3
m18.voice1.event4
m18.voice2.event2
new_event
ornament
unresolved
```

## Intended pitch

``` text
Which intended pitch best explains the supplied evidence and musical context?

F4
F#4
G4
unresolved
```

## Performance artifact

``` text
Is the observed pitch movement more consistent with expressive vibrato
than with a distinct written pitch?
```

## Timing interpretation

``` text
Is the timing deviation more consistent with expressive timing
than with a separately notated rhythmic event?
```

## Notational role

``` text
Which role best describes this event?

written_note
grace_note
ornament
breath
continuation
performance_artifact
unresolved
```

These are interpretation semantics, not permission to modify a score.

------------------------------------------------------------------------

# 15. Interpretation Is Not Mutation

This boundary is absolute.

A provider may conclude:

``` text
most_likely_pitch: F#4
most_likely_score_event: m18.voice1.event3
```

That does not authorize engraving or state mutation.

``` text
EVIDENCE
   |
   v
INTERPRETATION
   |
   v
PROPOSED MUSICAL MEANING
   |
   v
AUTHORITY CHECK
   |
   v
CONSTRAINT CHECK
   |
   v
TRANSACTION
   |
   v
VALIDATION
   |
   v
COMMIT / ROLLBACK
```

Jev or any evaluator MUST NOT write directly to Authoritative Musical
State.

------------------------------------------------------------------------

# 16. Live Score Following

Preserve the possibility of score following.

``` text
              EXISTING SCORE
                    |
          previous/current/next
               score window
                    |
                    +----------------+
                                     |
LIVE AUDIO                           |
    |                                |
    v                                |
AUDIO ANALYZER                       |
    |                                |
    v                                |
MUSICAL EVIDENCE --------------------+
                    |
                    v
          INTERPRETATION PROVIDER
                    |
                    v
             SCORE ALIGNMENT
                    |
                    v
              MUSICMCP CORE
```

Instead of asking which event in all possible music was heard, an
evaluator may choose among nearby plausible score events.

The implementation must still support skipped measures, repeats,
performer mistakes, restarts, jumps, ornaments, improvisation, inserted
material, and unresolved position.

Never force alignment merely because a score exists.

------------------------------------------------------------------------

# 17. Existing Score vs Performance vs Human Intent

Keep three concepts distinct:

``` text
EXISTING NOTATION
PERFORMED EVIDENCE
CONFIRMED HUMAN INTENT
```

A performance mismatch does not prove the score is wrong.

The performer may have made a mistake. The notation may be wrong. The
performer may be demonstrating a desired revision.

Task context determines the question.

------------------------------------------------------------------------

# 18. Low-Latency Capability Discovery

Evidence and interpretation contracts SHOULD support bounded incremental
events/windows.

Do not require every provider to support streaming.

Capability discovery may eventually expose:

``` yaml
capabilities:
  incremental_evaluation: true
  streaming_input: false
  batch_evaluation: true
  probability_distribution: true
  score_alignment: true
```

A batch-only provider remains valid for suitable work.

------------------------------------------------------------------------

# 19. TypeSafe Jev Adapter

If implemented, Jev MUST live behind a replaceable adapter.

The adapter may translate provider-neutral requests into TypeSafe
primitives such as Choice, Score, and Noul.

It may consume selected choices, scores, Noul values, probability
distributions, confidence metrics, and usage metadata.

Provider-specific structures MUST NOT leak throughout unrelated modules.

------------------------------------------------------------------------

# 20. Credentials and BYOK

Do not place TypeSafe credentials in the repository.

Do not paste credentials into source files, Markdown documentation,
committed configuration, fixtures, `handoff.md`,
`whats_and_hows_log.md`, error logs, or published screenshots.

Current TypeSafe documentation uses:

``` text
TYPESAFE_API_KEY
```

The system SHOULD support Bring Your Own Key for optional hosted
evaluators.

MusicMCP maintainers SHOULD NOT be assumed to subsidize unlimited
inference for downstream users.

No valid core behavior should depend upon a maintainer-owned shared API
key.

------------------------------------------------------------------------

# 21. Secret Handling

Adapters MUST avoid leaking secrets through diagnostics.

Allowed:

``` text
provider: typesafe
credential_status: configured
authentication_result: failed
```

Forbidden:

``` text
api_key: <secret>
```

Tests should eventually verify redaction.

------------------------------------------------------------------------

# 22. Provider Failure Behavior

Possible failures include missing/invalid credentials, quota exhaustion,
rate limiting, network failure, provider outage, malformed responses,
timeout, unsupported questions, incompatible SDK versions, unavailable
models, and policy restrictions.

Map them into the MusicMCP error system.

Illustrative example:

``` text
MUSICMCP-EVALUATION-PROVIDER-UNAVAILABLE

Severity: DEGRADED
Provider: typesafe_jev
Operation: evaluate_choice

Authoritative State Modified: NO
State Safe: YES

Fallback Available: YES
Fallback: generic_agent_evaluator
```

Reconcile exact codes with `ERRORS.md`.

------------------------------------------------------------------------

# 23. Provider Failure Must Not Corrupt AMS

If an evaluator fails:

-   authoritative state remains safe;
-   no half-applied interpretation becomes authoritative;
-   failure is observable;
-   fallback is explicit;
-   retry behavior is bounded and documented;
-   the user is not told evaluation succeeded when it did not.

This is a conformance invariant.

------------------------------------------------------------------------

# 24. Deterministic Logic Stays Deterministic

Do not send everything to AI.

Prefer deterministic code for things such as numeric range checks,
required-field validation, revision existence, transaction status,
locked-object diffs, known export omissions, and Git sync comparisons.

Use evaluators for judgments that genuinely require interpretation.

------------------------------------------------------------------------

# 25. Cost and Latency Are Architectural Inputs

Hosted evaluators consume resources.

Evaluation strategy should eventually be configurable. Potential modes
might include:

``` text
OFFLINE
DETERMINISTIC_ONLY
LOCAL
HOSTED_FAST
HOSTED_DEEP
ENSEMBLE
HUMAN_REVIEW
```

These names are illustrative.

Do not make expensive hosted inference silently mandatory.

------------------------------------------------------------------------

# 26. Privacy and Data Boundaries

Before sending state externally, adapters must eventually make clear
what leaves the local system.

Do not assume users may transmit source audio, unpublished compositions,
lyrics, client work, copyrighted scores, personally identifying
metadata, or project notes.

Provider contracts should declare network requirements and data
exposure.

Send only the minimum state necessary where practical.

------------------------------------------------------------------------

# 27. Conformance Requirements Introduced Here

Future tests should cover:

-   Jev adapter disabled: core still works.
-   Missing `TYPESAFE_API_KEY`: core still works; capability
    unavailable.
-   Provider outage: no AMS corruption.
-   Adapter replacement: unrelated modules unchanged.
-   Provider disagreement: disagreement preserved appropriately.
-   Provider probabilities: provenance preserved.
-   Provider without numerical confidence: uncertainty still
    representable.
-   Human override: confirmed human intent wins.
-   Deterministic invariants: no hosted inference required.
-   Secret redaction: credentials absent from logs/diagnostics.
-   Incremental compatibility: evidence can represent bounded
    events/windows.

------------------------------------------------------------------------

# 28. Documentation Changes Required

Before implementing a Jev adapter, determine which governing documents
need amendment.

Likely candidates:

``` text
ARCHITECTURE_PRINCIPLES.md
SPECIFICATION.md
CONFORMANCE.md
ERRORS.md
SECURITY.md
AGENTS.md
goals_and_dreams.md
whats_and_hows_log.md
handoff.md
```

Do not paste this entire addendum into every file.

Promote each principle into its proper authoritative location.

------------------------------------------------------------------------

# 29. Architectural Now vs Experimental Later

## Adopt architecturally now

-   provider-neutral evaluation contracts;
-   optional evaluator architecture;
-   strict provider isolation;
-   evaluation provenance;
-   no fake confidence;
-   provider probability distributions allowed with provenance;
-   deterministic logic remains deterministic;
-   external evaluator failure containment;
-   BYOK-compatible credentials;
-   no evaluator directly mutates AMS;
-   evidence/interpretation contracts do not prohibit incremental
    operation.

## Explore experimentally

-   Jev-accelerated conformance;
-   Jev musical interpretation;
-   low-latency score alignment;
-   live performance following;
-   simultaneous atomic musical judgments;
-   evaluator ensembles;
-   musical probability calibration;
-   latency/cost benchmarking;
-   human-vs-evaluator comparison;
-   specialized musical question libraries.

------------------------------------------------------------------------

# 30. Initial Agent Assignment

Do NOT immediately install the TypeSafe SDK.

Do NOT immediately obtain or require an API key.

Do NOT immediately implement live transcription.

First:

1.  Read this addendum and existing governing documentation.
2.  Inspect repository and sync state.
3.  Determine whether a provider-neutral evaluation boundary already
    exists.
4.  Determine whether evidence/interpretation contracts accidentally
    require batch-only workflows.
5.  Identify current probability/confidence semantics.
6.  Identify error, security, privacy, and conformance implications.
7.  Propose the smallest documentation changes necessary.
8.  Record architectural reasoning in `whats_and_hows_log.md`.
9.  Put speculative live-listening and score-following capabilities in
    `goals_and_dreams.md`.
10. Update `handoff.md`.
11. STOP for review before introducing a TypeSafe runtime dependency
    unless explicitly authorized.

The review should answer:

``` text
EXISTING SUPPORT:
...

CONFLICTS:
...

REQUIRED ARCHITECTURAL CHANGES:
...

DOCUMENTS TO MODIFY:
...

PROPOSED EVALUATION CONTRACT:
...

PROPOSED PROVIDER BOUNDARY:
...

LIVE/INCREMENTAL COMPATIBILITY:
...

SECURITY / PRIVACY RISKS:
...

OPEN QUESTIONS:
...
```

------------------------------------------------------------------------

# 31. Rules for a Future Jev Prototype

When explicitly authorized:

1.  Implement the provider-neutral contract first.
2.  Implement Jev only as an adapter.
3.  Use environment-based credentials.
4.  Never commit credentials.
5.  Provide mocks/fixtures so tests run offline.
6.  Mark network/integration tests separately.
7.  Ensure ordinary tests do not require paid inference.
8.  Capture provider/model provenance.
9.  Normalize provider errors.
10. Preserve raw provider responses only where appropriate and safe.
11. Benchmark latency rather than assuming it.
12. Benchmark cost rather than assuming it.
13. Test MusicMCP-specific calibration before setting action thresholds.
14. Never let confidence bypass authority rules.
15. Never allow Jev to mutate AMS directly.
16. Document adapter removal.
17. Prove removal does not destabilize the core.

------------------------------------------------------------------------

# 32. Future High-Value Experiment

When ready, test:

> Given a known score, a monophonic performance, and normalized audio
> evidence, can a structured evaluation provider rapidly align observed
> events to nearby score events and distinguish likely written notes
> from expressive performance artifacts?

Measure:

-   alignment accuracy;
-   intended-pitch accuracy;
-   rhythm interpretation accuracy;
-   ornament classification;
-   ambiguity detection;
-   calibration;
-   false certainty;
-   latency;
-   cost;
-   performer mistakes;
-   incorrect source notation;
-   intentional performer changes.

Compare against deterministic baselines, a general frontier model, and
human-confirmed ground truth.

Attack the experiment with adversarial musical cases.

------------------------------------------------------------------------

# 33. Architectural Test

Before accepting any Jev-related design, ask:

> If TypeSafe disappears tomorrow, does MusicMCP still work?

**Yes.**

> If Jev gives a confident but incorrect answer, can it corrupt
> authoritative musical state?

**No.**

> Can another evaluator execute the same semantic evaluation?

**Yes.**

> Can we determine which provider produced a judgment and what happened
> because of it?

**Yes.**

> Can the musician override the evaluator?

**Yes.**

> Can MusicMCP say "unresolved" instead of inventing certainty?

**Yes.**

If any answer fails, repair the architecture first.

------------------------------------------------------------------------

# 34. Final Direction

Jev may become a powerful MusicMCP capability.

It must never become MusicMCP's foundation.

Build the evaluation language so Jev can be exceptionally good at
executing it.

Build the musical interpretation boundary so fast evaluators can be
exceptionally useful inside it.

Build the authority system so no evaluator becomes the artist.

Build the silos so any provider can be replaced.

Build the provenance system so every judgment can be traced.

Build the uncertainty system so probabilities can inform decisions
without pretending to be truth.

Build the evidence contracts so future live musical workflows remain
possible.

Preserve the central rule:

> **The musician stays the artist. The machine does the notation,
> calculation, and clerical work.**

**Build the wall.**
