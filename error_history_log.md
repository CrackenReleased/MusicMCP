## 2026-09-22 23:44:13 - Preview retained partial records after failed ingestion/save

Cause: `/api/upload` added evidence and analyzed it before `_execute_mutation` captured its rollback snapshot; `/api/propose_alternative` likewise added an observation first. Invalid audio left orphaned evidence; a failed alternative save left an orphaned observation in memory. Two HTTP regressions in `tests/test_preview.py` failed on the old code with evidence/observation counts increased by one. Moving the complete record creation into the existing mutation closure makes both pass while retaining the old revision and records on failure. Same-class scan found no other preview workspace write outside the mutation boundary. Implementation v0.1.01 Unreleased; no schema change.

## 2026-09-22 22:50:47 — Stored provenance links accepted without audit

Cause: load reconstructed dataclass records directly and integrity reporting checked hashes/parents but did not join observations, proposals, revisions, and restore sources. A damaged project could reopen with dangling or contradictory provenance. A shared record audit now rejects inconsistent lineage, publication origin, restoration semantics, and malformed note/constraint JSON. `TestStorageSafety.test_corrupt_record_relationships_fail_audit_and_load` failed 11 initial cases on the old code; three strict-decoding cases also failed before decoder hardening. A disposable on-disk project test and a separate writer-termination test pass. Full suite: 140 passed. No historical file was silently repaired; format remains v0.1.01.

A test-fixture cleanup error occurred when the first on-disk corruption test used SQLite's context manager without closing its connection. The test now closes explicitly and subsequent runs clean up. Its one earlier temp database remains at `C:/Users/CRACKE~1/AppData/Local/Temp/tmp2nmtxt5h/project.musicmcp` (57,344 bytes). Automatic approval review rejected exact and narrower cleanup commands as 'blocked by policy'; no user project data was involved.

## 2026-09-22 22:28:31 — Review deck page overflow resolved

Populated 640px/600px notation canvases made the desktop grid's `1fr` center track expand to intrinsic canvas width; the document measured 1489px at a 1250px viewport. The single-column track similarly made a 375px viewport's document 741px wide. Header and proposal badges were also forced onto one line. The layout decision now allows grid/card shrinkage and wraps controls while preserving internal staff scrolling. `CONFORMANCE.md` records the red baseline and repeatable browser check. Green document widths: 1235/1250px, 753/768px, 360/375px; proposal card content fits at 375px. Preview suite 24 passed; active QA page console had no warnings/errors. No musical state or authority impact observed.

Version v0.1.01 Unreleased. No commit/push, no retained QA artifact. Continue with storage relationship validation as the next bounded maturation milestone; fixture provenance and intended music remain unverified.

## 2026-09-22 21:45:00 — Antigravity resume here: vertical staff clipping fixed

The fixed 120px staff canvas clipped C#8 above and C3 below the staff. `drawStaff()` now sizes canvas backing and CSS height to the displayed pitch range, with a minimum height; note pitches are unchanged. A regression in `tests/test_preview.py::TestCorrectionEditor.test_editor_uses_confirmed_notes_and_preserves_new_drafts` recorded the shipped renderer's coordinates and failed on old bounds. Scoped preview suite: 24 passed. Browser displayed C#8, C3, E4 and associated staff elements inside the canvas; zero console warnings/errors. Disposable tab/server stopped; no assets retained.

Next exact task: horizontal page overflow is still present. Reproduce and fix that separate layout issue with scoped regression and browser verification. Do not widen scope to full responsive redesign. Preserve pending Antigravity/Codex work, `audio/`, and `live_proof.musicmcp`. Implementation/schema v0.1.01, Unreleased; no commit/push. Latest full-project test remains 137 passed from the prior task; this task ran only all 24 preview tests. Last known sync main/origin/main was 41c27416be17da6bc405def77ca5dcbb682f27a2 at 0 ahead/behind; refresh before publication. No new files, datasets, or dependencies.

## 2026-09-22 19:52:23 — Misleading PENDING labels resolved

