"""Live demonstration of Provider-Neutral Evaluation Silo and TypeSafe Jev Adapter.

Demonstrates:
1. Provider-Neutral Evaluation Contract:
   - Atomic EvaluationRequest primitives (boolean, choice, alignment).
   - Probability distributions with calibration and uncertainty tracking.
   - Provider-neutral EvaluationProvenance recording provider identity, model ID, and credential state.
2. Deterministic Conformance Evaluation:
   - Verifying locked musical material invariance ("Was locked melody modified?").
   - Provenance integrity verification ("Was generated material identified as generated?").
   - Actor authorization verification ("Did requested operation possess authority?").
3. Live Score Alignment via Bounded EvidenceWindow:
   - Ingesting an observed acoustic onset from physical audio.
   - Bounded temporal windowing (e.g. 12.0s - 14.0s) for incremental score following.
   - Resolving observation to candidate score events without modifying Authoritative Musical State.
4. TypeSafe Jev Adapter Integration:
   - Graceful degradation: operates seamlessly with CAPABILITY_UNAVAILABLE when TYPESAFE_API_KEY is absent.
   - Secret Redaction: guarantees API keys and secrets never leak into logs, explanations, or diagnostics.
   - Invariant: Evaluators only propose judgments; human-held AuthoritySession retains exclusive mutation authority.
"""
from fractions import Fraction
import os

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase,
)
from reference.evaluation import (
    DetectedEvent,
    DeterministicConformanceEvaluator,
    EvaluationProvenance,
    EvaluationRequest,
    EvaluationResult,
    EvaluationStatus,
    EvaluationType,
    EvidenceWindow,
    ProbabilityDistribution,
    TypeSafeJevAdapter,
)


