"""Music MCP reference monophonic audio analyzer silo. See ANALYZER_CONTRACT.md."""
from dataclasses import dataclass
from fractions import Fraction
import io
import math
import struct
from uuid import uuid4
import wave

from reference.core import Diagnostic, MusicError, Note, Producer, UNCERTAINTY, phrase, text
from reference.spectrum import SpectrumReport, watch_audio_bytes

VERSION = '0.1.01'
ANALYZER_PRODUCER = Producer(identity='reference-monophonic-analyzer', version=VERSION)

NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')

RATIONAL_GRID = (
    Fraction(1, 16), Fraction(1, 8), Fraction(1, 6), Fraction(1, 4),
    Fraction(1, 3), Fraction(3, 8), Fraction(1, 2), Fraction(2, 3),
    Fraction(3, 4), Fraction(1, 1), Fraction(5, 4), Fraction(3, 2),
    Fraction(2, 1), Fraction(3, 1), Fraction(4, 1)
)


def _analyzer_fail(code: str, message: str, action: str = 'Supply valid 16-bit mono PCM WAV audio.',
                   operation: str = 'analyze', scope: str = 'analysis'):
    raise MusicError(Diagnostic('MUSICMCP-ANALYZER-' + code, message, action, operation, scope, uuid4().hex))


