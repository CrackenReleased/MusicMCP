"""Format adapters silo for Music MCP.
Provides bi-directional conversion between reference symbolic phrases (Note, phrase)
and standard music formats (MusicXML, MIDI) with explicit loss disclosure.
"""
from reference.adapters.midi import midi_to_phrase, phrase_to_midi
from reference.adapters.musicxml import musicxml_to_phrase, phrase_to_musicxml

__all__ = [
    'phrase_to_musicxml',
    'musicxml_to_phrase',
    'phrase_to_midi',
    'midi_to_phrase',
]
