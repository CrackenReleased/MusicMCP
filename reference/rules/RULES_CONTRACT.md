# Rules Contract: Constraint-Aware Arranging and Range Protection

**Contract Version:** 0.1.01  
**Module:** `reference.rules`  
**Status:** Implemented Reference Silo  

---

## 1. Purpose and Constitutional Invariants

Music MCP's philosophy dictates: **The musician stays the artist. The machine does the notation, calculation, and clerical work.**
When arranging, harmonizing, or adapting a phrase for different instruments or voices:
1. **Musician-Defined Constraints**:
   Style guidelines, vocal tessituras, and physical instrument bounds belong to the human artist. The machine audits conformance, alerting the artist to impossible or fatiguing performance demands.
2. **Transposition Invariant**:
   Transposition (shifting pitch by an exact semitone interval) **must NEVER silently authorize revoicing**. The pitch intervals between notes must remain mathematically invariant under transposition. Changing chord inversions or revoicing requires explicit, attributed human authorization.
3. **Warning vs. Blocking Semantics**:
   - `BLOCKING`: Hard constraint (e.g. pitch exceeds physical hardware or absolute biological voice limits). Candidate validation fails fail-closed (`MUSICMCP-CORE-VALIDATION_FAILED`).
   - `WARNING`: Advisory constraint (e.g. pitch falls outside comfortable tessitura, or contains an awkward melodic leap like a tritone). Logged in `RulesReport` for human review without obstructing deliberate artistic choices.
4. **Zero External Dependencies**:
   Pure Python 3.11+ standard library only.

---

## 2. Standard Vocal Range & Tessitura Profiles

| Voice Profile | Absolute MIDI Range | Comfortable Tessitura | Typical Pitches |
|---|---|---|---|
| `SOPRANO` | 60 (C4) to 84 (C6) | 64 (E4) to 79 (G5) | Middle C to High C |
| `ALTO` | 53 (F3) to 74 (D5) | 57 (A3) to 71 (B4) | F below Mid C to D5 |
| `TENOR` | 48 (C3) to 69 (A4) | 52 (E3) to 67 (G4) | C below Mid C to A4 |
| `BASS` | 40 (E2) to 64 (E4) | 43 (G2) to 60 (C4) | Low E to Middle C |

---

## 3. Voice-Leading and Melodic Invariants

1. **Maximum Melodic Leap**:
   Melodic leaps greater than an octave (12 semitones) or unsingable compound intervals trigger a `WARNING` flag.
2. **Parallel Fifths and Octaves**:
   When analyzing two concurrent polyphonic voice streams, consecutive perfect 5ths (7 semitones) or perfect octaves (12 semitones) moving in parallel motion trigger a classical voice-leading advisory.
3. **Tessitura Overflow**:
   Notes residing in the extreme ~10% edges of an artist's range trigger fatigue warnings.
