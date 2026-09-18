# Compatibility and deprecation

Policy revision 1 · foundation v0.1.0 · 2026-09-18

This policy covers public operations, contracts, schemas, error codes, modules, tools, adapters, and capability identifiers. It protects users from silent changes while allowing unsafe or inadequate components to be replaced.

## Current status

v0.1.0 is experimental. No stable interoperability or wire-format contract is claimed. Future 0.x versions may change contracts, but changes still require an explicit version, migration explanation, tests, and changelog entry. Do not reinterpret an old field or error identifier silently.

Use semantic versions for published implementations and explicitly identify their supported contract versions. Once a contract is declared stable, compatible additions belong in a minor release, compatible fixes in a patch release, and incompatible changes require a major contract version. Capability support must be declared rather than inferred from an implementation's version alone.

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
