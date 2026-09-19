# Decisions and architectural assessment

## 2026-09-18 21:35:00 — Durable Evidence and Revision Storage Silo with Content-Addressable Integrity

Decision: Implement the isolated Durable Storage Silo (`reference/storage/STORAGE_CONTRACT.md`, `reference/storage/sqlite_store.py`) using pure Python 3.11+ standard library (`sqlite3`, `hashlib`, `json`, `pathlib`).
- Rationale: As documented in `goals_and_dreams.md` and the Founding Directive, the in-process authority kernel discards state upon process termination. True musical stewardship requires sessions and provenance to survive process exit and power failure without corruption.
- Schema & ACID Durability: Uses SQLite in WAL mode with synchronous=NORMAL and foreign_keys=ON. Enforces strict transactional atomicity (`with conn:`) across `schema_meta`, `evidence`, `observations`, `proposals`, `revisions`, `grants`, and `constraints`.
- Content-Addressable Evidence: Raw performance WAV bytes are stored alongside their computed SHA-256 digests. Tampered evidence bytes are detected immediately and cause `EVIDENCE_CORRUPTED` fail-closed rejection upon audit or load.
- Revision Chain Continuity: Verifies that revision 1 has parent 0, and each subsequent revision `r_i` has `parent == r_{i-1}.number`. Any divergence raises `REVISION_CHAIN_BROKEN`.
- Authority Boundary: The storage engine is a persistence facilitator only. Restoring state creates genuine `Workspace` instances and re-binds host `AuthoritySession` tokens; the storage engine cannot forge revisions or grant unverified permissions.
- Verification: 5 conformance tests in `tests/test_storage.py` and live demonstration in `reference/demo_storage.py`. Full test suite passes (65/65 tests).

## 2026-09-18 21:30:00 — MusicXML and MIDI Format Adapters with Explicit Loss Disclosure

Decision: Implement isolated MusicXML and MIDI format adapters adhering to SPECIFICATION REP-1 and zero-dependency Python 3.11+ standard library.
- Constitutional Boundary: In accordance with REP-1 and the Founding Directive, external musical formats carry inherent loss and formatting assumptions. Every conversion must explicitly disclose all discarded or approximated features via an immutable `LossReport(source_format, target_format, loss_type, disclosed_losses, summary)`.
- MusicXML Adapter (`reference/adapters/musicxml.py`): Converts `phrase` to MusicXML 3.1 Partwise XML string using `xml.etree.ElementTree`. Uses divisions = 480 to preserve exact rational note durations without float rounding. Discloses visual engraving omission, expression marking omission, and monophonic voice assumption. Re-imports MusicXML by parsing pitch steps, octaves, alter values, and forward/duration tags into exact rational `Note` objects.
- MIDI Adapter (`reference/adapters/midi.py`): Pure Python binary SMF Format 0 generation and parsing with standard `struct` and VLQ encoding. Writes MThd header and single MTrk track with set-tempo (microseconds per quarter) and note-on/note-off events with delta-times at 480 ticks/quarter note. Discloses velocity standardization to 64, enharmonic spelling flattening to MIDI key numbers, and channel 0 binding. Re-imports binary MIDI streams by parsing track chunks, delta times, and note-on/note-off pairs into exact rational `Note` objects.
- Authority Isolation: Adapters are purely functional transformation tools. They have no access to `AuthoritySession` and cannot mutate or publish workspace revisions.
- Verification: 5 conformance tests in `tests/test_adapters.py` verifying export, import, loss disclosure, and exact round-tripping. Full test suite passes (60/60 tests). Executable demonstration in `reference/demo_adapters.py`.

## 2026-09-18 21:25:00 — Model-Facing MCP Transport Contract and Reference Implementation

