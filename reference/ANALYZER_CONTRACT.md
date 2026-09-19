# Monophonic audio analyzer contract — 0.1.01

Owner: Music MCP analysis maintainers. Implementation: `reference/analyzer.py`. Consumer: trusted local hosts, proposal pipelines, and conformance tests. Dependencies: Python 3.11+ standard library only (`wave`, `struct`, `math`, `fractions`). No external binary, model provider, network request, or native C library required. Experimental reference silo; not a polyphonic transcription product.

## Boundary and authority isolation

The analyzer is strictly an observation and proposal generator. It converts audio evidence into structured observations and provisional phrase proposals.
1. The analyzer MUST NOT hold, receive, or invoke an `AuthoritySession`. It cannot commit revisions or alter authoritative workspace state.
2. The analyzer MUST NOT access internal workspace dictionaries or private fields. All interactions with the core occur through public methods (`workspace.evidence(id)`, `workspace.observe(...)`, `workspace.propose(...)`).
3. An analyzer failure, invalid input, or internal exception MUST NOT affect the state safety of the workspace or corrupt existing evidence/history.

## Input specifications and validation

`analyze_monophonic_wav(data: bytes, *, tempo_bpm: int = 120, tuning_a4: float = 440.0)` accepts raw audio bytes:
- **Format:** RIFF/WAV container with uncompressed Linear PCM encoding.
- **Channels:** Exactly 1 channel (mono). Multi-channel audio is rejected with `VALIDATION_FAILED` to prevent unstated spatial mixing assumptions.
- **Sample Rate:** 8,000 Hz to 48,000 Hz.
- **Bit Depth:** 16-bit signed integer PCM (`struct` format `<h`).
- **Size & Duration Limits:** 44 bytes (header only) to 1,048,576 bytes (1 MiB), representing at most 30 seconds of audio at 48kHz.
- **Validation:** Malformed headers, missing data chunks, non-PCM compression formats, empty payloads, or unsupported sample dimensions are rejected with `VALIDATION_FAILED` and descriptive diagnostics.

## Signal processing and feature extraction

1. **RMS Energy & Voicing:** Frames of 20–40ms (default 1024 samples at 44.1kHz with 50% overlap) are evaluated for root-mean-square amplitude. Frames below the silence threshold (default 0.02 relative amplitude) are classified as unvoiced / silence.
2. **Fundamental Frequency ($f_0$):** Voiced frames are analyzed using normalized square-difference autocorrelation over the pitch range 55 Hz (A1) to 1046.5 Hz (C6).
3. **Symbolic Pitch Mapping:** Continuous $f_0$ values are mapped to 12-tone equal temperament (12-TET) relative to `tuning_a4` (default 440.0 Hz). Pitch spellings use uppercase note names (`A` through `G`), optional single sharp `#` or flat `b`, and octave number `0` through `9`, matching the reference symbolic profile in [CONTRACT.md](CONTRACT.md).
4. **Note Segmentation & Quantization:** Contiguous voiced frames with consistent pitch (within 50 cents) are merged into symbolic `Note` events. Durations are calculated from frame counts and sample rate, then quantized to exact positive `fractions.Fraction` quarter-note units based on `tempo_bpm`. Durations smaller than 1/16 quarter note are clamped or rejected. Contiguous silent intervals are represented as `Note(pitch="rest", duration=Fraction(...))`.

## Qualitative uncertainty classification

Every proposal assigns an explicit uncertainty label from the six recognized constitutional categories:
- **`HIGH`:** Clear periodicity, strong harmonic energy, pitch deviation < 20 cents, stable duration.
- **`MEDIUM`:** Moderate harmonic clarity, slight pitch deviation (20–40 cents), or minor timing jitter.
- **`LOW`:** Weak harmonic correlation, high noise ratio, or duration near segmentation boundaries.
- **`AMBIGUOUS`:** Vibrato modulation exceeding ±35 cents, expressive pitch slides, or competing octave readings.
- **`INSUFFICIENT_EVIDENCE`:** Audio payload contains exclusively silence, ambient background noise, or unvoiced breath below the energy threshold.
- **`UNRESOLVED`:** Signal analysis encountered conflicting transient markers or contradictory framing.

Per [../SPECIFICATION.md](../SPECIFICATION.md), uncertainty describes the producer's assessment. No label confers permission or enables automated selection without human review.

## Attribution and provenance

Every observation and proposal emitted by this silo MUST include an immutable attribution record:
`Producer(identity="reference-monophonic-analyzer", version="0.1.01")`
Proposals MUST declare `mode="intended"` and `origin="interpreted"`. Analysis proposals must NEVER claim `origin="human"`.

## High-level helper

`ingest_and_propose(workspace, evidence_id, scope, *, tempo_bpm=120) -> tuple[Observation, Proposal]`:
Reads the raw bytes from `workspace.evidence(evidence_id)`, runs `analyze_monophonic_wav`, calls `workspace.observe`, and calls `workspace.propose`. Returns the created immutable records.
