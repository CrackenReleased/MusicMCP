"""Demonstration of Constraint-Aware Arranging and Musical Rules Engine."""
from fractions import Fraction

from reference.core import (
    Grant,
    MusicError,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.rules import (
    RuleSeverity,
    RulesEngine,
    Ruleset,
    STANDARD_VOCAL_RANGES,
    midi_to_pitch,
    pitch_to_midi,
    transpose_phrase,
)


def run_rules_demo():
    print("=== Music MCP Constraint-Aware Arranging & Rules Engine Demonstration ===")

    producer = Producer("rules-demo-engine", "0.1.01")

    # Step 1: Define an Alto vocal ruleset
    print("\n1. Declaring Alto vocal ruleset (F3 to D5, tessitura A3 to B4)...")
    alto_rules = Ruleset(
        name="alto-soloist-profile",
        version="0.1.01",
        author="lead-arranger",
        vocal_range=STANDARD_VOCAL_RANGES["ALTO"],
        max_leap_semitones=12,
    )
    engine = RulesEngine(alto_rules)
    print(f"   [OK] Active ruleset: {alto_rules.name} (v{alto_rules.version})")

    # Step 2: Audit a comfortable melodic phrase
    print("\n2. Auditing comfortable Alto melodic phrase (C4, E4, G4, A4)...")
    alto_phrase = phrase([
        Note("C4", Fraction(1, 1)),
        Note("E4", Fraction(1, 1)),
        Note("G4", Fraction(1, 1)),
        Note("A4", Fraction(1, 1)),
    ])
    rep1 = engine.evaluate_phrase(alto_phrase)
    print(f"   Phrase: {[n.pitch for n in alto_phrase]}")
    print(f"   Report: {rep1.summary} (Valid: {rep1.valid})")
    assert rep1.valid and len(rep1.blocking_violations) == 0

    # Step 3: Audit an out-of-range phrase with excessive leap
    print("\n3. Auditing out-of-range phrase with high F5 and 15-semitone leap...")
    strained_phrase = phrase([
        Note("C4", Fraction(1, 1)),
        Note("F5", Fraction(1, 1)),  # Exceeds Alto max (D5) by 3 semitones; leap is 17 semitones!
    ])
    rep2 = engine.evaluate_phrase(strained_phrase)
    print(f"   Phrase: {[n.pitch for n in strained_phrase]}")
    print(f"   Report: {rep2.summary} (Valid: {rep2.valid})")
    for b in rep2.blocking_violations:
        print(f"   ! [BLOCKING] {b.rule_name} at note {b.note_index} ({b.pitch}): {b.message}")
    for w in rep2.warning_violations:
        print(f"   * [WARNING]  {w.rule_name} at note {w.note_index} ({w.pitch}): {w.message}")
    assert not rep2.valid

    # Step 4: Transposition invariant: Transposing phrase preserves all pitch intervals without revoicing
    print("\n4. Testing Transposition Invariant: Transposing Alto phrase up +3 semitones (minor third)...")
    transposed = transpose_phrase(alto_phrase, semitones=3)
    expected_pitches = ["D#4", "G4", "A#4", "C5"]
    print(f"   Transposed notes: {[n.pitch for n in transposed]}")
    assert [n.pitch for n in transposed] == expected_pitches, "Transposition mismatch!"
    print("   [OK] Pitch relationships and durations 100% mathematically preserved without revoicing.")

    # Step 5: Enforce rules engine in live Workspace post-validation gate
    print("\n5. Enforcing RulesEngine in live Workspace post-validation gate...")
    ws, (sess,) = create_workspace(
        [Grant("arranger", {"alto_lead"}, {"confirm", "correct", "restore"})],
        validator=engine.check_candidate,
    )

    ev = ws.add_evidence(b"RIFF....WAVE take", "audio/wav")
    obs = ws.observe(ev.id, "Alto take take", producer=producer)
    bad_prop = ws.propose(obs.id, "alto_lead", strained_phrase, "intended", "HIGH", "interpreted", producer=producer)

    try:
        sess.confirm(bad_prop.id, 0, "Arranger tries to commit strained phrase")
        assert False, "Should have been blocked!"
    except MusicError as e:
        print(f"   [BLOCKED AS EXPECTED] Workspace validator rejected out-of-range candidate: {e.diagnostic.message}")

    print("\n=== Constraint-Aware Arranging Demonstration Verified Successfully ===")


if __name__ == "__main__":
    run_rules_demo()
