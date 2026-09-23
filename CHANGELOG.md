## Unreleased - analyzer pitch-excursion uncertainty (implementation v0.1.01)

- Mark a proposal `AMBIGUOUS` when a voiced pitch lasting at most two analysis hops jumps at least an octave from both voiced neighbors. Keep all proposed notes and explain the review flag in the observation.
- Add a focused proposal-path regression. Its old-code `HIGH` failure and new-code pass were observed before the owner moved further regression testing to Antigravity; Antigravity verified the complete 143-test regression suite green on Windows.

## Documentation - owner scope correction (implementation v0.1.01)

- Remove independent MCP-client and external MIDI/MusicXML interoperability testing from active roadmap/checklist/release requirements. Retain it only as an owner-reopened long-term possibility, roughly 2-3 years out. Existing adapters and internal tests are unchanged.

## Unreleased - preview ingestion atomicity (implementation v0.1.01)

- Keep upload evidence/observation/proposal creation and generated-alternative observation/proposal creation inside the existing mutation/persistence recovery boundary. Failed analysis or save no longer leaves partial in-memory records.
- Add red/green regressions for invalid upload and failed alternative save. No version or schema change.

## Unreleased - source conformance gate (implementation v0.1.01)

- Add a read-only GitHub Actions check for the existing synthetic demo and full unittest suite on Windows and Ubuntu, Python 3.11 with Node 22 for preview-script coverage. No package publishing or deployment step.
- Document clean source checkout commands, exact locally observed validation, revision-specific CI evidence, and the separate musician-approved recording gate.
- First clean-checkout workflow run at `c4a184a` passed the demo and 142 tests on both Windows and Ubuntu (Python 3.11, Node 22); no package release was made.

## Documentation — v0.1.01 status reconciliation (Unreleased)

- Separate the in-memory core from implemented experimental reference silos in the README, specification, architecture, security, diagnostics, conformance, and idea vault. State verified local behaviors and remaining evidence gaps without claiming a new release.
- Align the specification's probability total tolerance with the implemented 1e-6 contract. Historical 0.1.02/0.1.03 headings below are retained as records of earlier work; the current package and storage schema still declare v0.1.01.

## Unreleased — stored project relationship validation (implementation v0.1.01)

- Reject stored evidence, observation, proposal, revision, and restoration links that are missing or inconsistent; report them through `verify_integrity` and a storage diagnostic on reopen.
- Validate serialized notes, constraints, attribution, and publication origin against the recorded causal chain; reject boolean duration fields and unexpected serialized fields. Add in-memory and disposable-file corruption regressions. No schema or version change.
- Verify process termination immediately before a real save commits leaves the prior revision and state token intact. Hardware power loss remains unverified.

## Unreleased — preview page width containment (implementation v0.1.01)

- Keep the three-column and single-column review deck within the viewport when fixed-width notation canvases render; scroll each staff inside its card.
- Wrap header controls and proposal badges at narrow widths. Browser regression passed at 1250px, 768px, and 375px; preview suite passed 24 tests. No version or schema change.

## Unreleased — pitch-aware preview staff bounds (implementation v0.1.01)

- Size the staff canvas vertically to the visible pitch range so high and low notes, ledger lines, stems and pitch labels remain inside the canvas without changing note data.
- Extend shipped-renderer regression coverage for C#8 and C3. Preview suite: 24 passed; scoped browser rendering verified. Horizontal page overflow remains a separate issue.
## Unreleased — proposal review status (implementation v0.1.01)

- Count Pending and Reviewed proposals from revision history; retain reviewed originals and label each card explicitly.
- Extend the existing executable browser-script regression for initial, corrected and mixed/historical status. No version or schema change.

## Unreleased — correction editor source (implementation v0.1.01)

- Load the selected proposal's current confirmed notes into a clean correction editor, and label the source and button behavior.
- Preserve dirty drafts through refresh and same-proposal reselection; avoid clearing newer input when a correction response returns.
- Add executable browser-script regression and scoped browser verification. Original proposal content, confirmation semantics and version remain unchanged.

