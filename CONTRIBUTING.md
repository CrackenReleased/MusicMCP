# Contributing

Music MCP welcomes contributions that preserve human musical authority and make the project understandable to the next maintainer. The foundation is experimental v0.1.0; it is not yet a production server or transcription system.

## Start here

Read [PHILOSOPHY.md](PHILOSOPHY.md), [AGENTS.md](AGENTS.md), [ARCHITECTURE_PRINCIPLES.md](ARCHITECTURE_PRINCIPLES.md), and the relevant [SPECIFICATION.md](SPECIFICATION.md) requirements. Inspect [handoff.md](handoff.md) and [whats_and_hows_log.md](whats_and_hows_log.md) before reopening an architectural choice.

Verify the canonical repository is `https://github.com/CrackenReleased/MusicMCP.git`, fetch its current state, and preserve existing local changes. Use a focused branch and a reviewable contribution. The existing Apache-2.0 [LICENSE](LICENSE) remains unchanged; provide only code and fixtures you have permission to contribute.

## A focused change

1. Identify the observable behavior, affected contract, and authority/state consequences.
2. For a reproducible bug, add a test that fails before the fix. For new behavior, add adversarial coverage of the relevant invariants.
3. Make the smallest coherent change at the decision point. Inspect siblings of the same failure pattern without expanding into unrelated repairs.
4. Run the applicable checks documented in [CONFORMANCE.md](CONFORMANCE.md) and the repository's current setup instructions. Report failures and untested boundaries honestly.
5. Update changed contracts, errors, security assumptions, and [CHANGELOG.md](CHANGELOG.md). Record consequential reasoning in the decision log and significant failure history in [error_history_log.md](error_history_log.md).

The reference core targets Python 3.11+ with no external runtime dependencies. Follow existing test and packaging conventions. Before adding a dependency, establish why the standard library or existing code cannot reasonably serve the need, then document its licensing, network/data access, failure behavior, and replacement route.

## Review expectations

A contribution should explain the problem, resulting behavior, validation command/results, and limitations. For security-sensitive changes, identify the actual trust boundary and attack being prevented. A frozen object is not proof of malicious-code isolation. A successful demo is not proof of transaction safety.

Tests should protect behavior rather than copy implementation details. Include denial paths, locked constraints, human-correction precedence, provenance retention, and unchanged state after failure when those properties are affected. Document any conversion loss; do not silently normalize away the musician's intent.

Keep provider and adapter dependencies outside the core. Significant modules need an explicit contract including permissions, state access, failure and recovery guarantees, compatibility, and retention. Do not add unused abstraction layers or empty directory trees.

Changes to philosophy, authority, security boundaries, licensing, public compatibility, irreversible structure, or major scope require the project owner's explicit decision. Preserve alternatives and consequences in the decision log. Interesting work outside the current milestone belongs in [goals_and_dreams.md](goals_and_dreams.md), where it remains an idea rather than a commitment.

Before stopping, update the handoff with exact continuation instructions and local/remote sync state. Follow [DEPRECATION.md](DEPRECATION.md) for breaking changes and [SECURITY.md](SECURITY.md) for vulnerability reports.
