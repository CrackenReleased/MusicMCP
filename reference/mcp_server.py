"""Model Context Protocol (MCP) reference transport server for Music MCP.
Exposes read, analysis, spectrum inspection, and proposal operations to external Ai models
while strictly keeping mutation/authority sessions human-held on the host.
"""
import base64
from dataclasses import asdict
from fractions import Fraction
import io
import json
import sys
from uuid import uuid4

from reference.analyzer import (
    ANALYZER_PRODUCER,
    analyze_monophonic_wav
)
from reference.core import (
    Diagnostic,
    Grant,
    LockConstraint,
    MusicError,
    Note,
    Producer,
    UNCERTAINTY,
    create_workspace,
    phrase
)
from reference.spectrum import inspect_audio_spectrum, watch_audio_bytes

VERSION = '0.1.01'
SERVER_NAME = 'music-mcp-reference'
PROTOCOL_VERSION = '2024-11-05'

FORBIDDEN_MUTATION_TOOLS = frozenset({
    'confirm', 'confirm_phrase',
    'correct', 'correct_phrase',
    'restore', 'restore_phrase',
    'create_authority_session', 'acquire_session', 'authorize'
})


class MusicMCPServer:
    """In-process stdio JSON-RPC 2.0 MCP server wrapping Music MCP workspace."""

    def __init__(self, workspace=None):
        if workspace is None:
            default_grants = [Grant('host-human', frozenset({'opening'}), frozenset({'confirm', 'correct', 'restore'}))]
            self.workspace, _ = create_workspace(default_grants)
        else:
            self.workspace = workspace
        self.client_info = None

    def handle_request(self, request: dict) -> dict:
        """Process a single JSON-RPC 2.0 request and return response dict."""
        if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
            return {
                'jsonrpc': '2.0',
                'id': request.get('id') if isinstance(request, dict) else None,
                'error': {'code': -32600, 'message': 'Invalid Request: expected JSON-RPC 2.0'}
            }

        req_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {}) or {}

        # Handle notifications (no id)
        if req_id is None:
            if method == 'notifications/initialized':
                return None
            return None

        try:
            if method == 'initialize':
                return self._handle_initialize(req_id, params)
            elif method == 'tools/list':
                return self._handle_tools_list(req_id)
            elif method == 'tools/call':
                return self._handle_tools_call(req_id, params)
            elif method == 'resources/list':
                return self._handle_resources_list(req_id)
            elif method == 'resources/read':
                return self._handle_resources_read(req_id, params)
            elif method == 'prompts/list':
                return self._handle_prompts_list(req_id)
            elif method == 'prompts/get':
                return self._handle_prompts_get(req_id, params)
            elif method in FORBIDDEN_MUTATION_TOOLS:
                return self._authority_violation(req_id, method)
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'error': {'code': -32601, 'message': f'Method not found: {method}'}
                }
        except MusicError as me:
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {
                    'content': [{'type': 'text', 'text': json.dumps(asdict(me.diagnostic), indent=2)}],
                    'isError': True
                }
            }
        except Exception as ex:
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'error': {'code': -32000, 'message': f'Internal Server Error: {ex}'}
            }

    def _handle_initialize(self, req_id, params):
        self.client_info = params.get('clientInfo', {})
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'protocolVersion': PROTOCOL_VERSION,
                'serverInfo': {
                    'name': SERVER_NAME,
                    'version': VERSION
                },
                'capabilities': {
                    'tools': {},
                    'resources': {},
                    'prompts': {}
                }
            }
        }

    def _handle_tools_list(self, req_id):
        tools = [
            {
                'name': 'get_workspace_summary',
                'description': 'Inspect active workspace: current revision, registered scopes, active lock constraints, and evidence count.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            },
            {
                'name': 'list_scopes',
                'description': 'List all registered musical phrase scopes with their note count and last modified revision.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            },
            {
                'name': 'get_phrase',
                'description': 'Retrieve the current authoritative notes and revision history for a named scope.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'scope': {'type': 'string', 'description': 'The named musical scope to read'}
                    },
                    'required': ['scope']
                }
            },
            {
                'name': 'inspect_spectrum',
                'description': 'Execute full 10 Hz – 28,000 Hz (28 kHz) spectrum inspection and non-musical anomaly checks (clipping, DC offset, clicks, hum, rumble, ultrasonic leak).',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'evidence_id': {'type': 'string', 'description': 'Workspace evidence ID to inspect'},
                        'wav_base64': {'type': 'string', 'description': 'Base64-encoded WAV audio bytes'}
                    }
                }
            },
            {
                'name': 'analyze_audio',
                'description': 'Run monophonic pitch extraction, rational duration quantization, and spectrum inspection on WAV audio.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'evidence_id': {'type': 'string', 'description': 'Workspace evidence ID to analyze'},
                        'wav_base64': {'type': 'string', 'description': 'Base64-encoded WAV audio bytes'},
                        'tempo_bpm': {'type': 'integer', 'description': 'Tempo in BPM (30-300, default 120)', 'default': 120},
                        'tuning_a4': {'type': 'number', 'description': 'Tuning pitch of A4 in Hz (default 440.0)', 'default': 440.0}
                    }
                }
            },
            {
                'name': 'propose_phrase',
                'description': 'Submit a provisional machine phrase proposal for human artist review. Does NOT mutate authoritative state.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'observation_id': {'type': 'string', 'description': 'Source observation ID'},
                        'scope': {'type': 'string', 'description': 'Target musical scope'},
                        'notes': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'pitch': {'type': 'string', 'description': 'Pitch name e.g. C4, A#3, rest'},
                                    'duration': {'type': 'string', 'description': 'Quarter-note fraction e.g. 1/4, 1/2, 1'}
                                },
                                'required': ['pitch', 'duration']
                            }
                        },
                        'mode': {'type': 'string', 'enum': ['intended', 'literal'], 'default': 'intended'},
                        'uncertainty': {'type': 'string', 'enum': list(UNCERTAINTY), 'default': 'MEDIUM'},
                        'origin': {'type': 'string', 'enum': ['interpreted', 'generated'], 'default': 'interpreted'},
                        'producer_name': {'type': 'string', 'description': 'Producer name/model identity'},
                        'producer_version': {'type': 'string', 'description': 'Producer model version'}
                    },
                    'required': ['observation_id', 'scope', 'notes']
                }
            }
        ]
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {'tools': tools}
        }

    def _handle_tools_call(self, req_id, params):
        name = params.get('name')
        args = params.get('arguments', {}) or {}

        if name in FORBIDDEN_MUTATION_TOOLS:
            return self._authority_violation(req_id, name)

        if name == 'get_workspace_summary':
            snap = self.workspace.snapshot()
            summary = {
                'revision': snap.revision,
                'scopes': [r.scope for r in snap.phrases],
                'constraints': [
                    {'scope': c.scope, 'origin': c.origin, 'reason': c.reason}
                    for c in getattr(self.workspace, '_constraints', ())
                ],
                'phrases_count': len(snap.phrases),
                'history_count': len(snap.history)
            }
            return self._tool_success(req_id, summary)

        elif name == 'list_scopes':
            snap = self.workspace.snapshot()
            result = []
            for r in snap.phrases:
                result.append({
                    'scope': r.scope,
                    'revision': r.number,
                    'actor': r.actor,
                    'origin': r.origin,
                    'note_count': len(r.notes),
                    'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in r.notes]
                })
            return self._tool_success(req_id, result)

        elif name == 'get_phrase':
            scope = args.get('scope')
            if not scope:
                return self._tool_error(req_id, 'Scope argument is required.')
            snap = self.workspace.snapshot()
            matching = [r for r in snap.phrases if r.scope == scope]
            if not matching:
                return self._tool_error(req_id, f"Scope '{scope}' does not exist in workspace.")
            r = matching[0]
            result = {
                'scope': r.scope,
                'revision': r.number,
                'origin': r.origin,
                'actor': r.actor,
                'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in r.notes]
            }
            return self._tool_success(req_id, result)

        elif name == 'inspect_spectrum':
            data = self._resolve_audio_bytes(args)
            if data is None:
                return self._tool_error(req_id, 'Must provide either evidence_id or wav_base64.')
            report = watch_audio_bytes(data)
            return self._tool_success(req_id, asdict(report))

        elif name == 'analyze_audio':
            data = self._resolve_audio_bytes(args)
            if data is None:
                return self._tool_error(req_id, 'Must provide either evidence_id or wav_base64.')
            tempo = args.get('tempo_bpm', 120)
            tuning = args.get('tuning_a4', 440.0)
            analysis = analyze_monophonic_wav(data, tempo_bpm=tempo, tuning_a4=tuning)
            result = {
                'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in analysis.notes],
                'uncertainty': analysis.uncertainty,
                'duration_seconds': analysis.duration_seconds,
                'tempo_bpm': analysis.tempo_bpm,
                'description': analysis.description,
                'spectrum': asdict(analysis.spectrum_report)
            }
            return self._tool_success(req_id, result)

        elif name == 'propose_phrase':
            obs_id = args.get('observation_id')
            scope = args.get('scope')
            raw_notes = args.get('notes', [])
            mode = args.get('mode', 'intended')
            uncertainty = args.get('uncertainty', 'MEDIUM')
            origin = args.get('origin', 'interpreted')
            p_name = args.get('producer_name', 'model-mcp-client')
            p_ver = args.get('producer_version', '1.0')

            if not obs_id or not scope or not raw_notes:
                return self._tool_error(req_id, 'observation_id, scope, and notes are required.')

            parsed_notes = []
            for rn in raw_notes:
                p = rn.get('pitch')
                d_str = str(rn.get('duration', '1/4'))
                dur = Fraction(d_str)
                parsed_notes.append(Note(pitch=p, duration=dur))

            producer = Producer(identity=p_name, version=p_ver)
            prop = self.workspace.propose(
                obs_id,
                scope,
                phrase(parsed_notes),
                mode,
                uncertainty,
                origin,
                producer=producer
            )
            result = {
                'proposal_id': prop.id,
                'scope': prop.scope,
                'mode': prop.mode,
                'uncertainty': prop.uncertainty,
                'origin': prop.origin,
                'notes_count': len(prop.notes),
                'notice': 'Provisional proposal recorded. Does NOT alter authoritative state. Awaiting human review.'
            }
            return self._tool_success(req_id, result)

        return self._tool_error(req_id, f'Unknown tool: {name}')

    def _handle_resources_list(self, req_id):
        snap = self.workspace.snapshot()
        resources = [
            {
                'uri': 'music://workspace/summary',
                'name': 'Workspace Summary',
                'mimeType': 'application/json',
                'description': 'Current workspace revision, lock constraints, and scope inventory'
            }
        ]
        for r in snap.phrases:
            resources.append({
                'uri': f'music://workspace/scopes/{r.scope}/phrase',
                'name': f"Scope '{r.scope}' Authoritative Phrase",
                'mimeType': 'application/json',
                'description': f"Current confirmed notes for musical scope '{r.scope}'"
            })
            resources.append({
                'uri': f'music://workspace/scopes/{r.scope}/history',
                'name': f"Scope '{r.scope}' Revision History",
                'mimeType': 'application/json',
                'description': f"Complete immutable revision records for scope '{r.scope}'"
            })
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {'resources': resources}
        }

    def _handle_resources_read(self, req_id, params):
        uri = params.get('uri', '')
        snap = self.workspace.snapshot()

        if uri == 'music://workspace/summary':
            data = {
                'revision': snap.revision,
                'scopes': [r.scope for r in snap.phrases],
                'constraints': [
                    {'scope': c.scope, 'origin': c.origin, 'reason': c.reason}
                    for c in getattr(self.workspace, '_constraints', ())
                ]
            }
            return self._resource_success(req_id, uri, data)

        parts = uri.replace('music://workspace/', '').split('/')
        if len(parts) >= 3 and parts[0] == 'scopes':
            scope = parts[1]
            sub = parts[2]
            matching = [r for r in snap.phrases if r.scope == scope]
            if not matching:
                return self._tool_error(req_id, f"Resource not found: {uri}")
            r = matching[0]

            if sub == 'phrase':
                data = {
                    'scope': r.scope,
                    'revision': r.number,
                    'origin': r.origin,
                    'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in r.notes]
                }
                return self._resource_success(req_id, uri, data)
            elif sub == 'history':
                history = [rev for rev in snap.history if rev.scope == scope]
                data = {
                    'scope': scope,
                    'revisions': [
                        {
                            'number': rev.number,
                            'actor': rev.actor,
                            'operation': rev.operation,
                            'origin': rev.origin,
                            'notes': [{'pitch': n.pitch, 'duration': str(n.duration)} for n in rev.notes]
                        }
                        for rev in history
                    ]
                }
                return self._resource_success(req_id, uri, data)

        return self._tool_error(req_id, f"Unsupported resource URI: {uri}")

    def _handle_prompts_list(self, req_id):
        prompts = [
            {
                'name': 'review_musical_proposal',
                'description': 'Guided workflow presenting machine proposal side-by-side with authoritative state and 10Hz-28kHz spectrum checks for human artist review.',
                'arguments': [
                    {'name': 'scope', 'description': 'Scope being reviewed', 'required': True},
                    {'name': 'proposal_id', 'description': 'Proposal ID under review', 'required': True}
                ]
            }
        ]
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {'prompts': prompts}
        }

    def _handle_prompts_get(self, req_id, params):
        name = params.get('name')
        args = params.get('arguments', {})
        if name == 'review_musical_proposal':
            scope = args.get('scope', 'opening')
            prop_id = args.get('proposal_id', '<proposal_id>')
            messages = [
                {
                    'role': 'system',
                    'content': {
                        'type': 'text',
                        'text': (
                            "You are Music MCP Review Assistant. The human musician is the ultimate author and artist. "
                            "Present machine suggestions objectively with declared uncertainty and spectral watcher results. "
                            "Remind the user that only their explicit confirmation will commit changes to authoritative state."
                        )
                    }
                },
                {
                    'role': 'user',
                    'content': {
                        'type': 'text',
                        'text': f"Please review machine proposal '{prop_id}' for musical scope '{scope}'."
                    }
                }
            ]
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {'messages': messages}
            }
        return self._tool_error(req_id, f"Prompt not found: {name}")

    def _resolve_audio_bytes(self, args) -> bytes | None:
        if 'evidence_id' in args and args['evidence_id']:
            ev = self.workspace.evidence(args['evidence_id'])
            return ev.data
        elif 'wav_base64' in args and args['wav_base64']:
            return base64.b64decode(args['wav_base64'])
        return None

    def _tool_success(self, req_id, data):
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'content': [{'type': 'text', 'text': json.dumps(data, indent=2)}],
                'isError': False
            }
        }

    def _tool_error(self, req_id, msg):
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'content': [{'type': 'text', 'text': json.dumps({'error': msg}, indent=2)}],
                'isError': True
            }
        }

    def _resource_success(self, req_id, uri, data):
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'contents': [{
                    'uri': uri,
                    'mimeType': 'application/json',
                    'text': json.dumps(data, indent=2)
                }]
            }
        }

    def _authority_violation(self, req_id, method):
        diag = Diagnostic(
            code='MUSICMCP-MCP-AUTHORITY_BOUNDARY_VIOLATION',
            message=(
                f"Model Context Protocol client attempted to invoke privileged mutation method '{method}'. "
                "Models cannot possess authority to modify musical state. All mutations require host-held human authority."
            ),
            next_action="Submit a provisional proposal via 'propose_phrase' for explicit human confirmation.",
            operation=method,
            scope='mcp_gateway',
            trace_id=uuid4().hex
        )
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'content': [{'type': 'text', 'text': json.dumps(asdict(diag), indent=2)}],
                'isError': True
            }
        }
