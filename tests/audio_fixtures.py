"""Synthetic WAV audio fixtures for analyzer conformance testing."""
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
            # Frequency modulation in cents
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
