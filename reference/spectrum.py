"""Audio Spectrum Inspector and Non-Musical Anomaly Watcher for Music MCP.
Monitors full 10 Hz to 28,000 Hz (28 kHz) range, extended ultrasonic and infrasonic bands,
and watches for non-musical artifacts (DC offset, clipping, clicks, hum, spurious tones, ultrasonic leak).
"""
from dataclasses import dataclass
import io
import math
import struct
from uuid import uuid4
import wave

from reference.core import Diagnostic, MusicError

VERSION = '0.1.01'

# Full frequency spectrum band limits from 0 Hz up to >28 kHz
BAND_LIMITS = {
    'deep_infrasonic': (0.0, 10.0),              # Sub-10Hz DC drift & structural rumble
    'infrasonic_tactile': (10.0, 20.0),          # 10Hz - 20Hz physical/tactile vibration
    'sub_bass': (20.0, 60.0),                    # 20Hz - 60Hz audible sub-bass
    'bass': (60.0, 250.0),                       # 60Hz - 250Hz musical bass
    'low_mid': (250.0, 500.0),                   # 250Hz - 500Hz body and warmth
    'mid': (500.0, 2000.0),                      # 500Hz - 2kHz presence and core
    'high_mid': (2000.0, 6000.0),                # 2kHz - 6kHz attack and brightness
    'high_treble': (6000.0, 20000.0),            # 6kHz - 20kHz brilliance and air
    'extended_ultrasonic': (20000.0, 28000.0),   # 20kHz - 28kHz extended ultrasonic band
    'extreme_ultrasonic': (28000.0, float('inf'))# > 28kHz extreme out-of-band energy
}


@dataclass(frozen=True)
class SpectralAnomaly:
    kind: str  # 'CLIPPING', 'DC_OFFSET', 'CLICK_DISCONTINUITY', 'MAINS_HUM', 'ULTRASONIC_LEAK', 'EXTREME_ULTRASONIC', 'INFRASONIC_RUMBLE'
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    magnitude: float  # Relevant metric (e.g. dB, count, DC value)
    frequency_hz: float | None
    description: str


@dataclass(frozen=True)
class SpectrumReport:
    duration_seconds: float
    sample_rate: int
    nyquist_hz: float
    peak_amplitude: float
    rms_amplitude: float
    dc_offset: float
    snr_db: float
    band_energies: dict[str, float]  # Fraction of total energy in each band (0.0 to 1.0)
    anomalies: tuple[SpectralAnomaly, ...]
    clean_musical_signal: bool
    summary: str


def _fft_radix2(x: list[complex]) -> list[complex]:
    """Pure Python Cooley-Tukey radix-2 FFT."""
    n = len(x)
    if n <= 1:
        return x
    even = _fft_radix2(x[0::2])
    odd = _fft_radix2(x[1::2])
    half = n // 2
    factor = -2.0 * math.pi / float(n)
    terms = [complex(math.cos(factor * k), math.sin(factor * k)) * odd[k] for k in range(half)]
    return [even[k] + terms[k] for k in range(half)] + [even[k] - terms[k] for k in range(half)]


