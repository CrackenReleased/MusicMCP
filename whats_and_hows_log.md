## 2026-09-23 10:41:49 - Owner removes external compatibility testing from active scope

The assistant incorrectly promoted independent MCP-client and external MIDI/MusicXML compatibility checks into the active next steps. The owner explicitly rejected that priority: possible in 2-3 years, not on the active radar. Updated README, CONFORMANCE, the canonical handoff sequence, and idea vault to exclude this work from active priorities and gates until explicitly reopened. Kept historical verification limits and existing adapter/internal test behavior; absence of external evidence is not an obligation to pursue it now. Prose-only correction, no application tests or version change. Implementation/schema v0.1.01.

## 2026-09-22 23:50:44 - Coherent source commits and first clean-checkout CI result

User authorized moving the pending maturation work through commits and CI. Fresh origin fetch showed main and origin/main at 41c27416be17da6bc405def77ca5dcbb682f27a2 with no divergence. Preserved untracked audio/ and live_proof.musicmcp, staging only reviewed source/contracts/tests/docs/workflow. Four v0.1.01 commits on main grouped evaluation validation (bd62b20), preview/host workflow including the new red/green ingestion atomicity fix (4ab4bf0), storage integrity/atomicity (89382d4), and current-status docs/source CI gate (c4a184a). No package/schema version jump, license change, package publication, or release tag. Push to origin/main succeeded through c4a184a; no force operation.

Before push, the complete local suite passed 142 tests in 54.372s; targeted preview regressions were red on old code and green after the decision-point fix. The first clean-checkout Source conformance run 35815806392 at c4a184a passed on GitHub-hosted Windows and Ubuntu, both Python 3.11 and Node 22, with synthetic demo plus 142 tests and no reported skips. Windows suite 54.058s, Ubuntu 79.698s. This closes the source-run automation portion of milestone 5 for those environments; it does not establish a packaged install, broader Python matrix, musical ground truth, independent interoperability, hardware power-loss behavior, or a release. Recording provenance and intended notes were requested separately for the musician acceptance gate. Reconsider release numbering only with owner decision and compatibility evidence.

## 2026-09-22 23:44:13 - Preview partial-ingestion fix at the mutation boundary

Release-gate review of the mixed preview diff found a decision-point gap: `_execute_mutation` snapshots state only when called, but upload and alternative handlers had already created evidence or an observation. Two HTTP regressions proved the failure on the old code: malformed uploaded WAV retained one new evidence record; forced alternative save failure retained one new observation. Moved both complete record-creation sequences inside the existing serialized mutation/persistence boundary, so its rollback restores the true pre-request state. Chose this over endpoint-specific cleanup because the shared boundary already owns recovery and concurrency. Targeted red-to-green tests pass; the final full suite passed 142 tests in 54.372s before publication. Sibling scan checked all preview workspace write sites and found no other pre-boundary mutation. Update the preview contract and error history; implementation/schema stays v0.1.01, Unreleased.

## 2026-09-22 23:01:34 - First source release gate established; CI evidence pending

Inspected pyproject, contributor instructions, test commands, and .github: package metadata still declares 0.1.01 and experimental-source-only; no existing CI, build backend, or install/publish procedure. Chose a minimal source-check workflow over inventing package/release machinery. New .github/workflows/conformance.yml checks out a clean tree, sets up Python 3.11 and Node 22, then runs the existing synthetic demo and complete unittest suite on Windows and Ubuntu pull requests and main pushes. Read-only token permissions and no deployment/publishing steps. README, CONFORMANCE, CONTRIBUTING, and CHANGELOG now give exact commands and distinguish local observations from future CI results. Official GitHub action docs were checked for current checkout/setup versions; v7 was selected. This stage adds one workflow file, no runtime dependency, schema field, application behavior, or version change.

Verification: workflow parsed as YAML with expected triggers, OS matrix, and two commands; local relative Markdown links resolve; git diff --check is clean apart from Git line-ending notices. The synthetic demo passed locally after the workflow/doc change. The complete suite already passed 140 tests on this same code working tree before these prose/workflow edits, so it was not rerun. Local environment is Windows, Python 3.11.15, Node 24.19.0. The new workflow has not run, Ubuntu and Node 22 remain unverified, and this dirty working tree is not a clean published checkout. The source-only project offers no installed distribution; the documented clone-and-run flow is its present reproducibility path. Real-musician provenance/intended-note acceptance remains separate and open. Reconsider packaging/CI matrix/version only with compatibility evidence and owner release decision; no commit/push/release here.

## 2026-09-22 22:57:22 - Current-status documentation reconciled

Decision: keep declared package/schema version v0.1.01, Unreleased, while describing the repository as a small in-memory authority core plus separate experimental reference silos. The former core-only descriptions in README, specification, architecture, security, errors, conformance, and idea vault had become false when read as claims about the whole repository. The alternative of renumbering to the old draft 0.1.02/0.1.03 labels would imply a release decision and compatibility evidence we do not have. Historical change entries remain intact; current headings and status text now distinguish those records from the declared version. The evaluation probability tolerance now matches the implemented 1e-6 contract, and EvidenceWindow is described as a primitive rather than proof of live score following.

Evidence: module contracts and entry points for analyzer, MCP stdio gateway, SQLite storage, adapters, preview, evaluation, collaboration, rules, and alternatives; pyproject declares 0.1.01 with no runtime dependencies; last full suite passed 140 tests on the prior code-working tree. Local recording walkthrough proves mechanical review/reopen/export only. Link check found no broken relative Markdown links across eight edited status documents; exact diff and git diff --check reviewed. No code, schema, dependency, or application test change in this pass. No new release, commit, or push. Hardware power loss, musical ground truth, independent format/MCP compatibility, provider integration, and authenticated human consent remain open. No Hub project mirror exists at E:/AI_Hub/Projects/MusicMCP. Reconsider this wording when those acceptance checks land or package version actually changes.

