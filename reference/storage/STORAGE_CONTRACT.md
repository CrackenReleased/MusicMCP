# Storage Contract: Durable Evidence and Revision Storage

**Contract Version:** 0.1.01  
**Module:** `reference.storage`  
**Status:** Implemented Reference Silo  

---

## 1. Purpose and Constitutional Invariants

The reference core in `reference.core` is intentionally an **in-process memory authority kernel**. When the process terminates, in-memory state is discarded. The Storage Silo provides durable, crash-consistent persistence on local disk while strictly upholding the founding principles:

1. **Evidence Is Sacred and Content-Addressable**:
   Raw audio and performance artifacts are stored immutably. Every stored evidence blob is keyed by its SHA-256 cryptographic digest. Modifying, truncating, or corrupting evidence bytes is detected immediately upon verification.
2. **Provenance Is Preserved Through the Lifecycle**:
   Observations, provisional proposals, lock constraints, and published revisions carry immutable attribution to their human or machine producers. Disk serialization retains the full evidence-observation-proposal-revision causal DAG.
3. **Strict Authority Boundary**:
   The storage engine is a persistence facilitator, NOT an authority agent. It cannot issue mutation tokens, bypass lock constraints, or fabricate revisions. Restoring a workspace restores the state into a genuine `Workspace` instance subject to identical runtime invariant checks.
4. **Crash Consistency and Atomicity**:
   All database writes occur within ACID transactions (`BEGIN IMMEDIATE ... COMMIT`) using SQLite Write-Ahead Logging (WAL) mode. An interrupted save or process crash leaves the database in a consistent prior state without partial writes.
5. **Zero External Dependencies**:
   Pure Python 3.11+ standard library (`sqlite3`, `pathlib`, `json`, `hashlib`, `fractions`, `dataclasses`).

---

## 2. Relational Schema Specification

A single SQLite database file (`.musicmcp` or `.sqlite3`) stores the complete workspace snapshot:

### 2.1 Table `schema_meta`
- `key` TEXT PRIMARY KEY
- `value` TEXT NOT NULL

Stores `schema_version` (e.g. `'0.1.01'`), `format_id` (`'musicmcp-sqlite'`), `created_at` (ISO-8601 UTC), and `updated_at`.

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
- `notes_json` TEXT NOT NULL  -- Array of serialized notes: [{"pitch": "C4", "duration": "1/1"}]
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
- `actor` TEXT PRIMARY KEY
- `scopes_json` TEXT NOT NULL
- `operations_json` TEXT NOT NULL

### 2.7 Table `constraints`
- `scope` TEXT PRIMARY KEY
- `origin` TEXT NOT NULL
- `reason` TEXT NOT NULL

---

## 3. Data Integrity and Verification

`SqliteStorageEngine.verify_integrity(path)` conducts a non-destructive multi-stage audit:
1. **SQLite PRAGMA check**: Executes `PRAGMA integrity_check` and `PRAGMA quick_check`.
2. **Evidence Hash Verification**: Iterates over every row in `evidence` and recalculates `hashlib.sha256(data).hexdigest()`. Discrepancies raise `EVIDENCE_CORRUPTED`.
3. **Revision Chain Continuity**: Verifies that revision 1 has parent 0, and each subsequent revision `r_i` has `parent == r_{i-1}.number`. Gaps or forks raise `REVISION_CHAIN_BROKEN`.
4. **Symbolic Note Validation**: Validates that all stored `notes_json` strings conform to the reference symbolic note profile.
