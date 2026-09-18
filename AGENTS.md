# Music MCP agent instructions

Policy revision 1 · 2026-09-18 · foundation v0.1.0

For work on the founding Windows workspace, read `E:\AI_Hub\AGENTS.md` end to end before code work, particularly §20, then this file. That local workspace guidance applies there; contributors elsewhere need no access to that drive. Project behavior is governed by the documents below.

## Begin with known state

The canonical repository is `https://github.com/CrackenReleased/MusicMCP.git`, currently using `main` as the default branch. Verify `origin`, fetch current refs, inspect the branch, local HEAD, corresponding remote HEAD, ahead/behind counts, dirty files, untracked files, and unpushed commits before significant work. A transport-equivalent authenticated SSH URL is acceptable when its repository identity is verified. A failed fetch means remote freshness is unknown; disclose that limitation.

Do not reset, clean, force-push, or discard either side of a divergence to make the checkout appear synchronized. Preserve existing work. In coordinated work, the lead agent owns shared Git operations and logs; bounded agents report their changes to the lead rather than racing on those files.

Read in order:

1. This file and [PHILOSOPHY.md](PHILOSOPHY.md).
2. Relevant [SPECIFICATION.md](SPECIFICATION.md) requirements and [ARCHITECTURE_PRINCIPLES.md](ARCHITECTURE_PRINCIPLES.md).
3. Root [handoff.md](handoff.md), then applicable module instructions and handoff if present.
4. Relevant [whats_and_hows_log.md](whats_and_hows_log.md) decisions, contracts, tests, [ERRORS.md](ERRORS.md), and [SECURITY.md](SECURITY.md).

Read the founding directive for unresolved foundational questions. Inspect existing implementations before introducing replacements. Do not create upfront planning artifacts unless requested; record substantial architectural reasoning in the existing decision log.

## Bound the work

v0.1.0 is an experimental dependency-free Python 3.11+ in-process reference core. Do not describe it as an MCP server, audio analyzer, notation application, or export pipeline. Add those capabilities only through a separately scoped contract and milestone.

Never expose host approval, grants, or authoritative mutation control to models. Do not collapse evidence, observation, interpretation, suggestion, confirmation, and change. Do not silently broaden authorization, override human correction, mutate locked content, discard provenance, or disguise generated material as original human material.

No private cross-silo access, provider imports in core, silent lossy conversions, invented security guarantees, or undocumented shortcuts. In-process isolation is not a malicious-code sandbox. Keep changes directly within the requested scope; preserve interesting unrelated work in [goals_and_dreams.md](goals_and_dreams.md).

Use existing tools before adding dependencies or scripts. Every persistent artifact needs an owner, consumer, canonical location, and lifecycle. Create directories when meaningful content exists.

## Verify and document

Inspect the relevant contract and write a failing regression test before a reproducible non-trivial fix. Cover its failure class and inspect sibling call sites within the affected scope. Run the targeted test and appropriate conformance checks; report exact commands and outcomes. Do not claim a test failed on old code unless that was observed. Prose-only changes need diff and reference review, not application tests or version churn.

Tests must attack unauthorized mutation, lost provenance, ignored human correction, constraint bypass, partial publication, stale operations, and false rollback claims where relevant. Follow [CONFORMANCE.md](CONFORMANCE.md); do not mistake test coverage of the reference slice for full ecosystem compatibility.

Update contracts and [CHANGELOG.md](CHANGELOG.md) when behavior changes. Record meaningful decisions with context, alternatives, reasons, consequences, and reconsideration triggers in [whats_and_hows_log.md](whats_and_hows_log.md). Record significant bugs, causes, state impact, regression tests, and architectural lessons in [error_history_log.md](error_history_log.md). Update module-local documents where they own the detail; link upward instead of copying root text.

Ask the project owner before materially changing philosophy, authority, security boundaries, licensing, public compatibility, irreversible structure, or major scope. Make safely reversible implementation decisions within the approved architecture and record why. If a requirement is unsound, document the requirement, problem, evidence, alternative, tradeoffs, and migration consequences; do not silently replace it.

## Leave a usable handoff

Before stopping, put the repository in the safest practical state and update [handoff.md](handoff.md). Include timestamp, agent/session, milestone, objective, completed and incomplete work, changed files, test commands/results, known problems, decisions, last known good state, do-not-repeat guidance, and reason for stopping. Whenever work remains, give an exact next action with a file, test, or inspectable condition.

Record local branch/HEAD, tracking branch, last observed remote HEAD and observation time, ahead/behind/diverged state, uncommitted and untracked work, and whether unpushed commits remain. Distinguish a local commit from a successful push. State the implementation version in completion reports without inventing a release.

On the founding workspace, complete its required Hub handoff, intent-miner, and project-log synchronization through the lead agent. Keep project reasoning canonical here. Do not leave essential continuation information only in chat.
