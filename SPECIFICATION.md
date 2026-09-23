# Music MCP specification — 0.1.01 (experimental)

MUST/MUST NOT are requirements; SHOULD identifies an expected default whose exceptions need documented reasons. This specification describes the founding architecture. The implemented subset is identified below, in the module contracts, and in [CONFORMANCE.md](CONFORMANCE.md). The declared package/schema version remains v0.1.01. Earlier draft labels v0.1.02 and v0.1.03 in historical records do not establish a later package release or full MCP/music-format interoperability.

## Foundational requirements

1. **AUTH-1:** Human intent MUST be authoritative. Models MUST NOT possess direct access to authoritative mutation. Host-established, scoped authorization MUST precede every consequential change; authorization MUST NOT expand to consequential artistic remedies.
2. **EVID-1:** Source evidence MUST remain distinguishable from derived observations, provisional interpretations, generated suggestions, and authoritative state. Interpretations MUST NOT overwrite source evidence.
3. **INTENT-1:** Confirmed human corrections MUST NOT be overwritten by later analysis. Reopening or changing intent requires fresh appropriate human authority.
4. **PROV-1:** Every revision MUST identify its actor, operation, reason, source proposal, material origin, constraints, and predecessor. Accepting generated music MUST NOT relabel it as human-authored.
5. **TX-1:** A failed operation MUST NOT expose partial authoritative changes. Expected-revision preconditions MUST prevent stale writes. Restore MUST preserve intervening history. A failure result MUST state actual state and rollback consequences.
6. **ISO-1:** Optional modules MUST use documented boundaries and MUST NOT own authoritative state. Capability, authority, policy, and musical constraints MUST remain separate decisions. Failure of optional analysis MUST NOT prevent reading existing state.
7. **REP-1:** Adapters MUST disclose loss, ambiguity, and unsupported representations before consequential export. Musical concepts MUST NOT be limited globally to the reference profile or any external format.
8. **UNC-1:** Uncertainty MUST describe its meaning; uncalibrated numeric confidence MUST NOT establish authority. Competing interpretations MAY coexist without selecting a model winner.
9. **ERR-1:** Failures MUST provide a stable code, human explanation, module/operation/scope, trace, state impact, rollback status, and recovery action. Unknown safety MUST NOT be reported as safe.

## Implemented reference profile

One in-process workspace contains named phrase scopes. Original bytes, observations, and interpretations are append-only. An interpretation links an observation to a proposed ordered monophonic phrase and carries `intended` or `literal` task mode, uncertainty, and `interpreted` or `generated` origin. Each observation and each proposal MUST retain its own immutable producer identity and version. The observer and interpreter MAY be different producers. The trusted host supplies this attribution; it is not cryptographic proof of identity or correctness. Missing or invalid producer records MUST be rejected. The core performs no inference; the separate experimental [audio analyzer](reference/ANALYZER_CONTRACT.md) can supply provisional observations and proposals.

The narrow core note profile is spelled Western pitches (A–G, optional single sharp/flat, octave 0–9) or `rest`; duration is an exact positive rational number of quarter-note units. The ordered phrase has no overlap, meter, voice, tuning conversion, or implicit quantization. The separate preview draws a limited staff representation; it does not extend the core's symbolic profile. Unsupported representations MUST be rejected, never silently approximated. These limits apply to this profile only.

Authority is a separate host-held capability bound to actor, scope set, and operation set (`confirm`, `correct`, `restore`). Default is denial. The factory is trusted host setup; it MUST NOT be exposed as a model tool. Each lock MUST retain its scope, origin, and reason as an immutable constraint record. Duplicate lock scopes MUST be rejected. Locked scopes reject all content mutations in this release. Constraints and grants remain fixed for the workspace lifetime; each candidate and committed revision MUST retain the complete active constraint records. Policy is a host-provided pure decision callback, independently evaluated for every write and denied on exceptions or non-boolean results.

Confirmation chooses a supplied interpretation. Correction records explicit human replacement content while retaining the original proposal/evidence lineage. Restore selects the content and origin of a historical revision of the same scope and appends a new revision. All writes require the current **workspace-wide** revision, a nonempty reason, and a scoped session. Preview and analysis do not mutate authoritative state. No automatic authorization, delegated machine writes, or inferred approval is supported.

See [reference/CONTRACT.md](reference/CONTRACT.md) for callable core API, bounds, state lifecycle and exact failure behavior. A host using the core alone MUST retain originals durably before relying on its volatile workspace for real work; the optional [SQLite storage silo](reference/storage/STORAGE_CONTRACT.md) provides local persistence with its own limits.

## Uncertainty semantics

Uncertainty labels describe the proposal producer's assessment, not a calibrated probability or authorization:

| Label | Meaning |
| --- | --- |
| HIGH | The producer assesses strong support for this reading from the available evidence and task context. |
| MEDIUM | The producer assesses moderate support; material uncertainty remains. |
| LOW | The producer assesses weak support; the reading is tentative. |
| AMBIGUOUS | Competing readings remain plausible and unresolved. |
| UNRESOLVED | The assessment or interpretation has not been settled, including when it has not been assessed. |
| INSUFFICIENT_EVIDENCE | Available input is inadequate to support a settled interpretation. |

