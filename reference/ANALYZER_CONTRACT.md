# Monophonic audio analyzer & spectrum watcher contract — 0.1.01

Owner: Music MCP analysis maintainers. Implementation: `reference/analyzer.py`, `reference/spectrum.py`. Consumer: trusted local hosts, proposal pipelines, and conformance tests. Dependencies: Python 3.11+ standard library only (`wave`, `struct`, `math`, `fractions`). No external binary, model provider, network request, or native C library required. Experimental reference silo; not a polyphonic transcription product.

## Boundary and authority isolation

The analyzer and spectrum watcher are strictly observation and proposal generators. They convert audio evidence into structured observations, provisional phrase proposals, and non-musical anomaly reports.
1. The analyzer and watcher MUST NOT hold, receive, or invoke an `AuthoritySession`. They cannot commit revisions or alter authoritative workspace state.
2. The analyzer and watcher MUST NOT access internal workspace dictionaries or private fields. All interactions with the core occur through public methods (`workspace.evidence(id)`, `workspace.observe(...)`, `workspace.propose(...)`).
3. An analyzer or watcher failure, invalid input, or internal exception MUST NOT affect the state safety of the workspace or corrupt existing evidence/history.

## Input specifications and validation

`analyze_monophonic_wav(data: bytes, *, tempo_bpm: int = 120, tuning_a4: float = 440.0)` accepts raw audio bytes:
- **Format:** RIFF/WAV container with uncompressed Linear PCM encoding.
- **Channels:** Exactly 1 channel (mono). Multi-channel audio is rejected with `VALIDATION_FAILED` to prevent unstated spatial mixing assumptions.
- **Sample Rate:** 8,000 Hz to 192,000 Hz. Sample rates $\ge 64,000$ Hz allow full Nyquist frequency analysis up to and beyond 28 kHz ($F_s / 2 \ge 28$ kHz).
- **Bit Depth:** 16-bit signed integer PCM (`struct` format `<h`).
- **Size & Duration Limits:** 44 bytes (header only) to 1,048,576 bytes (1 MiB), representing at most 30 seconds of audio at 48kHz (or proportional limit at higher rates).
- **Validation:** Malformed headers, missing data chunks, non-PCM compression formats, empty payloads, or unsupported sample dimensions are rejected with `VALIDATION_FAILED` and descriptive diagnostics.

## Audio Spectrum Inspection and Non-Musical Anomaly Watcher (10 Hz – 28 kHz)

To ensure that what we intend is indeed all that is playing, and because extra sounds exist beyond what is considered "music" (infrasound, ultrasonic leak, mains hum, clipping, pops, DC offset), the analyzer integrates an independent Spectrum Watcher (`reference/spectrum.py`). Without a dedicated watcher for sounds outside the musical domain, an audio system cannot be certain it is not producing or suffering from unobserved acoustic anomalies.

### Frequency Band Decomposition (10 Hz to 28,000 Hz and beyond)

The spectrum inspector computes normalized band energy fractions across 10 distinct acoustic zones:
1. **`deep_infrasonic` (0.0 Hz – 10.0 Hz):** DC drift, mechanical thumps, and subsonic speaker excursion.
2. **`infrasonic_tactile` (10.0 Hz – 20.0 Hz):** Felt/tactile physical vibration, sub-audible flutter.
3. **`sub_bass` (20.0 Hz – 60.0 Hz):** Low-end audible foundation and rumble.
4. **`bass` (60.0 Hz – 250.0 Hz):** Musical bass fundamentals and body.
5. **`low_mid` (250.0 Hz – 500.0 Hz):** Instrumental warmth and resonance.
6. **`mid` (500.0 Hz – 2,000.0 Hz):** Core melodic presence, vocal vowel formants.
7. **`high_mid` (2,000.0 Hz – 6,000.0 Hz):** Attack transients, percussive bite, and consonants.
8. **`high_treble` (6,000.0 Hz – 20,000.0 Hz):** Air, shimmer, brilliance, and human hearing upper threshold.
9. **`extended_ultrasonic` (20,000.0 Hz – 28,000.0 Hz):** Extended ultrasonic band (20 kHz to 28 kHz) monitoring high-frequency synthesizer leakage or aliasing.
10. **`extreme_ultrasonic` (> 28,000.0 Hz):** Out-of-band energy beyond 28 kHz.