## 2026-09-22 22:50:47 — Stored causal-chain and process-interruption validation

The storage loader previously checked evidence hashes and revision sequence/parents but accepted missing or mismatched evidence -> observation -> proposal -> revision links; `verify_integrity` reported such files valid. A new parameterized corruption regression was observed red on 11 initial relationship/serialization cases before the fix. Added one shared record audit used by `load_workspace` (fail-closed `MUSICMCP-STORAGE-INTEGRITY_FAILURE`) and `verify_integrity` (invalid report). It checks causal IDs, scope, producer fields, operation/origin/notes semantics, and earlier restoration sources. A disposable on-disk `.musicmcp` tamper test confirms rejection on a fresh connection. Three later red cases showed JSON booleans and unexpected note/constraint fields were silently accepted; the decoders now require exact field sets and integer duration parts. No schema migration or repair of evidence.

A separate subprocess test kills an actual writer after the storage engine stages a correction and reaches `conn.commit()`, then reopens the file. The prior revision, evidence count, state token, and integrity report remain intact. Existing tests cover competing writers, rejected forced replacement, and legacy-grant migration failures. This is a real process-interruption check, not a hardware power-loss test. Sibling scan covered both read paths (`load_workspace`, `verify_integrity`), note/constraint decoders, preview recovery and CLI reopen consumers, and the existing save conflict/migration paths. `python -B -m unittest discover -s tests` passed all 140 tests in 53.421s on the final tree. The targeted corruption cases, disposable-file case, and process-kill case also passed.

Changed two existing source/test files (`reference/storage/sqlite_store.py`, `tests/test_storage.py`) and existing `reference/storage/STORAGE_CONTRACT.md`, `CONFORMANCE.md`, `CHANGELOG.md`, `error_history_log.md`, and `handoff.md`; Hub handoff updated separately. Artifact impact: zero new/removed project files, about 260 task-owned source/test lines for the shared audit and three regressions (current Git diff also contains older pending edits), zero dependencies/schema fields/datasets, no retained project fixture. Implementation/schema remains v0.1.01, Unreleased. No commit/push; user `audio/`, `live_proof.musicmcp`, and all prior Antigravity/Codex work preserved. Fresh fetch: main and origin/main both `41c27416be17da6bc405def77ca5dcbb682f27a2`, 0 ahead/behind, no unpushed commits. Full 140-test suite is the last known good working-tree state.

One failed early disposable-file test kept its SQLite connection open, so its temporary fixture directory was not removed by test teardown. The test now closes that connection and later runs clean up. Automatic approval review rejected both an exact temp-directory cleanup and a narrower direct-file cleanup with reason 'blocked by policy'. The remaining owned fixture is `C:/Users/CRACKE~1/AppData/Local/Temp/tmp2nmtxt5h/project.musicmcp` (57,344 bytes); no application or user project references it. It remains for manual removal or a future allowed cleanup path.

Next milestone: reconcile current documentation against implemented behavior and test evidence per handoff milestone 4. Do not claim verified hardware power-loss durability, producer authenticity, or musical transcription accuracy from these tests.

## 2026-09-22 22:28:31 — Preview horizontal overflow fixed

A populated review deck reproduced page overflow: at a 1250px viewport, the document was 1489px wide; at 375px, it was 741px. The decision point was the grid's default minimum track size (`1fr`), which let the 640px staff canvas enlarge the center column. The header and proposal title row also held controls on one line at narrow widths. Changed the grid tracks to `minmax(0, 1fr)`, allowed grid sections/cards to shrink, and wrapped the affected header/title rows. The staff canvases retain their drawing width and scroll inside their wrappers. No musical data or authority behavior changed.

Added the reproducible browser width check to `CONFORMANCE.md` before changing CSS; observed its red baseline. After the fix, settled document widths were 1235/1250px, 753/768px, and 360/375px. Both staff canvases rendered; wrapper scroll widths exceeded client widths where appropriate. At 375px, the proposal card's client and scroll widths both measured 254px, badges wrapped, and mutation controls were visible. Browser screenshots inspected; the active QA page had no console warnings/errors. `python -B -m unittest tests.test_preview` passed 24 tests. Sibling scan covered the desktop/mobile grid tracks, fixed-width staff wrappers, header and card title rows, scope/proposal title rows, and the three two-column form grids; none still caused page overflow at the checked widths.

Artifact impact: one existing source file and six existing project docs changed, plus the Hub handoff; no files added/removed, no test-code growth, about 12 net source lines, no dependencies or persisted fields/datasets. The browser regression is a written, runnable manual check in the existing conformance file. Disposable in-memory QA server and static server stopped; browser tab closed and viewport reset; no fixtures or screenshots retained. Prior Antigravity/Codex changes, `audio/`, and `live_proof.musicmcp` preserved. Implementation/schema remains v0.1.01, Unreleased; no commit/push. Git fetch succeeded this session: main/HEAD and origin/main are `41c27416be17da6bc405def77ca5dcbb682f27a2`, 0 ahead/behind, no unpushed commits. Latest full suite remains the earlier 137-test pass; this task ran the complete 24-test preview suite.

Next bounded maturation action: inspect relationship validation in `reference/storage/sqlite_store.py` for evidence -> observation -> proposal -> revision and add a corrupt-project regression in `tests/test_storage.py` before any storage fix. Musical acceptance of the recorded fixture still awaits owner-confirmed provenance and intended notes; do not treat mechanical walkthrough as transcription accuracy.

## 2026-09-22 21:45:00 — Staff bounds fix and handoff

