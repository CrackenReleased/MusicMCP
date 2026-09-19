# Musical format adapters contract — 0.1.01

Owner: Music MCP adapter maintainers. Implementation: `reference/adapters/musicxml.py`, `reference/adapters/midi.py`. Consumer: external music applications (Dorico, MuseScore, Sibelius, DAWs), hardware synthesizers, export pipelines, and conformance tests. Dependencies: Python 3.11+ standard library only (`xml.etree.ElementTree`, `struct`, `io`, `fractions`, `dataclasses`). Zero external dependencies.

## 1. Boundary and isolation principles

Per Founding Directive §2, §6, and SPECIFICATION REP-1:
> **Adapters MUST disclose loss, ambiguity, and unsupported representations before consequential export. Musical concepts MUST NOT be limited globally to the reference profile or any external format.**

1. **Separation of Representations:** An adapter is a translation layer between the in-process authoritative symbolic core (`Note(pitch, duration)`) and an external file encoding (MusicXML or MIDI). An adapter NEVER holds an `AuthoritySession` and CANNOT commit changes to the workspace.
2. **Loss and Ambiguity Disclosure:** Standard file formats (such as MIDI and MusicXML) contain features absent from the minimal reference monophonic phrase (e.g., velocity, instruments, key signatures, lyrics, engraving coordinates), while the reference phrase represents exact rational quarter-note durations. Every export and import produces an immutable `LossReport` disclosing all discarded, default-inferred, or quantized parameters.
3. **Failure Isolation:** Malformed XML, invalid MIDI byte magic, or truncated streams MUST be rejected with explicit `MusicError` diagnostics without corrupting workspace memory.

## 2. Common LossReport record

```python
@dataclass(frozen=True)
class LossReport:
    format: str                    # 'musicxml' | 'midi'
    direction: str                 # 'export' | 'import'
    lossless: bool                 # True if round-trip fidelity is mathematically preserved
    disclosed_losses: tuple[str, ...]  # Explicit list of discarded or approximated elements
    notes_processed: int           # Count of notes handled
    summary: str                   # Human-readable summary
```

## 3. MusicXML Adapter (`reference/adapters/musicxml.py`)

Converts between ordered monophonic phrases and W3C MusicXML 3.1/4.0 partwise score documents:
- **Export (`phrase_to_musicxml`):**
  - Generates well-formed, validating XML with `<score-partwise>`, `<part-list>`, `<measure>`, and `<note>` elements.
  - Automatically calculates optimal division factor (default 480 divisions per quarter note).
  - Encodes pitches with `<step>`, `<octave>`, and `<alter>` (-1 for flat, 1 for sharp). Encodes rests with `<rest/>`.
  - Encodes duration in divisions and computes standard `<type>` tags (`whole`, `half`, `quarter`, `eighth`, `16th`, `32nd`).
  - Discloses omitted layout coordinates, dynamics, and multi-voice polyphony in `LossReport`.
- **Import (`musicxml_to_phrase`):**
  - Parses XML document, extracts `<divisions>`, and converts note durations to exact rational `fractions.Fraction` quarter-note units.
  - Resolves pitch steps, alters, and octaves into standardized pitch strings (e.g. `C#4`, `Bb3`).
  - Discloses discarded layout tags, lyrics, or key/time signature meta in `LossReport`.

## 4. MIDI Adapter (`reference/adapters/midi.py`)

Converts between ordered monophonic phrases and Standard MIDI Files (SMF Format 0 / Type 0):
- **Export (`phrase_to_midi`):**
  - Generates binary SMF containing standard 14-byte `MThd` header chunk and `MTrk` track chunk.
  - Resolution: 480 ticks per quarter note (PPQ).
  - Generates `Set Tempo` meta-event ($60,000,000 / \text{BPM}$ microseconds per quarter).
  - Encodes sequential `Note On` (velocity 64) and `Note Off` events with variable-length quantity (VLQ) delta times.
  - Appends `End of Track` meta-event (`0xFF 0x2F 0x00`).
  - Discloses velocity normalization and enharmonic flattening in `LossReport`.
- **Import (`midi_to_phrase`):**
  - Validates `MThd` and `MTrk` chunk headers.
  - Reads delta times using VLQ decoder, tracks running tick counts, and pairs Note On / Note Off events.
  - Converts tick intervals to exact `Fraction` quarter units based on division header.
  - Maps MIDI numbers (0–127) to standard note spellings (Middle C / 60 = `C4`).
  - Discloses discarded controller data, pitch bends, and polyphonic overlaps in `LossReport`.