Cause: total stored proposal count was labeled Pending even after confirmation/correction. Fix: derive Reviewed from revision-history proposal IDs, show pending/reviewed counts and retain original cards. Existing JS regression extended and observed red/green; final preview suite 24 passed and browser confirm/reload verified. Earlier test-fixture duplication corrected; one HTTP test error did not recur on suite rerun. High-note clipping and horizontal overflow remain unfixed.

## 2026-09-22 00:46:48 — Correction editor reset resolved

Earlier walkthrough issue (editor resets to original notes after successful correction) fixed at source selection. TestCorrectionEditor observed failure on old behavior and passes now; browser save/refresh/reselection/reload verified. Confirmed phrase and proposal scope/ID must match; dirty drafts remain protected. Full suite 137 passed. Remaining unfixed walkthrough issues: PENDING labeling, high-note clipping; additionally observed horizontal page overflow in wide layout. See latest why-log and PREVIEW_CONTRACT.md for limits. No unrelated UI fixes claimed.

## 2026-09-21 19:29:35 — Local walkthrough findings (unfixed)

Preview static/index.html, reproduced with acoustic_melody.wav on disposable project: after confirm/correct, proposal count still says PENDING; after successful correction, editor repopulates original proposal rather than current corrected notes (AMS/history are correct); C#8 proposal glyphs clip at top of staff canvas while textual chips remain visible. Repro: follow CONFORMANCE.md local recording checklist using original seven-note proposal, confirm, edit to C4 1/E4 1/G4 1/C5 1, refresh, submit correction. Screenshots/AX observations verified in session. No code change or regression fix claimed. Prioritize the correction-editor ambiguity before broad UI polish. Analyzer transition notes are suspicious, not proven incorrect without labeled musical evidence.

## 2026-09-21 19:24:38 — Evaluation evidence/result validation

Cause: missing context defaulted into successful comparisons and untyped provider responses were accepted; mock probabilities asserted calibration automatically. Fixed required-field/result decision boundaries and shared mock/HTTP normalization. TestEvaluationValidation covers each missing field, malformed evidence, absent candidate events, bad response types/scores/keys/labels/calibration, valid negatives and zero, and invalid request envelopes; confirmed-state test covers all result statuses. Seven new methods observed failing/erroring before fix; eight new methods now pass. Full suite: 136 passed. Existing probability tolerance tightened and recorded in EVALUATION_CONTRACT.md. No release/schema migration. See latest why-log for limits.

## 2026-09-21 19:11:57 — Evaluation execution and unsupported success

Missing json import prevented the HTTP request from being constructed; the old network-failure test passed for this unrelated internal exception. Deterministic default returned first candidate or False as SUCCESS without a supporting rule. Fixed at import/fallback decision points. Two new tests in tests/test_evaluation.py observed failing before fix and passing after; transport-error and confirmed-state assertions strengthened. Full suite 128 passed. Implementation v0.1.01 unchanged, Unreleased. See current why-log for limits and sibling findings.

## 2026-09-21 19:07:40 — Persistence transaction and recovery defects (implementation v0.1.01)

Cause: schema setup/force clearing committed before the write; token checks occurred before reserving the writer; recovery omitted host callbacks/grants and swallowed reload failures. Impact: lost saved data, competing-writer overwrite, changed permissions, and false safety claims. Corrected at transaction/recovery decision points. Regressions: TestStorageSafety failed-force/legacy-grant/schema tests; TestConcurrentStorage competing save; TestPreviewRecovery callback retention, unknown recovery, partial ingestion, grant subset and serialization. Full suite: 126 passed. Six new tests observed red then green. See the same-timestamp whats_and_hows_log.md decision for limits and version rationale.

# Error history

## 2026-09-19 16:13:00 — Nine Code Review Findings Resolved & Regression Coverage Established

