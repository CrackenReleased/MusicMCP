# Conformance — experimental profile 0.1.01

Run from the repository root with Python 3.11+: `python -B -m unittest discover -s tests -v`. No dependencies, recordings, secrets, network access, or application installations are required. The synthetic demo is also independently runnable with `python -B -m reference.demo`.

Passing these tests establishes only the implemented in-memory phrase profile. It does not establish MCP protocol compatibility, production security, durable recovery, transcription quality, format interoperability, or a complete third-party conformance standard.

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

`tests/test_provenance.py` adds six cases: missing producer rejection; separate observer/interpreter lineage across confirmation/correction/restore; malformed producer rejection at both boundaries; immutable constraint origin/reason retained through revisions; invalid/duplicate constraint rejection; and all six uncertainty labels remaining provisional until human action. The original v0.1.0 accepted an unattributed observation, so that regression failed before the fix. The other initial failures were missing new record types, not historical runtime defects. The full suite now contains 27 passing tests.

Host consent presentation is a normative integration obligation, not an implemented UI or authentication system. This suite checks the kernel's grants, revision preconditions and publication boundaries; it cannot certify that a host actually displayed the reviewed values or obtained consent. A future host implementation must provide its own consent and stale-retry tests before claiming that conformance.

## Future profiles

Audio analysis must add rights-cleared fixtures covering vibrato, pitch drift, deliberately inaccurate singing, literal transcription, rubato, breath, ornaments, ambiguous rhythm, enharmonics, pickups, and model disagreement. The current tests exercise correction and disagreement semantics, not detection accuracy for those musical phenomena.

Adapters must test declared losses and refusal of unsupported conversion. Durable stores must test crash points, rollback failure, recovery and truthful unknown/unsafe state. Transposition must test range consequences without unauthorized revoicing. Transports must test authentication, privilege separation, invalid wire data, approval binding and replay. Each implementation must name the exact contract/profile/version it passes; unimplemented tests cannot be silently counted as passing.