## Documentation — local audio walkthrough

- Record authorized fixture workflow through browser correction, reopen and MusicXML/MIDI round trips; add reusable conformance checklist and three unfixed UI findings. Musical acceptance remains open. No implementation version change.

## Unreleased — evaluation validation (implementation v0.1.01)

- Require deterministic rule evidence; distinguish missing evidence, malformed input and valid negative judgments.
- Validate provider decisions, probability distributions, uncertainty and calibration claims through one mock/HTTP response boundary.
- Reject invalid request envelopes and tighten probability normalization tolerance to 1e-6; preserve valid False and zero results.
- Add eight evaluation validation tests and expand confirmed-state coverage. No release or storage schema change.

## Documentation — maturation handoff revision 1

- Document six prioritized maturation milestones, acceptance checks and Antigravity continuation guidance in handoff.md. No implementation or release version change.

## Unreleased — evaluation reliability (implementation v0.1.01)

- Import JSON support so provider request construction reaches the HTTP transport.
- Return capability unavailable for unsupported deterministic questions instead of inventing a successful first-candidate/Boolean decision; report unsupported choice/score capabilities accurately.
- Add request/response and unsupported-question regressions; strengthen transport-error and confirmed-state tests. No release or schema change.

## Unreleased — persistence/recovery fixes (implementation v0.1.01)

- Make save conflict checks, legacy grant migration, forced clearing, and writes one transaction; preserve the prior database on failure.
- Load and verify from consistent snapshots; serialize workspace saves through token publication.
- Preserve preview host policy, validation, and grants during recovery; report unknown disk state honestly and block writes when reconciliation fails.
- Add nine regressions in existing storage/preview test modules. No release or schema version change; this repairs existing behavior.

## [0.1.04] - 2026-09-19

### Fixed
- **XSS & HTML Injection Defense**: Added HTML entity escaping across `index.html` for proposal scope, mode, uncertainty, origin, actor, reason, note pitches, duration, and acoustic reports.
- **Localhost & Origin Validation**: Restricted preview server endpoints against foreign Origin, foreign Host headers, cross-site fetch sites, and untyped/form POST payloads.
- **Storage Concurrency & Stale Save Conflict Check**: Added `state_token` tracking and pre-save revision conflict checks in `SqliteStorageEngine.save_workspace`, preventing stale writes from overwriting history.
- **Provider Authenticity in Evaluation Silo**: Replaced synthetic fallback in `TypeSafeJevAdapter` live branch with genuine HTTP execution and graceful error reporting with secret redaction.
- **Memory-Disk Consistency on Persist Failure**: Added transactional rollback in `PreviewServer` mutating endpoints ensuring memory is never left ahead of disk when saves fail.
- **Draft Preservation During Polling**: Prevented 5-second UI polling timer from resetting active proposal selection or overwriting in-progress correction edits.
- **Clean Force Initialization**: Fixed `musicmcp init --force` to clear all previous project tables rather than retaining obsolete revisions and evidence.
- **Schema & Revision Parent Chain Validation**: Enforced strict `schema_version` and revision `parent` continuity checks during SQLite database loading.
- **Multi-Grant Actor Persistence**: Updated `grants` table schema to auto-incrementing primary key, enabling multiple distinct scoped grants per actor without permission merging.

## [0.1.03] - 2026-09-19

