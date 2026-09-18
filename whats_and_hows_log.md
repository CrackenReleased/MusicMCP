# Decisions and architectural assessment

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
