# Error history

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