### Added
- **HTML5 Canvas 2D Musical Staff Notation Engraving (`drawStaff`)**: Live rendering of standard 5-line treble staff, clef, pitch positions, ledger lines, solid/hollow note heads, duration stems/flags, accidentals (`♯`/`♭`), rests, and measure barlines.
- **Web Audio API Acoustic Synthesizer (`playPhraseAudio`)**: Auditory auditioning of phrases with fundamental frequencies, harmonic overtones, warm attack/decay envelopes, and active glowing note highlights during playback.
- **Direct Audio Drag-and-Drop & File Upload Zone**: Web interface upload card wired to `/api/upload`, ingesting 16-bit PCM mono WAV audio into evidence, generating pitch proposals, and rendering 10-band FFT spectrum energy bars.
- **SQLite Project Auto-Persistence (`PreviewServer.persist()`)**: Synchronous disk persistence of all review deck state mutations (`/api/confirm`, `/api/correct`, `/api/restore`, `/api/upload`, `/api/propose_alternative`) to the target `.musicmcp` container.
- **Host CLI Subcommand `musicmcp serve`**: Command to launch the interactive local visualizer deck on loopback with optional browser auto-open.
- **Acoustic Audio Test Fixture (`audio/acoustic_melody.wav`)**: 158,804-byte 16-bit 44.1kHz PCM mono multi-harmonic audio file for real-world acoustic verification.
- **Physical Verification Artifacts**: Recorded browser session (`review_deck_proof_1789790264268.webp`), full-resolution screenshots (`initial_page_load_1789790352457.png`, `ams_revision_1_published_1789790456306.png`, `final_verification_state_1789790558204.png`), and validated export files (`audio/melody.xml`, `audio/melody.mid`).

### Fixed
- **Systemic Headless Verification Gap**: Resolved the disconnect between purely synthetic unit-test assertions and actual sensory/interactive user interfaces.
- **PreviewServer Ephemeral State Gap**: Resolved issue where web UI actions were kept only in-memory and never saved to the SQLite database file on disk.

# Changelog

## 0.1.02 — 2026-09-18 — Provider-Neutral Evaluation Silo & TypeSafe Jev Adapter

- Define Provider-Neutral Evaluation Contract (`reference/evaluation/EVALUATION_CONTRACT.md`):
  - Establish provider-neutral abstractions (`EvaluationProvider`, `EvaluationRequest`, `EvaluationResult`, `ProbabilityDistribution`, `EvaluationProvenance`).
  - Enforce core invariant: Interpretation is not mutation. Evaluators propose judgments; only human-held `AuthoritySession` can mutate Authoritative Musical State (AMS).
  - Enforce Bring-Your-Own-Key (BYOK) policy (`TYPESAFE_API_KEY`) and secret redaction (`[REDACTED_SECRET]`).
  - Establish atomic single-judgment request design over monolithic unstructured prompts.

- Implement Evaluation Domain Primitives (`reference/evaluation/contract.py`):
  - `EvaluationType` (`BOOLEAN`, `CHOICE`, `SCORE`, `ALIGNMENT`) and `EvaluationStatus` (`SUCCESS`, `CAPABILITY_UNAVAILABLE`, `AMBIGUOUS`, `UNRESOLVED`, `ERROR`).
  - `ProbabilityDistribution` with calibration tracking and sum-to-1.0 validation.
  - `EvaluationProvenance` capturing provider identity, model ID, timestamp, and credential status.
  - `DetectedEvent` and bounded `EvidenceWindow` for incremental listening and live score-following.

- Implement Evaluator Engines (`reference/evaluation/evaluators.py`):
  - `DeterministicConformanceEvaluator`: Pure local evaluation of atomic conformance rules (locked phrase invariance, generated origin verification, actor authority audits, and score event onset alignment).
  - `TypeSafeJevAdapter`: Optional hosted evaluator adapter. Degrades gracefully to `CAPABILITY_UNAVAILABLE` when `TYPESAFE_API_KEY` is not configured; enforces secret redaction when keys are present.

- Add Conformance Test Suite & Invariant Verification (`tests/test_evaluation.py`):
  - 8 new unit and conformance tests verifying contract primitives, atomic checks, score alignment, graceful degradation, secret redaction, and AMS immutability.
  - Total test suite expanded to 102 tests passing cleanly in ~46s.

- Implement Live Demonstrator (`reference/demo_evaluation.py`):
  - Demonstrates deterministic conformance evaluation, live score alignment via bounded `EvidenceWindow`, Jev adapter graceful fallback, secret redaction, and authoritative state preservation.