Reproduced clipping in `reference/preview/static/index.html::drawStaff`: its fixed 120px canvas did not contain drawing coordinates for C#8 or C3. Extended the existing shipped-JavaScript regression harness to capture canvas draw coordinates and verify they fit after dynamic sizing; observed the new assertion fail on the old fixed bounds. Resized the canvas from the displayed pitch range while retaining minimum height and unchanged note data. `python -B -m unittest tests.test_preview.TestCorrectionEditor` passed; full scoped `python -B -m unittest tests.test_preview` passed 24 tests. Disposable browser visual check showed C#8, C3 and E4, ledger lines, stems and labels fully inside the resized staff canvas; console had no warnings/errors. The page still has horizontal overflow, a separate remaining issue and the next bounded rendering task. This verifies vertical pitch bounds only, not general responsive layout or musical accuracy.

Updated `reference/preview/PREVIEW_CONTRACT.md`, `CONFORMANCE.md`, `CHANGELOG.md`, `error_history_log.md`, `handoff.md`, and Hub `Communication/HANDOFF.md`. Implementation/schema remains v0.1.01, Unreleased. No commit/push, dependency, fixture or retained QA artifact. Preserved existing unrelated/Antigravity changes, `audio/`, and `live_proof.musicmcp`. Artifact impact for this task: 2 existing implementation/test files plus 7 existing project/Hub documentation files updated; no new files.

Next exact task: reproduce and fix horizontal page overflow in the preview as an independent bounded layout issue. First identify the causing layout decision and add scoped regression coverage, then verify the browser layout. Do not broaden into full responsive redesign. Preserve all pending work. Last known sync state is prior `main`/`origin/main` at `41c27416be17da6bc405def77ca5dcbb682f27a2`, 0 ahead/behind; refresh before any future publication decision. No commit or push was performed.

## 2026-09-22 19:52:23 — Pending/reviewed labels corrected

User asked to continue; bounded next task was misleading PENDING labels. Changed review deck to derive reviewed IDs from revision history and count pending/reviewed separately; added per-card status while retaining every original. History chosen over current phrases so a later replacement cannot make a reviewed proposal pending again. Reviewed is intentionally used instead of Published because a correction may publish changed notes, not the original interpretation.

Extended existing TestCorrectionEditor JS harness (no new test framework/files): initial count, correction count/status, and mixed list with historical reviewed proposal no longer current. Regression observed failing before change. During verification the harness accidentally shared/pushed the same proposal array twice; fixed fixture ownership. First preview-suite run had that fixture failure plus one foreign-host HTTP test error; final rerun python -B -m unittest tests.test_preview passed all 24 tests in 12.231s. HTTP error did not recur; no network/security fix claimed. Last full-suite run remains prior 137-test pass, not rerun for this scoped HTML change.

Browser QA: two disposable in-memory proposals showed 2 Pending / 0 Reviewed; confirming one showed 1 Pending / 1 Reviewed, matching per-card labels, retaining both originals. Reload preserved counts/status. Rendered screenshot inspected. Existing horizontal overflow remains; no layout fix claimed. Invalid placeholder audio in this status-only fixture means spectrum results were not under test. Closed tab and stopped exact qa-status server on 8878; no retained outputs or user asset writes.

Sibling scan: header count, per-card status, empty/loading text and project-history refresh inspected; selection/correction state regression still passes. Changed seven existing project files (HTML, test, preview contract, changelog, why-log, error log, handoff); no added/removed files, runtime dependencies, datasets or fields. Source/test growth bounded to history/count/card labels plus harness assertions. Implementation v0.1.01 unchanged; no commit/push. Next task: high-note clipping, then horizontal overflow as separate rendering issues; real-recording musical acceptance remains open.

## 2026-09-22 00:46:48 — Correction editor reset fixed; Antigravity continuation ready

User authorized the correction-editor fix and requested a complete handoff before stopping. Root cause: handleCorrect cleared dirty state and refresh repopulated the field directly from immutable prop.notes. Corrected decision point in selectProposal: use matching current confirmed phrase (scope + proposal ID) for clean editor, otherwise original proposal; display source and explain buttons. Fetch project before proposals. Dirty drafts survive refresh and same-card clicks; successful save only clears dirty state for unchanged submitted input. Original proposals and authority semantics remain intact.

Regression: tests/test_preview.py::TestCorrectionEditor.test_editor_uses_confirmed_notes_and_preserves_new_drafts runs the real inline JS using installed Node and a minimal DOM/fetch harness. Observed red before fix (C4 1 != E4 2), green afterward. Covers save, clean reload/reselection, dirty draft retention and switching to a distinct proposal. Node is test-only; explicit skip if absent. Full suite: python -B -m unittest discover -s tests — 137 passed in 54.900s, no skips observed. git diff --check passed.

Browser QA on disposable in-memory qa-editor project at 127.0.0.1:8877: submitted E4 2 over C4 1, saw AMS and editor E4 2 plus confirmed-revision source label; typed unsaved G4 3, Refresh and same-proposal click preserved it; page reload returned saved E4 2. Screenshot visually checked source label and editor, zero captured console warnings/errors. Dynamic card ID changed during polling once; reselected its stable DOM ID successfully. No persistent QA database, recording copies or screenshots retained; browser closed and exact QA server stopped. Original user assets untouched.

Sibling scan: selectProposal, fetchProject/fetchProposals, refreshAll, dirty-state event listener, and confirm/correct/restore refresh paths inspected. Same-card dirty reset addressed within same failure class. No unrelated pending-label or notation patch. Remaining findings: published proposals still marked PENDING; high-note staff glyph clipping; horizontal overflow at the default wide browser viewport observed during visual inspection (not a responsive-layout pass). Source-label layout readable after scrolling to the editor; no universal layout claim.

Artifact impact: eight existing project files modified by task (HTML, tests/test_preview.py, preview contract, CONFORMANCE.md, changelog, why-log, error log, handoff). No files added/removed, dependencies installed, persisted fields or generated assets retained. Task net source/test growth +82 lines (HTML +13, tests +69), reusing existing modules. Implementation v0.1.01 unchanged, Unreleased. No commit/push; preserve all prior Antigravity/Codex pending changes.

