# Error contract — 0.1.01

`MusicError.diagnostic` describes one rejected operation. Its human `message` explains the failure; `next_action` supplies recovery without requiring implementation knowledge. Fields: `code`, `severity`, `module`, `operation`, `scope`, `trace_id`, `message`, `next_action`, `authoritative_state_modified`, `state_safe`, `transaction`, `rollback`. Trace IDs connect host diagnostics without embedding raw performance data or exception text.

The reference kernel uses `MUSICMCP-CORE-<CATEGORY>` stable identifiers, severity ERROR, module `core`, unique UUID traces, unchanged authoritative state, `state_safe=True`, transaction `not_committed`, and rollback `not_required`. Errors do not imply that a previously successful operation was reversed. Read/proposal failures have no authoritative effect either.

| Category | Meaning | Recovery |
| --- | --- | --- |
| VALIDATION_FAILED | Malformed or unsupported input/candidate | Correct the input using the contract |
| NOT_FOUND | Referenced evidence/observation/proposal/revision absent | Read existing IDs and retry |
| UNAUTHORIZED | No session grant for exact scope and operation | Ask the trusted host for appropriate human authorization |
| REVISION_CONFLICT | Expected workspace revision is stale | Read current state, review differences, then authorize again |
| CONSTRAINT_CONFLICT | Scope is locked | Leave it unchanged; request a deliberate host-level constraint decision |
| POLICY_BLOCKED | Configured policy denies change | Review the configured policy |
| POLICY_UNAVAILABLE | Policy throws or returns an invalid decision | Repair policy integration; retry only after review |
| TRANSACTION_FAILED | Post-validator fails or a callback attempts reentrant mutation | Repair integration and retry from current state |
| CAPACITY_EXCEEDED | In-memory reference limit reached | Export through a future explicit persistence implementation or start a separate workspace; do not drop history |

Example: `REVISION_CONFLICT`: “The workspace changed after this operation was prepared.” Nothing was changed by this attempt; read the latest snapshot and review before retrying.

Reserved future categories, **not implemented outcomes**: REVIEW_REQUIRED, AMBIGUOUS, INSUFFICIENT_EVIDENCE, AUTHORITY_CONFLICT, UNSUPPORTED, CAPABILITY_UNAVAILABLE, DEPENDENCY_UNAVAILABLE, LOSSY_OPERATION, LOSSY_EXPORT, ROLLBACK_FAILED, SECURITY_BLOCKED, RIGHTS_RESTRICTED, INTERNAL_FAILURE. Uncertainty currently belongs to proposals, not mutation failures. Success returns a Revision; partial success is unsupported.

New error categories require a documented cause, human action, state/transaction/rollback consequences and tests. An adapter that cannot establish safety MUST report unknown or unsafe; it MUST NOT reuse this in-memory profile's safe=True assertion. Rollback failure must report the actual affected scope and freeze further writes pending reconciliation; never report successful rollback without evidence.

In 0.1.01, absent or malformed Producer records, malformed LockConstraint records, and duplicate lock scopes use VALIDATION_FAILED. There is no fabricated default attribution or silent constraint deduplication. Model-reported names do not establish authenticated provenance.