- **Affected modules:** `reference.preview`, `reference.storage`, `reference.evaluation`, `reference.cli`
- **Findings Addressed:**
  1. P1 HTML Injection: `index.html` interpolated untrusted proposal scopes directly into `innerHTML`. Fixed with `escapeHtml` sanitization. Verified with `test_preview_html_escapes_model_controlled_proposal_fields`.
  2. P1 Foreign Origin Acceptance: `server.py` checked only client IP. Fixed with Host/Origin/Sec-Fetch-Site and Content-Type validation. Verified with `test_security_boundary_rejects_foreign_origin`, `test_security_boundary_rejects_foreign_host`, and `test_security_boundary_rejects_untyped_or_text_plain_post`.
  3. P1 Stale Save Overwrites: `sqlite_store.py` lacked concurrency checks. Fixed with `state_token` and stored revision conflict detection. Verified with `test_stale_authoritative_save_preserves_first_writer` and `test_stale_nonrevision_save_is_rejected`.
  4. P1 Fabricated Provider Output: `evaluators.py` fabricated successful results without calling providers. Fixed with live HTTP dispatch and error reporting. Verified with `test_typesafe_jev_adapter_live_invalid_key_does_not_fabricate_success`.
  5. P1 Memory Ahead of Disk: `server.py` committed memory before persistence. Fixed with transactional memory rollback on persist failures. Verified with `test_persistence_failure_rolls_back_memory_to_preserve_disk_consistency`.
  6. P2 Polling Erasing Drafts: `index.html` 5s poll reset selection and draft inputs. Fixed by retaining selection and dirty tracking. Verified with `test_preview_html_preserves_correction_drafts_across_polling`.
  7. P2 `init --force` Stale Retention: `cli.py` saved new workspace over old rows without clearing tables. Fixed by clearing all tables on `force=True`. Verified with `test_force_init_replaces_all_content`.
  8. P2 Bypassed Schema/Parent Checks: `sqlite_store.py` loaded unsupported schema and broken revision chains. Fixed by validating schema version and parent continuity. Verified with `test_load_rejects_unsupported_schema` and `test_load_rejects_invalid_parent`.
  9. P2 Actor UNIQUE Constraint: `sqlite_store.py` prevented multiple grants per actor. Fixed with auto-incrementing `id` primary key. Verified with `test_separate_grants_same_actor_round_trip_without_broadening`.
- **Suite Result:** 117 tests passing in 53s.

## 2026-09-18 23:55:00 — Systemic Headless Verification Illusion and Missing Interactive Surfaces

Identifier: HEADLESS_VERIFICATION_ILLUSION, INTERFACE_GAPS. Module: preview, cli, visualizer, audio ingestion.
Symptom: The agent declared capabilities "verified" based purely on automated headless unit test scripts passing in background processes (102 green tests), but had never once launched a browser, rendered the interface for a human, engraved a musical staff, or played an audible note.

Root Cause: The agent fell into the path of least resistance—treating programmatic HTTP assertions (`urllib.request.urlopen`) as equivalent to human visual and auditory experience. It never launched a browser or tested real acoustic performance.

Gaps Identified:
1. Missing CLI Serve Command: `reference/cli.py` lacked a `serve` subcommand, preventing musicians from launching the review deck from the terminal.
2. Missing Preview Server Entrypoint: `reference/preview/server.py` had no `if __name__ == '__main__':` entrypoint to run standalone.
3. Missing Audio Upload Endpoint: `PreviewServer` lacked an `/api/upload` endpoint to ingest real audio files from the browser.
4. Missing Visual Musical Staff Engraving: The visualizer rendered notes only as text pills (`C4 1`), with zero standard notation (no 5-line staff, clefs, note heads, or stems).
5. Missing Audible Playback: The review deck had no audio playback mechanism; musicians could not hear what the engine captured.
6. Zero Visual/Browser Verification: The UI had never been rendered, screenshotted, or verified in an actual browser engine.
7. Synthetic-Only Audio Testing: Pitch and spectrum tests relied entirely on idealized mathematical sine waves (`math.sin`) rather than real acoustic performances with harmonic overtones, vibrato, and room resonance.