## 2026-09-21 19:29:35 — Local audio walkthrough: mechanics passed, musical acceptance open

Input authorized by owner: audio/acoustic_melody.wav, 158804 bytes, 1.8 seconds, 44100 Hz, mono PCM16. SHA-256: 2baf339536b4b0de31c2c242e52e5ff52efc2782ccc70b3a82cd3c0a3b524aa3. Existing handoff calls it an acoustic audio fixture; real-performance provenance and musician-intended notes are not established. Tempo 120 BPM was an explicit QA reference, not measured tempo.

Executed locally on verification/local-audio-walkthrough/review.musicmcp with actor local-walkthrough; originals never opened for mutation. CLI ingestion produced HIGH uncertainty: C4 2/3, C#8 1/16, E4 3/4, C#8 1/16, G4 3/4, C3 1/16, C5 1. This agrees with the prior export but is not independent musical ground truth. Short extreme notes merit investigation with labeled performance evidence; do not silently filter them based on this one example.

Browser QA at 127.0.0.1:8876: inspected actual rendered review deck and corrected staff at default viewport (approximately 895x779). Clicked proposal to populate spectrum. Confirmed the original analyzer output as QA revision 1, explicitly labeled not artist-approved. Entered four quarter notes C4/E4/G4/C5 and an explicit QA correction reason; manual Refresh preserved the unsaved draft. Submitted correction; AMS showed revision 2, the four notes, and both historical revisions. Screenshots observed inline in session; no screenshot files retained. Browser console reported no captured warnings/errors. No audible quality, file-picker upload, mobile/responsive matrix, or independent notation application verification claimed.

Stopped the exact isolated preview process, reopened database in a new process, verified revision 2/history/evidence bytes and storage integrity. Exported via CLI to MusicXML/MIDI; each internal importer reconstructed the exact four QA notes and durations. This is an internal round trip, not independent interoperability certification. Export loss disclosures remain applicable (expression/layout/voices, MIDI velocity/channel/enharmonics). Protected original WAV, original XML/MIDI, and live_proof.musicmcp SHA-256 hashes were identical before/after. Preview stopped; QA tab closed; disposable project/exports removed after results recorded.

Findings: (1) published/then-corrected proposal still displays 1 PENDING; (2) after correction, editor resets to original analyzer notes while AMS correctly retains the correction, risking accidental re-submission; (3) extreme-pitch proposal staff rendering clips high-note glyphs at the top, although text chips show their pitches. No source fixes made during this bounded walkthrough. Musical acceptance remains open: establish fixture provenance/intended phrase, obtain musician feedback, and compare export in an independent consumer. Do not count this as completed real-performance validation.

## 2026-09-21 19:24:38 — Maturation milestone 1 complete locally (implementation v0.1.01)

User authorized the first maturation steps. Completed evaluation validation only. Missing/null rule fields now yield UNRESOLVED; malformed fields yield ERROR; wrong rule result type is unavailable. Empty grant sets and zero onsets remain valid evidence. Provider mock/HTTP paths share one result validator for strict Boolean/choice/alignment/score decisions, labels, explanation and probabilities; absent calibration defaults false. Request envelope construction now rejects invalid types/candidates. Probability normalization tightened from +/-0.05 to +/-1e-6 and documented; no release or storage schema change.

Reasoning: default substitution cannot distinguish no evidence from a measured negative. One shared provider response boundary avoids divergent mock/live acceptance. Preserve valid False and zero rather than testing decision truthiness. Calibration is only a provider claim, not independent scientific validation. Existing musical ranking rules remain unchanged; these checks validate shape/completeness, not identity, musical accuracy, live provider compatibility or quality of supplied evidence.

Regression evidence: seven new TestEvaluationValidation methods were run before implementation, producing 70 failing parameter cases and 5 errors; corrected suite passes. Added an eighth valid-empty-grants/zero-onset/type-mismatch case and expanded the confirmed-state test across success, unavailable, unresolved, ambiguous and error. Exact commands: python -B -m unittest tests.test_evaluation — 19 passed; python -B -m unittest discover -s tests — 136 passed in 54.529s. The latter includes synthetic CLI lifecycle and storage/preview coverage. git diff --check passed. No new tests use live provider calls.

Sibling scan: three Boolean rules plus alignment, two provider execution paths, and shared probability/request constructors inspected. Five demo request sites use supported envelopes/context; demo was not executed because it can call a configured live provider. Mock forced calibrated=True removed. No new arbitrary fallback. Deferred: real-recording musical validation (milestone 2), project-file relationship validation, documentation reconciliation, release gate and live integration verification.

Artifact impact: eight existing project files changed by this task (contract.py, evaluators.py, tests/test_evaluation.py, EVALUATION_CONTRACT.md, CHANGELOG.md, whats_and_hows_log.md, error_history_log.md, handoff.md); none added/removed. Three affected source/test files total net +323 lines versus HEAD, including preexisting work. No dependency, persisted field or dataset added; no generated artifacts retained. User audio/ and live_proof.musicmcp preserved. Local code only, no commit/push. Implementation remains v0.1.01, Unreleased.

## 2026-09-21 19:14:54 — Maturation handoff documentation, revision 1

User requested a reusable Antigravity handoff. Added the canonical six-stage maturation sequence to handoff.md with starting paths, acceptance evidence, existing baseline, scope and release/data boundaries. Reused the existing handoff instead of adding a new plan artifact; goals_and_dreams.md remains the idea vault. Documentation only: no source/test changes, dependencies, generated project artifacts or version bump. Implementation remains v0.1.01, fixes Unreleased. Verification: inspect six stages, referenced files and diff whitespace; no application test rerun required. The earlier 128-test result is historical verification, not a new run.

## 2026-09-21 19:11:57 — Codex — evaluation reliability (unreleased, implementation v0.1.01)

