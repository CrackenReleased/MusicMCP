# Collaboration Contract: Scoped Multi-Role Authority and Delegation

**Contract Version:** 0.1.01  
**Module:** `reference.collaboration`  
**Status:** Implemented Reference Silo  

---

## 1. Constitutional Foundations & Authority Preservation

In commercial and artistic music production, music is rarely created in isolation. Multiple human artists collaborate across distinct musical disciplines:
* **Composer / Songwriter**: Originates thematic melody, lyrics, and core chord progression.
* **Arranger / Orchestrator**: Voicing, instrumentation, counter-melodies, rhythm section feel.
* **Performer / Session Musician**: Audio performance takes, expressive phrasing, timing nuances.
* **Producer / Executive Artist**: Overall aesthetic coherence, scope approvals, final mix approval.
* **Mix Engineer / Editor**: Frequency cleaning, acoustic artifact removal, stem balancing.

### Core Invariants:
1. **Human Authority Boundaries Never Collapse**:
   Collaboration must never blur who authorized what. Every published revision immutably records the `actor`, the `operation`, the `scope`, the `origin`, and the human `reason`.
2. **Explicit Scope Ownership**:
   Every musical scope has an identified primary owner. Non-owners cannot mutate a scope without explicit, revocable delegation from the owner.
3. **Delegation With Provenance and Expiration**:
   An artist can delegate specific operations (`confirm`, `correct`, `restore`) on their owned scopes to another artist. Sub-delegation is strictly controlled, and delegations can be revoked at any time.
4. **Zero Model Authority**:
   External Ai models, transcription analyzers, and format adapters NEVER hold roles or delegation grants. They remain unprivileged proposal agents.
5. **Fail-Closed Policy Integration**:
   Integrates directly with the `Workspace._policy` callback hook. If an actor attempts an unauthorized mutation, the transaction fails with `MUSICMCP-COLLAB-UNAUTHORIZED_DELEGATION` or `MUSICMCP-CORE-POLICY_BLOCKED`.

---

## 2. Specification & Authority Matrix

| Role | Typical Scopes | Permitted Operations (Owned Scopes) |
|---|---|---|
| `COMPOSER` | `lead_melody`, `chords`, `lyrics` | `confirm`, `correct`, `restore`, `delegate` |
| `ARRANGER` | `instrumentation`, `harmony_voices`, `rhythm` | `confirm`, `correct`, `restore` (on assigned scopes) |
| `PERFORMER` | `lead_take`, `guitar_take`, `backing_take` | Propose evidence/notes; confirm take if delegated |
| `PRODUCER` | `workspace`, `master_arrangement` | Universal review, lock enforcement, executive sign-off |
| `EDITOR` | `audio_cleanup`, `comping` | Audio spectral inspection, non-musical artifact cleanup |

---

## 3. Delegation Lifecycle

1. **Grant Creation**:
   `manager.delegate(delegator="joel", delegatee="sarah", scope="harmony_voices", operations={"confirm", "correct"}, reason="Harmonize chorus")`
   - Validates that `delegator` owns `scope`.
   - Generates immutable `DelegationGrant` record.
2. **Execution Check**:
   During `session.confirm()` or `session.correct()`, `manager.check_policy(candidate)` is invoked:
   - Validates that `candidate.actor` is either the registered owner or holds an active delegation for `candidate.scope` and `candidate.operation`.
3. **Revocation**:
   `manager.revoke(delegator="joel", delegation_id="...", reason="Arrangement completed")`
   - Instantly deactivates the grant. Any subsequent mutation attempts by the delegatee are blocked immediately.