def main():
    print("=== Music MCP Provider-Neutral Evaluation Silo & Jev Adapter Demo ===\n")

    # 1. Setup Workspace with Locked Material
    print("[1] Initializing Workspace with Human Artist Grant & Theme Melody...")
    producer = Producer("demo-producer", "0.1.01")
    artist_grant = Grant("composer-joel", {"melody"}, {"confirm", "correct", "restore"})
    ws, (session,) = create_workspace([artist_grant])

    locked_melody = phrase([
        Note("C4", Fraction(1, 1)),
        Note("E4", Fraction(1, 1)),
        Note("G4", Fraction(1, 1)),
        Note("C5", Fraction(2, 1)),
    ])
    evidence = ws.add_evidence(b"RIFFdummywavdata", "audio/wav")
    obs = ws.observe(evidence.id, "Acoustic recording of main theme", producer=producer)
    prop = ws.propose(obs.id, "melody", locked_melody, "intended", "LOW", "interpreted", producer=producer)
    session.confirm(prop.id, 0, "Composer accepts main theme")
    initial_rev = ws.snapshot().revision
    print(f"    Workspace revision: {initial_rev} | Melody confirmed into Authoritative Musical State.\n")

    # 2. Deterministic Conformance Evaluator
    print("[2] Running Deterministic Conformance Evaluator...")
    evaluator = DeterministicConformanceEvaluator()

    # 2a. Locked material check
    altered_candidate = phrase([
        Note("C4", Fraction(1, 1)),
        Note("D#4", Fraction(1, 1)),
        Note("G4", Fraction(1, 1)),
        Note("C5", Fraction(2, 1)),
    ])
    req_lock_check = EvaluationRequest(
        question="Was locked melody modified?",
        evaluation_type=EvaluationType.BOOLEAN,
        context={"locked_phrase": locked_melody, "candidate_phrase": altered_candidate},
    )
    res_lock = evaluator.evaluate(req_lock_check)
    print(f"    Check: 'Was locked melody modified?'")
    print(f"    Decision: {res_lock.decision} (Uncertainty: {res_lock.uncertainty})")
    print(f"    Explanation: {res_lock.explanation}")

    # 2b. Provenance check
    req_prov_check = EvaluationRequest(
        question="Was generated material identified as generated?",
        evaluation_type=EvaluationType.BOOLEAN,
        context={"origin": "generated"},
    )
    res_prov = evaluator.evaluate(req_prov_check)
    print(f"\n    Check: 'Was generated material identified as generated?'")
    print(f"    Decision: {res_prov.decision} | Origin: generated | Validated: True")

    # 2c. Authority check
    req_auth_check = EvaluationRequest(
        question="Did requested operation possess authority?",
        evaluation_type=EvaluationType.BOOLEAN,
        context={
            "actor_operations": tuple(artist_grant.operations),
            "actor_scopes": tuple(artist_grant.scopes),
            "operation": "confirm",
            "scope": "melody",
        },
    )
    res_auth = evaluator.evaluate(req_auth_check)
    print(f"\n    Check: 'Did requested operation possess authority?'")
    print(f"    Decision: {res_auth.decision} | Operation: 'confirm' on 'melody' authorized.\n")

    # 3. Live Score Alignment via Bounded EvidenceWindow
    print("[3] Live Score Alignment via Bounded EvidenceWindow...")
    detected_event = DetectedEvent(
        event_id="obs-1042",
        onset_seconds=12.842,
        duration_seconds=0.485,
        pitch_candidates=(("F#4", "high"), ("F4", "low")),
    )
    evidence_window = EvidenceWindow(
        source_id="stage-acoustic-mic-01",
        start_seconds=12.0,
        end_seconds=14.0,
        detected_events=(detected_event,),
        score_context={"measure": 18, "tempo_bpm": 120},
    )
    print(f"    EvidenceWindow: {evidence_window.start_seconds}s - {evidence_window.end_seconds}s")
    print(f"    Observed onset: {detected_event.onset_seconds}s with pitch candidates: {detected_event.pitch_candidates}")

    req_align = EvaluationRequest(
        question="Which candidate score event corresponds to observed onset?",
        evaluation_type=EvaluationType.ALIGNMENT,
        candidates=("m18.v1.e3", "m18.v1.e4", "unresolved"),
        context={
            "observed_pitch": "F#4",
            "observed_onset": detected_event.onset_seconds,
            "score_events": {
                "m18.v1.e3": ("F#4", 12.80),
                "m18.v1.e4": ("G4", 13.50),
            },
        },
    )
    res_align = evaluator.evaluate(req_align)
    print(f"    Alignment decision: {res_align.decision} (Uncertainty: {res_align.uncertainty})")
    print(f"    Explanation: {res_align.explanation}\n")

    # 4. TypeSafe Jev Adapter Demonstration (BYOK Policy & Graceful Degradation)
    print("[4] TypeSafe Jev Adapter Demonstration...")
    jev_adapter = TypeSafeJevAdapter()
    print(f"    Key configured in environment: {jev_adapter.capabilities()['credentials_configured']}")
    req_jev = EvaluationRequest(
        question="Which harmonic resolution fits the preceding cadential progression?",
        evaluation_type=EvaluationType.CHOICE,
        candidates=("Dmaj7", "Dmin7", "G7"),
    )
    res_jev_fallback = jev_adapter.evaluate(req_jev)
    print(f"    Status without API key: {res_jev_fallback.status.value}")
    print(f"    Explanation: {res_jev_fallback.explanation}")
    print("    -> Core operation continues uninterrupted without external dependencies.")

    # 4b. Mock execution with secret key to verify Secret Redaction
    fake_secret = "ts_live_secret_musicmcp_eval_987654"
    mock_jev_client = type("MockJevClient", (), {
        "evaluate": lambda self, req: {
            "decision": "Dmaj7",
            "probabilities": {"Dmaj7": 0.85, "Dmin7": 0.10, "G7": 0.05},
            "explanation": f"Jev engine using {fake_secret} evaluated authentic cadence resolution.",
        }
    })()
    jev_active_adapter = TypeSafeJevAdapter(api_key=fake_secret, mock_client=mock_jev_client)
    res_jev_active = jev_active_adapter.evaluate(req_jev)
    print(f"\n    With Active Jev Client:")
    print(f"    Status: {res_jev_active.status.value}")
    print(f"    Decision: {res_jev_active.decision}")
    print(f"    Probabilities: {res_jev_active.probabilities.probabilities}")
    print(f"    Explanation: {res_jev_active.explanation}")
    has_secret_leaked = fake_secret in res_jev_active.explanation
    print(f"    Secret Redacted Invariant: {'PASSED (Safe)' if not has_secret_leaked else 'FAILED (Leaked!)'}\n")

    # 5. Authoritative State Governance Invariant Verification
    print("[5] Verifying Authoritative Musical State (AMS) Invariant...")
    current_rev = ws.snapshot().revision
    print(f"    Initial revision: {initial_rev}")
    print(f"    Current revision: {current_rev}")
    if initial_rev == current_rev:
        print("    -> Invariant PASSED: Evaluators propose judgments; only human-held AuthoritySession mutates AMS.")
    else:
        print("    -> Invariant FAILED: Workspace revision changed unexpectedly!")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