Approved scope: fix missing JSON import and unsupported deterministic fallback, then verify existing end-to-end workflow. Added JSON import so existing HTTP path reaches transport; replaced invented fallback SUCCESS with CAPABILITY_UNAVAILABLE, no decision/probabilities, and UNRESOLVED uncertainty. Choice/score capabilities now reflect their lack of implementation. Kept existing named Boolean/alignment rules and provider transport architecture. No release/schema change; fixes are Unreleased.

Regression evidence: tests/test_evaluation.py::test_live_transport_constructs_request_and_preserves_provider_result failed before fix because transport was called zero times; test_unsupported_questions_never_invent_a_judgment failed for Boolean, choice and score before fix. Both now pass. Strengthened existing transport-error test to assert transport invocation (prevents serialization bugs masquerading as network errors), and existing state test to compare an actually confirmed snapshot. Provider response is mocked; no live API/model compatibility or calibration claim.

Validation: python -B -m unittest tests.test_evaluation — 11 passed; python -B -m unittest discover -s tests — 128 passed in 52.951s. Includes tests/test_cli.py::TestCli.test_full_cli_lifecycle: synthetic A4 ingest/proposal, host confirmation/correction, saved project reopened by successive CLI calls, MusicXML/MIDI export, import and restore. Existing suite fixtures cleaned themselves; user audio/ and live_proof.musicmcp untouched. git diff --check passed.

Sibling scan: checked five remaining SUCCESS sites (three named Boolean rules, alignment, provider return), both JSON use sites, and first-candidate/default selectors across reference/evaluation. Removed the only remaining arbitrary first-candidate fallback. Separate follow-up concerns: named rules still default missing context, and provider responses lack comprehensive type/decision validation. These require their own failing cases; do not claim all evaluation input is validated.

Artifact impact: seven existing project files modified in this task; zero added/removed, dependencies, persistent fields or retained generated artifacts. Source/test combined net +94 lines versus HEAD includes prior Antigravity edits, not solely this task. No parallel agent work. Preserved all pending changes. Canonical evaluation contract now distinguishes missing capability from attempted-request errors. No public version renumbering; no commit/push.

## 2026-09-21 19:07:40 — Codex — atomic saves and truthful preview recovery (unreleased, implementation v0.1.01)

Context: user approved only save/reopen/recovery reliability after reviewing Antigravity's pending work. Three storage regressions were observed failing before changes: failed force replacement erased stored content; rejected legacy-grants migration changed schema/permissions; normal save rewrote an unsupported schema. Three preview regressions also failed before changes: recovery lost host configuration, failed reconciliation continued accepting writes, and failed ingestion left partial records.

Decision: use one BEGIN IMMEDIATE transaction across schema migration, conflict checks, force clearing and writes; remove executescript's implicit commit. Hold the workspace lock until commit and token publication, use FULL synchronization, and use consistent read transactions for load/integrity. The alternative of moving serialization earlier alone would not close migration or competing-writer gaps. Runtime host callbacks remain outside the database and are explicitly retained on preview recovery. Preview request locking covers session selection through persistence/recovery; failed reload reports unknown state and freezes writes until reopen.

Verification: python -m unittest discover -s tests — 126 passed in 54.382s. Nine new regressions in tests/test_storage.py and tests/test_preview.py; six observed failing on the pre-fix code and passing afterward. The additional competing-connection, restricted-session-subset, and serialized-request checks pass; no claim of a pre-fix run for those three. Storage targeted suite passed before final full run. Existing suite owns disposable fixtures; new storage tests use in-memory databases, and new preview tests use mocked handlers. No power-loss or hardware durability certification.

Sibling scan: all persistence callers are in CLI (6 saves), demo_storage (2 saves), and preview (1 save); all share the corrected engine. Load and integrity readers now use consistent snapshots. Preview mutation routes share one recovery path. Direct external in-process writers are outside preview's HTTP lock. No new dependencies, files, data fields, databases or retained generated artifacts. Existing audio/ and live_proof.musicmcp untouched.

Version rationale: this repairs existing behavior, with no new public feature or schema. Added an Unreleased changelog entry, retaining implementation/schema v0.1.01 and existing pending v0.1.04 history; no unilateral release numbering or broad metadata reconciliation. Reconsider version only when cutting an explicit release.

Delegation: foundation_docs changed only preview server and tests; lead inspected those changes and ran the integrated suite. Evaluation issues previously found remain out of scope: missing json import and first-candidate fallback success. Next separately scoped task: failing evaluator tests for real request construction and unsupported evaluation behavior. Canonical contracts updated for actual guarantees.

# Decisions and architectural assessment

## 2026-09-18 23:25:00 — Provider-Neutral Evaluation Silo & TypeSafe Jev Integration

Decision: Adopt and adapt the Provider-Neutral Evaluation Architecture from `01_MusicMCP_Jev_Evaluation_Architecture_Addendum.md` across Music MCP.
- Core Architecture:
  - Provider-Neutral Contract (`reference/evaluation/EVALUATION_CONTRACT.md`, `reference/evaluation/contract.py`):
    - Establishes `EvaluationProvider`, `EvaluationRequest`, `EvaluationResult`, `ProbabilityDistribution`, `EvaluationProvenance`.
    - Enforces four distinct layers: Physical Audio Signal -> Normalized Musical Evidence -> Musical Interpretation -> Authoritative State Governance.
    - Constitutional Invariant: Interpretation is not mutation. Evaluators propose judgments; only human-held `AuthoritySession` can mutate Authoritative Musical State (AMS).
  - Deterministic Conformance Evaluator (`reference/evaluation/evaluators.py`):
    - Evaluates atomic conformance rules purely with local logic: locked phrase immutability, generated provenance tracking, actor authority audits, and score event onset alignment.
  - TypeSafe Jev Adapter (`reference/evaluation/evaluators.py`):
    - BYOK integration (`TYPESAFE_API_KEY`) for TypeSafe Jev.
    - Invariant: When credentials are not configured, degrades gracefully to `CAPABILITY_UNAVAILABLE` with zero impact on core state and zero network overhead.
    - Secret Redaction Invariant: Sanitizes all sensitive API keys and tokens, replacing them with `[REDACTED_SECRET]` in explanations, logs, and diagnostics.
  - Incremental Evidence & Live Score Following (`EvidenceWindow`, `DetectedEvent`):
    - Introduces bounded temporal windows (e.g. 12.0s - 14.0s) with acoustic onsets, durations, and pitch candidates, laying the foundation for low-latency live score-following without forcing whole-file batch transcription.
