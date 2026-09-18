"""Music MCP's experimental in-memory authority kernel. See CONTRACT.md."""
from dataclasses import dataclass, replace
from functools import wraps
from fractions import Fraction
from hashlib import sha256
import re
from threading import RLock
from typing import Callable
from uuid import uuid4

VERSION = '0.1.0'
OPERATIONS = frozenset({'confirm', 'correct', 'restore'})
UNCERTAINTY = frozenset({'HIGH', 'MEDIUM', 'LOW', 'AMBIGUOUS', 'UNRESOLVED', 'INSUFFICIENT_EVIDENCE'})


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    next_action: str
    operation: str
    scope: str
    trace_id: str
    severity: str = 'ERROR'
    module: str = 'core'
    authoritative_state_modified: bool = False
    state_safe: bool = True
    transaction: str = 'not_committed'
    rollback: str = 'not_required'


class MusicError(Exception):
    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


def fail(code, message, action='Review the contract and correct the request.', operation='validate', scope='workspace'):
    raise MusicError(Diagnostic('MUSICMCP-CORE-' + code, message, action, operation, scope, uuid4().hex))


def text(value, limit=128):
    if type(value) is not str or not value.strip() or len(value) > limit:
        fail('VALIDATION_FAILED', f'Expected nonempty text of at most {limit} characters.')
    return value


def diagnosed(method):
    """Keep public read/proposal operation identity when a shared guard fails."""
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except MusicError as error:
            raise MusicError(replace(error.diagnostic, operation=method.__name__)) from None
    return call


@dataclass(frozen=True)
class Note:
    pitch: str
    duration: Fraction

    def __post_init__(self):
        if type(self.pitch) is not str or not re.fullmatch(r'(?:[A-G][#b]?[0-9]|rest)', self.pitch):
            fail('VALIDATION_FAILED', 'Pitch is outside the reference symbolic profile.')
        if type(self.duration) is not Fraction or self.duration <= 0:
            fail('VALIDATION_FAILED', 'Duration must be a positive exact Fraction in quarter-note units.')


def phrase(notes):
    if type(notes) not in (list, tuple) or not 1 <= len(notes) <= 4096 or any(type(n) is not Note for n in notes):
        fail('VALIDATION_FAILED', 'A phrase must contain 1–4096 validated Notes.')
    return tuple(notes)


@dataclass(frozen=True)
class Grant:
    actor: str
    scopes: frozenset[str]
    operations: frozenset[str]

    def __post_init__(self):
        text(self.actor)
        for name in ('scopes', 'operations'):
            supplied = getattr(self, name)
            if type(supplied) not in (set, frozenset, list, tuple):
                fail('VALIDATION_FAILED', 'Grant scopes and operations must be explicit collections.')
            for item in supplied:
                text(item)
            object.__setattr__(self, name, frozenset(supplied))
        if not self.operations <= OPERATIONS:
            fail('VALIDATION_FAILED', 'Grant contains an unsupported operation.')


@dataclass(frozen=True)
class Evidence:
    id: str
    data: bytes
    media_type: str
    sha256: str


@dataclass(frozen=True)
class Observation:
    id: str
    evidence_id: str
    description: str


@dataclass(frozen=True)
class Proposal:
    id: str
    observation_id: str
    evidence_id: str
    scope: str
    notes: tuple[Note, ...]
    mode: str
    uncertainty: str
    origin: str


@dataclass(frozen=True)
class Candidate:
    actor: str
    operation: str
    scope: str
    notes: tuple[Note, ...]
    proposal_id: str
    observation_id: str
    evidence_id: str
    origin: str
    reason: str
    expected_revision: int
    restored_from: int | None
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class Revision:
    number: int
    parent: int
    actor: str
    operation: str
    scope: str
    notes: tuple[Note, ...]
    proposal_id: str
    observation_id: str
    evidence_id: str
    origin: str
    reason: str
    restored_from: int | None
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    revision: int = 0
    phrases: tuple[Revision, ...] = ()
    history: tuple[Revision, ...] = ()


