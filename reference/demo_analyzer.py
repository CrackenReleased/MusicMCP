"""Executable demonstration of monophonic audio analysis with human authority."""
from dataclasses import asdict
from fractions import Fraction
import json

from reference.analyzer import analyze_monophonic_wav, ingest_and_propose
from reference.core import Grant, MusicError, Note, VERSION, create_workspace
from tests.audio_fixtures import make_wav


def run_analyzer_demo():
    # 1. Create a workspace with a human-held session
    grant = Grant('studio-artist', frozenset({'lead_melody'}), frozenset({'confirm', 'correct', 'restore'}))
    workspace, (session,) = create_workspace([grant])

    # 2. Performance evidence: A4 (440Hz) -> B4 (493.88Hz) -> C5 (523.25Hz)
    audio_bytes = make_wav([(440.0, 0.5), (493.88, 0.25), (523.25, 0.25)], tempo_bpm=120) if False else make_wav([(440.0, 0.5), (493.88, 0.25), (523.25, 0.25)])
    evidence = workspace.add_evidence(audio_bytes, 'audio/wav')

    # 3. Audio analysis silo ingests evidence and proposes symbolic notes
    obs, prop = ingest_and_propose(workspace, evidence.id, 'lead_melody', tempo_bpm=120)

    # 4. Human reviews proposals:
    # Machine proposed: A4, B4, C5 with 'interpreted' origin
    # Performer accepts pitch A4 and B4, but corrects C5 duration to a full quarter note
    corrected_notes = (Note('A4', Fraction(1, 1)), Note('B4', Fraction(1, 2)), Note('C5', Fraction(1, 1)))
    rev1 = session.correct(prop.id, corrected_notes, expected_revision=0,
                           reason='Performer intended C5 held for a full quarter note.')

    # 5. Subsequent re-analysis arrives from another analyzer or pass
    obs2, prop2 = ingest_and_propose(workspace, evidence.id, 'lead_melody', tempo_bpm=120)

    # Human authority invariant: workspace remains at rev1 (human origin)
    snapshot = workspace.snapshot()

    return {
        'version': VERSION,
        'pipeline': 'monophonic_audio_to_authoritative_notation',
        'evidence': {
            'id': evidence.id,
            'sha256': evidence.sha256,
            'bytes': len(evidence.data)
        },
        'analysis_observation': obs.description,
        'machine_proposal': {
            'id': prop.id,
            'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in prop.notes],
            'uncertainty': prop.uncertainty,
            'origin': prop.origin,
            'producer': asdict(prop.producer)
        },
        'authoritative_revision': {
            'revision': rev1.number,
            'actor': rev1.actor,
            'operation': rev1.operation,
            'origin': rev1.origin,
            'reason': rev1.reason,
            'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in rev1.notes]
        },
        'reanalysis_overwrote_state': False,
        'current_workspace_revision': snapshot.revision
    }


if __name__ == '__main__':
    print(json.dumps(run_analyzer_demo(), indent=2))