- Conformance & Verification:
  - 8 new tests in `tests/test_evaluation.py` covering contract validation, atomic conformance checks, score alignment, graceful degradation, secret redaction, and AMS immutability.
  - Full test suite: 102/102 passing tests in 46.1s across the entire Music MCP workspace.
  - Live demonstrator: `reference/demo_evaluation.py` demonstrating all evaluation primitives, score alignment, Jev adapter fallback, and secret redaction.

## 2026-09-18 22:24:00 — Acoustic Resonance, Natural Harmonics, and Sympathetic String Modeling

Decision: Upgrade `reference/spectrum.py` and `reference/preview/` to actively analyze natural harmonic overtones, sympathetic octave resonance, and standing room modes.
- Physical Realities Modeled:
  - Open Piano Sympathetic Resonance: Striking Middle C with un-damped strings excites octave harmonics ($C_5, C_6, C_7$). The watcher tracks these as `sympathetic_octaves_present=True`.
  - Guitar Nodal Flageolets: Lightly touching a string node damps the fundamental and elevates the harmonic (e.g. 3rd harmonic $D_5$ on a $G_3$ string). The watcher employs subharmonic resolution within 4% frequency tolerance to identify the true string fundamental while recognizing the natural overtone bloom (`natural_harmonics_present=True`).
  - Standing Room Modes: Identifies low-frequency physical room resonance modes (< 300 Hz) that do not align with harmonic integer multiples, accurately distinguishing physical acoustic environments from electrical mains hum (50/60/100/120 Hz).
- Anomaly Invariant: Natural resonance is recognized as organic musical tone and is never penalized or flagged as an anomaly.
- Verification: 3 conformance tests added to `tests/test_spectrum.py` covering piano sympathetic octaves, guitar natural harmonics, and room modes. Full test suite passes (94/94 tests in 45.9s).

## 2026-09-18 22:18:00 — Guidance: Acoustic Experience Versus Technical Measurement

Decision: Add explicit acoustic guidance to `PHILOSOPHY.md` distinguishing physical/psychoacoustic experience from mechanical electronic measurement.
- Rationale: Real instruments and physical spaces generate sympathetic resonance (e.g. un-damped piano octave resonance), natural harmonics (guitar node flageolets), and room mode blooms that create complex overtone interactions. These phenomena alter electronic sensor readings and can register as "pitchy" or impure on mechanical meters while sounding deeply musical, resonant, and emotionally true to human listeners.
- Guidance Status: Framed deliberately as foundational guidance rather than a rigid dogmatic tenet, honoring human perceptual experience, room handling, and artistic presentation over mathematical sterility.
- Watcher Boundary Refinement: The acoustic watcher's duty is strictly to identify non-musical, unintended defects (clipping, DC offset, electrical hum, ultrasonic converter leakage), never to sanitize natural resonance or second-guess an artist's judgment. Human intent and perceived experience govern over mechanical metrics.

## 2026-09-18 22:07:00 — Local Interactive Visualizer Preview and Host Authority Review Deck

Decision: Implement the Local Interactive Visualizer Preview Silo (`reference/preview/PREVIEW_CONTRACT.md`, `reference/preview/server.py`, `reference/preview/static/index.html`).
- Rationale: Human authority review is the constitutional keystone of Music MCP. A terminal CLI is essential for host automation, but an accessible, zero-dependency visual interface allows musicians to immediately inspect audio evidence, 10-band spectrum analysis, non-musical anomalies, extracted pitch timelines, and candidate proposals side-by-side.
- Localhost Security Boundary: Binds strictly to `127.0.0.1` (loopback). Network calls from remote interfaces are strictly rejected with 403 `SECURITY_VIOLATION`. The server never exposes raw unauthenticated tokens over external networks.
- Full Acoustic Spectrum Visibility: Directly calls `watch_audio_bytes` to expose 10 frequency bands from 0 Hz to >28 kHz, flagging non-musical anomalies (clipping, DC offset, 50/60/100/120 Hz hum, 10-20 Hz rumble, 20k-28k Hz ultrasonic leak) before the artist commits musical changes.
- Provenance Invariant Safeguard: When accepting a generated alternative through the visualizer, `origin="generated"` is preserved in the published `Revision` without converting machine output into human authorship.
- Zero-Dependency Standard Library: Implemented purely with Python 3.11+ `http.server`, `socketserver`, `json`, `urllib.parse`, and vanilla HTML5/CSS/JS. Zero Node/npm, zero external Python libraries, zero CDN scripts.
- Verification: 10 conformance and security tests in `tests/test_preview.py` and live demonstration in `reference/demo_preview.py`. Full test suite passes (91/91 tests in 44.2s).

## 2026-09-18 21:55:00 — Requested Generated Alternatives and Provenance Protection

Decision: Implement the Requested Generated Alternatives Silo (`reference/alternatives/ALTERNATIVES_CONTRACT.md`, `reference/alternatives/generator.py`).
- Constitutional Invariant: Machine generation occurs strictly upon explicit, recorded human request (`AlternativeRequest`). Algorithmic models never autonomously alter score content.
- Permanent Generated Attribution: When an artist accepts a generated alternative into the authoritative score, the revision records `origin="generated"`, preserving historical integrity and preventing machine suggestions from masquerading as human authorship.
- Scope Isolation: Target alternatives (harmony, bass) populate designated scopes without modifying or overwriting the human composer's melody or locked constraints.
- Verification: 4 conformance tests in `tests/test_alternatives.py` and live demonstration in `reference/demo_alternatives.py`. Full test suite passes (81/81 tests).

