"""Standard-library MusicXML 3.1 partwise adapter for Music MCP.
Provides bi-directional conversion between reference Note phrases and MusicXML with loss disclosure.
"""
from dataclasses import dataclass
from fractions import Fraction
import io
from uuid import uuid4
import xml.etree.ElementTree as ET

from reference.core import Diagnostic, MusicError, Note, phrase

VERSION = '0.1.01'

NOTE_TYPES = {
    Fraction(4, 1): 'whole',
    Fraction(2, 1): 'half',
    Fraction(1, 1): 'quarter',
    Fraction(1, 2): 'eighth',
    Fraction(1, 4): '16th',
    Fraction(1, 8): '32nd',
    Fraction(1, 16): '64th',
}


@dataclass(frozen=True)
class LossReport:
    format: str
    direction: str
    lossless: bool
    disclosed_losses: tuple[str, ...]
    notes_processed: int
    summary: str


def _xml_fail(code: str, message: str, action: str = 'Supply valid MusicXML content.'):
    raise MusicError(Diagnostic('MUSICMCP-MUSICXML-' + code, message, action, 'convert', 'adapter', uuid4().hex))


def phrase_to_musicxml(notes: tuple[Note, ...], *, tempo_bpm: int = 120, title: str = 'Music MCP Phrase') -> tuple[str, LossReport]:
    """Export reference phrase to valid MusicXML 3.1 partwise XML document."""
    if not notes:
        _xml_fail('EMPTY_PHRASE', 'Cannot export an empty phrase to MusicXML.')

    divisions = 480  # 480 divisions per quarter note gives exact integer tick for standard durations
    root = ET.Element('score-partwise', version='3.1')
    
    # Work & Title
    work = ET.SubElement(root, 'work')
    work_title = ET.SubElement(work, 'work-title')
    work_title.text = title

    # Part list
    part_list = ET.SubElement(root, 'part-list')
    score_part = ET.SubElement(part_list, 'score-part', id='P1')
    part_name = ET.SubElement(score_part, 'part-name')
    part_name.text = 'Music'

    # Part & Measure
    part = ET.SubElement(root, 'part', id='P1')
    measure = ET.SubElement(part, 'measure', number='1')

    # Attributes
    attrs = ET.SubElement(measure, 'attributes')
    divs_elem = ET.SubElement(attrs, 'divisions')
    divs_elem.text = str(divisions)

    key_elem = ET.SubElement(attrs, 'key')
    fifths_elem = ET.SubElement(key_elem, 'fifths')
    fifths_elem.text = '0'

    time_elem = ET.SubElement(attrs, 'time')
    beats_elem = ET.SubElement(time_elem, 'beats')
    beats_elem.text = '4'
    beat_type = ET.SubElement(time_elem, 'beat-type')
    beat_type.text = '4'

    clef_elem = ET.SubElement(attrs, 'clef')
    sign_elem = ET.SubElement(clef_elem, 'sign')
    sign_elem.text = 'G'
    line_elem = ET.SubElement(clef_elem, 'line')
    line_elem.text = '2'

    losses = [
        'Engraving coordinates and visual layout omitted (semantic export only).',
        'Dynamics, articulation, and expressive markings omitted.',
        'Polyphonic voice assignments defaulted to voice 1.'
    ]

    for n in notes:
        note_elem = ET.SubElement(measure, 'note')
        duration_divs = int(round(float(n.duration) * divisions))

        if n.pitch == 'rest':
            ET.SubElement(note_elem, 'rest')
        else:
            pitch_elem = ET.SubElement(note_elem, 'pitch')
            step = n.pitch[0]
            step_elem = ET.SubElement(pitch_elem, 'step')
            step_elem.text = step

            # Check alter (# or b)
            if len(n.pitch) == 3:
                alter_char = n.pitch[1]
                octave = n.pitch[2]
                alter_val = '1' if alter_char == '#' else '-1'
                alter_elem = ET.SubElement(pitch_elem, 'alter')
                alter_elem.text = alter_val
            else:
                octave = n.pitch[1]

            octave_elem = ET.SubElement(pitch_elem, 'octave')
            octave_elem.text = octave

        dur_elem = ET.SubElement(note_elem, 'duration')
        dur_elem.text = str(duration_divs)

        voice_elem = ET.SubElement(note_elem, 'voice')
        voice_elem.text = '1'

        # Infer type if exact fraction matches
        if n.duration in NOTE_TYPES:
            type_elem = ET.SubElement(note_elem, 'type')
            type_elem.text = NOTE_TYPES[n.duration]

    xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

    report = LossReport(
        format='musicxml',
        direction='export',
        lossless=False,
        disclosed_losses=tuple(losses),
        notes_processed=len(notes),
        summary=f'Exported {len(notes)} notes to MusicXML. Disclosed {len(losses)} omitted formatting features.'
    )
    return xml_str, report


def musicxml_to_phrase(xml_content: str | bytes) -> tuple[tuple[Note, ...], LossReport]:
    """Import MusicXML partwise XML content into reference Note phrase."""
    if isinstance(xml_content, str):
        xml_bytes = xml_content.encode('utf-8')
    else:
        xml_bytes = xml_content

    if not xml_bytes or len(xml_bytes) < 10:
        _xml_fail('INVALID_INPUT', 'Empty or invalid MusicXML byte stream.')

    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        _xml_fail('MALFORMED_XML', f'XML parse failure: {e}')

    if not root.tag.endswith('score-partwise'):
        _xml_fail('UNSUPPORTED_ROOT', f"Expected '<score-partwise>' root, got '<{root.tag}>'.")

    # Find divisions
    div_elem = root.find('.//attributes/divisions')
    divisions = int(div_elem.text) if div_elem is not None and div_elem.text else 1
    if divisions <= 0:
        divisions = 1

    notes_list = []
    losses = [
        'Instrument metadata, clefs, and key signatures discarded.',
        'Visual notation engraving coordinates discarded.'
    ]

    for note_elem in root.findall('.//note'):
        # Check if grace note
        if note_elem.find('grace') is not None:
            losses.append('Omitted grace note (unsupported in reference monophonic grid).')
            continue

        # Check rest
        is_rest = note_elem.find('rest') is not None
        dur_elem = note_elem.find('duration')
        dur_val = int(dur_elem.text) if dur_elem is not None and dur_elem.text else divisions
        duration_frac = Fraction(dur_val, divisions)

        if is_rest:
            pitch_str = 'rest'
        else:
            pitch_elem = note_elem.find('pitch')
            if pitch_elem is None:
                continue
            step_elem = pitch_elem.find('step')
            octave_elem = pitch_elem.find('octave')
            alter_elem = pitch_elem.find('alter')

            step = step_elem.text if step_elem is not None else 'C'
            octave = octave_elem.text if octave_elem is not None else '4'
            alter = int(alter_elem.text) if alter_elem is not None and alter_elem.text else 0

            accidental = '#' if alter > 0 else ('b' if alter < 0 else '')
            pitch_str = f"{step}{accidental}{octave}"

        notes_list.append(Note(pitch=pitch_str, duration=duration_frac))

    if not notes_list:
        _xml_fail('EMPTY_RESULT', 'MusicXML contains zero convertible note events.')

    parsed_phrase = phrase(notes_list)
    report = LossReport(
        format='musicxml',
        direction='import',
        lossless=False,
        disclosed_losses=tuple(set(losses)),
        notes_processed=len(parsed_phrase),
        summary=f'Imported {len(parsed_phrase)} notes from MusicXML. Disclosed {len(set(losses))} discarded elements.'
    )
    return parsed_phrase, report