Correction & Proof Plan:
1. Implement `cmd_serve` in `reference/cli.py` and standalone main in `reference/preview/server.py`.
2. Implement `/api/upload` in `PreviewServer` to accept WAV files, run spectrum analysis, and generate proposals.
3. Build dynamic HTML5 Canvas musical staff engraving in `index.html` rendering standard 5-line notation with treble clef and duration-proportional notes.
4. Implement Web Audio API synthesis in `index.html` allowing immediate audible playback of phrases and proposals.
5. Ingest and test a real acoustic instrument recording through the pipeline.
6. Use `browser_subagent` to physically launch Chromium, load `http://127.0.0.1:8765`, inspect the DOM, trigger upload, verify staff rendering, verify playback controls, and capture visual video and screenshot evidence.

## 2026-09-18 19:54:52 — v0.1.0 provenance omissions corrected in v0.1.01

Identifier: VALIDATION_FAILED. Module: reference core. The approved assessment found that observations/proposals omitted producer identity/version and lock constraints retained only scope names. State safety guards still functioned, but users could not reconstruct which producer supplied a reading or why a lock existed from retained records.

Decision points: observe/propose ingestion now requires a validated Producer; workspace construction now requires attributed LockConstraint records. Candidate/Revision storage preserves complete constraint records, and immutable proposal/observation links preserve distinct producers through correction and restore. No default provenance is fabricated.

Regression evidence: `test_missing_producer_is_rejected_instead_of_retaining_unattributed_analysis` in tests/test_provenance.py failed on v0.1.0 because no MusicError was raised; it passes with v0.1.01. Five additional cases initially errored because the new record types did not exist and now pass. Full suite: 27 passing. Sibling scan covered both analysis ingestion boundaries, Candidate/Revision constraint retention, all three mutation operations, and demo/test callers. Uncertainty and host consent gaps were resolved in contracts; host UI/authentication behavior remains outside this kernel and unclaimed.

Lesson: retaining an immutable content object is insufficient provenance unless producer and governing constraint attribution are captured at entry. No broader architecture or philosophical change was necessary; the existing PROV-1 requirement and reference contract now specify those fields.

## 2026-09-18 — v0.1.0 pre-release — diagnostic context lost

Identifiers: VALIDATION_FAILED, NOT_FOUND, CAPACITY_EXCEEDED. Module: reference core. An independent bounded review found that shared validation helpers reported `validate/workspace` even when a correction or restore and its phrase scope were known. Music remained unchanged, but a user/developer could not reliably identify the attempted action from its diagnostic.

Root cause: contextual attribution lived at individual failure sites rather than at the public operation boundary. Added one write-boundary contextualizer preserving the existing code/message/trace/safety fields and seven read/proposal wrappers. Checked all three authoritative operations and seven read/proposal entry points for this same class.

Regression evidence: `test_rejected_writes_report_attempted_operation_and_known_scope` and `test_capacity_failure_preserves_history_and_diagnostic_context` failed before the fix (four assertions: correct, confirm, missing confirm and capacity restore). Added parameterized read/proposal attribution coverage as well. All pass after the fix. No architectural/security boundary change; ERR-1 is now enforced at the operation boundary.

## 2026-09-18 — v0.1.0 founding baseline

There was no prior application implementation to repair. The first conformance run failed with `ModuleNotFoundError: reference.core` before implementation, as expected. After implementation the initial 12 behavioral cases passed. This records the new-feature baseline honestly; it is not a historical product defect or a claim of audio-analysis correctness.

For future significant failures record: timestamp, error identifier, affected version/module, symptom, root cause, user and state impact, decision point fixed, regression test (including observed red/green evidence), sibling scan, lesson, and resulting contract/architecture changes. Never include private recordings or credentials in this log.


## 2026-09-18 23:55:00 — Systemic Headless Verification Gap (Missing Interactive & Sensory Surfaces)

