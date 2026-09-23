# Conformance — experimental profile 0.1.01

Run from the repository root with Python 3.11+: `python -B -m unittest discover -s tests -v`. No dependencies, recordings, secrets, network access, or application installations are required. The synthetic demo is also independently runnable with `python -B -m reference.demo`.

The suite exercises the in-memory phrase profile and separate reference modules for audio analysis, evaluation, stdio transport, format adapters, SQLite storage, CLI, and local preview. The complete suite executed by Antigravity on Windows (Python 3.11.15, Node 24.19.0) passed all 143 tests in 56.382s with zero failures, errors, or skips (`python -B -m unittest discover -s tests -v`), confirming the 2026-09-23 analyzer uncertainty change alongside all existing reference silos. The earlier suite establishes the tested reference behaviors, including local storage reopen and process interruption; it does not establish independent MCP-client compatibility, production security, hardware power-loss durability, transcription quality, independent format interoperability, live provider compatibility, or a third-party conformance standard.

## Source release gate

The repository is source-run (`pyproject.toml` status `experimental-source-only`); no wheel, package-index upload, or release tag is part of this gate. From a clean checkout, run the synthetic demo and complete suite using the commands above. `.github/workflows/conformance.yml` repeats those commands on GitHub-hosted Windows and Ubuntu with Python 3.11 and Node 22 for pull requests and pushes to `main`. Node is needed for the shipped JavaScript preview harness; a test skip is not evidence that its behavior passed. Check both jobs for the exact revision before claiming cross-platform verification. Locally, Windows with Python 3.11.15 and Node 24.19.0 passed all 142 tests after the preview fix; `python -B -m reference.demo` also passed.