## 0.1.01 — 2026-09-18 — local experimental foundation refinement

- Enhance Spectrum Watcher with Acoustic Resonance & Natural Harmonics Analysis (`reference/spectrum.py`):
  - Model natural harmonic series ($f_0, 2f_0, 3f_0, 4f_0, \dots$) with parabolic sub-bin frequency interpolation and relative decibel metrics.
  - Detect sympathetic octave resonance ($2f_0, 4f_0, 8f_0$) honoring acoustic piano open-damper string behavior.
  - Detect natural string harmonics ($3f_0, 5f_0, 7f_0$) with subharmonic fundamental resolution honoring guitar nodal flageolets.
  - Detect standing room resonance modes (< 300 Hz) distinct from electrical mains hum (50/60/100/120 Hz).
  - Invariant verified: Natural acoustic harmonics and room modes are explicitly recognized as acoustic beauty and never flagged as non-musical anomalies.
  - Expose acoustic resonance metrics across REST visualizer endpoints and render real-time resonance cards in `reference/preview/static/index.html`.
  - Add 3 acoustic resonance conformance tests in `tests/test_spectrum.py` (total 94 passing tests in 45.9s).

- Define Visualizer Preview Contract in `reference/preview/PREVIEW_CONTRACT.md` establishing loopback security boundary (127.0.0.1), REST inspection endpoints, and interactive host authority review.
- Implement `PreviewServer` in `reference/preview/server.py` with multi-threaded loopback HTTP server, REST endpoints (`/api/project`, `/api/spectrum`, `/api/proposals`, `/api/alternatives`, `/api/confirm`, `/api/correct`, `/api/restore`, `/api/propose_alternative`), and rich single-page visualizer interface in `reference/preview/static/index.html`.
- Provide interactive visual inspection of 10-band acoustic frequency spectrum (0 Hz to >28 kHz), non-musical anomaly protection (mains hum, infrasonic rumble, ultrasonic leakage, clipping, DC offset), and active phrases by scope.
- Enforce immutable provenance preservation during interactive review: confirming a generated proposal preserves `origin="generated"` in the published revision.
- Add 10 preview conformance and security tests in `tests/test_preview.py` (total 91 passing tests in 44.2s).
- Add live executable visualizer demonstration in `reference/demo_preview.py`.

- Define Alternatives Contract in `reference/alternatives/ALTERNATIVES_CONTRACT.md` establishing explicit request requirements, immutable `origin="generated"` provenance, and non-destructive arrangement isolation.
- Implement `AlternativeGenerator` in `reference/alternatives/generator.py` supporting diatonic harmonies (`HARMONY_THIRD_ABOVE`, `HARMONY_THIRD_BELOW`), octave doublings, root bass pedals, and cadential resolutions.
- Enforce provenance invariant: accepting a generated proposal in `Workspace` preserves `origin="generated"` in the published `Revision` without converting machine output to human authorship.
- Add 4 alternatives conformance and provenance tests in `tests/test_alternatives.py` (total 81 passing tests).
- Add executable demonstration in `reference/demo_alternatives.py`.

- Define Ruleset Contract in `reference/rules/RULES_CONTRACT.md` establishing vocal range & tessitura boundaries, voice-leading leap audits, warning vs. blocking semantics, and the transposition-without-revoicing invariant.
- Implement `RulesEngine` in `reference/rules/engine.py` integrating directly with `Workspace._validator` post-validation callback hook to block out-of-range candidates while logging advisory warnings.
- Implement `transpose_phrase` verifying that semitone transposition strictly preserves exact intervallic relationships without authorizing revoicing.
- Add 5 rules and transposition conformance tests in `tests/test_rules.py` (total 77 passing tests).
- Add executable rules demonstration in `reference/demo_rules.py`.