- **Affected version / module:** v0.1.02 / `reference.preview`, `reference.cli`, `reference.analyzer`
- **Symptom:** Tests passed against synthetic sine wave numbers while the system had never "heard" real acoustic music, never engraved notes on a standard musical staff, had no audible playback in the UI, and lacked a CLI command or direct file upload for the interactive preview deck.
- **Root Cause:** Headless verification complacency — relying exclusively on unit test assertions without building or validating sensory/interactive user interfaces in physical browser environments.
- **Decision Point Fixed:**
  1. Built HTML5 Canvas 2D musical staff notation engine (`drawStaff`) with clef, pitch mapping, ledger lines, accidentals, duration flags, and rests.
  2. Built Web Audio API synthesizer (`playPhraseAudio`) with fundamental frequency, harmonic overtones, and attack/decay envelopes.
  3. Added `/api/upload` endpoint and UI drag-and-drop zone for 16-bit PCM mono WAV audio.
  4. Added `musicmcp serve` CLI subcommand to launch the preview deck.
- **Physical Proof:** Created real acoustic test fixture `audio/acoustic_melody.wav` (158KB). Executed browser subagent session (`review_deck_proof_1789790264268.webp`), captured screenshots (`initial_page_load_1789790352457.png`, `ams_revision_1_published_1789790456306.png`, `final_verification_state_1789790558204.png`), verified Web Audio synthesis, and confirmed proposal into AMS Revision 1.
- **Regression Test:** `test_api_upload_endpoint_ingests_and_analyzes_audio` in `tests/test_preview.py`.

## 2026-09-19 00:04:00 — Ephemeral PreviewServer State Gap (Missing SQLite Project Auto-Persistence)

- **Affected version / module:** v0.1.02 / `reference.preview.server`, `reference.cli`
- **Symptom:** Actions performed in the visualizer review deck (`/api/confirm`, `/api/correct`, `/api/restore`, `/api/upload`, `/api/propose_alternative`) successfully mutated the in-memory `Workspace` object, but were never persisted back to the `.musicmcp` SQLite container file on disk. A subsequent CLI `export` or server restart saw revision 0 and zero active phrases.
- **Root Cause:** `PreviewServer` lacked a binding to the project's file path on disk and did not trigger `SqliteStorageEngine.save_workspace` upon state mutations.
- **Decision Point Fixed:** Added `project_path` parameter to `PreviewServer.__init__` and implemented `PreviewServer.persist()`. Wired `self.preview.persist()` immediately after successful executions of `/api/confirm`, `/api/correct`, `/api/restore`, `/api/propose_alternative`, and `/api/upload`. Updated `cmd_serve` in `reference.cli` to pass `project_path`.
- **Physical Proof:** Ran live server persistence test (`test_live_server_persistence.py`), executed HTTP POST to `/api/confirm`, stopped server, and reloaded `live_proof.musicmcp` fresh from SQLite to confirm Revision 1 and 1 active phrase on disk. Subsequently exported and verified `audio/melody.xml` (MusicXML) and `audio/melody.mid` (MIDI).
- **Regression Test:** `test_preview_server_auto_persists_to_sqlite_project_on_disk` in `tests/test_preview.py`.
- **Sibling Scan:** Audited all endpoints in `reference.preview.server`. Confirmed every mutating endpoint calls `self.preview.persist()`.
## 2026-09-23 11:48:24 - Brief extreme pitch segments received HIGH support

Cause: the analyzer's final uncertainty decision considered mean frame correlation, cents spread, and spectrum anomalies but ignored the sequence of mapped pitches. A local acoustic proposal contained one-hop C#8 and C3 segments between nearby notes and was labeled `HIGH`. The intended notes are unknown, so the defect is overconfident labeling, not a proven wrong transcription. The decision now marks a voiced segment of at most two hops `AMBIGUOUS` when it jumps at least an octave from both voiced neighbors; the notes remain in the proposal and the observation explains the flag. `test_brief_large_pitch_excursions_require_review_without_losing_notes` failed on old code (`HIGH`) and passed after the fix. No authoritative workspace state is changed by analysis. The owner moved further regression testing to Antigravity before a complete-suite outcome was observed. Implementation v0.1.01 remains Unreleased.
