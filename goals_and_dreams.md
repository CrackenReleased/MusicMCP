# Goals and dreams

Idea vault · 2026-09-18

> Nothing in this file is a commitment. Nothing valuable gets forgotten.

Owner scope correction (2026-09-23): Independent MCP-client testing and external MIDI/MusicXML interoperability testing are outside the active roadmap and all current acceptance/release gates. The owner may revisit them in roughly 2-3 years; that is a possibility, not a schedule or commitment. Do not research, implement, test, or propose this work as a next step unless the owner explicitly reopens it.

These ideas originate in the founding directive. The declared package/schema version remains experimental v0.1.01. Several ideas below now have bounded reference implementations and contracts (monophonic analysis, stdio gateway, format adapters, local storage, collaboration, rules, alternatives, and evaluation). Their broader product aims and evidence gates remain open; a listing here does not authorize scope expansion. See [current status](README.md) and [conformance limits](CONFORMANCE.md).

| Idea | Why it matters | Evidence needed before promotion |
| --- | --- | --- |
| Monophonic performance to intended notation | Helps a musician express a phrase without repeated manual transcription. | A replaceable analyzer contract, rights-cleared evaluation recordings, resource bounds, and preserved evidence through human review. |
| Musical ambiguity review | Lets a person compare straight/triplet rhythm, grace notes, pitch drift, vibrato, rubato, breaths, pickups, and enharmonic readings. | Concrete examples distinguishing measured performance from intention; accessible review that preserves alternatives and human correction. |
| Read/proposal MCP transport | Makes the same musical contracts usable by different models. | An authenticated host boundary, model-visible capability inventory, approval separation, and transport-level adversarial tests. |
| MusicXML and MIDI adapters | Connects the work to existing musical tools. | Declared versions, loss/ambiguity reports, round-trip fixtures, and a clear boundary between representations and authoritative state. |
| Durable evidence and revision store | Allows sessions to survive process exit and makes recovery useful beyond a demonstration. | Storage schema, crash consistency, migration, corruption recovery, confidentiality, retention, and backup tests. |
| Scoped collaboration | Lets composers, arrangers, performers, and editors collaborate without collapsing their authority. | Identity, revocation, delegation, conflict resolution, stale approval handling, and explicit ownership of each musical scope. |
| Constraint-aware arranging | Supports vocal ranges and chosen style rules while protecting melody and lyrics. | Ruleset provenance, warning versus blocking behavior, and proof that transposition never silently authorizes revoicing. |
| Requested generated alternatives | Offers harmonies, cadences, or parts while retaining the musician's decisions. | Explicit request and permission, durable generated-origin attribution, accept/reject workflow, and independent provider silos. |
| Dorico, MuseScore, DAW, and computer-use adapters | Reduces clerical effort inside tools musicians already use. | Application-specific capabilities, observable effects, external transaction/compensation limits, and isolated failure/recovery. |
| Broader musical representation | Makes room for microtonality, non-Western tuning, unmetered music, graphic notation, and extended techniques. | Real use cases and small representation extensions that avoid a premature universal format. |
| Optical and polyphonic transcription | Extends ingestion to scores and richer recordings. | Separate capability contracts, defensible quality evidence, rights/policy boundaries, and no dependency imposed on monophonic work. |
| Third-party conformance profiles | Lets independent implementations make precise, testable compatibility claims. | Versioned profiles, portable adversarial fixtures, failure semantics, and independent implementations exercising the same contract. |
| Low-latency score following & incremental listening | Tracks live performer position against existing score using bounded EvidenceWindow and room-mode aware subharmonic listening. | Latency benchmarks under 50ms, skipped/repeated measure resilience, adversarial tempo drift tests, and proof that tracking never mutates score notation without authority. |
| Multi-evaluator conformance & consensus ensembles | Accelerates conformance verification and surfaces musical ambiguity using structured evaluators (TypeSafe Jev, local models) with calibrated distributions. | Provider-independent benchmark suite, reproducible disagreement metrics, secret redaction verification, and zero core dependency on hosted APIs. |
| Physical resonance watcher & room calibration | Dynamically isolates room modes and sympathetic overtones from acoustic instrument timbres during live performance. | Acoustic sweep calibration tests, subharmonic ratio verification, and integration with the 10-band spectrum watcher. |

For new ideas, record the problem, source/date, likely value, open risks, and evidence required for evaluation. Record a promotion or rejection with its reason rather than silently deleting the idea or letting it become accidental architecture.