- Define Collaboration Contract in `reference/collaboration/COLLABORATION_CONTRACT.md` establishing multi-role authority matrices across disciplines (`COMPOSER`, `ARRANGER`, `PERFORMER`, `PRODUCER`, `EDITOR`), explicit scope ownership, and fine-grained delegation with instant revocation.
- Implement `CollaborationManager` in `reference/collaboration/manager.py` integrating directly with `Workspace._policy` callback hook to enforce role boundaries and active delegation grants.
- Add 5 collaboration conformance and security tests in `tests/test_collaboration.py` (total 72 passing tests).
- Add executable multi-role collaboration demonstration in `reference/demo_collaboration.py`.

- Implement Host-Held Interactive Review Shell and CLI in `reference/cli.py` providing an end-to-end interface for human artists holding privileged `AuthoritySession` on the host.
- Provide CLI subcommands: `init` (project creation with scoped grants & locks), `info` (project summary & integrity audit), `inspect-audio` (10-band spectrum breakdown & non-musical anomaly report), `propose-audio` (audio ingestion & pitch proposal), `review` (interactive human confirmation or correction to new published Revision), `export` (MusicXML and MIDI export with REP-1 loss disclosure), `import` (MusicXML and MIDI ingestion with loss reporting), `history` (immutable revision audit log), and `restore` (historical revision restoration).
- Add note string parser (`parse_notes_string`) supporting comma-separated and space-separated pitch-duration pairs (e.g. `'C4 1, E4 1/2, G4 1/2, rest 1'`).
- Add 2 CLI lifecycle conformance tests in `tests/test_cli.py` (total 67 passing tests).
- Add executable CLI demonstration in `reference/demo_cli.py`.

- Define Durable Storage Contract in `reference/storage/STORAGE_CONTRACT.md` establishing content-addressable SHA-256 evidence storage, complete provenance preservation, and SQLite WAL atomic transactions.
- Implement pure Python SQLite Storage Engine in `reference/storage/sqlite_store.py` (`SqliteStorageEngine`) supporting atomic `save_workspace`, `load_workspace`, and deep `verify_integrity` (checking SQLite PRAGMA, schema version, evidence SHA-256 digests, and revision parent-chain continuity).
- Add 5 storage conformance and adversarial corruption tests in `tests/test_storage.py` (total 65 passing tests).
- Add executable durable storage demonstration in `reference/demo_storage.py` demonstrating state survival across workspace destruction, restoration from disk, and continuation of human authority lifecycle.

- Define Format Adapters Contract in `reference/adapters/ADAPTER_CONTRACT.md` establishing SPECIFICATION REP-1 loss disclosure and strict isolation from host authority.
- Implement MusicXML 3.1 Partwise adapter (`reference/adapters/musicxml.py`) supporting bi-directional conversion (`phrase_to_musicxml` and `musicxml_to_phrase`) with explicit `LossReport` disclosing omitted layout, formatting, dynamics, and polyphony details.
- Implement Standard MIDI File (SMF Format 0) adapter (`reference/adapters/midi.py`) with pure Python variable-length quantity (VLQ) encoder/decoder, supporting bi-directional conversion (`phrase_to_midi` and `midi_to_phrase`) with explicit `LossReport` disclosing velocity standardization, enharmonic flattening, and channel assignments.
- Add 5 adapter conformance tests in `tests/test_adapters.py` (total 60 passing tests).
- Add executable format adapters demonstration in `reference/demo_adapters.py` confirming 100% exact mathematical round-tripping for both MusicXML and MIDI.