Decision: Implement the Model-Facing Model Context Protocol (MCP) Transport Contract (`reference/MCP_CONTRACT.md`) and standard-library reference server (`reference/mcp_server.py`).
- Constitutional Boundary: In accordance with Founding Directive §1 and §4, the model MUST NOT own authoritative state or possess mutation permissions. The MCP server operates as a read-and-proposal gateway only. Privileged `AuthoritySession` capabilities remain strictly held on the host.
- Tool Inventory: Models discover and call safe read/proposal tools: `get_workspace_summary`, `list_scopes`, `get_phrase`, `inspect_spectrum` (10 Hz – 28 kHz checks), `analyze_audio` (monophonic pitch extraction & quantization), and `propose_phrase` (records uncommitted proposals with `origin="interpreted"` or `origin="generated"`).
- Dynamic Resources: Exposes `music://workspace/summary`, `music://workspace/scopes/{scope}/phrase`, and `music://workspace/scopes/{scope}/history`.
- Boundary Enforcement: Any attempt to invoke mutation operations (`confirm`, `correct`, `restore`, `acquire_session`) via JSON-RPC is denied at the transport gate with diagnostic code `MUSICMCP-MCP-AUTHORITY_BOUNDARY_VIOLATION`.
- Conformance & Demo: Added 7 conformance tests in `tests/test_mcp.py` covering protocol initialization, tool listing, phrase reading, 10Hz-28kHz spectrum inspection over MCP, non-mutating proposals, and adversarial mutation attack rejections. Full test suite passes (55/55 tests in 38.2s). Added live demonstration in `reference/demo_mcp.py`.

## 2026-09-18 21:15:00 — Expanded 10 Hz to 28 kHz spectrum checks and non-musical anomaly watcher

Decision: Expand testable frequency ranges and spectrum inspection in Music MCP to encompass the full 10 Hz to 28,000 Hz (28 kHz) range, and implement a dedicated non-musical anomaly watcher in `reference/spectrum.py`.
- Rationale: As formulated in the founding directive and architectural principles, machine analysis must ensure that what we intend is indeed all that is playing. Extra sounds exist beyond what is considered "music" (DC offset, flat-topping clipping, sample-to-sample click pops, 50/60/100/120 Hz mains hum, 10–20 Hz tactile infrasound, and 20k–28k Hz extended ultrasonic leakage). Without a dedicated watcher for non-musical sounds, an audio pipeline cannot verify that unintended acoustic energy is not being produced or ingested.
- Frequency Band Decomposition: Evaluates 10 distinct bands: `deep_infrasonic` (0–10 Hz), `infrasonic_tactile` (10–20 Hz), `sub_bass` (20–60 Hz), `bass` (60–250 Hz), `low_mid` (250–500 Hz), `mid` (500–2000 Hz), `high_mid` (2000–6000 Hz), `high_treble` (6000–20000 Hz), `extended_ultrasonic` (20000–28000 Hz), and `extreme_ultrasonic` (>28000 Hz).
- Watcher Anomaly Detection: Detects `DC_OFFSET` (>0.008 FS), `CLIPPING` (|s| >= 0.999), `CLICK_DISCONTINUITY` (jump > 0.40), `MAINS_HUM` (50, 60, 100, 120 Hz using 4096-point FFT with parabolic peak interpolation), `INFRASONIC_RUMBLE` (>5% in 0–20 Hz), and `ULTRASONIC_LEAK` (>2% in 20k–28k Hz).
- Sample Rates: Supports 8,000 Hz to 192,000 Hz across `reference/analyzer.py` and `reference/spectrum.py`, allowing full Nyquist frequency representation up to and beyond 28 kHz ($F_s \ge 64$ kHz).
- Pitch Mapping Boundary: Frequencies within standard musical octaves 0–9 map to symbolic `Note` names. Frequencies outside this range (e.g. 10 Hz tactile rumble or 28 kHz ultrasonic tones) map to `'rest'` in symbolic transcription and are surfaced via the `SpectrumReport`. Critical anomalies degrade analyzer uncertainty to `AMBIGUOUS`.
- Verification: 12 new conformance tests in `tests/test_spectrum.py`. Full test suite passing (48/48 tests in 36.9s). Pure standard library Python 3.11+ only. Zero external dependencies.

## 2026-09-18 20:52:00 — Monophonic audio analyzer contract and isolated reference silo

