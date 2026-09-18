# Error history

## 2026-09-18 — v0.1.0 pre-release — diagnostic context lost

Identifiers: VALIDATION_FAILED, NOT_FOUND, CAPACITY_EXCEEDED. Module: reference core. An independent bounded review found that shared validation helpers reported `validate/workspace` even when a correction or restore and its phrase scope were known. Music remained unchanged, but a user/developer could not reliably identify the attempted action from its diagnostic.

Root cause: contextual attribution lived at individual failure sites rather than at the public operation boundary. Added one write-boundary contextualizer preserving the existing code/message/trace/safety fields and seven read/proposal wrappers. Checked all three authoritative operations and seven read/proposal entry points for this same class.

Regression evidence: `test_rejected_writes_report_attempted_operation_and_known_scope` and `test_capacity_failure_preserves_history_and_diagnostic_context` failed before the fix (four assertions: correct, confirm, missing confirm and capacity restore). Added parameterized read/proposal attribution coverage as well. All pass after the fix. No architectural/security boundary change; ERR-1 is now enforced at the operation boundary.

## 2026-09-18 — v0.1.0 founding baseline

There was no prior application implementation to repair. The first conformance run failed with `ModuleNotFoundError: reference.core` before implementation, as expected. After implementation the initial 12 behavioral cases passed. This records the new-feature baseline honestly; it is not a historical product defect or a claim of audio-analysis correctness.

For future significant failures record: timestamp, error identifier, affected version/module, symptom, root cause, user and state impact, decision point fixed, regression test (including observed red/green evidence), sibling scan, lesson, and resulting contract/architecture changes. Never include private recordings or credentials in this log.
