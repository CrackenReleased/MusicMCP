# Alternatives Contract: Requested Generated Alternatives with Immutable Provenance

**Contract Version:** 0.1.01  
**Module:** `reference.alternatives`  
**Status:** Implemented Reference Silo  

---

## 1. Purpose and Constitutional Invariants

In accordance with Founding Directive §1 and §4:
**The musician stays the artist. The machine does the notation, calculation, and clerical work.**
When machine assistance is invoked to propose harmonies, countermelodies, or bass lines:

1. **Explicit Request and Permission Only**:
   Machine models and algorithmic generators **must NEVER autonomously inject or generate alternatives** without an explicit, recorded human request. Every generation is linked to an `AlternativeRequest` identifying the requesting artist and intent.
2. **Immutable `origin="generated"` Provenance**:
   Every note proposed by an alternative generator is stamped with `origin="generated"` and its generating producer attribution.
   - **Crucial Invariant**: When a human artist confirms and accepts a generated proposal, the published `Revision` **retains `origin="generated"`**. Machine generation is NEVER rewritten as human authorship.
3. **Protected Lead Material**:
   Generating alternatives in a target scope (e.g. `backing_harmony` or `bass_pedal`) leaves the source phrase, lyrics, and locked scopes completely untouched.
4. **Accept / Reject Workflow**:
   Generated proposals remain strictly uncommitted until explicit human confirmation. Rejecting an alternative leaves zero mutation footprint on the authoritative workspace state.
5. **Zero External Dependencies**:
   Pure Python 3.11+ standard library only.

---

## 2. Alternative Types Specification

| Alternative Type | Musical Description | Target Scope |
|---|---|---|
| `HARMONY_THIRD_ABOVE` | Diatonic parallel 3rd above the melodic line | `vocal_harmony` / `horns` |
| `HARMONY_THIRD_BELOW` | Diatonic parallel 3rd below the melodic line | `vocal_harmony` / `backing` |
| `OCTAVE_DOUBLING_BELOW`| Octave transposition downward (-12 semitones) | `bass_double` / `cello` |
| `ROOT_BASS_PEDAL` | Sustained or rhythmic tonic/dominant bass notes | `bass_line` |
| `CADENCE_RESOLUTION` | Leading-tone and dominant resolving motion (V7 -> I) | `cadence_fill` |
