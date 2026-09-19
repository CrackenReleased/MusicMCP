"""Synthetic WAV audio fixtures for analyzer and spectrum watcher conformance testing."""
import io
import math
import struct
import wave


def make_wav(segments: list[tuple[float, float]], sample_rate: int = 44100, volume: float = 0.5) -> bytes:
    """Generate 16-bit mono PCM WAV bytes from [(freq_hz, duration_sec), ...]. freq_hz <= 0 produces silence."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        all_samples = []
        for freq, duration in segments:
            n_samples = int(duration * sample_rate)
            if freq <= 0:
                all_samples.extend([0] * n_samples)
            else:
                for i in range(n_samples):
                    t = i / float(sample_rate)
                    val = volume * math.sin(2.0 * math.pi * freq * t)
                    all_samples.append(int(val * 32767))

        wf.writeframes(struct.pack(f"<{len(all_samples)}h", *all_samples))
    return buf.getvalue()


def make_vibrato_wav(base_freq: float = 440.0, duration: float = 1.0,
                     vib_rate: float = 5.0, vib_cents: float = 50.0,
                     sample_rate: int = 44100, volume: float = 0.5) -> bytes:
    """Generate audio with sinusoidal vibrato frequency modulation."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        n_samples = int(duration * sample_rate)
        samples = []
        phase = 0.0
        for i in range(n_samples):
            t = i / float(sample_rate)
            cents_mod = vib_cents * math.sin(2.0 * math.pi * vib_rate * t)
            instant_freq = base_freq * (2.0 ** (cents_mod / 1200.0))
            phase += 2.0 * math.pi * instant_freq / float(sample_rate)
            val = volume * math.sin(phase)
            samples.append(int(val * 32767))

        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_silence_wav(duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate pure silence WAV."""
    return make_wav([(0.0, duration)], sample_rate=sample_rate)


def make_stereo_wav(duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate 2-channel stereo WAV to test multi-channel rejection."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        raw = struct.pack(f"<{n_samples * 2}h", *([0] * (n_samples * 2)))
        wf.writeframes(raw)
    return buf.getvalue()


def make_clipped_wav(freq: float = 440.0, duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate heavily clipped (overdriven) audio with flat-topping at ±32767."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            val = 2.5 * math.sin(2.0 * math.pi * freq * t)  # 2.5x overdrive
            clamped = max(-32767, min(32767, int(val * 32767)))
            samples.append(clamped)
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_dc_offset_wav(freq: float = 440.0, duration: float = 0.5, dc_bias: float = 0.08, sample_rate: int = 44100) -> bytes:
    """Generate audio with positive DC offset bias."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            val = 0.4 * math.sin(2.0 * math.pi * freq * t) + dc_bias
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_click_pop_wav(freq: float = 440.0, duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate audio with sudden sample discontinuities (clicks/pops)."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            val = 0.4 * math.sin(2.0 * math.pi * freq * t)
            samples.append(int(val * 32767))
        # Insert 3 hard clicks
        for click_idx in (n_samples // 4, n_samples // 2, 3 * n_samples // 4):
            samples[click_idx] = 32000
            samples[click_idx + 1] = -32000
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_mains_hum_wav(freq: float = 440.0, duration: float = 0.5, hum_freq: float = 60.0, sample_rate: int = 44100) -> bytes:
    """Generate musical tone with electrical 60Hz mains hum mixed in."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            # Music tone + prominent 60Hz hum
            val = 0.4 * math.sin(2.0 * math.pi * freq * t) + 0.15 * math.sin(2.0 * math.pi * hum_freq * t)
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_ultrasonic_leak_wav(freq: float = 440.0, duration: float = 0.5, sample_rate: int = 48000) -> bytes:
    """Generate audio at 48kHz with unintended 22,000 Hz ultrasonic tone."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            # 440Hz music + strong 22kHz ultrasonic tone
            val = 0.4 * math.sin(2.0 * math.pi * freq * t) + 0.12 * math.sin(2.0 * math.pi * 22000.0 * t)
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_infrasonic_wav(freq: float = 12.0, duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate audio with high energy in the 10-20 Hz tactile infrasonic range."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            # High amplitude 12 Hz tactile wave
            val = 0.6 * math.sin(2.0 * math.pi * freq * t)
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_extended_ultrasonic_wav(freq: float = 24000.0, duration: float = 0.5, sample_rate: int = 64000) -> bytes:
    """Generate audio sampled at 64kHz with high energy in 20kHz - 28kHz extended ultrasonic band."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            # 440 Hz fundamental + strong 24 kHz extended ultrasonic tone
            val = 0.3 * math.sin(2.0 * math.pi * 440.0 * t) + 0.3 * math.sin(2.0 * math.pi * freq * t)
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_extreme_ultrasonic_wav(freq: float = 30000.0, duration: float = 0.5, sample_rate: int = 96000) -> bytes:
    """Generate audio sampled at 96kHz with high energy above 28 kHz."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            # Strong 30 kHz tone (> 28 kHz)
            val = 0.3 * math.sin(2.0 * math.pi * 440.0 * t) + 0.3 * math.sin(2.0 * math.pi * freq * t)
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()

def make_piano_sympathetic_resonance_wav(fundamental_freq: float = 261.63, duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate simulated piano Middle C strike with open damper sympathetic resonance on octave strings (C5=523Hz, C6=1046Hz)."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            decay = math.exp(-2.0 * t)
            val = (
                0.4 * math.sin(2.0 * math.pi * fundamental_freq * t) +
                0.2 * math.sin(2.0 * math.pi * (2.0 * fundamental_freq) * t) +
                0.1 * math.sin(2.0 * math.pi * (4.0 * fundamental_freq) * t)
            ) * decay
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()


def make_guitar_natural_harmonic_wav(base_freq: float = 196.0, duration: float = 0.5, sample_rate: int = 44100) -> bytes:
    """Generate simulated guitar natural harmonic at 7th fret (3rd harmonic / perfect fifth node, 3f0 = 588Hz)."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            decay = math.exp(-1.5 * t)
            val = (
                0.25 * math.sin(2.0 * math.pi * base_freq * t) +
                0.45 * math.sin(2.0 * math.pi * (3.0 * base_freq) * t)
            ) * decay
            samples.append(max(-32767, min(32767, int(val * 32767))))
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
    return buf.getvalue()