Decision: Implement the monophonic audio analyzer contract (`reference/ANALYZER_CONTRACT.md`) and reference implementation (`reference/analyzer.py`) adhering strictly to Python 3.11+ standard library only (`wave`, `struct`, `math`, `fractions`).
- Authority Boundary: The analyzer produces observations and provisional proposals only; it has zero access to host-held `AuthoritySession` and cannot mutate or commit workspace state.
- Signal Processing: Evaluates 16-bit PCM mono WAV audio. Computes frame RMS energy to segregate silence/unvoiced segments. Computes normalized square-difference autocorrelation with parabolic sub-sample peak refinement over 55 Hz to 1050 Hz to extract fundamental frequency f0.
- Symbolic Mapping & Quantization: Maps continuous f0 to standard Western pitches and cents deviation. Quantizes segment durations to exact rational `Fraction` quarter-note units on a defined musical grid based on tempo BPM.
- Uncertainty Classification: Categorizes phrases into `HIGH` (steady pitch), `MEDIUM` (minor drift), `AMBIGUOUS` (vibrato > ±35 cents), `LOW` (weak periodicity), or `INSUFFICIENT_EVIDENCE` (silence/noise).
- Conformance & Architecture: Added 9 conformance tests in `tests/test_analyzer.py` and `tests/test_architecture.py`. Full test suite passes (36/36 tests). Added executable demonstration in `reference/demo_analyzer.py`.

## 2026-09-18 19:54:52 — v0.1.01 approved foundation refinements

The user approved the review checkpoint with "Great. Take the next steps." Scope remains the four identified foundation gaps: uncertainty semantics, producer attribution, constraint provenance and trusted-host approval obligations. No transcription, MCP transport, storage, adapters, GUI or website work was added.

Decision: add immutable Producer(identity, version) separately to observations and proposals. Require genuine host-supplied attribution instead of inventing an anonymous/default producer to preserve old call signatures. Retain provenance via immutable observation/proposal links across confirmation, correction and restore. Replace bare scope locks with LockConstraint(scope, origin, reason), preserve full records in candidates/history, and reject duplicate scope entries rather than silently choosing one origin. Both changes affect the source API; 0.1.01 explicitly documents migration from experimental 0.1.0. No durable schema migration or published compatibility claim exists.

Define HIGH/MEDIUM/LOW as producer-assessed support; other labels express competing readings, unresolved assessment or inadequate evidence. No label supplies numeric calibration, cross-producer ranking or authority. Tests prove all labels leave state provisional. Host documentation now requires exact reviewed workspace/revision, operation, resulting content, provenance, constraints and reason, explicit human action, and fresh review after stale rejection. A new approval-token/authentication subsystem was rejected as outside this trusted-host slice; no consent UI is claimed by the kernel.

Verification: six new cases written before implementation; missing attribution rejection failed on the old behavior and five cases initially errored on absent record types. All 27 cases passed after implementation and fixture migration. A bounded agent updated four contract/security/migration documents; lead inspected their diffs and integration with the code. No new dependencies or disk-persisted music records. The existing Obsidian synchronizer filename mismatch remains unchanged and was not retried or repaired outside scope.

## 2026-09-18 19:45:06 — Review checkpoint 1 — v0.1.0 unchanged

Authority for this checkpoint: the user explicitly requested the entire governing-document review, repository/sync inspection, architectural assessment and a stop for review before substantial implementation. This supersedes the earlier handoff's instruction to proceed to an analyzer contract. Existing implementation from the preceding turn is preserved as a review candidate; this checkpoint neither approves it nor adds implementation.

### Existing state

Reviewed the founding directive, workspace/project agent rules, all required root documents, reference contract, source/demo, tests and package metadata. All 15 required root documents exist. The local v0.1.0 contains a dependency-free Python reference core, synthetic demonstration and 21 tests last verified in the preceding turn at the same source state. Tests were inspected, not redundantly rerun for this documentation-only checkpoint. There is no transcription engine, MCP server, adapter, GUI or durable store. Apache-2.0 LICENSE is unchanged. Canonical remote main contains only README.md and LICENSE.

### Sync state

Fetched origin successfully and verified its URL is https://github.com/CrackenReleased/MusicMCP.git. Current branch: codex/founding-v0.1.0, with no upstream or matching remote branch. Local HEAD: 6e50dcdb4724f03eb216f707e3b81749626ba5f5. Remote origin/main HEAD: 2cb7a038e7941a007d4f130528bcce8e2880d72f. Local main is also at that initial commit. Current branch is ahead 1, behind 0 relative to origin/main; not diverged. One unpushed commit. Working tree was clean on inspection, with no untracked files. This checkpoint changes only this log and handoff.md, leaving two uncommitted documentation edits and no new commits or pushes.