## 2026-09-18 21:50:00 — Constraint-Aware Arranging and Musical Rules Engine

Decision: Implement the Constraint-Aware Arranging Ruleset Silo (`reference/rules/RULES_CONTRACT.md`, `reference/rules/engine.py`).
- Rationale: The human artist defines vocal ranges and style constraints; the machine audits conformance to prevent physical vocal strain or hardware boundary overflow.
- Transposition vs. Revoicing Invariant: Semitone transposition preserves exact rational durations and relative pitch intervals. Changing chord inversions or revoicing requires explicit human action and cannot be authorized under the guise of transposition.
- Warning vs. Blocking:
  - `BLOCKING`: Range overflows and physical impossibility trigger `VALIDATION_FAILED` via `Workspace._validator`.
  - `WARNING`: Tessitura edge notes and large melodic leaps (>12 semitones) are logged in `RulesReport` for human consideration without obstructing deliberate artistic choices.
- Zero-Core-Mutation Integration: Uses the native `Workspace._validator` callback hook (`check_candidate(candidate) -> bool`), keeping the core kernel untouched.
- Verification: 5 conformance tests in `tests/test_rules.py` and live demonstration in `reference/demo_rules.py`. Full test suite passes (77/77 tests).

## 2026-09-18 21:45:00 — Scoped Multi-Role Collaboration and Delegation Protocol

Decision: Implement the Scoped Multi-Role Collaboration Silo (`reference/collaboration/COLLABORATION_CONTRACT.md`, `reference/collaboration/manager.py`).
- Constitutional Invariant: Multi-artist collaboration must never blur who authorized what. Every published revision immutably records the actor, operation, scope, and reason.
- Ownership & Delegation: Every musical scope has a registered primary owner. Primary owners can issue revocable `DelegationGrant`s for specific operations (`confirm`, `correct`, `restore`). Non-owners attempting unauthorized mutations are blocked by policy with `MUSICMCP-CORE-POLICY_BLOCKED`.
- Zero-Core-Mutation Architecture: Uses the native `Workspace._policy` callback hook (`check_policy(candidate) -> bool`), keeping the core authority kernel untouched while enforcing role boundaries.
- Verification: 5 conformance tests in `tests/test_collaboration.py` and live demonstration in `reference/demo_collaboration.py`. Full test suite passes (72/72 tests).

## 2026-09-18 21:40:00 — Host-Held Interactive Review Shell & Authority CLI Implementation

Decision: Implement the Host-Held Interactive Review Shell and Command-Line Interface (`reference/cli.py`) adhering to pure Python 3.11+ standard library (`argparse`, `sys`, `pathlib`).
- Constitutional Boundary: As specified in Founding Directive §1 and §4, the human musician holds ultimate artistic authority. Machine models propose; the human governs. The CLI provides a direct interface on the host where human authority sessions are held and exercised, completely isolated from external model transport or remote access.
- Comprehensive Workflow:
  - Project lifecycle: `init`, `info`, `history`, `restore`.
  - Acoustic inspection: `inspect-audio` surfaces 10-band spectrum energy and anomaly flags (`MAINS_HUM`, `CLIPPING`, `DC_OFFSET`, `RUMBLE`, `LEAK`).
  - Evidence ingestion: `propose-audio` records evidence, observation, and pitch proposal with qualitative uncertainty.
  - Authority review: `review` provides human decision point: `confirm` accepts proposal into revision, `correct` records human-authored pitch corrections with `origin="human"`.
  - External exchange: `export` and `import` connect MusicXML and MIDI formats with mandatory SPECIFICATION REP-1 loss disclosure reports.
- Verification: Conformance tests in `tests/test_cli.py` and live demonstration in `reference/demo_cli.py`. Full test suite passes (67/67 tests).

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


## 2026-09-19 00:05:00 — Systemic Headless Verification Gap Eradication & Interactive Deck Proof

- **What:** Completed physical end-to-end sensory verification of Music MCP. Added HTML5 Canvas 2D musical staff engraving, Web Audio API acoustic synthesis, drag-and-drop WAV audio upload (`/api/upload`), host CLI `musicmcp serve`, and automatic SQLite disk persistence (`PreviewServer.persist()`). Proved operation through physical browser automation, WebP video recording, screenshots, and export validation of MusicXML and MIDI files on disk.
- **Why:** The project had fallen into the trap of "headless verification complacency" — running unit tests against synthetic sine waves without ever rendering music onto a visual staff, auditioning audible sound, or verifying physical software interfaces in a browser. Furthermore, an audit revealed that actions taken in the web UI were not auto-persisted back to the SQLite container file on disk.
- **How:**
  1. Built standard 5-line musical staff engraving engine (`drawStaff`) in pure HTML5 Canvas 2D rendering treble clefs, ledger lines for high/low pitches, duration stems/flags, accidentals, and rests.
  2. Implemented Web Audio API acoustic synthesis (`playPhraseAudio`) modeling fundamental frequencies and natural harmonic overtones with smooth envelopes.
  3. Added drag-and-drop WAV upload with base64 decoding and automated pitch tracking / spectrum watching.
  4. Implemented `PreviewServer.persist()` to automatically commit all state changes (`confirm`, `correct`, `restore`, `upload`, `propose_alternative`) to SQLite on disk.
  5. Tested end-to-end with real acoustic audio file `audio/acoustic_melody.wav` (158KB).
  6. Captured physical proof: browser video recording (`review_deck_proof_1789790264268.webp`), screenshots, validated SQLite Revision 1 state, and exported/validated `audio/melody.xml` and `audio/melody.mid`.
