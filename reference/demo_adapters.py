"""Demonstration of MusicXML and MIDI format adapters with explicit loss disclosure."""
from fractions import Fraction

from reference.adapters.midi import midi_to_phrase, phrase_to_midi
from reference.adapters.musicxml import musicxml_to_phrase, phrase_to_musicxml
from reference.core import Note, phrase


def run_adapters_demo():
    print("=== Music MCP Format Adapters Demonstration ===")

    # 1. Authoritative phrase in reference model
    original_phrase = phrase([
        Note('C4', Fraction(1, 1)),      # Quarter note C4
        Note('E4', Fraction(1, 1)),      # Quarter note E4
        Note('G4', Fraction(1, 2)),      # Eighth note G4
        Note('rest', Fraction(1, 2)),    # Eighth rest
        Note('C5', Fraction(2, 1)),      # Half note C5
    ])
    print(f"1. Original Symbolic Phrase: {[f'{n.pitch} ({n.duration})' for n in original_phrase]}")

    # 2. Export to MusicXML
    xml_str, xml_exp_report = phrase_to_musicxml(original_phrase, tempo_bpm=120, title='Adapters Demo')
    print(f"\n2. Export to MusicXML ({len(xml_str)} chars):")
    print(f"   Summary: {xml_exp_report.summary}")
    for loss in xml_exp_report.disclosed_losses:
        print(f"   - Disclosed: {loss}")

    # 3. Round-trip Import from MusicXML
    reimported_xml_phrase, xml_imp_report = musicxml_to_phrase(xml_str)
    print(f"\n3. Re-imported from MusicXML: {[f'{n.pitch} ({n.duration})' for n in reimported_xml_phrase]}")
    assert reimported_xml_phrase == original_phrase, "MusicXML round-trip mismatch!"
    print("   [OK] MusicXML round-trip verified 100% mathematically exact.")

    # 4. Export to Standard MIDI File
    midi_bytes, midi_exp_report = phrase_to_midi(original_phrase, tempo_bpm=120)
    print(f"\n4. Export to MIDI ({len(midi_bytes)} bytes):")
    print(f"   Summary: {midi_exp_report.summary}")
    for loss in midi_exp_report.disclosed_losses:
        print(f"   - Disclosed: {loss}")

    # 5. Round-trip Import from MIDI
    reimported_midi_phrase, midi_imp_report = midi_to_phrase(midi_bytes)
    print(f"\n5. Re-imported from MIDI: {[f'{n.pitch} ({n.duration})' for n in reimported_midi_phrase]}")
    assert reimported_midi_phrase == original_phrase, "MIDI round-trip mismatch!"
    print("   [OK] MIDI round-trip verified 100% mathematically exact.")

    print("\n=== Format Adapters Demonstration Verified Successfully ===")


if __name__ == '__main__':
    run_adapters_demo()
