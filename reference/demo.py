"""Executable synthetic confirmation story, not a transcription demonstration."""
from dataclasses import asdict
from fractions import Fraction
from io import BytesIO
import json
import math
import struct
import wave

from reference.core import Grant, MusicError, Note, Producer, VERSION, create_workspace

PRODUCER = Producer('synthetic-demo-fixture', '1')


def run():
    # Owned synthetic fixture: a short A4 tone, generated in memory, never saved.
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as recording:
        recording.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        recording.writeframes(b''.join(struct.pack('<h', int(8000 * math.sin(2 * math.pi * 440 * n / 8000)))
                                      for n in range(1600)))
    workspace, (human,) = create_workspace([Grant('demo-musician', {'opening'}, {'confirm', 'correct', 'restore'})])
    evidence = workspace.add_evidence(buffer.getvalue(), 'audio/wav')
    observation = workspace.observe(evidence.id, 'Synthetic demonstration: supplied A4 observation; no analyzer ran.', producer=PRODUCER)
    triplet = workspace.propose(observation.id, 'opening', (Note('A4', Fraction(1, 3)),),
                                'intended', 'AMBIGUOUS', 'interpreted', producer=PRODUCER)
    eighth = workspace.propose(observation.id, 'opening', (Note('A4', Fraction(1, 2)),),
                               'intended', 'AMBIGUOUS', 'interpreted', producer=PRODUCER)
    before = workspace.snapshot().revision
    human.confirm(triplet.id, 0, 'Demonstration host explicitly accepts the first reading')
    human.correct(eighth.id, eighth.notes, 1, 'I intended a straight eighth note')
    workspace.propose(observation.id, 'opening', triplet.notes, 'intended', 'HIGH', 'interpreted', producer=PRODUCER)
    after_analysis = workspace.snapshot()
    try:
        human.confirm(triplet.id, 1, 'Stale confirmation attempt')
    except MusicError as error:
        rejected = asdict(error.diagnostic)
    return {
        'version': VERSION,
        'demonstration': 'Synthetic evidence and supplied interpretations; no audio analysis performed',
        'evidence_bytes': len(evidence.data), 'evidence_sha256': evidence.sha256,
        'revision_before_human_action': before,
        'revision_after_correction_and_reanalysis': after_analysis.revision,
        'authoritative_note': {'pitch': after_analysis.phrases[0].notes[0].pitch,
                               'quarter_units': str(after_analysis.phrases[0].notes[0].duration)},
        'material_origin': after_analysis.phrases[0].origin,
        'interpretation_producer': asdict(workspace.proposal(after_analysis.phrases[0].proposal_id).producer),
        'history_operations': [entry.operation for entry in after_analysis.history],
        'stale_operation': rejected,
    }


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