- **Invariants Preserved:** Pure Python 3.11+ standard library only (zero external libraries). Strict localhost loopback security boundary. Immutable provenance and human authority sovereignty. "Ai" capitalization standard strictly maintained.


## 2026-09-19 16:13:00 — Resolution of 9 Code Review Findings (Security, Storage Concurrency, Provider Authenticity, State Consistency)

- **What:** Resolved all nine actionable defects identified during code review across security boundaries, SQLite persistence concurrency, external evaluation authenticity, preview server state synchrony, CLI project initialization, and review deck DOM safety:
  1. [P1] Untrusted HTML injection in `reference/preview/static/index.html`: Implemented `escapeHtml` utility and sanitized all model-controlled and attributable fields (scope, mode, uncertainty, origin, reason, actor, pitch, duration, anomalies, resonances).
  2. [P1] Foreign origin / CSRF acceptance in `reference/preview/server.py`: Strengthened `_check_security()` with Host header validation (strictly localhost/127.0.0.1/::1), Origin header checks (rejecting foreign origins), `Sec-Fetch-Site` validation (rejecting cross-site), and mandatory `Content-Type: application/json` on mutating POST requests.
  3. [P1] Stale saves overwriting revision history in `reference/storage/sqlite_store.py`: Introduced `state_token` tracking in `schema_meta` and stored revision conflict validation in `save_workspace`, rejecting concurrent modifications and divergent revisions with `StorageError`.
  4. [P1] Fabricated provider results in `reference/evaluation/evaluators.py`: Removed synthetic mock fallback from live branch; live adapter now performs real HTTP request via standard library `urllib.request` and returns `EvaluationStatus.ERROR` or `CAPABILITY_UNAVAILABLE` on failures with uncalibrated probabilities and secret redaction.
  5. [P1] Failed saves leaving memory ahead of disk in `reference/preview/server.py`: Implemented `_execute_mutation()` transactional wrapper across all mutating endpoints (`/api/confirm`, `/api/correct`, `/api/restore`, `/api/propose_alternative`, `/api/upload`); on persistence failure, in-memory state is automatically rolled back to match disk state and HTTP 500 is returned.
  6. [P2] Polling erases correction drafts in `reference/preview/static/index.html`: Preserved selected proposal ID across polls (`currentSelectedProposalId`) and added draft dirty tracking (`isDraftDirty` / active input focus), preventing 5-second polling cycles from wiping user edits.
  7. [P2] `init --force` retaining previous project content in `reference/cli.py` & `reference/storage/sqlite_store.py`: Passed `force=args.force` to `save_workspace`, wiping all prior table rows (evidence, observations, proposals, revisions, grants, constraints) when reinitializing.
  8. [P2] Loading bypassing schema and parent validation in `reference/storage/sqlite_store.py`: Added explicit `schema_version` validation against `SCHEMA_VERSION` (rejecting 9.9.9) and parent chain continuity check (`parent == expected_next - 1`, rejecting broken parent chains like 999).
  9. [P2] Multiple grants for one actor failing on UNIQUE constraint in `reference/storage/sqlite_store.py`: Changed `grants` table primary key to an auto-incrementing integer `id`, allowing multiple independent scoped grants per actor without permission broadening or integrity errors.
- **Why:** Adhere strictly to the Cardinal Rule and Operating Rules for E:\AI_Hub: no unverified fixes, no headless complacency, no security shortcuts, and complete state consistency between database, memory, and UI.
- **Verification:** All 117 tests passing in 53s across 12 test modules (`tests/test_storage.py`, `tests/test_preview.py`, `tests/test_evaluation.py`, `tests/test_spectrum.py`, `tests/test_cli.py`, `tests/test_mcp.py`, `tests/test_adapters.py`, `tests/test_alternatives.py`, `tests/test_analyzer.py`, `tests/test_collaboration.py`, `tests/test_core.py`, `tests/test_rules.py`).
## 2026-09-23 11:48:24 - Keep brief extreme pitch proposals, lower unsupported confidence

The authorized local `audio/acoustic_melody.wav` produced seven proposed notes, including one-hop C#8 and C3 events between other pitches, while the analyzer labeled the whole proposal `HIGH`. Without musician-approved intended notes, that is evidence of a confidence decision problem, not proof of transcription error. The uncertainty branch only checked correlation, cents spread, and spectrum anomalies. A focused proposal-path test first reproduced `HIGH` from a controlled voiced stream with two brief octave-sized excursions. The decision now marks such proposals `AMBIGUOUS` and adds an observation explanation, while preserving every note for human correction and leaving the authoritative revision at zero. The test passed after the change; the local fixture still yielded seven notes and now reports `AMBIGUOUS`.

Chose a narrow, conservative review flag over deleting the short notes or silently smoothing them, because a quick wide leap may be musically intended. The rule applies only when a voiced segment lasts at most two 20ms hops and differs by at least 12 semitones from both voiced neighbors. Sibling scan found one uncertainty decision in `reference/analyzer.py`; CLI, MCP, and proposal helper consume its result without their own analyzer confidence logic. The analyzer contract now states the actual window/hop and confidence rule. Reconsider thresholds only with labeled recordings and musician review. The owner then assigned further regression testing to Antigravity. Antigravity executed the full test suite (`python -B -m unittest discover -s tests -v`), passing all 143 tests in 56.382s on Windows with Python 3.11.15 and Node 24.19.0 (0 failures, 0 errors, 0 skips). In addition, `python -B -m reference.demo` and all 8 silo demo scripts passed. A read-only acoustic check on `audio/acoustic_melody.wav` confirmed 7 events extracted, flagged `uncertainty: AMBIGUOUS` with explanation "Brief large pitch excursion requires human review", while preserving all proposed notes and leaving authoritative state at revision 0. Implementation/schema stays v0.1.01, Unreleased. Existing owner scope-correction docs remain pending; original user audio and `live_proof.musicmcp` were not modified.
