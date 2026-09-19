"""Conformance tests for the Audio Spectrum Inspector and Anomaly Watcher (10 Hz - 28 kHz)."""
import unittest

from reference.analyzer import analyze_monophonic_wav, freq_to_pitch
from reference.spectrum import inspect_audio_spectrum, watch_audio_bytes
from tests.audio_fixtures import (
    make_clipped_wav,
    make_click_pop_wav,
    make_dc_offset_wav,
    make_extended_ultrasonic_wav,
    make_extreme_ultrasonic_wav,
    make_guitar_natural_harmonic_wav,
    make_infrasonic_wav,
    make_mains_hum_wav,
    make_piano_sympathetic_resonance_wav,
    make_silence_wav,
    make_ultrasonic_leak_wav,
    make_wav
)


class SpectrumWatcherConformance(unittest.TestCase):
    def test_musical_range_pitch_mapping(self):
        # A0 (27.5 Hz) - lowest standard piano key
        pitch_a0, cents_a0 = freq_to_pitch(27.5)
        self.assertEqual(pitch_a0, 'A0')
        self.assertLess(abs(cents_a0), 1.0)

        # C4 (261.63 Hz) - middle C
        pitch_c4, cents_c4 = freq_to_pitch(261.63)
        self.assertEqual(pitch_c4, 'C4')
        self.assertLess(abs(cents_c4), 1.0)

        # C8 (4186.0 Hz) - highest standard piano key
        pitch_c8, cents_c8 = freq_to_pitch(4186.0)
        self.assertEqual(pitch_c8, 'C8')
        self.assertLess(abs(cents_c8), 1.0)

        # Infrasonic tactile sound (10 Hz) maps to rest in symbolic musical pitch
        pitch_sub, _ = freq_to_pitch(10.0)
        self.assertEqual(pitch_sub, 'rest')

        # Extended ultrasonic (28 kHz) maps to rest in symbolic musical pitch
        pitch_ultra, _ = freq_to_pitch(28000.0)
        self.assertEqual(pitch_ultra, 'rest')

    def test_clean_musical_signal_passes_watcher(self):
        audio = make_wav([(440.0, 0.4)], sample_rate=44100)
        report = watch_audio_bytes(audio)

        self.assertTrue(report.clean_musical_signal)
        self.assertEqual(len(report.anomalies), 0)
        self.assertIn('Clean acoustic spectrum', report.summary)
        self.assertGreater(report.snr_db, 20.0)
        self.assertLess(abs(report.dc_offset), 0.005)

    def test_clipping_watcher_flags_flat_topping(self):
        clipped_audio = make_clipped_wav(freq=440.0, duration=0.4)
        report = watch_audio_bytes(clipped_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('CLIPPING', kinds)
        self.assertFalse(report.clean_musical_signal)
        clipping_anomaly = next(a for a in report.anomalies if a.kind == 'CLIPPING')
        self.assertEqual(clipping_anomaly.severity, 'CRITICAL')
        self.assertIn('Clipping / saturation detected', clipping_anomaly.description)

    def test_dc_offset_watcher_flags_bias(self):
        dc_audio = make_dc_offset_wav(freq=440.0, duration=0.4, dc_bias=0.08)
        report = watch_audio_bytes(dc_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('DC_OFFSET', kinds)
        dc_anomaly = next(a for a in report.anomalies if a.kind == 'DC_OFFSET')
        self.assertGreater(abs(dc_anomaly.magnitude), 0.05)
        self.assertEqual(dc_anomaly.severity, 'CRITICAL')

    def test_click_discontinuity_watcher_flags_pop_artifacts(self):
        click_audio = make_click_pop_wav(freq=440.0, duration=0.4)
        report = watch_audio_bytes(click_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('CLICK_DISCONTINUITY', kinds)
        click_anomaly = next(a for a in report.anomalies if a.kind == 'CLICK_DISCONTINUITY')
        self.assertGreater(click_anomaly.magnitude, 0.5)

    def test_mains_hum_watcher_detects_60hz(self):
        hum_audio = make_mains_hum_wav(freq=440.0, duration=0.5, hum_freq=60.0)
        report = watch_audio_bytes(hum_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('MAINS_HUM', kinds)
        hum_anomaly = next(a for a in report.anomalies if a.kind == 'MAINS_HUM')
        self.assertEqual(hum_anomaly.frequency_hz, 60.0)
        self.assertIn('Mains electrical hum detected at 60 Hz', hum_anomaly.description)

    def test_mains_hum_watcher_detects_50hz(self):
        hum_audio = make_mains_hum_wav(freq=440.0, duration=0.5, hum_freq=50.0)
        report = watch_audio_bytes(hum_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('MAINS_HUM', kinds)
        hum_anomaly = next(a for a in report.anomalies if a.kind == 'MAINS_HUM')
        self.assertEqual(hum_anomaly.frequency_hz, 50.0)
        self.assertIn('Mains electrical hum detected at 50 Hz', hum_anomaly.description)

    def test_infrasonic_tactile_watcher_detects_10hz_to_20hz(self):
        infra_audio = make_infrasonic_wav(freq=12.0, duration=0.5)
        report = watch_audio_bytes(infra_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('INFRASONIC_RUMBLE', kinds)
        self.assertGreater(report.band_energies['infrasonic_tactile'], 0.05)
        self.assertGreater(report.band_energies['infrasonic'], 0.05)

    def test_extended_ultrasonic_watcher_detects_20k_to_28k(self):
        ultra_audio = make_extended_ultrasonic_wav(freq=24000.0, duration=0.5, sample_rate=64000)
        report = watch_audio_bytes(ultra_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('ULTRASONIC_LEAK', kinds)
        self.assertGreater(report.band_energies['extended_ultrasonic'], 0.02)
        self.assertGreater(report.band_energies['ultrasonic'], 0.02)

    def test_extreme_ultrasonic_watcher_detects_above_28k(self):
        extreme_audio = make_extreme_ultrasonic_wav(freq=30000.0, duration=0.5, sample_rate=96000)
        report = watch_audio_bytes(extreme_audio)

        kinds = [a.kind for a in report.anomalies]
        self.assertIn('EXTREME_ULTRASONIC', kinds)
        self.assertGreater(report.band_energies['extreme_ultrasonic'], 0.01)

    def test_sample_rate_up_to_192khz_accepted(self):
        hi_res_audio = make_wav([(440.0, 0.2)], sample_rate=96000)
        result = analyze_monophonic_wav(hi_res_audio, tempo_bpm=120)
        self.assertEqual(result.spectrum_report.sample_rate, 96000)
        self.assertEqual(result.spectrum_report.nyquist_hz, 48000.0)

    def test_analyzer_integrates_watcher_and_marks_critical_anomalies_ambiguous(self):
        # When severe clipping is present, analyzer uncertainty flags AMBIGUOUS
        clipped_audio = make_clipped_wav(freq=440.0, duration=0.4)
        result = analyze_monophonic_wav(clipped_audio, tempo_bpm=120)

        self.assertEqual(result.uncertainty, 'AMBIGUOUS')
        self.assertIsNotNone(result.spectrum_report)
        self.assertIn('CLIPPING', [a.kind for a in result.spectrum_report.anomalies])
        self.assertIn('Watcher Anomalies', result.description)


    def test_piano_sympathetic_resonance_octaves_recognized_as_clean_music(self):
        # Middle C with open damper sympathetic resonance on C5 (2f0) and C6 (4f0)
        audio = make_piano_sympathetic_resonance_wav(fundamental_freq=261.63, duration=0.5)
        report = watch_audio_bytes(audio)

        # Invariant: Natural acoustic resonance MUST NEVER be flagged as non-musical anomaly
        self.assertTrue(report.clean_musical_signal)
        self.assertEqual(len(report.anomalies), 0)
        self.assertIsNotNone(report.resonance)
        self.assertTrue(report.resonance.sympathetic_octaves_present)
        harmonic_nums = [h.harmonic_number for h in report.resonance.harmonics]
        self.assertIn(1, harmonic_nums)
        self.assertIn(2, harmonic_nums)
        self.assertIn('Sympathetic octave resonance active', report.resonance.description)

    def test_guitar_natural_harmonic_series_recognized(self):
        # Guitar 7th fret natural harmonic (196 Hz base with prominent 3rd harmonic 588 Hz)
        audio = make_guitar_natural_harmonic_wav(base_freq=196.0, duration=0.5)
        report = watch_audio_bytes(audio)

        self.assertTrue(report.clean_musical_signal)
        self.assertIsNotNone(report.resonance)
        self.assertTrue(report.resonance.natural_harmonics_present)
        self.assertIn('Natural harmonic overtone bloom active', report.resonance.description)

    def test_room_resonance_distinct_from_mains_hum(self):
        # Middle C (261.63 Hz) + 73 Hz room standing wave mode (not mains hum, not harmonic of C4)
        import math, io, wave, struct
        sample_rate = 44100
        n_samples = int(0.5 * sample_rate)
        samples = []
        for i in range(n_samples):
            t = i / float(sample_rate)
            val = 0.4 * math.sin(2.0 * math.pi * 261.63 * t) + 0.15 * math.sin(2.0 * math.pi * 73.0 * t)
            samples.append(int(val * 32767))
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f"<{n_samples}h", *samples))

        report = watch_audio_bytes(buf.getvalue())
        self.assertTrue(report.clean_musical_signal)
        self.assertIsNotNone(report.resonance)
        # 73 Hz is tracked as room resonance, NOT erroneously flagged as 60Hz/100Hz MAINS_HUM
        self.assertNotIn('MAINS_HUM', [a.kind for a in report.anomalies])
        self.assertTrue(any(abs(r - 73.0) < 6.0 for r in report.resonance.room_resonances))


if __name__ == '__main__':
    unittest.main()