class Workspace:
    """Read/proposal surface. Only host-issued sessions can commit through it."""
    def __init__(self, locked_scopes=(), policy=None, validator=None):
        if type(locked_scopes) not in (tuple, list, set, frozenset):
            fail('VALIDATION_FAILED', 'Locked scopes must be an explicit collection.')
        self._locked = frozenset(text(scope) for scope in locked_scopes)
        if any(callback is not None and not callable(callback) for callback in (policy, validator)):
            fail('VALIDATION_FAILED', 'Policy and validator must be callable or absent.')
        self._policy = policy
        self._validator = validator
        self._lock = RLock()
        self._busy = False
        self._state = Snapshot()
        self._evidence = {}
        self._observations = {}
        self._proposals = {}
        self._grants = {}

    def snapshot(self):
        with self._lock:
            return self._state

    def capabilities(self):
        return (('human_confirmation', True), ('human_correction', True), ('restore', True),
                ('transcription', False), ('mcp_transport', False), ('durable_storage', False),
                ('musicxml', False), ('midi', False))

    def _lookup(self, records, identifier):
        text(identifier)
        if identifier not in records:
            fail('NOT_FOUND', 'The referenced record does not exist.', 'Read existing record IDs and retry.')
        return records[identifier]

    @diagnosed
    def evidence(self, identifier):
        with self._lock:
            return self._lookup(self._evidence, identifier)

    @diagnosed
    def observation(self, identifier):
        with self._lock:
            return self._lookup(self._observations, identifier)

    @diagnosed
    def proposal(self, identifier):
        with self._lock:
            return self._lookup(self._proposals, identifier)

    @diagnosed
    def preview(self, proposal_id):
        return self.proposal(proposal_id)

    @staticmethod
    def _capacity(records, maximum):
        if len(records) >= maximum:
            fail('CAPACITY_EXCEEDED', 'This in-memory workspace reached its retention limit.',
                 'Preserve this workspace; use a separate workspace for new work.')

    @diagnosed
    def add_evidence(self, data, media_type):
        text(media_type)
        if type(data) is not bytes or not 1 <= len(data) <= 1024 * 1024:
            fail('VALIDATION_FAILED', 'Evidence must contain 1–1048576 original bytes.')
        with self._lock:
            self._capacity(self._evidence, 128)
            record = Evidence(uuid4().hex, data, media_type, sha256(data).hexdigest())
            self._evidence[record.id] = record
            return record

    @diagnosed
    def observe(self, evidence_id, description):
        text(description, 4096)
        with self._lock:
            evidence = self.evidence(evidence_id)
            self._capacity(self._observations, 1024)
            record = Observation(uuid4().hex, evidence.id, description)
            self._observations[record.id] = record
            return record

    @diagnosed
    def propose(self, observation_id, scope, notes, mode, uncertainty, origin):
        text(scope)
        notes = phrase(notes)
        if (type(mode) is not str or mode not in ('intended', 'literal')
                or type(uncertainty) is not str or uncertainty not in UNCERTAINTY
                or type(origin) is not str or origin not in ('interpreted', 'generated')):
            fail('VALIDATION_FAILED', 'Task mode, uncertainty, or material origin is unsupported.')
        with self._lock:
            observation = self.observation(observation_id)
            self._capacity(self._proposals, 1024)
            record = Proposal(uuid4().hex, observation.id, observation.evidence_id, scope,
                              notes, mode, uncertainty, origin)
            self._proposals[record.id] = record
            return record

    def _decision(self, callback, candidate, policy):
        if callback is None:
            return
        try:
            allowed = callback(candidate)
        except Exception:
            fail('POLICY_UNAVAILABLE' if policy else 'TRANSACTION_FAILED',
                 'The configured policy or validator could not complete. Nothing was committed.',
                 'Repair the host integration and review current state before retrying.',
                 candidate.operation, candidate.scope)
        if type(allowed) is not bool:
            fail('POLICY_UNAVAILABLE' if policy else 'TRANSACTION_FAILED',
                 'The host integration returned an invalid decision.', operation=candidate.operation, scope=candidate.scope)
        if not allowed:
            fail('POLICY_BLOCKED' if policy else 'VALIDATION_FAILED',
                 'Configured policy denied the change.' if policy else 'The candidate failed post-validation.',
                 'Review policy or candidate content before retrying.', candidate.operation, candidate.scope)

    def _commit(self, token, operation, source, notes, expected_revision, reason):
        # Resolve only known context here; all permission/input decisions remain below.
        # Hold the same lock so restore context and the actual operation see one snapshot.
        with self._lock:
            scope = 'workspace'
            if operation == 'restore' and type(source) is int and 0 < source <= len(self._state.history):
                scope = self._state.history[source - 1].scope
            elif type(source) is str and source in self._proposals:
                scope = self._proposals[source].scope
            try:
                return self._commit_candidate(token, operation, source, notes, expected_revision, reason)
            except MusicError as error:
                raise MusicError(replace(error.diagnostic, operation=operation, scope=scope)) from None

    def _commit_candidate(self, token, operation, source, notes, expected_revision, reason):
        text(reason, 4096)
        if type(expected_revision) is not int or expected_revision < 0:
            fail('VALIDATION_FAILED', 'Expected revision must be a nonnegative integer.')
        with self._lock:
            if self._busy:
                fail('TRANSACTION_FAILED', 'Reentrant authoritative mutation is forbidden.')
            grant = self._grants.get(token)
            if grant is None or operation not in grant.operations:
                fail('UNAUTHORIZED', 'No authority exists for this operation.',
                     'Request explicit scoped authorization from the trusted host.', operation)
            restored_from = None
            if operation == 'restore':
                if type(source) is not int or source <= 0 or source > len(self._state.history):
                    fail('NOT_FOUND', 'The requested historical revision does not exist.', operation=operation)
                record = self._state.history[source - 1]
                proposal = self.proposal(record.proposal_id)
                chosen_notes, origin, restored_from = record.notes, record.origin, record.number
            else:
                proposal = self.proposal(source)
                chosen_notes = phrase(notes) if operation == 'correct' else proposal.notes
                origin = 'human' if operation == 'correct' else proposal.origin
            scope = proposal.scope
            if scope not in grant.scopes:
                fail('UNAUTHORIZED', 'This scope is outside the supplied authority.',
                     'Request authorization for this exact scope.', operation, scope)
            if expected_revision != self._state.revision:
                fail('REVISION_CONFLICT', 'The workspace changed after this operation was prepared.',
                     'Read current state, review differences, then authorize again.', operation, scope)
            candidate = Candidate(grant.actor, operation, scope, chosen_notes, proposal.id,
                                  proposal.observation_id, proposal.evidence_id, origin, reason,
                                  expected_revision, restored_from, tuple(sorted(self._locked)))
            self._busy = True
            try:
                self._decision(self._policy, candidate, policy=True)
                if scope in self._locked:
                    fail('CONSTRAINT_CONFLICT', 'The requested phrase is locked.',
                         'Leave it unchanged; request a deliberate host constraint decision.', operation, scope)
                self._decision(self._validator, candidate, policy=False)
                self._capacity(self._state.history, 1024)
                revision = Revision(self._state.revision + 1, self._state.revision, grant.actor,
                                    operation, scope, chosen_notes, proposal.id, proposal.observation_id,
                                    proposal.evidence_id, origin, reason, restored_from, candidate.constraints)
                phrases = tuple(sorted((r for r in self._state.phrases if r.scope != scope), key=lambda r: r.scope))
                new_state = Snapshot(revision.number,
                                     tuple(sorted((*phrases, revision), key=lambda r: r.scope)),
                                     (*self._state.history, revision))
                self._state = new_state
                return revision
            finally:
                self._busy = False


class AuthoritySession:
    """Privileged capability retained by the trusted host, never given to a model."""
    def __init__(self, workspace, token):
        self._workspace = workspace
        self._token = token

    def confirm(self, proposal_id, expected_revision, reason):
        return self._workspace._commit(self._token, 'confirm', proposal_id, None, expected_revision, reason)

    def correct(self, proposal_id, notes, expected_revision, reason):
        return self._workspace._commit(self._token, 'correct', proposal_id, notes, expected_revision, reason)

    def restore(self, revision, expected_revision, reason):
        return self._workspace._commit(self._token, 'restore', revision, None, expected_revision, reason)


def create_workspace(grants, locked_scopes=(), policy: Callable | None = None, validator: Callable | None = None):
    """Trusted host setup. Factory/session creation is not a model-facing tool."""
    if type(grants) not in (tuple, list) or any(type(grant) is not Grant for grant in grants):
        fail('VALIDATION_FAILED', 'Expected an explicit list of validated host grants.')
    workspace = Workspace(locked_scopes, policy, validator)
    sessions = []
    for grant in grants:
        token = object()
        workspace._grants[token] = grant
        sessions.append(AuthoritySession(workspace, token))
    return workspace, tuple(sessions)
