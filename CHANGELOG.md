# Changelog

## 0.1.01 — 2026-09-18 — local experimental foundation refinement

- Define Format Adapters Contract in `reference/adapters/ADAPTER_CONTRACT.md` establishing SPECIFICATION REP-1 loss disclosure and strict isolation from host authority.
- Implement MusicXML 3.1 Partwise adapter (`reference/adapters/musicxml.py`) supporting bi-directional conversion (`phrase_to_musicxml` and `musicxml_to_phrase`) with explicit `LossReport` disclosing omitted layout, formatting, dynamics, and polyphony details.
- Implement Standard MIDI File (SMF Format 0) adapter (`reference/adapters/midi.py`) with pure Python variable-length quantity (VLQ) encoder/decoder, supporting bi-directional conversion (`phrase_to_midi` and `midi_to_phrase`) with explicit `LossReport` disclosing velocity standardization, enharmonic flattening, and channel assignments.
- Add 5 adapter conformance tests in `tests/test_adapters.py` (total 60 passing tests).
- Add executable format adapters demonstration in `reference/demo_adapters.py` confirming 100% exact mathematical round-tripping for both MusicXML and MIDI.

- Define Model-Facing MCP Transport Contract in `reference/MCP_CONTRACT.md` exposing read, analysis, spectrum inspection, and proposal operations to external Ai models while strictly preserving host-held human authority.
- Implement dependency-free standard-library Model Context Protocol (MCP) server in `reference/mcp_server.py` supporting stdio JSON-RPC 2.0 framing, tools discovery (`get_workspace_summary`, `list_scopes`, `get_phrase`, `inspect_spectrum`, `analyze_audio`, `propose_phrase`), dynamic `music://` resources, and prompt workflows.
- Enforce strict authority gate: models cannot possess mutation tokens or execute `confirm`, `correct`, or `restore`; attempts to mutate via MCP return `MUSICMCP-MCP-AUTHORITY_BOUNDARY_VIOLATION`.
- Add 7 MCP transport conformance and security tests in `tests/test_mcp.py` (total 55 passing tests).
- Add executable MCP server demonstration in `reference/demo_mcp.py` simulating an external model interaction workflow.
- Expand frequency spectrum checks and monitoring to encompass the full 10 Hz to 28,000 Hz (28 kHz) range.
- Implement dependency-free Audio Spectrum Inspector and Non-Musical Anomaly Watcher in `reference/spectrum.py` using pure Python Cooley-Tukey Radix-2 FFT and Hann-windowed frame evaluation.
- Monitor 10 distinct acoustic bands: `deep_infrasonic` (0–10 Hz), `infrasonic_tactile` (10–20 Hz), `sub_bass` (20–60 Hz), `bass` (60–250 Hz), `low_mid` (250–500 Hz), `mid` (500–2k Hz), `high_mid` (2k–6k Hz), `high_treble` (6k–20k Hz), `extended_ultrasonic` (20k–28k Hz), and `extreme_ultrasonic` (>28 kHz).
- Watch for non-musical artifacts beyond music: DC offset bias (>0.008 FS), hard clipping/saturation, sample discontinuity pops, mains electrical hum (50/60/100/120 Hz) with parabolic peak interpolation, 10–20 Hz tactile infrasonic rumble, and 20k–28k Hz extended ultrasonic leakage.
- Expand supported sample rates in `reference/analyzer.py` and `reference/spectrum.py` to 8,000 Hz – 192,000 Hz, supporting high-resolution Nyquist analysis up to and beyond 28 kHz.
- Integrate spectrum reports directly into monophonic analysis results, degrading uncertainty to `AMBIGUOUS` upon critical non-musical anomalies.
- Define monophonic audio analyzer contract in `reference/ANALYZER_CONTRACT.md`.
- Implement dependency-free reference monophonic audio analyzer in `reference/analyzer.py` with normalized autocorrelation pitch tracking, duration quantization to exact `Fraction` units, and qualitative uncertainty classification.
- Add audio fixtures generator in `tests/audio_fixtures.py` and 21 comprehensive conformance/watcher tests across `tests/test_analyzer.py` and `tests/test_spectrum.py` (total 48 passing tests).
- Add executable monophonic audio analysis demonstration in `reference/demo_analyzer.py`.
- Require immutable producer identity/version on each observation and proposal; missing or invalid attribution is rejected.
- Replace bare `locked_scopes` with attributed `LockConstraint(scope, origin, reason)` records retained in candidates and revisions; reject duplicate lock scopes.
- Define all six uncertainty labels and their non-authorizing semantics.
- Specify exact human review and fresh-consent obligations for trusted hosts; no UI, authentication or approval-token subsystem is claimed.
- Add six provenance/uncertainty conformance cases; all 27 tests pass. Source migration is documented in `DEPRECATION.md`.
- Experimental source API changes are intentionally incompatible with 0.1.0. No dependency, durable data format, network capability or musical representation expansion was introduced.

## 0.1.0 — 2026-09-18 — local experimental foundation

- Preserved the existing Apache-2.0 license and founding directive; established governing documentation, contracts, error semantics and continuation records.
- Added a dependency-free Python reference core retaining original evidence, provisional interpretations and structured uncertainty.
- Added host-held scoped authority for confirmation, correction and historical phrase restoration; immutable provenance and workspace revision checks protect publication.
- Added lock/policy/post-validation denial paths and bounded in-memory retention.
- Added adversarial conformance tests, architecture checks and an executable synthetic demonstration.
- No MCP transport, actual transcription, durable storage, adapters, GUI, deployment or published package is included.