[Source conformance run 35815806392](https://github.com/CrackenReleased/MusicMCP/actions/runs/35815806392) passed at commit `c4a184a` on 2026-09-22/23: Windows and Ubuntu each ran the demo and all 142 tests under Python 3.11 and Node 22, with no reported skips. Windows took 54.058s for the suite; Ubuntu took 79.698s. This verifies those two clean-checkout environments only. Other Python versions, package installation, hardware power-loss durability, and musical accuracy remain unverified.

Release review must also complete the [local recording checklist](#local-recording-review-checklist-added-2026-09-21-192935) with rights-cleared source provenance and musician-approved intended notes. The earlier mechanical walkthrough does not satisfy that musical gate. Review pending work by ownership and coherent change before any commit; no automatic version bump, publication, or deployment follows from a green workflow.

| Requirement | Executable coverage |
| --- | --- |
| AUTH-1 scoped authority | `test_scope_and_operation_authority_do_not_expand` |
| EVID-1 evidence vs competing interpretations | `test_evidence_and_competing_interpretations_never_establish_authority` |
| INTENT-1 correction survives reanalysis | `test_confirm_correct_and_restore_preserve_lineage`; synthetic story test |
| PROV-1 attributable revisions/generated origin | lineage test; `test_generated_acceptance_does_not_become_human_authorship` |
| TX-1 atomicity and revision conflict | failed-policy/post-validation, concurrent-confirmation, stale-revision, reentrancy tests |
| Constraint enforcement | `test_lock_rejects_confirm_and_correct` |
| Immutable public values | `test_mutable_inputs_and_return_values_cannot_mutate_state` |
| Runtime input/reference validation | `test_unknown_and_malformed_input_fail_closed` |
| ERR-1 accurate attempted operation/scope | rejected-write, history-capacity and read/proposal diagnostic context tests |
| Restore isolation and current policy | `test_restore_checks_current_policy_and_preserves_unrelated_scope` |
| Retention without silent eviction | history-capacity and evidence-capacity tests |
| ISO-1 inward dependency direction | `test_core_imports_only_standard_library` |
| Honest capabilities | `test_capabilities_do_not_claim_transcription_or_mcp` |
| Maintainable contracts | document-link and version-metadata checks |

The shared rejection helper asserts snapshot equality, safe unchanged authoritative state, no rollback claim, trace ID, and recovery guidance after each tested failure. Tests were written before the kernel and initially failed because `reference.core` did not exist. This is a new-feature red baseline, not a claim to have reproduced a preexisting product bug.

## Provenance and approval refinement

`tests/test_provenance.py` adds six cases: missing producer rejection; separate observer/interpreter lineage across confirmation/correction/restore; malformed producer rejection at both boundaries; immutable constraint origin/reason retained through revisions; invalid/duplicate constraint rejection; and all six uncertainty labels remaining provisional until human action. The original v0.1.0 accepted an unattributed observation, so that regression failed before the fix. The other initial failures were missing new record types, not historical runtime defects. At that refinement the suite had 27 passing tests; the latest complete run has 142.

Host consent presentation is a normative integration obligation. The separate preview supplies a local review UI, but neither it nor this suite establishes human identity, independently proves what a person saw, or certifies that consent was obtained. Tests check core grants, revision preconditions, publication boundaries, and scoped preview behavior; any production host must add its own authenticated consent and stale-retry evidence before claiming that conformance.

## Active conformance limits and deferred work

Audio analysis has synthetic fixtures and a mechanical local recording walkthrough, but still needs provenance-cleared recordings with intended-note ground truth covering vibrato, pitch drift, deliberately inaccurate singing, literal transcription, rubato, breath, ornaments, ambiguous rhythm, enharmonics, pickups, and model disagreement. Current tests do not establish detection accuracy for those phenomena.

Adapters retain internal loss/round-trip tests. Independent consumer checks are deferred by the owner, outside current acceptance/release gates; unsupported-conversion coverage may still be improved within the local implementation. SQLite storage has conflict, corruption, rollback, and process-interruption tests, but no hardware power-loss certification or comprehensive backup/restore validation. Transposition still needs range-consequence tests without unauthorized revoicing. Independent MCP-client interoperability testing is also deferred, not a current requirement. Any future remote transport would need separately scoped authentication, privilege separation, invalid wire data, approval binding, and replay tests. Each implementation must name the exact contract/profile/version it passes; unimplemented tests cannot be silently counted as passing.


## Local recording review checklist (added 2026-09-21 19:29:35)

Run on a fresh disposable project under the repository, never on a user's original project. Record source permission/provenance, WAV format, hash and tempo assumption. Reuse the existing CLI commands (`python -B -m reference.cli --help`) and PreviewServer.

1. Hash the recording and protected existing project/exports. Initialize a separate project with a clearly labeled QA actor; propose the selected WAV into melody. Record all notes and uncertainty before edits.
2. Serve only that project on an unused loopback port. Inspect the actual proposal staff, text, spectrum and uncertainty; record rendering/console problems. Do not infer musical intent from a generated proposal.
3. For workflow testing, use explicit QA-only reasons when confirming/correcting. Verify draft survives Refresh, revision increments once per action, and AMS/history distinguish the correction from the original proposal. A test correction is not a musician-approved transcription.
4. Stop the server and reopen storage in a fresh process. Assert exact corrected notes/durations, both history entries, unchanged evidence bytes and storage integrity.
5. Export MusicXML/MIDI and compare internal import results with confirmed QA notes. Record representation loss. External consumer checks are outside this checklist and the active roadmap; internal round trips do not establish external interoperability.
6. Verify original hashes unchanged. Stop only the server started for this check, close QA tabs, remove only owned disposable outputs, and record observed results in whats_and_hows_log.md. No whole-suite rerun is required for a read-only walkthrough unless a code fix follows.

Latest checklist execution: 2026-09-21 19:29:35, selected acoustic_melody.wav, mechanical flow passed through revision 2 and both internal export round trips. Real-performance provenance, intended transcription, and audible assessment remain open. Independent consumer comparison is deferred by the owner. See the matching why-log entry and error_history_log.md for the observed UI issues.

## Brief pitch excursion review regression (2026-09-23)

`tests.test_analyzer.MonophonicAnalyzerConformance.test_brief_large_pitch_excursions_require_review_without_losing_notes` feeds a deterministic voiced signal through the proposal path while isolating the mapped pitch sequence. It checks that two one-hop, octave-sized excursions produce an `AMBIGUOUS` proposal, remain in its notes, appear in the observation explanation, and leave the authoritative revision unchanged. The focused test failed on the old decision (`HIGH`) and passed after the change. The local acoustic fixture likewise retained its seven proposed notes while changing its label from `HIGH` to `AMBIGUOUS`; no intended-note ground truth is available, so this is a confidence review finding, not an accuracy result. The owner assigned further regression execution to Antigravity. Antigravity ran the complete regression suite on Windows: all 143 tests passed in 56.382s, with zero failures, errors, or skips. The synthetic core demo and all 8 silo demos also passed without error.


## Correction editor regression

Run `python -B -m unittest tests.test_preview.TestCorrectionEditor` with Node.js on PATH. The test executes the actual inline review script: save E4 2 over original C4 1; verify confirmed notes/source after refresh and reselection; preserve a new G4 3 draft; reload clean selection from confirmed state; switch to a different proposal without substituting another proposal's confirmed notes. This test failed before the fix with C4 1 instead of E4 2. An explicit skip means Node was unavailable, not that the behavior passed.

Manual browser check: on a disposable project, submit E4 2, verify both AMS and editor, type G4 3 without submitting, Refresh and click the same proposal, then reload the page. Expect the unsaved draft to survive Refresh/reselection and the saved E4 2 to load after page reload. The source label must remain readable. Original proposal remains C4 1. Inspect console and rendered editor; do not claim a full responsive-layout pass from this scoped check.

## Extreme staff pitch rendering

Run `python -B -m unittest tests.test_preview` with Node.js available. Its shipped-JavaScript harness renders C#8 and C3 and checks the recorded drawing coordinates stay within the pitch-sized backing canvas; a Node skip does not verify this behavior. For a visual spot check, use a disposable local PreviewServer workspace with C#8, C3, and an ordinary note, then inspect the rendered staff and labels in a browser and check the console. Verify the extreme noteheads, ledger lines, stems and labels are visible. Close the browser and stop only the QA server started for this check. This does not verify horizontal overflow or general responsive layout.

Latest execution: 2026-09-22, `python -B -m unittest tests.test_preview` passed 24 tests; browser rendering of C#8, C3 and E4 showed all staff elements inside the canvas with no console warnings/errors. The disposable server/tab were stopped/closed; no project assets were retained.

## Preview page width regression

Run the local PreviewServer with a disposable in-memory workspace containing a confirmed phrase and its retained proposal, so both the 640px and 600px staff canvases render. One PowerShell command, from the project root, starts that existing server without writing a project file (choose another unused loopback port if 8881 is occupied):

```powershell
python -u -B -c 'from fractions import Fraction; from reference.core import Grant,Note,Producer,create_workspace; from reference.preview.server import PreviewServer; from tests.test_preview import make_clean_sine_wav; ws,(s,)=create_workspace([Grant("layout-qa",{"melody"},{"confirm"})]); producer=Producer("layout-qa","0.1.01"); e=ws.add_evidence(make_clean_sine_wav(),"audio/wav"); o=ws.observe(e.id,"Disposable layout check",producer=producer); p=ws.propose(o.id,scope="melody",notes=(Note("E4",Fraction(1)),),mode="intended",uncertainty="LOW",origin="interpreted",producer=producer); s.confirm(p.id,0,"Disposable layout check"); PreviewServer(ws,s,port=8881).start(background=False)'
```

Open `http://127.0.0.1:8881/`. At browser widths 1250px, 768px, and 375px, compare `document.documentElement.scrollWidth` with `window.innerWidth`; the document must not be wider than the viewport. The staff canvas wrappers may scroll horizontally inside their cards, and the page header, upload controls, note chips, review card, and mutation buttons must remain readable and reachable. Check browser console errors. Close the QA tab and stop its server afterward. This is a repeatable browser layout regression check, not a claim about every device size.

Red baseline observed before the layout fix on 2026-09-22: with both staff canvases present, 1250px viewport -> 1489px document; 375px viewport -> 741px document. At 768px the document fit (753px), but the 375px header controls also extended beyond their available width.

Green check after the fix: settled document widths were 1235px at 1250px, 753px at 768px, and 360px at 375px. The two staff wrappers scroll internally where their canvases exceed card width. At 375px, the proposal card's 254px client and scroll widths matched, its badges wrapped, and mutation controls remained visible. The active PreviewServer page produced no console warnings or errors. `python -B -m unittest tests.test_preview` passed 24 tests. Browser check used an in-memory QA workspace; it does not assert independent engraving quality or every responsive width.

## Stored causal-chain regression

Run `python -B -m unittest tests.test_storage.TestStorageSafety.test_corrupt_record_relationships_fail_audit_and_load tests.test_storage.TestSqliteStorage.test_corrupt_project_file_rejects_dangling_observation`. The first test tampers an in-memory SQLite project with missing or mismatched evidence, observation, proposal, revision, scope, origin, notes, constraints, and restore references. For each corruption, `verify_integrity` must report an invalid file and `load_workspace` must reject it with a storage integrity diagnostic; restoring the original rows must permit a clean reopen. The second test applies a dangling observation to a disposable on-disk `.musicmcp` fixture and verifies the same failure across a new connection. The in-memory regression failed all 11 initial relationship cases before the fix; three later cases for boolean duration and unexpected note/constraint fields also failed before strict decoding. They pass now. These tests do not simulate hardware power loss or prove producer identity.

Run `python -B -m unittest tests.test_storage.TestSqliteStorage.test_terminated_writer_preserves_last_committed_revision` for process interruption. It starts a separate writer process against a disposable file, waits until the storage engine reaches commit, terminates the writer, and reopens the file. The prior revision, evidence count, and state token must remain intact and the integrity report valid. Existing `TestConcurrentStorage` and `TestStorageSafety` cover competing writers, failed forced replacement, and rejected legacy-grant migration. These tests do not simulate hardware power loss.

## Preview ingestion failure regression

Run `python -B -m unittest tests.test_preview.TestPreviewServer.test_failed_upload_does_not_retain_partial_evidence tests.test_preview.TestPreviewServer.test_failed_alternative_save_does_not_retain_partial_observation`. Invalid uploaded WAV data must not leave an evidence record, and a failed generated-alternative save must not leave its observation. Both HTTP tests failed on the old preview code with one extra partial record and pass after moving complete record creation inside the mutation boundary. The full suite passed 142 tests after the fix.
