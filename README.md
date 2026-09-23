# Music MCP

**The musician stays the artist. The machine does the notation, calculation, and clerical work.**

Open musical intelligence infrastructure connecting human intention, evidence, responsible machine assistance, and existing musical tools. Models propose; explicit human authority governs changes. MusicXML, MIDI, notation applications, and MCP transports will connect through replaceable boundaries.

## Current status: experimental source build v0.1.01

The **in-process authority kernel** preserves supplied evidence and competing interpretations, supports human confirmation/correction, rejects unauthorized and stale changes, retains provenance, and restores historical phrase content through new revisions. The kernel itself is neither an MCP server nor an audio analyzer. Separate experimental reference modules now implement a stdio model-facing gateway, monophonic WAV analysis and spectrum inspection, SQLite project storage, MusicXML/MIDI adapters, a host CLI, a loopback review preview, evaluation, collaboration, rules, and alternatives. These modules do not establish production readiness or full format/protocol interoperability. See [conformance and limits](CONFORMANCE.md) and each module's contract.

Observations and proposals require their own producer identity/version. Locks retain who supplied them and why; revisions preserve those records. Qualitative uncertainty describes a producer's assessment and never grants authority. See [source migration](DEPRECATION.md) for the 0.1.0 → 0.1.01 API changes and [host approval obligations](SECURITY.md) before integrating the core.

The source build uses Python 3.11+ and no third-party runtime dependencies. It includes local SQLite `.musicmcp` persistence, bounded monophonic PCM WAV analysis, spectral inspection, MusicXML/MIDI adapters with loss reporting, CLI commands, and a browser review preview with staff drawing and Web Audio playback. The real-recording walkthrough verified a mechanical review/reopen/export path; source provenance, intended notes, musical accuracy, independent consumer interoperability, hardware power-loss durability, and live provider compatibility remain unverified.

## Run it

From this repository using Python 3.11 or later, with no installation or external dependencies:

```sh
python -B -m reference.demo
python -B -m unittest discover -s tests -v
```

For a clean source checkout:

```sh
git clone https://github.com/CrackenReleased/MusicMCP.git
cd MusicMCP
python -B -m reference.demo
python -B -m unittest discover -s tests -v
```

This is a source-run project; `pyproject.toml` does not declare a published distribution or install command. The [source conformance workflow](.github/workflows/conformance.yml) runs the same demo and tests on GitHub-hosted Windows and Ubuntu with Python 3.11 and Node 22. Check the actual workflow result for the revision being reviewed. The [recording review checklist](CONFORMANCE.md#local-recording-review-checklist-added-2026-09-21-192935) is a separate human/musical gate.

### Interactive Host CLI

Execute the host-held review shell and authority interface:

```sh
# Start interactive visualizer review deck in browser
python -m reference.cli serve my_project.musicmcp --open

# Ingest acoustic audio evidence and propose notes
python -m reference.cli propose-audio my_project.musicmcp acoustic.wav --scope melody

# Review and confirm proposals with composer authority
python -m reference.cli review my_project.musicmcp --action confirm --reason "Composer confirmation"

# Export authoritative state to standard notation and performance formats
python -m reference.cli export my_project.musicmcp --scope melody --format musicxml --out score.xml
python -m reference.cli export my_project.musicmcp --scope melody --format midi --out score.mid
```

### Provider-Neutral Evaluation Silo & Jev Adapter

Execute the provider-neutral evaluation contract and TypeSafe Jev adapter demonstrator:

```sh
python -m reference.demo_evaluation
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

Model-facing code must never receive the privileged authority session. The host handles human identity and approvals. Python object boundaries are not a sandbox against malicious code in the same process. A core-only workspace is volatile; hosts using the separate SQLite storage silo can persist and reopen a `.musicmcp` project. Neither path authenticates a human or proves that the musician approved a transcription.

## Read the repository

| Document | Purpose |
| --- | --- |
| [PHILOSOPHY.md](PHILOSOPHY.md) | Founding constitution |
| [SPECIFICATION.md](SPECIFICATION.md) | Normative requirements and implemented profile |
| [ARCHITECTURE_PRINCIPLES.md](ARCHITECTURE_PRINCIPLES.md) | Ownership, dependencies, isolation and evolution |
| [reference/CONTRACT.md](reference/CONTRACT.md) | Concrete API, authority boundary and resource limits |
| [reference/evaluation/EVALUATION_CONTRACT.md](reference/evaluation/EVALUATION_CONTRACT.md) | Provider-neutral evaluation and Jev adapter contract |
| [ERRORS.md](ERRORS.md) | State-aware diagnostic contract |
| [CONFORMANCE.md](CONFORMANCE.md) | Executable coverage and honest limitations |
| [SECURITY.md](SECURITY.md) | Trust boundaries and reporting |
| [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) | Safe human and agent contribution |
| [whats_and_hows_log.md](whats_and_hows_log.md) | Assessment and decision rationale |
| [handoff.md](handoff.md) | Current work and exact continuation |
| [goals_and_dreams.md](goals_and_dreams.md) | Future ideas, not commitments |
| [CHANGELOG.md](CHANGELOG.md), [error_history_log.md](error_history_log.md), [DEPRECATION.md](DEPRECATION.md) | Changes, failures and migration rules |

The [founding directive](01_MusicMCP_Codex_Founding_Build_Directive.md) is preserved as supplied. The canonical repository is [CrackenReleased/MusicMCP](https://github.com/CrackenReleased/MusicMCP). See [LICENSE](LICENSE) for Apache-2.0 terms. Historical version labels in older entries describe the work recorded then; the current declared package and storage schema version is v0.1.01, with newer work Unreleased.