def compute_power_spectrum(samples: list[float], sample_rate: int, n_fft: int = 4096) -> list[tuple[float, float]]:
    """Compute average magnitude spectrum across samples using Hann windowed FFT frames.
    Returns list of (freq_hz, magnitude).
    """
    if not samples:
        return []

    # Choose power of 2, up to 4096 for fine 10Hz/hum resolution
    n_fft = 2 ** int(math.log2(max(256, min(n_fft, len(samples)))))
    if n_fft > len(samples):
        n_fft = 2 ** int(math.log2(max(256, len(samples))))

    hann = [0.5 * (1.0 - math.cos(2.0 * math.pi * i / (n_fft - 1))) for i in range(n_fft)]

    acc_magnitudes = [0.0] * (n_fft // 2)

    # Analyze up to 4 evenly distributed frames across the audio buffer for fast pure-Python execution
    max_frames = 4
    if len(samples) <= n_fft:
        frame_starts = [0]
    else:
        step = max(n_fft // 2, (len(samples) - n_fft) // max_frames)
        frame_starts = list(range(0, len(samples) - n_fft + 1, step))[:max_frames]

    n_frames = len(frame_starts)
    for pos in frame_starts:
        frame = [samples[pos + i] * hann[i] for i in range(n_fft)]
        c_frame = [complex(s, 0.0) for s in frame]
        fft_out = _fft_radix2(c_frame)
        for k in range(n_fft // 2):
            mag = math.sqrt(fft_out[k].real ** 2 + fft_out[k].imag ** 2)
            acc_magnitudes[k] += mag

    bin_hz = sample_rate / float(n_fft)
    return [(k * bin_hz, acc_magnitudes[k] / float(n_frames)) for k in range(n_fft // 2)]


def inspect_audio_spectrum(samples: list[float], sample_rate: int) -> SpectrumReport:
    """Run full spectral checks from 10 Hz to 28 kHz and non-musical anomaly watcher."""
    if not samples:
        raise MusicError(Diagnostic('MUSICMCP-SPECTRUM-EMPTY', 'Cannot inspect empty audio buffer.',
                                    'Supply non-empty audio samples.', 'inspect', 'spectrum', uuid4().hex))

    n_samples = len(samples)
    duration = n_samples / float(sample_rate)
    nyquist_hz = sample_rate / 2.0

    # 1. Time-Domain Metrics
    peak_amp = max(abs(s) for s in samples)
    sum_squares = sum(s * s for s in samples)
    rms_amp = math.sqrt(sum_squares / float(n_samples))
    dc_offset = sum(samples) / float(n_samples)

    anomalies = []

    # 2. DC Offset Check (< 10 Hz static drift)
    if abs(dc_offset) > 0.008:
        anomalies.append(SpectralAnomaly(
            kind='DC_OFFSET',
            severity='CRITICAL' if abs(dc_offset) > 0.04 else 'WARNING',
            magnitude=dc_offset,
            frequency_hz=0.0,
            description=f'DC offset bias detected ({dc_offset:+.3f} FS). May cause asymmetry or speaker excursion.'
        ))

    # 3. Clipping Check (Hard flat-topping)
    clip_count = sum(1 for s in samples if abs(s) >= 0.999)
    if clip_count > 0:
        clip_pct = (clip_count / float(n_samples)) * 100.0
        anomalies.append(SpectralAnomaly(
            kind='CLIPPING',
            severity='CRITICAL' if clip_count > 10 else 'WARNING',
            magnitude=float(clip_count),
            frequency_hz=None,
            description=f'Clipping / saturation detected ({clip_count} samples, {clip_pct:.2f}% of signal).'
        ))

    # 4. Impulsive Discontinuity / Click & Pop Watcher
    click_count = 0
    max_jump = 0.0
    for i in range(1, n_samples):
        diff = abs(samples[i] - samples[i - 1])
        if diff > max_jump:
            max_jump = diff
        if diff > 0.40:
            click_count += 1

    if click_count > 0:
        anomalies.append(SpectralAnomaly(
            kind='CLICK_DISCONTINUITY',
            severity='CRITICAL' if click_count > 5 else 'WARNING',
            magnitude=max_jump,
            frequency_hz=None,
            description=f'Sudden sample discontinuities / click pops detected ({click_count} occurrences, max jump {max_jump:.2f}).'
        ))

    # 5. Frequency-Domain Band Decomposition (up to 4096 FFT points for fine resolution)
    n_fft = 4096 if n_samples >= 4096 else (2048 if n_samples >= 2048 else 1024)
    spectrum = compute_power_spectrum(samples, sample_rate, n_fft=n_fft)

    band_energies = {band: 0.0 for band in BAND_LIMITS}
    total_spectral_energy = 0.0

    if spectrum:
        bin_width = spectrum[1][0] - spectrum[0][0] if len(spectrum) > 1 else 1.0
        for freq, mag in spectrum:
            energy = (mag ** 2) * bin_width
            total_spectral_energy += energy
            for band, (low, high) in BAND_LIMITS.items():
                if low <= freq < high:
                    band_energies[band] += energy
                    break

        if total_spectral_energy > 1e-12:
            for band in band_energies:
                band_energies[band] = band_energies[band] / total_spectral_energy

        # Populate backwards-compatible alias bands
        band_energies['infrasonic'] = band_energies['deep_infrasonic'] + band_energies['infrasonic_tactile']
        band_energies['audible'] = (
            band_energies['sub_bass'] + band_energies['bass'] + band_energies['low_mid'] +
            band_energies['mid'] + band_energies['high_mid'] + band_energies['high_treble']
        )
        band_energies['ultrasonic'] = band_energies['extended_ultrasonic'] + band_energies['extreme_ultrasonic']

        # 6. Deep Infrasonic & Tactile Rumble Check (0 Hz - 20 Hz)
        infrasound_total = band_energies['infrasonic']
        if infrasound_total > 0.05 and total_spectral_energy > 1e-6:
            infrasound_pct = infrasound_total * 100.0
            anomalies.append(SpectralAnomaly(
                kind='INFRASONIC_RUMBLE',
                severity='WARNING',
                magnitude=infrasound_pct,
                frequency_hz=10.0,
                description=f'Excessive infrasonic energy in 10-20 Hz tactile range ({infrasound_pct:.1f}% of total spectrum).'
            ))

        # 7. Extended Ultrasonic Watcher (20 kHz - 28 kHz)
        ultra_extended = band_energies['extended_ultrasonic']
        if ultra_extended > 0.02 and total_spectral_energy > 1e-6:
            ultra_pct = ultra_extended * 100.0
            anomalies.append(SpectralAnomaly(
                kind='ULTRASONIC_LEAK',
                severity='WARNING',
                magnitude=ultra_pct,
                frequency_hz=24000.0,
                description=f'Unintended ultrasonic energy detected in 20kHz-28kHz range ({ultra_pct:.1f}% of total spectrum).'
            ))

        # 8. Extreme Ultrasonic Watcher (> 28 kHz)
        ultra_extreme = band_energies['extreme_ultrasonic']
        if ultra_extreme > 0.01 and total_spectral_energy > 1e-6:
            extreme_pct = ultra_extreme * 100.0
            anomalies.append(SpectralAnomaly(
                kind='EXTREME_ULTRASONIC',
                severity='WARNING',
                magnitude=extreme_pct,
                frequency_hz=30000.0,
                description=f'Extreme ultrasonic energy detected above 28 kHz ({extreme_pct:.1f}% of total spectrum).'
            ))

        # 9. Mains Hum Watcher (Detect isolated prominent peak around 50Hz, 60Hz, 100Hz, or 120Hz)
        TARGET_HUMS = (50.0, 60.0, 100.0, 120.0)
        # Search window in spectrum bins (40 Hz to 135 Hz)
        hum_min_bin = max(1, int(40.0 / bin_width))
        hum_max_bin = min(len(spectrum) - 2, int(135.0 / bin_width))

        if hum_max_bin > hum_min_bin + 2:
            mags = [m for _, m in spectrum]
            sub_mags = mags[hum_min_bin:hum_max_bin + 1]
            peak_sub_idx = sub_mags.index(max(sub_mags))
            peak_bin = hum_min_bin + peak_sub_idx
            peak_mag = mags[peak_bin]

            # Parabolic interpolation on peak for sub-bin precision
            y1 = mags[peak_bin - 1]
            y2 = mags[peak_bin]
            y3 = mags[peak_bin + 1]
            denom = 2.0 * (2.0 * y2 - y1 - y3)
            p = (y3 - y1) / denom if abs(denom) > 1e-9 else 0.0
            detected_hum_hz = (peak_bin + p) * bin_width

            # Check if this peak aligns with a known mains hum frequency (within 3.0 Hz)
            closest_target = min(TARGET_HUMS, key=lambda t: abs(detected_hum_hz - t))
            if abs(detected_hum_hz - closest_target) <= 3.0:
                # Compare to surrounding local floor (±5 bins away)
                left = max(0, peak_bin - 5)
                right = min(len(spectrum) - 1, peak_bin + 5)
                neighbors = [mags[j] for j in range(left, right + 1) if abs(j - peak_bin) > 1]
                if neighbors:
                    floor = sum(neighbors) / float(len(neighbors))
                    if floor > 1e-6 and (peak_mag / floor) > 3.0:  # > 9.5 dB prominence
                        prominence_db = 20.0 * math.log10(peak_mag / floor)
                        anomalies.append(SpectralAnomaly(
                            kind='MAINS_HUM',
                            severity='WARNING',
                            magnitude=prominence_db,
                            frequency_hz=closest_target,
                            description=f'Mains electrical hum detected at {closest_target:.0f} Hz ({detected_hum_hz:.1f} Hz, +{prominence_db:.1f} dB above local floor).'
                        ))

    # 10. Estimated SNR in dB
    noise_est = min((abs(s) for s in samples[::10]), default=0.001)
    noise_floor = max(1e-5, noise_est)
    snr_db = 20.0 * math.log10((rms_amp + 1e-6) / noise_floor)

    clean = not any(a.severity == 'CRITICAL' for a in anomalies)
    summary_parts = [
        f'Audio {duration:.2f}s @ {sample_rate}Hz (Nyquist {nyquist_hz:.0f}Hz)',
        f'Peak: {peak_amp:.2f}',
        f'RMS: {rms_amp:.2f}',
        f'SNR: {snr_db:.1f}dB'
    ]
    if anomalies:
        summary_parts.append(f'Watcher Anomalies: {len(anomalies)} [{", ".join(a.kind for a in anomalies)}]')
    else:
        summary_parts.append('Watcher: Clean acoustic spectrum (no non-musical artifacts detected across 10Hz-28kHz)')

    return SpectrumReport(
        duration_seconds=duration,
        sample_rate=sample_rate,
        nyquist_hz=nyquist_hz,
        peak_amplitude=peak_amp,
        rms_amplitude=rms_amp,
        dc_offset=dc_offset,
        snr_db=snr_db,
        band_energies=band_energies,
        anomalies=tuple(anomalies),
        clean_musical_signal=clean,
        summary=' | '.join(summary_parts)
    )


def watch_audio_bytes(wav_data: bytes) -> SpectrumReport:
    """Inspect raw WAV audio bytes directly for 10Hz-28kHz range and non-musical artifacts."""
    if type(wav_data) is not bytes or len(wav_data) < 44:
        raise MusicError(Diagnostic('MUSICMCP-SPECTRUM-INPUT_INVALID', 'Invalid WAV byte stream.',
                                    'Supply valid WAV audio.', 'watch', 'spectrum', uuid4().hex))
    try:
        with wave.open(io.BytesIO(wav_data), 'rb') as wf:
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            rate = wf.getframerate()
            nframes = wf.getnframes()
            raw = wf.readframes(nframes)
    except Exception as e:
        raise MusicError(Diagnostic('MUSICMCP-SPECTRUM-INPUT_INVALID', f'Malformed WAV header: {e}',
                                    'Supply valid WAV audio.', 'watch', 'spectrum', uuid4().hex))

    if width != 2:
        raise MusicError(Diagnostic('MUSICMCP-SPECTRUM-FORMAT_UNSUPPORTED', f'Expected 16-bit PCM, got {width * 8}-bit.',
                                    'Supply 16-bit PCM audio.', 'watch', 'spectrum', uuid4().hex))

    total_samples = nframes * channels
    unpacked = struct.unpack(f"<{total_samples}h", raw)

    if channels == 1:
        mono_samples = [s / 32768.0 for s in unpacked]
    else:
        # Average channels to mono for inspection
        mono_samples = [(unpacked[i] + unpacked[i + 1]) / (2.0 * 32768.0) for i in range(0, total_samples, 2)]

    return inspect_audio_spectrum(mono_samples, rate)