Labels MUST NOT be treated as numerical probabilities, comparable scores across producers, permission, or a basis for automatic selection. Every label requires the same explicit human confirmation before a proposal becomes authoritative. The host MUST preserve the distinction between the producer's assessment and the human's decision.

## Trusted-host approval obligations

Possession of a scoped session establishes a technical capability; it does not prove authentication or per-operation consent. Before invoking a session, the host MUST present the exact workspace and current workspace-wide revision, operation, affected scope, proposal or historical restore target, resulting notes, source producer identity/version, material origin and uncertainty, active constraint records, and the reason for the change. For correction or restore, the host MUST distinguish the proposed resulting material from the source proposal's interpretation and uncertainty rather than implying that the producer assessed the human replacement.

The host MUST obtain an explicit human action through a trusted route and invoke the session with the reviewed immutable values and expected revision. A stale revision rejection requires fresh review and consent; the host MUST NOT silently substitute a newer revision and retry. Model text claiming approval is not a trusted human action. These are host integration obligations: the in-process kernel does not implement a UI, identity service, or per-operation approval-token subsystem.


## Provider-Neutral Evaluation Silo & Structured Interpretation (experimental v0.1.01 reference)

1. **EVAL-1 (Optionality & Isolation):** Evaluation providers MUST remain optional. Core state operations, revision history, and authority MUST NOT depend upon external hosted evaluators. Absence of credentials degrades gracefully to status `CAPABILITY_UNAVAILABLE` without throwing unhandled exceptions or altering core state.
2. **EVAL-2 (Interpretation is not Mutation):** Evaluators propose judgments; they MUST NOT hold an `AuthoritySession` and MUST NOT mutate Authoritative Musical State (AMS).
3. **EVAL-3 (Atomic Request Primitives):** Evaluation requests MUST be structured as atomic, single-judgment primitives specifying question text, `EvaluationType` (`BOOLEAN`, `CHOICE`, `SCORE`, `ALIGNMENT`), candidates, and contextual parameters. Monolithic unconstrained review requests MUST NOT be accepted.
4. **EVAL-4 (Probability & Provenance):** Evaluators MAY supply a `ProbabilityDistribution` when probabilities sum to 1.0 within tolerance (±1e-6) and calibration status is explicitly tracked. A provider's calibration flag is a claim, not independent proof. Every result MUST retain immutable `EvaluationProvenance` capturing provider identity, model ID, timestamp, and credential status.
5. **EVAL-5 (Bounded Incremental Evidence):** The evaluation contract represents bounded temporal windows (`EvidenceWindow`) containing acoustic observations (`DetectedEvent`) with onset seconds, duration seconds, and pitch candidate tuples. These primitives permit evaluator alignment against candidate score events; they do not establish a tested low-latency live score-following product.
6. **EVAL-6 (Secret Redaction & BYOK):** Adapters for hosted providers (including `TypeSafeJevAdapter` via `TYPESAFE_API_KEY`) MUST support Bring-Your-Own-Key configuration and MUST redact sensitive API keys and tokens (`[REDACTED_SECRET]`) from all explanations, user-facing messages, and diagnostics.


## Interactive Visualizer Review Deck & Sensory Verification (experimental v0.1.01 reference)

1. **DECK-1 (Localhost Security Boundary):** The visualizer review deck (`PreviewServer`) MUST bind exclusively to local loopback interfaces (`127.0.0.1`, `localhost`, `::1`). Non-local client addresses MUST be rejected with diagnostic `SECURITY_VIOLATION`.
2. **DECK-2 (Persistent State Synchrony):** When initialized with a `.musicmcp` project path, every authority-executed state transition (`/api/confirm`, `/api/correct`, `/api/restore`, `/api/upload`, `/api/propose_alternative`) MUST automatically persist the updated workspace to SQLite storage on disk. State MUST NOT exist solely as transient in-memory representation.
3. **DECK-3 (Visual Notation Engraving):** The review deck MUST render musical pitch, duration, accidentals, and rests onto a standard 5-line musical staff via HTML5 Canvas 2D engraving (`drawStaff`). Raw text tokens or pill badges alone MUST NOT serve as the sole representation of musical proposals.
4. **DECK-4 (Acoustic Auditory Verification):** The review deck MUST synthesize and audibly play proposed phrases and authoritative revisions via the browser Web Audio API, modeling fundamental frequencies, natural harmonic overtones, and attack/decay envelopes.
5. **DECK-5 (Direct Ingestion & Spectral Watching):** The review deck MUST provide direct drag-and-drop and file upload ingestion (`/api/upload`) for 16-bit PCM mono WAV audio, automatically performing pitch tracking, proposal generation, and FFT spectral inspection with 10-band energy visualization.

## Further extension requirements

Future modules MUST declare version/capabilities, schemas, permissions, side effects, network/data retention, policy restrictions, validation, failure modes, and rollback guarantees. Discovery MUST distinguish supported, disabled, degraded, and unsupported capabilities. Experimental local storage, format adapters, collaboration, and audio analysis now have separate reference contracts; distributed identity, independently validated calibration, full collaborative conflict resolution, and musically validated transcription still require additional evidence and conformance profiles. Supporting a future feature MUST NOT weaken the above invariants.
