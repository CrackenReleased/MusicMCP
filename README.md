# Music MCP

**The musician stays the artist. The machine does the notation, calculation, and clerical work.**

Open musical intelligence infrastructure connecting human intention, evidence, responsible machine assistance, and existing musical tools. Models propose; explicit human authority governs changes. MusicXML, MIDI, notation applications, and MCP transports will connect through replaceable boundaries.

## Current status: v0.1.01 foundation, analyzer, spectrum watcher, MCP transport, adapters, storage, host CLI, collaboration, rules & alternatives

The first build provides a documented, executable **in-process authority kernel**, not a transcription product or MCP server. It preserves supplied evidence and competing interpretations, supports human confirmation/correction, rejects unauthorized and stale changes, retains provenance, and restores historical phrase content through new revisions.

Observations and proposals require their own producer identity/version. Locks retain who supplied them and why; revisions preserve those records. Qualitative uncertainty describes a producer's assessment and never grants authority. See [source migration](DEPRECATION.md) for the 0.1.0 → 0.1.01 API changes and [host approval obligations](SECURITY.md) before integrating the core.

No audio analysis, model integration, MCP transport, GUI, notation rendering, file export, or durable storage is implemented. Nothing here changes CrackenReleased.com or other projects. Original Apache-2.0 licensing is preserved.

## Run it

From this repository using Python 3.11 or later, with no installation or external dependencies:

```sh
python -B -m reference.demo
python -B -m unittest discover -s tests -v
```

### Interactive Host CLI

Execute the host-held review shell and authority interface:

```sh
python -m reference.cli --help
python -m reference.demo_cli
```


The demo generates a short synthetic tone in memory, supplies two illustrative rhythmic interpretations, then records a human correction to a straight eighth note. Subsequent analysis leaves that correction intact, and a stale write is rejected. The demo does **not** infer notes from audio. Its host approval calls are scripted examples, not an interactive consent system.

## How the boundary works

```text
Evidence → observation → competing interpretation / suggestion
                                      ↓
                          trusted human confirmation
                                      ↓
           scope + revision + policy + constraint checks
                                      ↓
                  complete candidate validation
                                      ↓
             atomic authoritative revision publication
```

Model-facing code must never receive the privileged authority session. The host handles human identity and approvals. Python object boundaries are not a sandbox against malicious code in the same process. All retained music disappears when this in-memory workspace is discarded; this is not a durable music project store.

## Read the repository

| Document | Purpose |
| --- | --- |
| [PHILOSOPHY.md](PHILOSOPHY.md) | Founding constitution |
| [SPECIFICATION.md](SPECIFICATION.md) | Normative requirements and implemented profile |
| [ARCHITECTURE_PRINCIPLES.md](ARCHITECTURE_PRINCIPLES.md) | Ownership, dependencies, isolation and evolution |
| [reference/CONTRACT.md](reference/CONTRACT.md) | Concrete API, authority boundary and resource limits |
| [ERRORS.md](ERRORS.md) | State-aware diagnostic contract |
| [CONFORMANCE.md](CONFORMANCE.md) | Executable coverage and honest limitations |
| [SECURITY.md](SECURITY.md) | Trust boundaries and reporting |
| [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) | Safe human and agent contribution |
| [whats_and_hows_log.md](whats_and_hows_log.md) | Assessment and decision rationale |
| [handoff.md](handoff.md) | Current work and exact continuation |
| [goals_and_dreams.md](goals_and_dreams.md) | Future ideas, not commitments |
| [CHANGELOG.md](CHANGELOG.md), [error_history_log.md](error_history_log.md), [DEPRECATION.md](DEPRECATION.md) | Changes, failures and migration rules |

The [founding directive](01_MusicMCP_Codex_Founding_Build_Directive.md) is preserved as supplied. The canonical repository is [CrackenReleased/MusicMCP](https://github.com/CrackenReleased/MusicMCP). See [LICENSE](LICENSE) for Apache-2.0 terms. This README was expanded in the v0.1.0 founding build.
