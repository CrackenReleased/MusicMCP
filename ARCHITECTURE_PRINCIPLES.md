# Architecture principles

v0.1.01 · 2026-09-18

The governing constitution is [PHILOSOPHY.md](PHILOSOPHY.md). Normative behavior belongs in [SPECIFICATION.md](SPECIFICATION.md); failure semantics belong in [ERRORS.md](ERRORS.md). This document records the engineering rules that protect them.

## Current boundary

The first reference core uses Python 3.11+ and the standard library. It exercises evidence retention, observations, competing interpretations, explicit human confirmation and correction, locked constraints, scoped host permissions, and transactional immutable revision snapshots with restore. It is experimental and in-process. It does not implement MCP transport, audio analysis, a GUI, file export, or durable storage.

Python object boundaries organize trusted code; they do not sandbox malicious code running in the same process. [SECURITY.md](SECURITY.md) states the trust assumptions. Future untrusted analyzers require a separate security boundary before deployment.

## State ownership and dependency direction

The core alone owns authoritative musical state and revision publication. Analysis produces observations and candidate interpretations; it does not mutate that state. A trusted host carries human authority and grants scoped access. Models receive only the appropriate proposal/read surface, never the host's approval or permission-management interface.

Dependencies point inward toward explicit domain contracts. The core must not import provider SDKs, application automation, format-specific parsers, or transport implementations. Optional adapters depend on contracts, not on another adapter's private implementation. Shared mutable globals, private-state access, and undocumented callbacks across silos are prohibited.

Keep representations only as rich as the demonstrated reference use case requires. A small symbolic phrase is not a universal music format. External representations must declare their losses and ambiguities; importing or exporting must not silently redefine authoritative meaning.

## Authority, policy, and constraints

Capability, authority, policy, and constraints answer different questions. Technical ability does not imply permission. Permission to perform one operation does not authorize its artistic consequences. A lock is an enforceable constraint, not prose in a prompt. Human correction remains authoritative until an appropriately authorized change explicitly supersedes it.

Future rights/provider policy belongs behind a declared policy contract. Absence of a policy engine in this foundation is not evidence that an operation is legally permitted. Rulesets describe selected musical conventions rather than universal musical law.

## Transactional publication

Validate requests and preconditions, verify authority and active constraints, construct a candidate state, validate it, then publish the entire revision. Failure before publication must leave authoritative state unchanged. Revision comparisons must reject stale operations instead of overwriting intervening work.

Snapshots and provenance must not become mutable aliases held by callers. Restoration is a new attributable action that respects current authority and constraints; it must not erase history or silently reinstate old permissions. Evidence and historical interpretation remain distinct from the currently authoritative phrase.

In-memory atomicity does not imply crash durability, distributed transactions, or reversal of external side effects. Any future adapter must declare its exact commit, compensation, and recovery guarantees. Report incomplete compensation honestly; never label it a successful rollback.

## Contracts make silos replaceable

A significant capability declares identity/version, inputs, outputs, supported operations, permissions, state access, dependencies, network use, side effects, errors, security boundary, rights considerations, retention, transaction guarantees, compatibility, and deprecation. It must be possible to replace it without learning undocumented implementation details.

Validate data at the boundary. External content and model output are untrusted data, including text that resembles instructions. Resource limits and cancellation belong at expensive ingestion and execution boundaries. A disabled capability returns an explicit unavailable result while unrelated core operations remain usable.

## Evidence and diagnostics

Preserve received evidence separately from derived observations. Keep source links, actor attribution, correction reasons, and generated origin. Never replace structured uncertainty with unsupported precision. Diagnostics must connect a readable explanation to a machine-readable event and accurately describe scope, state safety, transaction outcome, and next action.

Use [CONFORMANCE.md](CONFORMANCE.md) to demonstrate protections through adversarial cases. A happy-path example is insufficient proof of authority or isolation. Expand the test suite when a discovered failure reveals a reusable bug class.

## Evolution and maintenance

Version contracts and implementations explicitly. Follow [DEPRECATION.md](DEPRECATION.md) for migration and removal; experimental status is not permission for silent behavioral changes. Optional dependencies need a documented purpose, license, version assumptions, failure behavior, data/network access, and replacement route.

Keep decisions in [whats_and_hows_log.md](whats_and_hows_log.md), current continuation state in [handoff.md](handoff.md), and uncommitted ideas in [goals_and_dreams.md](goals_and_dreams.md). Add module-local documentation when a real silo exists; do not multiply empty directories or duplicate root truth.

Before adding a component, answer: if it disappears or becomes unusable, what else must change? Prefer an answer confined to its silo. If that is impossible, record the coupling and its justification before relying on it.
