# Storage Contract: Durable Evidence and Revision Storage

**Contract Version:** 0.1.01  
**Module:** `reference.storage`  
**Status:** Implemented Reference Silo  

---

## 1. Purpose and Constitutional Invariants

The reference core in `reference.core` is intentionally an **in-process memory authority kernel**. When the process terminates, in-memory state is discarded. The Storage Silo provides durable, crash-consistent persistence on local disk while strictly upholding the founding principles:

1. **Evidence Is Sacred and Content-Addressable**:
   Raw audio and performance artifacts are stored immutably. Every stored evidence blob has an immutable ID and a verified SHA-256 cryptographic digest. Modifying, truncating, or corrupting evidence bytes is detected immediately upon verification.
2. **Provenance Is Preserved Through the Lifecycle**:
   Observations, provisional proposals, lock constraints, and published revisions carry immutable attribution to their human or machine producers. Disk serialization retains the full evidence-observation-proposal-revision causal DAG.
3. **Strict Authority Boundary**:
   The storage engine is a persistence facilitator, NOT an authority agent. It cannot issue mutation tokens, bypass lock constraints, or fabricate revisions. Restoring a workspace restores the state into a genuine `Workspace` instance subject to identical runtime invariant checks.
4. **Crash Consistency and Atomicity**:
   All database writes occur within ACID transactions (`BEGIN IMMEDIATE ... COMMIT`) using SQLite Write-Ahead Logging (WAL) mode. Schema migration, conflict checks, forced replacement, and content writes share one transaction. A failed transaction preserves prior committed data; recovery after interruption may expose the complete prior or complete new state, never a partially committed save. WAL uses synchronous=FULL; this is not a certification of hardware or filesystem power-loss behavior.
5. **Zero External Dependencies**:
   Pure Python 3.11+ standard library (`sqlite3`, `pathlib`, `json`, `hashlib`, `fractions`, `dataclasses`).

---

## 2. Relational Schema Specification

A single SQLite database file (`.musicmcp` or `.sqlite3`) stores the complete workspace snapshot:

### 2.1 Table `schema_meta`
- `key` TEXT PRIMARY KEY
- `value` TEXT NOT NULL

Stores `schema_version` (e.g. `'0.1.01'`), `format_id` (`'musicmcp-sqlite'`), `updated_at` (ISO-8601 UTC), and `state_token` for optimistic concurrency.

### 2.2 Table `evidence`
- `id` TEXT PRIMARY KEY
- `data` BLOB NOT NULL
- `media_type` TEXT NOT NULL
- `sha256` TEXT NOT NULL

Stores raw evidence blobs. On insertion and retrieval, `sha256(data)` is verified against the recorded digest.

### 2.3 Table `observations`
- `id` TEXT PRIMARY KEY
- `evidence_id` TEXT NOT NULL REFERENCES evidence(id)
- `description` TEXT NOT NULL
- `producer_identity` TEXT NOT NULL
- `producer_version` TEXT NOT NULL

### 2.4 Table `proposals`
- `id` TEXT PRIMARY KEY
- `observation_id` TEXT NOT NULL REFERENCES observations(id)
- `evidence_id` TEXT NOT NULL REFERENCES evidence(id)
- `scope` TEXT NOT NULL
- `notes_json` TEXT NOT NULL  -- Array of serialized notes: [{"pitch": "C4", "num": 1, "den": 1}]
- `mode` TEXT NOT NULL
- `uncertainty` TEXT NOT NULL
- `origin` TEXT NOT NULL
- `producer_identity` TEXT NOT NULL
- `producer_version` TEXT NOT NULL

### 2.5 Table `revisions`
- `number` INTEGER PRIMARY KEY
- `parent` INTEGER NOT NULL
- `actor` TEXT NOT NULL
- `operation` TEXT NOT NULL
- `scope` TEXT NOT NULL
- `notes_json` TEXT NOT NULL
- `proposal_id` TEXT NOT NULL
- `observation_id` TEXT NOT NULL
- `evidence_id` TEXT NOT NULL
- `origin` TEXT NOT NULL
- `reason` TEXT NOT NULL
- `restored_from` INTEGER
- `constraints_json` TEXT NOT NULL  -- Array of [{"scope": "...", "origin": "...", "reason": "..."}]

### 2.6 Table `grants`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `actor` TEXT NOT NULL
- `scopes_json` TEXT NOT NULL
- `operations_json` TEXT NOT NULL

### 2.7 Table `constraints`
- `scope` TEXT PRIMARY KEY
- `origin` TEXT NOT NULL
- `reason` TEXT NOT NULL

---

## 3. Data Integrity and Verification

`SqliteStorageEngine.verify_integrity(path)` reads one database snapshot and reports SQLite `integrity_check`, schema version, evidence SHA-256, revision number/parent continuity, and stored causal-chain errors. `load_workspace` checks the same record relationships before constructing a live workspace; it fails with `MUSICMCP-STORAGE-INTEGRITY_FAILURE` and a named offending record instead of silently reviving inconsistent state. Neither operation modifies the file or repairs original evidence.

The record audit requires each observation to reference existing evidence, each proposal to reference an existing observation and its evidence, and each revision to match its proposal's observation, evidence, and scope. It validates producer attribution, proposal mode/uncertainty/origin, symbolic note and revision-constraint serialization, confirmation notes/origin, correction origin, and restoration source/notes/origin. Note and constraint JSON objects must contain exactly their documented fields; note duration numerator and denominator must be integers, not booleans or coerced values. A restore source must be an earlier revision of the same causal line; non-restore operations cannot claim a restore source. Historical actor grants are not re-applied to past actions during load, because grants may legitimately change after publication. These checks establish consistency of stored references, not independent authenticity of an attributed producer or approval.

## 4. Save and recovery boundaries

`save_workspace` holds the workspace lock through snapshot capture and successful token publication. It obtains a SQLite writer reservation with `BEGIN IMMEDIATE` before checking the stored token or changing schema/data. A competing writer either waits and rechecks the token, or fails with SQLite's lock error; it cannot overwrite through a check/write gap. Failures roll back the transaction and do not advance the in-memory token.

A disposable subprocess test terminates an actual storage writer after its changes are staged and immediately before `conn.commit()`. Reopening then finds the prior complete revision, evidence, and state token, with a valid integrity report. This is process-termination evidence for the tested SQLite/WAL environment, not a hardware power-loss certification.

Normal saves reject unsupported schemas. Explicit `force=True` replaces stored content atomically, bypassing token preconditions; it is intentionally destructive on success. Legacy actor-keyed grants migrate within that same transaction. Distinct grants for one actor remain distinct.

Runtime policy and validator callbacks are host configuration, not serialized data. Hosts must supply them and any grant override when reopening after a failed save. The preview recovery contract specifies its fail-closed behavior.