### Non-Musical Anomaly Detection

The watcher evaluates each audio buffer for non-musical signal anomalies:
- **`DC_OFFSET`:** Evaluates static amplitude bias. Flagged if $|x_{	ext{DC}}| > 0.008$ FS (CRITICAL if $> 0.04$ FS).
- **`CLIPPING`:** Counts flat-topped samples at $|s| \ge 0.999$. Flagged if present (CRITICAL if $> 10$ samples).
- **`CLICK_DISCONTINUITY`:** Detects impulsive step jumps $> 0.40$ FS between adjacent samples indicating buffer under-runs or phase discontinuities.
- **`MAINS_HUM`:** Detects isolated electrical hum at 50 Hz, 60 Hz, 100 Hz, or 120 Hz with prominence $> 9.5$ dB ($> 3	imes$) above local floor using 4096-point FFT with parabolic peak interpolation.
- **`INFRASONIC_RUMBLE`:** Flags excessive energy in 0–20 Hz (specifically 10–20 Hz tactile vibration) exceeding 5% of spectral energy.
- **`ULTRASONIC_LEAK`:** Flags unintended ultrasonic energy in 20 kHz – 28 kHz exceeding 2% of spectral energy.
- **`EXTREME_ULTRASONIC`:** Flags out-of-band energy above 28 kHz exceeding 1% of spectral energy.

## Signal processing and feature extraction

1. **RMS Energy & Voicing:** Frames of 20–40ms (default 1024 samples at 44.1kHz with 50% overlap) are evaluated for root-mean-square amplitude. Frames below the silence threshold (default 0.012 relative amplitude) are classified as unvoiced / silence.
2. **Fundamental Frequency ($f_0$):** Voiced frames are analyzed using normalized square-difference autocorrelation over the pitch range 27.5 Hz (A0) to 4186 Hz (C8).
3. **Symbolic Pitch Mapping:** Continuous $f_0$ values are mapped to 12-tone equal temperament (12-TET) relative to `tuning_a4` (default 440.0 Hz). Pitch spellings use uppercase note names (`A` through `G`), optional single sharp `#` or flat `b`, and octave number `0` through `9`, matching the reference symbolic profile in [CONTRACT.md](CONTRACT.md). Frequencies outside musical octaves 0–9 map to `'rest'`.
4. **Note Segmentation & Quantization:** Contiguous voiced frames with consistent pitch (within 50 cents) are merged into symbolic `Note` events. Durations are calculated from frame counts and sample rate, then quantized to exact positive `fractions.Fraction` quarter-note units based on `tempo_bpm`. Durations smaller than 1/16 quarter note are clamped or rejected. Contiguous silent intervals are represented as `Note(pitch="rest", duration=Fraction(...))`.

## Qualitative uncertainty classification

Every proposal assigns an explicit uncertainty label from the six recognized constitutional categories:
- **`HIGH`:** Clear periodicity, strong harmonic energy, pitch deviation < 20 cents, stable duration, clean spectrum.
- **`MEDIUM`:** Moderate harmonic clarity, slight pitch deviation (20–40 cents), minor timing jitter, or non-critical spectral anomalies.
- **`LOW`:** Weak harmonic correlation, high noise ratio, or duration near segmentation boundaries.
- **`AMBIGUOUS`:** Vibrato modulation exceeding ±35 cents, expressive pitch slides, or critical non-musical anomalies (`CLIPPING`, severe `DC_OFFSET`, `CLICK_DISCONTINUITY`).
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