def freq_to_pitch(f0: float, tuning_a4: float = 440.0) -> tuple[str, float]:
    """Convert fundamental frequency in Hz to Western pitch name and cents deviation across A0-C8.
    Frequencies outside valid Western musical note octaves (0-9) map to 'rest'.
    """
    if f0 <= 0 or f0 < 16.0 or f0 > 20000.0:
        return 'rest', 0.0
    semitones = 12.0 * math.log2(f0 / tuning_a4) + 69.0
    midi = int(round(semitones))
    cents = (semitones - midi) * 100.0
    note_idx = midi % 12
    octave = (midi // 12) - 1
    if not (0 <= octave <= 9):
        return 'rest', 0.0
    pitch_str = f'{NOTE_NAMES[note_idx]}{octave}'
    return pitch_str, cents

def quantize_duration(seconds: float, tempo_bpm: int) -> Fraction:
    """Convert duration in seconds to nearest exact Fraction in quarter-note units."""
    quarter_seconds = 60.0 / float(tempo_bpm)
    quarters = seconds / quarter_seconds
    if quarters <= 0:
        return Fraction(1, 16)
    best_diff = float('inf')
    best_frac = Fraction(1, 4)
    for frac in RATIONAL_GRID:
        diff = abs(float(frac) - quarters)
        if diff < best_diff:
            best_diff = diff
            best_frac = frac
    return best_frac


@dataclass(frozen=True)
class AnalysisResult:
    notes: tuple[Note, ...]
    uncertainty: str
    tempo_bpm: int
    duration_seconds: float
    producer: Producer
    description: str
    spectrum_report: SpectrumReport


def analyze_monophonic_wav(data: bytes, *, tempo_bpm: int = 120, tuning_a4: float = 440.0) -> AnalysisResult:
    """Analyze 16-bit PCM mono WAV audio across full audible range (20Hz-20kHz) with anomaly watcher."""
    if type(data) is not bytes or not 44 <= len(data) <= 1024 * 1024:
        _analyzer_fail('INPUT_INVALID', 'Audio data must be a valid WAV byte stream of at most 1 MiB.')
    if type(tempo_bpm) is not int or not 30 <= tempo_bpm <= 300:
        _analyzer_fail('INPUT_INVALID', 'Tempo must be an integer between 30 and 300 BPM.')

    try:
        with wave.open(io.BytesIO(data), 'rb') as wf:
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            rate = wf.getframerate()
            nframes = wf.getnframes()
            if channels != 1:
                _analyzer_fail('CHANNEL_UNSUPPORTED', f'Expected mono (1-channel) audio, got {channels} channels.')
            if width != 2:
                _analyzer_fail('FORMAT_UNSUPPORTED', f'Expected 16-bit signed PCM audio, got {width * 8}-bit.')
            if not (8000 <= rate <= 192000):
                _analyzer_fail('SAMPLERATE_UNSUPPORTED', f'Sample rate must be 8000–192000 Hz, got {rate} Hz.')
            if nframes == 0:
                _analyzer_fail('EMPTY_PAYLOAD', 'Audio file contains zero audio frames.')
            if nframes > rate * 30:
                _analyzer_fail('DURATION_EXCEEDED', 'Audio duration exceeds the 30-second reference limit.')
            raw = wf.readframes(nframes)
    except MusicError:
        raise
    except Exception as e:
        _analyzer_fail('INPUT_INVALID', f'Malformed or unreadable WAV container: {e}')

    expected_bytes = nframes * 2
    if len(raw) < expected_bytes:
        _analyzer_fail('INPUT_INVALID', 'Audio payload truncated before declared frame count.')

    samples = [s / 32768.0 for s in struct.unpack(f"<{nframes}h", raw)]
    total_duration = nframes / float(rate)

    # 1. Run the Non-Musical Anomaly Watcher
    spectrum_report = watch_audio_bytes(data)

    # 2. Frame-by-frame pitch extraction over musical range (A0 27.5 Hz to C8 4186 Hz)
    frame_len = max(512, int(rate * 0.08))  # 80ms window to resolve low frequencies down to A0
    if frame_len > len(samples):
        frame_len = len(samples)
    hop_len = max(128, int(rate * 0.020))   # 20ms hop
    min_lag = max(2, int(rate / 4200.0))    # ~C8 upper bound (4186 Hz)
    max_lag = min(frame_len - 2, int(rate / 26.0))  # ~A0 lower bound (27.5 Hz)
    frames_pitch = []
    frames_conf = []
    frames_cents = []
    frames_voiced = []

    pos = 0
    while pos + frame_len <= len(samples):
        frame = samples[pos:pos + frame_len]
        energy = sum(x * x for x in frame)
        rms = math.sqrt(energy / float(frame_len))

        # Silence threshold
        if rms < 0.012:
            frames_voiced.append(False)
            frames_pitch.append('rest')
            frames_conf.append(1.0)
            frames_cents.append(0.0)
        else:
            # Autocorrelation
            best_lag = 0
            best_corr = -1.0
            corrs = [0.0] * (max_lag + 2)
            for lag in range(min_lag, max_lag + 1):
                c = sum(frame[i] * frame[i + lag] for i in range(frame_len - lag))
                corrs[lag] = c
                if c > best_corr:
                    best_corr = c
                    best_lag = lag

            conf = best_corr / energy if energy > 1e-6 else 0.0
            if conf < 0.40 or best_lag == 0:
                frames_voiced.append(False)
                frames_pitch.append('rest')
                frames_conf.append(conf)
                frames_cents.append(0.0)
            else:
                p = 0.0
                if min_lag < best_lag < max_lag:
                    denom = 2.0 * (corrs[best_lag - 1] - 2.0 * corrs[best_lag] + corrs[best_lag + 1])
                    if abs(denom) > 1e-9:
                        p = (corrs[best_lag - 1] - corrs[best_lag + 1]) / denom
                refined_lag = best_lag + p
                f0 = rate / refined_lag
                pitch_name, cents = freq_to_pitch(f0, tuning_a4)
                frames_voiced.append(True)
                frames_pitch.append(pitch_name)
                frames_conf.append(conf)
                frames_cents.append(cents)

        pos += hop_len

    if not frames_pitch:
        _analyzer_fail('EMPTY_PAYLOAD', 'No audio frames could be evaluated.')

    # Group contiguous frames into notes
    segments = []
    current_pitch = frames_pitch[0]
    current_count = 1
    current_confs = [frames_conf[0]]
    current_cents = [frames_cents[0]]
    current_voiced = [frames_voiced[0]]

    for p_name, conf, cents, voiced in zip(frames_pitch[1:], frames_conf[1:], frames_cents[1:], frames_voiced[1:]):
        if p_name == current_pitch:
            current_count += 1
            current_confs.append(conf)
            current_cents.append(cents)
            current_voiced.append(voiced)
        else:
            seg_duration = current_count * (hop_len / float(rate))
            segments.append((current_pitch, seg_duration, current_confs, current_cents, current_voiced))
            current_pitch = p_name
            current_count = 1
            current_confs = [conf]
            current_cents = [cents]
            current_voiced = [voiced]

    seg_duration = current_count * (hop_len / float(rate))
    segments.append((current_pitch, seg_duration, current_confs, current_cents, current_voiced))

    # Construct validated Notes
    notes_list = []
    all_voiced_cents = []
    all_confs = []

    for p_name, duration_sec, confs, cents_list, voiced_list in segments:
        if p_name == 'rest' and duration_sec < 0.04 and len(segments) > 1:
            continue
        frac_dur = quantize_duration(duration_sec, tempo_bpm)
        notes_list.append(Note(pitch=p_name, duration=frac_dur))
        if any(voiced_list):
            all_voiced_cents.extend([c for c, v in zip(cents_list, voiced_list) if v])
            all_confs.extend(confs)

    if not notes_list:
        notes_list.append(Note(pitch='rest', duration=Fraction(1, 1)))

    validated_notes = phrase(notes_list)

    # Determine uncertainty with spectral watcher inputs
    voiced_frame_count = sum(1 for v in frames_voiced if v)

    if voiced_frame_count == 0 or not all_voiced_cents:
        uncertainty = 'INSUFFICIENT_EVIDENCE'
    elif any(a.severity == 'CRITICAL' for a in spectrum_report.anomalies):
        # Critical anomalies (clipping, DC offset, clicks) compromise certainty
        uncertainty = 'AMBIGUOUS'
    else:
        mean_cents = sum(all_voiced_cents) / float(len(all_voiced_cents))
        cents_var = sum((c - mean_cents) ** 2 for c in all_voiced_cents) / float(len(all_voiced_cents))
        cents_std = math.sqrt(cents_var)
        mean_conf = sum(all_confs) / float(len(all_confs))

        if cents_std > 35.0:
            uncertainty = 'AMBIGUOUS'
        elif mean_conf < 0.60:
            uncertainty = 'LOW'
        elif mean_conf < 0.80 or cents_std > 20.0 or bool(spectrum_report.anomalies):
            uncertainty = 'MEDIUM'
        else:
            uncertainty = 'HIGH'

    desc_parts = [
        f'Monophonic analysis ({len(validated_notes)} events, {total_duration:.2f}s, {tempo_bpm} BPM, uncertainty: {uncertainty})',
        spectrum_report.summary
    ]
    desc = ' | '.join(desc_parts)

    return AnalysisResult(
        notes=validated_notes,
        uncertainty=uncertainty,
        tempo_bpm=tempo_bpm,
        duration_seconds=total_duration,
        producer=ANALYZER_PRODUCER,
        description=desc,
        spectrum_report=spectrum_report
    )


def ingest_and_propose(workspace, evidence_id: str, scope: str, *, tempo_bpm: int = 120, tuning_a4: float = 440.0):
    """High-level helper: read evidence, analyze, and propose to workspace without mutating state."""
    text(scope)
    evidence = workspace.evidence(evidence_id)
    result = analyze_monophonic_wav(evidence.data, tempo_bpm=tempo_bpm, tuning_a4=tuning_a4)
    obs = workspace.observe(evidence.id, result.description, producer=result.producer)
    prop = workspace.propose(obs.id, scope, result.notes, mode='intended',
                             uncertainty=result.uncertainty, origin='interpreted',
                             producer=result.producer)
    return obs, prop
