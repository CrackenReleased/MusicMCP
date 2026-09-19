"""Demonstration of Scoped Multi-Role Collaboration for Music MCP."""
from fractions import Fraction

from reference.collaboration import (
    CollaborationError,
    CollaborationManager,
    Role,
)
from reference.core import (
    MusicError,
    Note,
    Producer,
    phrase,
)


def run_collaboration_demo():
    print("=== Music MCP Multi-Role Collaboration Demonstration ===")

    mgr = CollaborationManager()
    producer = Producer("studio-collab-engine", "0.1.01")

    # Step 1: Register primary artistic scope ownerships
    print("\n1. Registering explicit scope ownerships across disciplines...")
    mgr.register_owner("lead_melody", "composer-joel", Role.COMPOSER, "Thematic vocal lead melody")
    mgr.register_owner("harmony_voices", "composer-joel", Role.COMPOSER, "Vocal harmonies")
    mgr.register_owner("rhythm_groove", "arranger-sarah", Role.ARRANGER, "Bassline and groove")
    print("   [OK] Registered scopes: lead_melody (Joel), harmony_voices (Joel), rhythm_groove (Sarah).")

    # Step 2: Initialize Workspace with multi-actor authority sessions
    actors = [
        ("composer-joel", {"lead_melody", "harmony_voices", "rhythm_groove"}, {"confirm", "correct", "restore"}),
        ("arranger-sarah", {"lead_melody", "harmony_voices", "rhythm_groove"}, {"confirm", "correct", "restore"}),
        ("performer-david", {"lead_melody"}, {"confirm"}),
    ]
    ws, sessions = mgr.build_workspace(actors)
    sess_joel = sessions["composer-joel"]
    sess_sarah = sessions["arranger-sarah"]

    # Step 3: Performer David records lead take -> machine proposes notes
    print("\n2. Ingesting lead vocal performance from Performer David...")
    ev = ws.add_evidence(b"RIFF....WAVE lead audio data", "audio/wav")
    obs = ws.observe(ev.id, "David's vocal take 1", producer=producer)
    lead_notes = phrase([
        Note("C4", Fraction(1, 1)),
        Note("E4", Fraction(1, 1)),
        Note("G4", Fraction(2, 1)),
    ])
    lead_prop = ws.propose(obs.id, "lead_melody", lead_notes, "intended", "HIGH", "interpreted", producer=producer)
    print(f"   Recorded proposal for 'lead_melody': {[n.pitch for n in lead_notes]}")

    # Step 4: Arranger Sarah attempts unauthorized confirmation on Joel's melody -> DENIED
    print("\n3. Testing authority boundary: Arranger attempts to confirm Composer's lead take...")
    try:
        sess_sarah.confirm(lead_prop.id, 0, "Arranger approves lead take")
        assert False, "Should have been blocked!"
    except MusicError as e:
        print(f"   [BLOCKED AS EXPECTED] Collaboration policy denied action: {e.diagnostic.message}")

    # Step 5: Composer Joel reviews and confirms Revision 1
    print("\n4. Composer Joel executes authoritative confirmation...")
    rev1 = sess_joel.confirm(lead_prop.id, 0, "Composer Joel approves vocal take")
    print(f"   [AUTHORITY OK] Published Revision {rev1.number} for '{rev1.scope}' by '{rev1.actor}'.")

    # Step 6: Composer Joel delegates harmony_voices to Arranger Sarah
    print("\n5. Composer Joel delegates 'harmony_voices' scope to Arranger Sarah...")
    grant = mgr.delegate(
        delegator="composer-joel",
        delegatee="arranger-sarah",
        scope="harmony_voices",
        operations={"confirm", "correct"},
        reason="Sarah creates four-part vocal harmony arrangement",
    )
    print(f"   [DELEGATION ISSUED] Grant ID: {grant.id[:12]}... (active: {grant.active})")

    # Step 7: Arranger Sarah creates harmony arrangement under delegation
    print("\n6. Arranger Sarah proposes and confirms harmony arrangement under active delegation...")
    ev_h = ws.add_evidence(b"harmony take audio bytes", "audio/wav")
    obs_h = ws.observe(ev_h.id, "Sarah harmony arrangement", producer=producer)
    h_notes = phrase([
        Note("E4", Fraction(1, 1)),
        Note("G4", Fraction(1, 1)),
        Note("C5", Fraction(2, 1)),
    ])
    h_prop = ws.propose(obs_h.id, "harmony_voices", h_notes, "intended", "HIGH", "interpreted", producer=producer)

    rev2 = sess_sarah.confirm(h_prop.id, 1, "Arranger confirms harmony under delegation")
    print(f"   [AUTHORITY OK] Published Revision {rev2.number} for '{rev2.scope}' by delegatee '{rev2.actor}'.")

    # Step 8: Composer Joel revokes delegation upon project milestone
    print("\n7. Composer Joel revokes delegation upon completion...")
    mgr.revoke("composer-joel", grant.id, "Chorus arrangement finalized")
    print("   [REVOCATION OK] Delegation grant deactivated.")

    # Step 9: Arranger Sarah attempts post-revocation mutation -> DENIED
    print("\n8. Verifying post-revocation safety...")
    try:
        sess_sarah.correct(h_prop.id, lead_notes, 2, "Sarah tries to alter harmony after revocation")
        assert False, "Should have been blocked!"
    except MusicError as e:
        print(f"   [BLOCKED AS EXPECTED] Policy blocked action after revocation: {e.diagnostic.message}")

    print("\n=== Scoped Collaboration Demonstration Verified Successfully ===")


if __name__ == "__main__":
    run_collaboration_demo()
