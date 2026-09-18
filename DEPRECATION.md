# Compatibility and deprecation

Policy revision 2 · foundation v0.1.01 · 2026-09-18

This policy covers public operations, contracts, schemas, error codes, modules, tools, adapters, and capability identifiers. It protects users from silent changes while allowing unsafe or inadequate components to be replaced.

## Current status

v0.1.01 is experimental. No stable interoperability or wire-format contract is claimed. Future 0.x versions may change contracts, but changes still require an explicit version, migration explanation, tests, and changelog entry. Do not reinterpret an old field or error identifier silently.

Use semantic versions for published implementations and explicitly identify their supported contract versions. Once a contract is declared stable, compatible additions belong in a minor release, compatible fixes in a patch release, and incompatible changes require a major contract version. Capability support must be declared rather than inferred from an implementation's version alone.

## Source migration: 0.1.0 to 0.1.01

This is an explicit breaking change to the experimental source API, not a migration of an already published stable API. The 0.1.0 source remains in Git history. There is no durable workspace format or automatic state migration; preserve any live workspace and its originals rather than discarding them to upgrade.

- Import and construct `Producer(identity, version)` with known nonempty identity/version strings, each at most 128 characters. Pass it by keyword to every `observe(..., producer=...)` and `propose(..., producer=...)` call. Missing or invalid values now fail with `VALIDATION_FAILED`. Use distinct producer records when the observer and interpreter differ. Do not invent historical attribution to satisfy the new API.
- Replace `create_workspace(..., locked_scopes=...)` with `create_workspace(..., constraints=...)`, supplying `LockConstraint(scope, origin, reason)` records. Scope/origin are nonempty strings up to 128 characters; reason is nonempty text up to 4096 characters. Resolve duplicate scopes deliberately; they are rejected rather than silently deduplicated.
- Update consumers of `Candidate.constraints` and `Revision.constraints`: each entry is now a complete immutable constraint record, not a scope string. Preserve its origin and reason in displays and diagnostics. Constraints remain fixed for the workspace lifetime.
- Interpret uncertainty according to [SPECIFICATION.md](SPECIFICATION.md); HIGH/MEDIUM/LOW are producer assessments, not probabilities or authorization. Keep explicit human confirmation for every label.
- Review host approval integration against [SECURITY.md](SECURITY.md). Present the exact operation and resulting material at the reviewed workspace revision, collect explicit human action, and reject silent stale-revision retries. Session possession does not constitute that action.

No analyzer, provider connection, persistence, transport, UI, or approval-token mechanism is introduced by this migration. Existing authority, evidence-retention, and transaction invariants still apply.

## Deprecate deliberately

Before normal retirement, document:

- The affected identifier and versions, reason, owner, and replacement if one exists.
- Consumers affected and the earliest removal version or condition.
- How a caller detects deprecation and migrates.
- Effects on musical meaning, retained evidence, provenance, revision history, and permissions.
- Compatibility tests and the test that demonstrates removal or rejection behavior.

Publish the decision in [CHANGELOG.md](CHANGELOG.md), update the governing contract, and preserve the rationale in [whats_and_hows_log.md](whats_and_hows_log.md). For stable contracts, provide at least one published release carrying a deprecation notice before normal removal. Do not promise a calendar support period that maintainers have not established.

Keep deprecated identifiers reserved with their original meaning. A successor error code or schema must not rewrite the meaning of historical records. Do not reuse a retired capability name for incompatible behavior.

## Migration and state safety

Migrations must be explicit, inspectable, and tested. They must preserve source evidence and provenance or refuse the conversion with an accurate loss report. Backups or immutable source revisions must exist before destructive durable migrations; this requirement does not imply that the current in-memory reference has durable storage.

Recheck permissions under the current authority model. Never silently widen grants, bypass locked constraints, or erase human correction during an upgrade. A compatibility adapter must declare unsupported and lossy cases rather than pretending the old contract is fulfilled.

Disabled or removed capabilities return an explicit unavailable/unsupported result using the current [ERRORS.md](ERRORS.md) contract. Unrelated capabilities should continue operating. Remove unused dependencies and documentation routes as part of retirement, while retaining historical decision and migration records.

## Emergency security or policy withdrawal

A vulnerability or binding policy restriction may require immediate disabling or removal without the normal notice release. Record the reason, affected versions, state/data consequences, mitigation, replacement options, and restoration conditions. Do not execute a known-unsafe operation merely to preserve compatibility. Keep unrelated capabilities available when their safety can be established.

Use [SECURITY.md](SECURITY.md) for coordinated reporting and [CONFORMANCE.md](CONFORMANCE.md) to verify the revised claims. Any compatibility claim must identify the contract version and capability scope actually tested.
