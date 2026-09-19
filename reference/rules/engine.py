"""Constraint-Aware Arranging and Musical Rules Engine for Music MCP.

Adheres strictly to Python 3.11+ standard library only: dataclasses, enum, fractions, typing.
"""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import re
from typing import Sequence

from reference.core import (
    Candidate,
    Note,
    phrase,
)

PITCH_OFFSETS = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

MIDI_TO_NOTE_NAME = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')


def pitch_to_midi(pitch: str) -> int | None:
    """Convert symbolic pitch string (e.g. 'C4', 'F#5', 'Bb3') to standard MIDI key number.
    Returns None for 'rest'.
    """
    if pitch == 'rest':
        return None
    m = re.fullmatch(r'([A-G][#b]?)([0-9])', pitch)
    if not m:
        raise ValueError(f"Invalid symbolic pitch string: {pitch}")
    step = m.group(1)
    octave = int(m.group(2))
    offset = PITCH_OFFSETS[step]
    return (octave + 1) * 12 + offset


def midi_to_pitch(midi_num: int) -> str:
    """Convert MIDI key number (0-127) to standard symbolic pitch string."""
    if not (0 <= midi_num <= 127):
        raise ValueError(f"MIDI note out of range (0-127): {midi_num}")
    note_idx = midi_num % 12
    octave = (midi_num // 12) - 1
    return f"{MIDI_TO_NOTE_NAME[note_idx]}{octave}"


class RuleSeverity(str, Enum):
    BLOCKING = "BLOCKING"  # Causes candidate validation failure
    WARNING = "WARNING"    # Logged advisory for human review
    INFO = "INFO"


@dataclass(frozen=True)
class VocalRange:
    name: str
    min_midi: int
    max_midi: int
    tessitura_min: int
    tessitura_max: int


STANDARD_VOCAL_RANGES = {
    "SOPRANO": VocalRange("SOPRANO", min_midi=60, max_midi=84, tessitura_min=64, tessitura_max=79),
    "ALTO":    VocalRange("ALTO", min_midi=53, max_midi=74, tessitura_min=57, tessitura_max=71),
    "TENOR":   VocalRange("TENOR", min_midi=48, max_midi=69, tessitura_min=52, tessitura_max=67),
    "BASS":    VocalRange("BASS", min_midi=40, max_midi=64, tessitura_min=43, tessitura_max=60),
}


@dataclass(frozen=True)
class RuleViolation:
    rule_name: str
    severity: RuleSeverity
    note_index: int
    pitch: str
    message: str


@dataclass(frozen=True)
class RulesReport:
    valid: bool
    blocking_violations: tuple[RuleViolation, ...]
    warning_violations: tuple[RuleViolation, ...]
    summary: str


@dataclass(frozen=True)
class Ruleset:
    name: str
    version: str
    author: str
    vocal_range: VocalRange | None = None
    max_leap_semitones: int = 12
    allow_tessitura_overflow: bool = True  # If False, tessitura overflow is blocking


def transpose_phrase(notes: Sequence[Note], semitones: int) -> tuple[Note, ...]:
    """Transposes a phrase by exact semitones while strictly preserving all pitch relationships.
    Fails if any transposed note would fall outside standard MIDI 0-127 range.
    """
    if semitones == 0:
        return phrase(list(notes))

    transposed = []
    for n in notes:
        if n.pitch == 'rest':
            transposed.append(n)
        else:
            midi = pitch_to_midi(n.pitch)
            new_midi = midi + semitones
            if not (0 <= new_midi <= 127):
                raise ValueError(f"Transposition by {semitones} semitones puts note {n.pitch} outside MIDI 0-127 range.")
            transposed.append(Note(pitch=midi_to_pitch(new_midi), duration=n.duration))

    return phrase(transposed)


class RulesEngine:
    """Evaluates phrases and candidates against declared musical constraints."""

    def __init__(self, ruleset: Ruleset | None = None):
        self.ruleset = ruleset or Ruleset(name="default", version="0.1.01", author="host")

    def evaluate_phrase(self, notes: Sequence[Note]) -> RulesReport:
        """Audits a sequence of Notes against the active ruleset."""
        blocking = []
        warnings = []

        prev_midi = None

        for idx, n in enumerate(notes):
            if n.pitch == 'rest':
                continue

            midi = pitch_to_midi(n.pitch)

            # 1. Range check
            if self.ruleset.vocal_range:
                vr = self.ruleset.vocal_range
                # Absolute physical range
                if midi < vr.min_midi:
                    blocking.append(RuleViolation(
                        rule_name="VOCAL_RANGE_EXCEEDED",
                        severity=RuleSeverity.BLOCKING,
                        note_index=idx,
                        pitch=n.pitch,
                        message=f"Pitch {n.pitch} (MIDI {midi}) is below absolute {vr.name} limit ({midi_to_pitch(vr.min_midi)}, MIDI {vr.min_midi}).",
                    ))
                elif midi > vr.max_midi:
                    blocking.append(RuleViolation(
                        rule_name="VOCAL_RANGE_EXCEEDED",
                        severity=RuleSeverity.BLOCKING,
                        note_index=idx,
                        pitch=n.pitch,
                        message=f"Pitch {n.pitch} (MIDI {midi}) is above absolute {vr.name} limit ({midi_to_pitch(vr.max_midi)}, MIDI {vr.max_midi}).",
                    ))
                # Tessitura comfort check
                elif midi < vr.tessitura_min or midi > vr.tessitura_max:
                    sev = RuleSeverity.WARNING if self.ruleset.allow_tessitura_overflow else RuleSeverity.BLOCKING
                    target_list = warnings if sev == RuleSeverity.WARNING else blocking
                    target_list.append(RuleViolation(
                        rule_name="TESSITURA_OVERFLOW",
                        severity=sev,
                        note_index=idx,
                        pitch=n.pitch,
                        message=f"Pitch {n.pitch} (MIDI {midi}) exceeds comfortable {vr.name} tessitura ({midi_to_pitch(vr.tessitura_min)}-{midi_to_pitch(vr.tessitura_max)}).",
                    ))

            # 2. Melodic Leap check
            if prev_midi is not None:
                leap = abs(midi - prev_midi)
                if leap > self.ruleset.max_leap_semitones:
                    warnings.append(RuleViolation(
                        rule_name="EXCESSIVE_MELODIC_LEAP",
                        severity=RuleSeverity.WARNING,
                        note_index=idx,
                        pitch=n.pitch,
                        message=f"Melodic leap of {leap} semitones from {midi_to_pitch(prev_midi)} to {n.pitch} exceeds limit of {self.ruleset.max_leap_semitones}.",
                    ))

            prev_midi = midi

        summary = f"Rules evaluation: {len(blocking)} blocking error(s), {len(warnings)} warning(s)."
        return RulesReport(
            valid=len(blocking) == 0,
            blocking_violations=tuple(blocking),
            warning_violations=tuple(warnings),
            summary=summary,
        )

    def check_candidate(self, candidate: Candidate) -> bool:
        """Workspace validator callback hook (used as Workspace._validator).
        Returns True if no blocking violations exist; returns False to deny candidate commit.
        """
        report = self.evaluate_phrase(candidate.notes)
        return report.valid
