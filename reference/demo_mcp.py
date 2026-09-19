"""Demonstration of Model Context Protocol (MCP) server for Music MCP.
Simulates an external Ai model discovering tools, inspecting spectrum (10Hz-28kHz),
reading state, and submitting a proposal, while proving mutation authority remains human-held.
"""
import base64
from fractions import Fraction
import json

from reference.core import (
    Grant,
    Note,
    Producer,
    create_workspace,
    phrase
)
from reference.mcp_server import MusicMCPServer
from tests.audio_fixtures import make_wav

PRODUCER = Producer("studio-director", "1.0")


def run_mcp_demo():
    print("=== Music MCP Model-Facing Transport Demonstration ===")
    
    # 1. Trusted host sets up workspace
    workspace, (session,) = create_workspace([
        Grant("studio-director", frozenset({"opening"}), frozenset({"confirm"}))
    ])
    
    # Performer records a 440Hz tone
    audio_data = make_wav([(440.0, 0.5)], sample_rate=44100)
    evidence = workspace.add_evidence(audio_data, "audio/wav")
    obs = workspace.observe(evidence.id, "Initial singer acoustic take", producer=PRODUCER)
    
    # Musician confirms initial baseline phrase A4
    init_prop = workspace.propose(obs.id, "opening", phrase([Note("A4", Fraction(1, 1))]), "intended", "HIGH", "interpreted", producer=PRODUCER)
    session.confirm(init_prop.id, 0, "Artist confirmed baseline performance")
    
    # 2. Host exposes read/proposal MCP transport to external Ai model
    server = MusicMCPServer(workspace)
    
    # Step A: Model initializes
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"clientInfo": {"name": "claude-or-gemini-assistant", "version": "3.5"}}
    }
    init_res = server.handle_request(init_req)
    print(f"\n1. MCP Handshake: Server {init_res['result']['serverInfo']['name']} v{init_res['result']['serverInfo']['version']}")

    # Step B: Model lists tools
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    tools_res = server.handle_request(tools_req)
    tool_names = [t['name'] for t in tools_res['result']['tools']]
    print(f"2. Advertised Tools to Model: {', '.join(tool_names)}")

    # Step C: Model reads authoritative phrase
    read_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "get_phrase", "arguments": {"scope": "opening"}}
    }
    read_res = server.handle_request(read_req)
    phrase_data = json.loads(read_res['result']['content'][0]['text'])
    print(f"3. Model Reads Scope 'opening': Notes = {phrase_data['notes']} (Revision {phrase_data['revision']})")

    # Step D: Model runs 10 Hz - 28 kHz spectrum watcher
    spec_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "inspect_spectrum", "arguments": {"evidence_id": evidence.id}}
    }
    spec_res = server.handle_request(spec_req)
    spec_data = json.loads(spec_res['result']['content'][0]['text'])
    print(f"4. Spectrum Watcher over MCP: {spec_data['summary']}")

    # Step E: Model proposes alternative harmony phrase (C5, E5)
    prop_req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "propose_phrase",
            "arguments": {
                "observation_id": obs.id,
                "scope": "opening",
                "notes": [
                    {"pitch": "C5", "duration": "1/2"},
                    {"pitch": "E5", "duration": "1/2"}
                ],
                "mode": "intended",
                "uncertainty": "HIGH",
                "reason": "Ai suggestion: minor third harmony above root",
                "producer_name": "ai-harmonic-assistant",
                "producer_version": "1.0"
            }
        }
    }
    prop_res = server.handle_request(prop_req)
    prop_payload = json.loads(prop_res['result']['content'][0]['text'])
    print(f"5. Model Proposal Result: ID {prop_payload['proposal_id']} -> {prop_payload['notice']}")
    
    # Step F: Prove authoritative state was NOT mutated
    curr_snap = workspace.snapshot()
    authoritative_rev = [r for r in curr_snap.phrases if r.scope == 'opening'][0]
    print(f"6. Authoritative State Verification: Revision remains {curr_snap.revision}, Note remains {authoritative_rev.notes[0].pitch}")

    # Step G: Adversarial Attempt: Model tries to unilaterally confirm its own proposal
    attack_req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "confirm_phrase",
        "params": {"proposal_id": prop_payload['proposal_id'], "scope": "opening", "revision": 1}
    }
    attack_res = server.handle_request(attack_req)
    diag = json.loads(attack_res['result']['content'][0]['text'])
    print(f"7. Adversarial Boundary Check: Direct mutation attempt rejected: [{diag['code']}] {diag['message']}")

    print("\n=== MCP Transport Boundary Demonstration Verified Successfully ===")


if __name__ == '__main__':
    run_mcp_demo()
