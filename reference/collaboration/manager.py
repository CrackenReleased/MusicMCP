"""Scoped Multi-Role Collaboration Manager for Music MCP.

Adheres strictly to Python 3.11+ standard library only: dataclasses, uuid, typing.
Integrates directly with Workspace._policy to enforce fine-grained role boundaries and delegations.
"""
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from reference.core import (
    Candidate,
    Diagnostic,
    Grant,
    MusicError,
    Workspace,
    create_workspace,
    fail,
    text,
)


class Role(str, Enum):
    COMPOSER = "COMPOSER"
    ARRANGER = "ARRANGER"
    PERFORMER = "PERFORMER"
    PRODUCER = "PRODUCER"
    EDITOR = "EDITOR"


@dataclass(frozen=True)
class ScopeOwnership:
    scope: str
    owner: str
    role: Role
    description: str


@dataclass(frozen=True)
class DelegationGrant:
    id: str
    delegator: str
    delegatee: str
    scope: str
    operations: frozenset[str]
    reason: str
    active: bool = True


class CollaborationError(MusicError):
    pass


def _collab_fail(code: str, message: str, action: str = "Review scope ownership and delegation grants.",
                 operation: str = "collaborate", scope: str = "workspace"):
    raise CollaborationError(
        Diagnostic(
            code=f"MUSICMCP-COLLAB-{code}",
            message=message,
            next_action=action,
            operation=operation,
            scope=scope,
            trace_id=uuid4().hex,
            module="collaboration",
        )
    )


class CollaborationManager:
    """Coordinates multi-artist scope ownership, delegations, and policy enforcement."""

    def __init__(self):
        self._ownerships: dict[str, ScopeOwnership] = {}  # scope -> ScopeOwnership
        self._delegations: dict[str, DelegationGrant] = {}  # id -> DelegationGrant

    def register_owner(self, scope: str, owner: str, role: Role | str, description: str = "") -> ScopeOwnership:
        """Assigns primary ownership of a musical scope to an artist."""
        text(scope)
        text(owner)
        if isinstance(role, str):
            role = Role(role.upper())

        record = ScopeOwnership(scope=scope, owner=owner, role=role, description=description)
        self._ownerships[scope] = record
        return record

    def get_ownership(self, scope: str) -> ScopeOwnership | None:
        return self._ownerships.get(scope)

    def delegate(
        self,
        delegator: str,
        delegatee: str,
        scope: str,
        operations: set[str] | frozenset[str],
        reason: str,
    ) -> DelegationGrant:
        """Issues a delegation grant allowing delegatee to mutate an owned scope."""
        text(delegator)
        text(delegatee)
        text(scope)
        text(reason, 4096)

        ownership = self.get_ownership(scope)
        if ownership is None:
            _collab_fail("SCOPE_UNREGISTERED", f"Cannot delegate unmanaged scope '{scope}'. Register ownership first.", scope=scope)
        if ownership.owner != delegator:
            _collab_fail("NOT_SCOPE_OWNER", f"Actor '{delegator}' does not own scope '{scope}' (owned by '{ownership.owner}').", scope=scope)

        ops = frozenset(operations)
        grant = DelegationGrant(
            id=uuid4().hex,
            delegator=delegator,
            delegatee=delegatee,
            scope=scope,
            operations=ops,
            reason=reason,
            active=True,
        )
        self._delegations[grant.id] = grant
        return grant

    def revoke(self, delegator: str, delegation_id: str, reason: str) -> DelegationGrant:
        """Revokes an existing delegation grant immediately."""
        text(delegator)
        text(delegation_id)
        text(reason, 4096)

        grant = self._delegations.get(delegation_id)
        if grant is None:
            _collab_fail("DELEGATION_NOT_FOUND", f"Delegation grant '{delegation_id}' not found.")
        if grant.delegator != delegator:
            _collab_fail("NOT_DELEGATOR", f"Actor '{delegator}' did not issue delegation '{delegation_id}'.")

        revoked = DelegationGrant(
            id=grant.id,
            delegator=grant.delegator,
            delegatee=grant.delegatee,
            scope=grant.scope,
            operations=grant.operations,
            reason=f"Revoked: {reason} (originally: {grant.reason})",
            active=False,
        )
        self._delegations[grant.id] = revoked
        return revoked

    def is_authorized(self, actor: str, scope: str, operation: str) -> bool:
        """Checks whether actor has primary ownership or active delegation for scope and operation."""
        # 1. Primary scope owner
        ownership = self.get_ownership(scope)
        if ownership is not None and ownership.owner == actor:
            return True

        # 2. Active delegation grant
        for grant in self._delegations.values():
            if (
                grant.active
                and grant.delegatee == actor
                and grant.scope == scope
                and operation in grant.operations
            ):
                return True

        return False

    def check_policy(self, candidate: Candidate) -> bool:
        """Workspace policy callback enforcing multi-role collaboration boundaries."""
        return self.is_authorized(candidate.actor, candidate.scope, candidate.operation)

    def build_workspace(self, actors: list[tuple[str, set[str], set[str]]], constraints=()) -> tuple[Workspace, dict[str, any]]:
        """Factory helper creating a Workspace wired with this collaboration manager's policy."""
        grants = []
        for actor, scopes, ops in actors:
            grants.append(Grant(actor=actor, scopes=frozenset(scopes), operations=frozenset(ops)))

        ws, sessions = create_workspace(grants=grants, constraints=constraints, policy=self.check_policy)
        actor_to_session = {g.actor: s for g, s in zip(grants, sessions)}
        return ws, actor_to_session
