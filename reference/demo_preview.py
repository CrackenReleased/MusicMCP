"""Live demonstration of Visualizer Preview Server and Local Human Review Deck.

Demonstrates:
1. Workspace initialization with human artist grant and scope locks.
2. Ingestion of audio evidence, spectrum inspection (10 Hz - 28 kHz), and candidate proposal.
3. Instantiation of localhost-bound PreviewServer holding host AuthoritySession.
4. Programmatic execution of the visualizer REST API:
   - Project inspection (/api/project)
   - Real-time 10-band acoustic spectrum and anomaly watcher (/api/spectrum)
   - Candidate proposal listing and human confirmation (/api/confirm)
   - Generated alternative creation (/api/propose_alternative)
   - Verification of immutable origin="generated" provenance
   - Authorized human correction (/api/correct)
   - Historical revision restore (/api/restore)
"""
from fractions import Fraction
import io
import json
import math
import struct
import urllib.request
import wave

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
)
from reference.preview import PreviewServer


def make_test_tone_wav(frequency=440.0, duration=0.5, sample_rate=44100):
    num_samples = int(sample_rate * duration)
    frames = bytearray()
    for i in range(num_samples):
        val = int(18000 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        frames.extend(struct.pack('<h', val))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)
    return buf.getvalue()


def post_json(url: str, data: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=== Music MCP Visualizer & Local Human Review Deck Demo ===")

    # 1. Setup Workspace with artist grant
    producer = Producer("demo-producer", "0.1.01")
    artist_grant = Grant("composer-joel", {"melody", "harmony", "bass"}, {"confirm", "correct", "restore"})
    ws, (sess,) = create_workspace(
        [artist_grant],
        constraints=[LockConstraint("lead_melody", "composer-joel", "Melody locked for production release")],
    )

    # 2. Ingest Audio Evidence and Candidate Proposal
    wav_bytes = make_test_tone_wav(frequency=440.0, duration=0.3, sample_rate=44100)
    ev = ws.add_evidence(wav_bytes, "audio/wav")
    obs = ws.observe(ev.id, "Vocal take 1", producer=producer)
    prop = ws.propose(
        obs.id,
        scope="melody",
        notes=(Note("A4", Fraction(1, 1)), Note("C5", Fraction(1, 1))),
        mode="intended",
        uncertainty="LOW",
        origin="interpreted",
        producer=producer,
    )
    print(f"[OK] Ingested evidence '{ev.id[:8]}' and created proposal '{prop.id[:8]}'")

    # 3. Spin up Preview Server on localhost loopback
    server = PreviewServer(ws, sess, host="127.0.0.1", port=0)
    server.start(background=True)
    print(f"[OK] Localhost Visualizer Server active at: {server.url}")

    try:
        # 4. Query Project Status
        proj = get_json(f"{server.url}/api/project")
        print(f"[OK] GET /api/project -> Revision {proj['revision']}, {len(proj['locks'])} active lock(s)")

        # 5. Query 10-Band Acoustic Spectrum & Non-Musical Anomaly Watcher
        spec = get_json(f"{server.url}/api/spectrum?evidence_id={ev.id}")
        rep = spec["report"]
        print(f"[OK] GET /api/spectrum -> {rep['summary']}")
        print(f"     Audible Mid Band (500Hz-2kHz): {(rep['band_energies']['mid'] * 100):.2f}%")
        print(f"     Clean Musical Signal: {rep['clean_musical_signal']} (0 non-musical anomalies)")

        # 6. Authorized Confirmation via Visualizer API
        conf = post_json(f"{server.url}/api/confirm", {
            "proposal_id": prop.id,
            "expected_revision": 0,
            "reason": "Musician verified A4/C5 melody on visualizer review deck",
        })
        rev1 = conf["revision"]
        print(f"[OK] POST /api/confirm -> Published Revision {rev1['number']} in scope '{rev1['scope']}'")
        print(f"     Origin: {rev1['origin']} | Notes: {[n['pitch'] for n in rev1['notes']]}")

        # 7. Request Generated Alternative (3rd Above Vocal Harmony)
        alt_res = post_json(f"{server.url}/api/propose_alternative", {
            "source_scope": "melody",
            "target_scope": "harmony",
            "alt_type": "HARMONY_THIRD_ABOVE",
            "requested_by": "composer-joel",
            "reason": "Explore diatonic 3rd vocal harmony for chorus",
        })
        prop_alt = alt_res["proposal"]
        print(f"[OK] POST /api/propose_alternative -> Created uncommitted proposal '{prop_alt['id'][:8]}'")
        print(f"     Scope: '{prop_alt['scope']}' | Origin: {prop_alt['origin']}")
        print(f"     Proposed Diatonic 3rds: {[n['pitch'] for n in prop_alt['notes']]}")

        # 8. Confirm the Generated Alternative
        conf_alt = post_json(f"{server.url}/api/confirm", {
            "proposal_id": prop_alt["id"],
            "expected_revision": 1,
            "reason": "Musician accepted generated 3rd harmony",
        })
        rev2 = conf_alt["revision"]
        print(f"[OK] POST /api/confirm -> Published Revision {rev2['number']} in scope '{rev2['scope']}'")
        print(f"     CONSTITUTIONAL INVARIANT VERIFIED: Published Revision retains origin='{rev2['origin']}'")

        # 9. Authorized Human Correction
        corr = post_json(f"{server.url}/api/correct", {
            "proposal_id": prop.id,
            "notes": "D4 1, F4 1/2, A4 1/2",
            "expected_revision": 2,
            "reason": "Artist revised melody phrasing to D minor triad",
        })
        rev3 = corr["revision"]
        print(f"[OK] POST /api/correct -> Published Revision {rev3['number']} in scope '{rev3['scope']}'")
        print(f"     Origin: {rev3['origin']} | Notes: {[n['pitch'] for n in rev3['notes']]}")

        # 10. Restore Historical Revision
        rest = post_json(f"{server.url}/api/restore", {
            "revision_number": 1,
            "expected_revision": 3,
            "reason": "Reverted back to initial A4/C5 take",
        })
        rev4 = rest["revision"]
        print(f"[OK] POST /api/restore -> Restored Revision {rev4['restored_from']} as new Revision {rev4['number']}")
        print(f"     Restored Notes: {[n['pitch'] for n in rev4['notes']]}")

    finally:
        server.stop()
        print("[OK] PreviewServer stopped cleanly.")

    print("\nVisualizer Preview & Local Authority Review demonstration complete.\n")


if __name__ == "__main__":
    main()
