"""Conformance and security tests for the Model-Facing MCP Transport Server."""
import base64
from fractions import Fraction
import json
import unittest

from reference.core import (
    Grant,
    LockConstraint,
    Note,
    Producer,
    create_workspace,
    phrase
)
from reference.mcp_server import MusicMCPServer
from tests.audio_fixtures import make_clipped_wav, make_wav

PRODUCER = Producer('test-producer', '1.0')


class MCPServerConformance(unittest.TestCase):
    def setUp(self):
        # Create a workspace with a human-confirmed phrase
        self.workspace, (self.session,) = create_workspace([
            Grant('studio-engineer', frozenset({'opening'}), frozenset({'confirm', 'correct', 'restore'}))
        ])
        
        # Add evidence and observation
        audio_data = make_wav([(440.0, 0.4)], sample_rate=44100)
        self.evidence = self.workspace.add_evidence(audio_data, 'audio/wav')
        self.obs = self.workspace.observe(self.evidence.id, 'Detected 440Hz tone', producer=PRODUCER)
        
        # Confirm initial phrase
        notes = phrase([Note('A4', Fraction(1, 1))])
        prop = self.workspace.propose(self.obs.id, 'opening', notes, 'intended', 'HIGH', 'interpreted', producer=PRODUCER)
        self.session.confirm(prop.id, 0, 'Human confirmed initial performance')

        self.server = MusicMCPServer(self.workspace)

    def test_mcp_initialize(self):
        req = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'clientInfo': {'name': 'test-agent', 'version': '1.0'}
            }
        }
        res = self.server.handle_request(req)
        self.assertEqual(res['id'], 1)
        self.assertIn('serverInfo', res['result'])
        self.assertEqual(res['result']['serverInfo']['name'], 'music-mcp-reference')
        self.assertEqual(res['result']['serverInfo']['version'], '0.1.01')

    def test_tools_list_advertises_read_and_proposal_tools(self):
        req = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}}
        res = self.server.handle_request(req)
        tool_names = [t['name'] for t in res['result']['tools']]

        self.assertIn('get_workspace_summary', tool_names)
        self.assertIn('list_scopes', tool_names)
        self.assertIn('get_phrase', tool_names)
        self.assertIn('inspect_spectrum', tool_names)
        self.assertIn('analyze_audio', tool_names)
        self.assertIn('propose_phrase', tool_names)

        # Confirm NO mutation tools are advertised
        self.assertNotIn('confirm', tool_names)
        self.assertNotIn('correct', tool_names)
        self.assertNotIn('restore', tool_names)

    def test_get_phrase_returns_authoritative_notes(self):
        req = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'get_phrase',
                'arguments': {'scope': 'opening'}
            }
        }
        res = self.server.handle_request(req)
        self.assertIn('result', res)
        self.assertFalse(res['result']['isError'])
        content = json.loads(res['result']['content'][0]['text'])
        self.assertEqual(content['scope'], 'opening')
        self.assertEqual(content['notes'][0]['pitch'], 'A4')
        self.assertEqual(content['notes'][0]['duration'], '1')

    def test_inspect_spectrum_runs_10hz_to_28khz_watcher_over_mcp(self):
        clipped_audio = make_clipped_wav(440.0, 0.4)
        b64 = base64.b64encode(clipped_audio).decode('ascii')
        req = {
            'jsonrpc': '2.0',
            'id': 4,
            'method': 'tools/call',
            'params': {
                'name': 'inspect_spectrum',
                'arguments': {'wav_base64': b64}
            }
        }
        res = self.server.handle_request(req)
        self.assertFalse(res['result']['isError'])
        report = json.loads(res['result']['content'][0]['text'])
        self.assertFalse(report['clean_musical_signal'])
        anomalies = [a['kind'] for a in report['anomalies']]
        self.assertIn('CLIPPING', anomalies)

    def test_propose_phrase_records_machine_proposal_without_mutating_state(self):
        rev_before = self.workspace.snapshot().revision
        req = {
            'jsonrpc': '2.0',
            'id': 5,
            'method': 'tools/call',
            'params': {
                'name': 'propose_phrase',
                'arguments': {
                    'observation_id': self.obs.id,
                    'scope': 'opening',
                    'notes': [
                        {'pitch': 'C5', 'duration': '1/2'},
                        {'pitch': 'D5', 'duration': '1/2'}
                    ],
                    'mode': 'intended',
                    'uncertainty': 'HIGH',
                    'reason': 'Arranger suggestion for higher register',
                    'producer_name': 'ai-arranger-model',
                    'producer_version': '0.9'
                }
            }
        }
        res = self.server.handle_request(req)
        self.assertFalse(res['result']['isError'])
        payload = json.loads(res['result']['content'][0]['text'])
        self.assertIn('proposal_id', payload)
        self.assertIn('Awaiting human review', payload['notice'])

        # Verify authoritative revision did NOT change
        rev_after = self.workspace.snapshot().revision
        self.assertEqual(rev_before, rev_after)
        # Verify authoritative phrase is still A4
        authoritative = [r for r in self.workspace.snapshot().phrases if r.scope == 'opening'][0]
        self.assertEqual(authoritative.notes[0].pitch, 'A4')

    def test_adversarial_mutation_attack_denied_with_authority_violation(self):
        # Model attempts to call forbidden confirm method
        for forbidden in ('confirm', 'confirm_phrase', 'correct', 'restore', 'acquire_session'):
            req = {
                'jsonrpc': '2.0',
                'id': 99,
                'method': forbidden,
                'params': {'scope': 'opening', 'revision': 1}
            }
            res = self.server.handle_request(req)
            self.assertTrue(res['result']['isError'])
            diag = json.loads(res['result']['content'][0]['text'])
            self.assertEqual(diag['code'], 'MUSICMCP-MCP-AUTHORITY_BOUNDARY_VIOLATION')
            self.assertIn('Models cannot possess authority', diag['message'])

    def test_resources_read_phrase_and_history(self):
        req = {
            'jsonrpc': '2.0',
            'id': 6,
            'method': 'resources/read',
            'params': {'uri': 'music://workspace/scopes/opening/phrase'}
        }
        res = self.server.handle_request(req)
        self.assertEqual(res['id'], 6)
        self.assertIn('result', res)
        data = json.loads(res['result']['contents'][0]['text'])
        self.assertEqual(data['scope'], 'opening')
        self.assertEqual(data['notes'][0]['pitch'], 'A4')


if __name__ == '__main__':
    unittest.main()
