"""Standard-library Standard MIDI File (SMF Format 0) adapter for Music MCP.
Provides bi-directional conversion between reference Note phrases and standard MIDI files with loss disclosure.
"""
from dataclasses import dataclass
from fractions import Fraction
import io
import struct
from uuid import uuid4

from reference.core import Diagnostic, MusicError, Note, phrase

VERSION = '0.1.01'

NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
PITCH_TO_SEMITONE = {
    'C': 0, 'B#': 0,
    'C#': 1, 'Db': 1,
    'D': 2,
    'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4,
    'F': 5, 'E#': 5,
    'F#': 6, 'Gb': 6,
    'G': 7,
    'G#': 8, 'Ab': 8,
    'A': 9,
    'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11,
}


@dataclass(frozen=True)
class LossReport:
    format: str
    direction: str
    lossless: bool
    disclosed_losses: tuple[str, ...]
    notes_processed: int
    summary: str


def _midi_fail(code: str, message: str, action: str = 'Supply valid Standard MIDI File bytes.'):
    raise MusicError(Diagnostic('MUSICMCP-MIDI-' + code, message, action, 'convert', 'adapter', uuid4().hex))


def encode_vlq(value: int) -> bytes:
    """Encode an integer as a standard MIDI Variable-Length Quantity (VLQ)."""
    if value < 0:
        raise ValueError('VLQ value must be non-negative.')
    buf = bytearray([value & 0x7F])
    value >>= 7
    while value > 0:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(buf))


