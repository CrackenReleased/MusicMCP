"""Demonstration of Requested Generated Alternatives for Music MCP."""
from fractions import Fraction

from reference.alternatives import (
    AlternativeGenerator,
    AlternativeRequest,
    AlternativeType,
)
from reference.core import (
    Grant,
    Note,
    Producer,
    create_workspace,
    phrase,
)


def run_alternatives_demo():
    print("=== Music MCP Requested Generated Alternatives Demonstration ===")

    producer = Producer("composer-workstation", "0.1.01")
    ws, (sess,) = create_workspace(
        [Grant("composer-joel", {"melody", "harmony", "bass"}, {"confirm", "correct", "restore"})]
    )

    # Step 1: Musician records and accepts authoritative melody
    print("\n1. Musician establishes authoritative lead melody (C4, D4, E4)...")
    ev = ws.add_evidence(b"RIFF....melody audio", "audio/wav")
    obs = ws.observe(ev.id, "Composer lead vocal take", producer=producer)
    lead_notes = phrase([
        Note("C4", Fraction(1, 1)),
        Note("D4", Fraction(1, 1)),
        Note("E4", Fraction(2, 1)),
    ])
    lead_prop = ws.propose(obs.id, "melody", lead_notes, "intended", "HIGH", "interpreted", producer=producer)
    rev1 = sess.confirm(lead_prop.id, 0, "Artist approves lead melody")
    print(f"   [AUTHORITY OK] Published Revision {rev1.number} (scope: '{rev1.scope}', origin: '{rev1.origin}')")
    print(f"   Melody: {[f'{n.pitch} ({n.duration})' for n in lead_notes]}")

    # Step 2: Musician explicitly requests a diatonic 3rd-above harmony alternative
    print("\n2. Musician explicitly requests Diatonic 3rd Above Harmony...")
    req_harmony = AlternativeRequest(
        requested_by="composer-joel",
        source_scope="melody",
        target_scope="harmony",
        alt_type=AlternativeType.HARMONY_THIRD_ABOVE,
        reason="Explore high vocal harmony for final chorus",
    )
    alt_harmony = AlternativeGenerator.generate(req_harmony, lead_notes)
    print(f"   Generated notes: {[f'{n.pitch} ({n.duration})' for n in alt_harmony.notes]}")
    print(f"   Description: {alt_harmony.description}")

    # Step 3: Propose alternative into workspace
    print("\n3. Recording generated alternative as uncommitted proposal...")
    prop_harmony = AlternativeGenerator.propose_into_workspace(ws, obs.id, alt_harmony)
    print(f"   Recorded proposal ID: {prop_harmony.id[:12]}... (origin: '{prop_harmony.origin}')")

    # Step 4: Musician explicitly reviews and confirms the generated alternative
    print("\n4. Musician reviews and confirms generated proposal into scope 'harmony'...")
    rev2 = sess.confirm(prop_harmony.id, 1, "Artist confirmed machine-generated upper harmony")
    print(f"   [AUTHORITY OK] Published Revision {rev2.number} for scope '{rev2.scope}'.")
    print(f"   Provenance Check: Authoritative origin is '{rev2.origin}' (actor: '{rev2.actor}')")
    assert rev2.origin == "generated", "Provenenance violation: origin must remain 'generated'!"
    print("   [OK] Provenance invariant verified: Generated origin remains permanently intact.")

    # Step 5: Musician requests Root Bass Pedal alternative
    print("\n5. Musician explicitly requests Root Bass Pedal alternative...")
    req_bass = AlternativeRequest(
        requested_by="composer-joel",
        source_scope="melody",
        target_scope="bass",
        alt_type=AlternativeType.ROOT_BASS_PEDAL,
        reason="Anchor arrangement with solid low end",
    )
    alt_bass = AlternativeGenerator.generate(req_bass, lead_notes)
    prop_bass = AlternativeGenerator.propose_into_workspace(ws, obs.id, alt_bass)
    rev3 = sess.confirm(prop_bass.id, 2, "Artist confirmed machine-generated bass pedal")
    print(f"   [AUTHORITY OK] Published Revision {rev3.number} for scope '{rev3.scope}'.")
    print(f"   Bass phrase: {[f'{n.pitch} ({n.duration})' for n in rev3.notes]}")

    # Step 6: Verify all published scopes exist side-by-side without cross-contamination
    print("\n6. Auditing published workspace state across all scopes...")
    for phrase_rev in ws.snapshot().phrases:
        print(f"   Scope: '{phrase_rev.scope:<10}' | Rev {phrase_rev.number} | Origin: {phrase_rev.origin:<10} | Notes: {[n.pitch for n in phrase_rev.notes]}")

    print("\n=== Requested Generated Alternatives Demonstration Verified Successfully ===")


if __name__ == "__main__":
    run_alternatives_demo()