### Architectural assessment and conflicts

The separation of evidence, proposals and authoritative publication is consistent with the founding philosophy. Host-held scoped sessions, immutable snapshots and revision checks form a useful narrow reference slice. The documented Python choice is retained for review, not reopened or expanded.

However, the prior implementation is already beyond the pre-implementation review gate requested now. Treat it as candidate work, not as accepted architecture. The earlier claim that the first milestone was complete does not mean the full first reference use case (performed phrase to intended notation) is implemented.

Concrete specification gaps: uncertainty accepts HIGH/MEDIUM/LOW without defining their interpretive semantics; constraints are stored as locked scope strings without origin/reason provenance; observations and proposals do not identify the producing analyzer or its version. This limits the intended explainability/replaceability contract. These are findings for review, not changes made during this checkpoint. Generated origin is caller-declared and cannot be treated as independently verified by the core.

### Missing foundations to resolve within the first milestone

Clarify the experimental acceptance profile, uncertainty meanings, minimum producer/constraint provenance, and what the trusted host must do to bind human review to exact proposal/content/revision. Preserve the existing operation-boundary error contract and adversarial tests. Explicitly distinguish construction-time scope grants from real human authentication, per-action consent, revocation and delegation. The latter are not implemented and must not be claimed.

### Proposed first milestone for review

Accept or refine one coherent foundation: governing documents and explicit contracts plus the smallest in-memory monophonic phrase authority demonstration. Supplied evidence and competing interpretations remain separate; a trusted host explicitly confirms/corrects a phrase; subsequent analysis cannot overwrite it; locked, unauthorized, stale or failed operations leave state unchanged; generated origin remains traceable; historical content is restored as a new revision.

Reuse the existing candidate rather than generating a second implementation. Acceptance requires agreement on the above contract gaps and executable tests for any approved refinements. Actual analysis, MCP exposure, persistence, MusicXML/MIDI, application integrations, website work and broad musical representation remain outside this milestone. No such implementation begins before review.

### Risks

- Authority: handing a session/factory to model-controlled code defeats the intended boundary. Python encapsulation is not a sandbox or identity system.
- Recovery: in-memory atomic publication protects failed calls, not process crashes, restarts or external side effects. Do not present restore as durable recovery.
- Semantics: prematurely stabilizing the narrow Western pitch/duration profile, whole-phrase origin, or undefined uncertainty labels would create expensive compatibility commitments.
- Integration: synchronous callbacks execute inside the workspace lock; they need trusted bounded execution and cannot yet serve as isolated untrusted modules.
- Continuity: the only implementation commit remains local. Obsidian sync is still blocked by the known canonical-log filename mismatch; no duplicate log or unrelated tool change is proposed here.

### Open questions requiring review

The immediate decision is whether to accept the existing Python in-memory authority prototype as the candidate first milestone, subject to contract clarification, or revise that milestone boundary before further work. Recommendation: retain it as experimental candidate work and resolve only the identified foundation gaps after review. No change to philosophy, Apache-2.0 licensing, model/application agnosticism or canonical state ownership is proposed. Production authentication, persistence, collaborative authority and public wire compatibility remain future decisions, not questions the user must settle now.

Status: stopped for user review. Implementation remains v0.1.0. No new source/tests/dependencies, version bump, commit, push or deployment in this checkpoint.

## 2026-09-18 19:31:36 — v0.1.0 founding assessment

Existing state: inspected the entire initial repository (README and Apache-2.0 LICENSE) and the supplied founding directive. E:\MusicMCP initially had only the directive and no Git metadata. Initialized Git in place, fetched the canonical origin, and checked out its existing main without overwriting the directive. No existing implementation or language decision exists.

Sync at start: main tracks origin/main; both HEADs are `2cb7a038e7941a007d4f130528bcce8e2880d72f`; ahead/behind 0/0. The directive is the only initially untracked file. No unpushed commits. Canonical remote: https://github.com/CrackenReleased/MusicMCP.git.

Conflicts: none in existing code. The original README describes a much narrower purpose than the directive and will be expanded. Preserve the existing license and founding directive.

Missing foundations: behavioral specification, explicit authority and provenance contracts, transaction/error semantics, executable adversarial tests, and developer continuity documents.