- Define Model-Facing MCP Transport Contract in `reference/MCP_CONTRACT.md` exposing read, analysis, spectrum inspection, and proposal operations to external Ai models while strictly preserving host-held human authority.
- Implement dependency-free standard-library Model Context Protocol (MCP) server in `reference/mcp_server.py` supporting stdio JSON-RPC 2.0 framing, tools discovery (`get_workspace_summary`, `list_scopes`, `get_phrase`, `inspect_spectrum`, `analyze_audio`, `propose_phrase`), dynamic `music://` resources, and prompt workflows.
- Enforce strict authority gate: models cannot possess mutation tokens or execute `confirm`, `correct`, or `restore`; attempts to mutate via MCP return `MUSICMCP-MCP-AUTHORITY_BOUNDARY_VIOLATION`.
- Add 7 MCP transport conformance and security tests in `tests/test_mcp.py` (total 55 passing tests).
- Add executable MCP server demonstration in `reference/demo_mcp.py` simulating an external model interaction workflow.
- Expand frequency spectrum checks and monitoring to encompass the full 10 Hz to 28,000 Hz (28 kHz) range.
- Implement dependency-free Audio Spectrum Inspector and Non-Musical Anomaly Watcher in `reference/spectrum.py` using pure Python Cooley-Tukey Radix-2 FFT and Hann-windowed frame evaluation.
- Monitor 10 distinct acoustic bands: `deep_infrasonic` (0–10 Hz), `infrasonic_tactile` (10–20 Hz), `sub_bass` (20–60 Hz), `bass` (60–250 Hz), `low_mid` (250–500 Hz), `mid` (500–2k Hz), `high_mid` (2k–6k Hz), `high_treble` (6k–20k Hz), `extended_ultrasonic` (20k–28k Hz), and `extreme_ultrasonic` (>28 kHz).
- Watch for non-musical artifacts beyond music: DC offset bias (>0.008 FS), hard clipping/saturation, sample discontinuity pops, mains electrical hum (50/60/100/120 Hz) with parabolic peak interpolation, 10–20 Hz tactile infrasonic rumble, and 20k–28k Hz extended ultrasonic leakage.
- Expand supported sample rates in `reference/analyzer.py` and `reference/spectrum.py` to 8,000 Hz – 192,000 Hz, supporting high-resolution Nyquist analysis up to and beyond 28 kHz.
- Integrate spectrum reports directly into monophonic analysis results, degrading uncertainty to `AMBIGUOUS` upon critical non-musical anomalies.
- Define monophonic audio analyzer contract in `reference/ANALYZER_CONTRACT.md`.
- Implement dependency-free reference monophonic audio analyzer in `reference/analyzer.py` with normalized autocorrelation pitch tracking, duration quantization to exact `Fraction` units, and qualitative uncertainty classification.
- Add audio fixtures generator in `tests/audio_fixtures.py` and 21 comprehensive conformance/watcher tests across `tests/test_analyzer.py` and `tests/test_spectrum.py` (total 48 passing tests).
- Add executable monophonic audio analysis demonstration in `reference/demo_analyzer.py`.
- Require immutable producer identity/version on each observation and proposal; missing or invalid attribution is rejected.
- Replace bare `locked_scopes` with attributed `LockConstraint(scope, origin, reason)` records retained in candidates and revisions; reject duplicate lock scopes.
- Define all six uncertainty labels and their non-authorizing semantics.
- Specify exact human review and fresh-consent obligations for trusted hosts; no UI, authentication or approval-token subsystem is claimed.
- Add six provenance/uncertainty conformance cases; all 27 tests pass. Source migration is documented in `DEPRECATION.md`.
- Experimental source API changes are intentionally incompatible with 0.1.0. No dependency, durable data format, network capability or musical representation expansion was introduced.

## 0.1.0 — 2026-09-18 — local experimental foundation

- Preserved the existing Apache-2.0 license and founding directive; established governing documentation, contracts, error semantics and continuation records.
- Added a dependency-free Python reference core retaining original evidence, provisional interpretations and structured uncertainty.
- Added host-held scoped authority for confirmation, correction and historical phrase restoration; immutable provenance and workspace revision checks protect publication.
- Added lock/policy/post-validation denial paths and bounded in-memory retention.
- Added adversarial conformance tests, architecture checks and an executable synthetic demonstration.
- No MCP transport, actual transcription, durable storage, adapters, GUI, deployment or published package is included.