def decode_vlq(data: bytes, offset: int) -> tuple[int, int]:
    """Decode a variable-length quantity from data at offset. Returns (value, next_offset)."""
    value = 0
    while offset < len(data):
        b = data[offset]
        offset += 1
        value = (value << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    return value, offset


def pitch_to_midi_number(pitch: str) -> int:
    """Convert standard pitch string (e.g. C4, A#3, Bb5) to MIDI note number (0-127)."""
    if len(pitch) == 3:
        name = pitch[:2]
        octave = int(pitch[2])
    else:
        name = pitch[0]
        octave = int(pitch[1])

    semitone = PITCH_TO_SEMITONE[name]
    midi_num = (octave + 1) * 12 + semitone
    if not (0 <= midi_num <= 127):
        _midi_fail('OUT_OF_RANGE', f"Pitch '{pitch}' maps to MIDI note {midi_num}, outside 0-127 bounds.")
    return midi_num


def midi_number_to_pitch(num: int) -> str:
    """Convert MIDI note number (0-127) to standard pitch name."""
    if not (0 <= num <= 127):
        _midi_fail('OUT_OF_RANGE', f"MIDI number {num} outside standard 0-127 bounds.")
    octave = (num // 12) - 1
    idx = num % 12
    return f"{NOTE_NAMES[idx]}{octave}"


def phrase_to_midi(notes: tuple[Note, ...], *, tempo_bpm: int = 120, ticks_per_quarter: int = 480) -> tuple[bytes, LossReport]:
    """Export reference phrase to Standard MIDI File (SMF Format 0) binary bytes."""
    if not notes:
        _midi_fail('EMPTY_PHRASE', 'Cannot export an empty phrase to MIDI.')

    track_bytes = bytearray()

    # 1. Set Tempo Meta Event (microseconds per quarter note)
    us_per_quarter = int(round(60_000_000.0 / float(tempo_bpm)))
    tempo_data = struct.pack('>I', us_per_quarter)[1:]  # 3 bytes
    track_bytes.extend(encode_vlq(0))  # delta time 0
    track_bytes.extend(b'\xFF\x51\x03' + tempo_data)

    accumulated_rest_ticks = 0
    losses = [
        'Velocity standardized to 64 for all notes.',
        'Enharmonic spelling flattened to MIDI pitch numbers (C# and Db are indistinguishable).',
        'Channel assignment fixed to MIDI Channel 0.'
    ]

    for n in notes:
        ticks = int(round(float(n.duration) * ticks_per_quarter))
        if n.pitch == 'rest':
            accumulated_rest_ticks += ticks
        else:
            midi_num = pitch_to_midi_number(n.pitch)
            # Note On event
            track_bytes.extend(encode_vlq(accumulated_rest_ticks))
            track_bytes.extend(bytes([0x90, midi_num, 64]))  # Note On, channel 0, vel 64
            accumulated_rest_ticks = 0

            # Note Off event
            track_bytes.extend(encode_vlq(ticks))
            track_bytes.extend(bytes([0x80, midi_num, 0]))   # Note Off, channel 0, vel 0

    # End of Track Meta Event
    track_bytes.extend(encode_vlq(accumulated_rest_ticks))
    track_bytes.extend(b'\xFF\x2F\x00')

    # Header Chunk (Format 0, 1 track, ticks_per_quarter)
    header_chunk = struct.pack('>4sIHHH', b'MThd', 6, 0, 1, ticks_per_quarter)
    track_chunk = struct.pack('>4sI', b'MTrk', len(track_bytes)) + bytes(track_bytes)

    midi_file = header_chunk + track_chunk

    report = LossReport(
        format='midi',
        direction='export',
        lossless=False,
        disclosed_losses=tuple(losses),
        notes_processed=len(notes),
        summary=f'Exported {len(notes)} notes to Standard MIDI File (SMF Format 0). Disclosed {len(losses)} MIDI-specific conventions.'
    )
    return bytes(midi_file), report


def midi_to_phrase(midi_bytes: bytes) -> tuple[tuple[Note, ...], LossReport]:
    """Import Standard MIDI File (SMF Format 0 or 1) binary bytes into reference Note phrase."""
    if len(midi_bytes) < 14:
        _midi_fail('INVALID_HEADER', 'MIDI byte stream is too short for valid SMF header.')

    magic, hdr_len, fmt, ntracks, ppq = struct.unpack('>4sIHHH', midi_bytes[:14])
    if magic != b'MThd' or hdr_len != 6:
        _midi_fail('INVALID_HEADER', "Invalid MIDI header chunk: expected 'MThd'.")

    # Find first track chunk
    offset = 14
    track_data = None
    while offset + 8 <= len(midi_bytes):
        chk_magic, chk_len = struct.unpack('>4sI', midi_bytes[offset:offset + 8])
        offset += 8
        if chk_magic == b'MTrk':
            track_data = midi_bytes[offset:offset + chk_len]
            break
        offset += chk_len

    if track_data is None:
        _midi_fail('MISSING_TRACK', 'No valid MTrk track chunk found in MIDI file.')

    # Parse MIDI events
    ptr = 0
    running_status = 0
    events = []
    losses = [
        'Polyphonic simultaneous notes serialized or filtered to monophonic line.',
        'Controller events, pitch bends, and program changes discarded.',
        'Velocities discarded in symbolic Note model.'
    ]

    while ptr < len(track_data):
        delta, ptr = decode_vlq(track_data, ptr)
        if ptr >= len(track_data):
            break
        b = track_data[ptr]
        if b & 0x80:
            status = b
            ptr += 1
            running_status = status
        else:
            status = running_status

        msg_type = status & 0xF0

        # Meta Event
        if status == 0xFF:
            meta_type = track_data[ptr]
            ptr += 1
            length, ptr = decode_vlq(track_data, ptr)
            meta_payload = track_data[ptr:ptr + length]
            ptr += length
            if meta_type == 0x2F:  # End of Track
                break
        # SysEx
        elif status in (0xF0, 0xF7):
            length, ptr = decode_vlq(track_data, ptr)
            ptr += length
        # Channel Voice Messages
        elif msg_type in (0x80, 0x90):  # Note Off or Note On
            note_num = track_data[ptr]
            vel = track_data[ptr + 1]
            ptr += 2
            is_on = (msg_type == 0x90 and vel > 0)
            events.append((delta, 'on' if is_on else 'off', note_num))
        elif msg_type in (0xA0, 0xB0, 0xE0):  # Aftertouch, CC, Pitch Bend (2 data bytes)
            ptr += 2
        elif msg_type in (0xC0, 0xD0):  # Program Change, Channel Pressure (1 data byte)
            ptr += 1

    # Convert events to Notes and rests
    notes_list = []
    active_note = None
    accumulated_ticks = 0

    for delta, ev_type, note_num in events:
        accumulated_ticks += delta
        if ev_type == 'on':
            if active_note is not None and accumulated_ticks > 0:
                dur_frac = Fraction(accumulated_ticks, ppq)
                notes_list.append(Note(pitch=midi_number_to_pitch(active_note), duration=dur_frac))
                accumulated_ticks = 0
            elif active_note is None and accumulated_ticks > 0:
                dur_frac = Fraction(accumulated_ticks, ppq)
                notes_list.append(Note(pitch='rest', duration=dur_frac))
                accumulated_ticks = 0
            active_note = note_num
        elif ev_type == 'off':
            if active_note == note_num and accumulated_ticks > 0:
                dur_frac = Fraction(accumulated_ticks, ppq)
                notes_list.append(Note(pitch=midi_number_to_pitch(active_note), duration=dur_frac))
                active_note = None
                accumulated_ticks = 0

    if not notes_list:
        _midi_fail('EMPTY_RESULT', 'MIDI file contained zero convertible note events.')

    parsed_phrase = phrase(notes_list)
    report = LossReport(
        format='midi',
        direction='import',
        lossless=False,
        disclosed_losses=tuple(set(losses)),
        notes_processed=len(parsed_phrase),
        summary=f'Imported {len(parsed_phrase)} notes from MIDI. Disclosed {len(set(losses))} discarded parameters.'
    )
    return parsed_phrase, report