First milestone: an experimental in-memory monophonic phrase confirmation kernel. Preserve supplied performance evidence and provisional interpretations, preview a proposed phrase, explicitly confirm/correct it through a host-held authority capability, and restore prior content as a new revision. Analysis is supplied input, not falsely advertised as implemented transcription. No MCP transport, notation application, external adapter, audio extraction, or website changes are included.

Risks: self-declared actor IDs are not authentication; immutable Python objects are not process isolation; in-memory atomicity is not durable crash recovery; a narrow symbolic note profile must not become a universal music format. Address these limits explicitly in contracts and tests. External side effects are forbidden in this first transaction boundary.

Open questions: no founder decision blocks this reversible experimental slice. Authentication for a future network transport, collaborative authority conflict resolution, durable storage, and public wire schemas require separate decisions before exposure.

## 2026-09-18 19:31:36 — v0.1.0 language and dependency decision

Choose Python 3.11+ for the reference kernel. Python and TypeScript both have official Tier 1 MCP SDKs ([official SDK inventory](https://modelcontextprotocol.io/docs/sdk), consulted 2026-09-18). Python also has an established music-analysis ecosystem, exemplified by [music21](https://music21.org/music21docs/about/what.html). These are ecosystem evidence, not dependencies added by this milestone.

Comparison: TypeScript offers stronger compile-time checking and convenient web distribution; Python offers direct access to later signal-processing/music tooling and standard-library dataclasses, fractions, hashing, threading, unittest, and packaging metadata. Both are cross-platform and accessible to contributors. Rust adds strong ownership guarantees but would increase the integration/contributor burden for this small analysis-oriented reference. Python type hints are insufficient for untrusted input: runtime validation is required at every implemented boundary.

Use only the Python standard library at runtime and for tests. No download, build backend, package installation, network permission, telemetry, or provider keys are needed to run from source. Python is replaceable infrastructure; public semantics live in SPECIFICATION.md and the reference contract. Reconsider the language only with evidence that profiling, deployment, or contributor constraints justify migration. Future MCP and audio libraries belong behind separate contracts and require version/license/security review when actually added.

## 2026-09-18 19:31:36 — v0.1.0 authority and transaction boundary

An untrusted proposal cannot contain its own authorization. A trusted host creates the workspace and retains separately issued, scoped authority-session objects; only those objects can confirm/correct/restore. Never hand those objects to a model or translate a model-supplied `approved: true` into their use. This is a capability API for a trusted host, not an identity provider or a Python sandbox.

Prepare changes from immutable values, check the expected revision and scoped grants, evaluate policy and locks, validate the whole candidate, then publish one immutable snapshot containing both content and revision history under a lock. Failures before publication need no compensating rollback. Restoring content appends history rather than deleting it. Disk transactions, external side effects, and rollback-failure recovery remain explicitly unsupported. The first contract tests attack stale writes, mutation without authority, locked scope, provenance loss, validator failure, and correction overwrite.

## 2026-09-18 19:39:54 — v0.1.0 verification and independent review

A bounded documentation agent wrote PHILOSOPHY, ARCHITECTURE_PRINCIPLES, AGENTS, SECURITY, CONTRIBUTING, DEPRECATION and goals_and_dreams; the lead read and integrated all seven. The same agent performed a read-only adversarial core review and identified lost diagnostic context. The lead reproduced four failing assertions, fixed attribution at the shared operation boundaries, and verified the full 21-test suite. The synthetic demo also ran successfully. The source-only kernel has zero third-party dependencies and no persisted user dataset.

Sibling scan: inspected all three mutation operations and seven read/proposal entry points for shared-helper attribution loss. All now contextualize diagnostics; write errors include known phrase scope. See error_history_log.md for red/green evidence. There is one authoritative implementation, one contract and one project decision log; no parallel legacy path or generated binary fixture remains.

The required Hub Obsidian sync command was attempted. It returned `Log not found.` because the existing tool hardcodes `what_and_how_log.md`, whereas this directive explicitly establishes `whats_and_hows_log.md`. Preserve the directive's canonical filename; do not create a duplicate writable log or silently modify unrelated Hub tooling. A later scoped change can add configurable log names to the existing synchronizer. No project mirror exists at E:\AI_Hub\Projects\MusicMCP.
