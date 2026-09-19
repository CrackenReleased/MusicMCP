"""Algorithmic and Model-Assisted Alternative Generation for Music MCP.

Adheres strictly to Python 3.11+ standard library only: dataclasses, enum, fractions, typing.
Enforces explicit request records and immutable origin="generated" provenance.
"""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Sequence
from uuid import uuid4

from reference.core import (
    Note,
    Producer,
    Proposal,
    Workspace,
    phrase,
    text,
)
from reference.rules.engine import (
    midi_to_pitch,
    pitch_to_midi,
)

GENERATOR_PRODUCER = Producer("diatonic-alternative-generator", "0.1.01")

# Standard C-Major diatonic scale semitone offsets: C D E F G A B
DIATONIC_SCALE_C = (0, 2, 4, 5, 7, 9, 11)


class AlternativeType(str, Enum):
    HARMONY_THIRD_ABOVE = "HARMONY_THIRD_ABOVE"
    HARMONY_THIRD_BELOW = "HARMONY_THIRD_BELOW"
    OCTAVE_DOUBLING_BELOW = "OCTAVE_DOUBLING_BELOW"
    ROOT_BASS_PEDAL = "ROOT_BASS_PEDAL"
    CADENCE_RESOLUTION = "CADENCE_RESOLUTION"


@dataclass(frozen=True)
class AlternativeRequest:
    requested_by: str
    source_scope: str
    target_scope: str
    alt_type: AlternativeType
    reason: str


@dataclass(frozen=True)
class GeneratedAlternative:
    id: str
    request: AlternativeRequest
    notes: tuple[Note, ...]
    description: str
    producer: Producer


def _shift_diatonic_third(midi: int, up: bool = True) -> int:
    """Calculates a diatonic third above or below in C-major.
    (3 semitones for minor 3rd, 4 semitones for major 3rd based on scale position).
    """
    scale_step = midi % 12
    if up:
        # Notes where 3rd above is a minor 3rd (3 semitones): D, E, A, B
        # Notes where 3rd above is a major 3rd (4 semitones): C, F, G
        interval = 3 if scale_step in (2, 4, 9, 11) else 4
        return midi + interval
    else:
        # Notes where 3rd below is a minor 3rd (3 semitones): F, G, C, D
        # Notes where 3rd below is a major 3rd (4 semitones): E, A, B
        interval = 3 if scale_step in (5, 7, 0, 2) else 4
        return midi - interval


class AlternativeGenerator:
    """Generates requested musical alternatives with strict generated provenance."""

    @classmethod
    def generate(
        cls,
        request: AlternativeRequest,
        source_notes: Sequence[Note],
    ) -> GeneratedAlternative:
        """Generates an alternative phrase based strictly on an explicit request."""
        text(request.requested_by)
        text(request.source_scope)
        text(request.target_scope)
        text(request.reason, 4096)

        if not source_notes:
            raise ValueError("Cannot generate alternatives for an empty phrase.")

        notes_out = []

        if request.alt_type == AlternativeType.HARMONY_THIRD_ABOVE:
            for n in source_notes:
                if n.pitch == 'rest':
                    notes_out.append(n)
                else:
                    m = pitch_to_midi(n.pitch)
                    new_m = _shift_diatonic_third(m, up=True)
                    notes_out.append(Note(pitch=midi_to_pitch(new_m), duration=n.duration))
            desc = "Diatonic parallel 3rd harmony above source melody"

        elif request.alt_type == AlternativeType.HARMONY_THIRD_BELOW:
            for n in source_notes:
                if n.pitch == 'rest':
                    notes_out.append(n)
                else:
                    m = pitch_to_midi(n.pitch)
                    new_m = _shift_diatonic_third(m, up=False)
                    notes_out.append(Note(pitch=midi_to_pitch(new_m), duration=n.duration))
            desc = "Diatonic parallel 3rd harmony below source melody"

        elif request.alt_type == AlternativeType.OCTAVE_DOUBLING_BELOW:
            for n in source_notes:
                if n.pitch == 'rest':
                    notes_out.append(n)
                else:
                    m = pitch_to_midi(n.pitch)
                    new_m = max(0, m - 12)
                    notes_out.append(Note(pitch=midi_to_pitch(new_m), duration=n.duration))
            desc = "Octave doubling 12 semitones below source melody"

        elif request.alt_type == AlternativeType.ROOT_BASS_PEDAL:
            # Generate C2 bass pedal notes matching the total rhythmic duration
            total_duration = sum(n.duration for n in source_notes)
            # Break into half-note or whole-note pulses
            notes_out.append(Note(pitch="C2", duration=total_duration))
            desc = f"Root C2 bass pedal spanning total phrase duration ({total_duration} quarters)"

        elif request.alt_type == AlternativeType.CADENCE_RESOLUTION:
            # Replicate phrase leading up to final resolving tonic note
            for idx, n in enumerate(source_notes):
                if idx == len(source_notes) - 1:
                    # Resolve to C4 (tonic) with length of final note
                    notes_out.append(Note(pitch="C4", duration=n.duration))
                else:
                    notes_out.append(n)
            desc = "Cadential resolution directing final pitch to tonic C4"

        else:
            raise ValueError(f"Unsupported alternative type: {request.alt_type}")

        return GeneratedAlternative(
            id=uuid4().hex,
            request=request,
            notes=phrase(notes_out),
            description=desc,
            producer=GENERATOR_PRODUCER,
        )

    @classmethod
    def propose_into_workspace(
        cls,
        workspace: Workspace,
        observation_id: str,
        alternative: GeneratedAlternative,
    ) -> Proposal:
        """Records a generated alternative as an uncommitted Proposal in the workspace.
        Origin is permanently stamped as 'generated'.
        """
        prop = workspace.propose(
            observation_id=observation_id,
            scope=alternative.request.target_scope,
            notes=alternative.notes,
            mode="intended",
            uncertainty="HIGH",
            origin="generated",  # Strictly 'generated' provenance
            producer=alternative.producer,
        )
        return prop
