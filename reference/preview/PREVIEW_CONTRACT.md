# Visualizer Preview Contract: Local Interactive Human Review and Inspection

**Contract Version:** 0.1.01  
**Module:** `reference.preview`  
**Status:** Reference Silo  

---

## 1. Purpose and Constitutional Invariants

In accordance with Founding Directive §1, §2, and §3:
**The musician stays the artist. The machine does the notation, calculation, and clerical work.**
The visualizer preview server provides an immediate, responsive, accessible local interface for human musicians, composers, and producers to inspect musical evidence, monitor acoustic spectrums, and exercise authoritative governance over candidate proposals.

1. **Localhost Security Boundary**:
   The preview server binds strictly to the loopback interface (`127.0.0.1`). It never binds to public network interfaces (`0.0.0.0`) or exposes unauthenticated authority tokens across external networks.
2. **Interactive Human Authority Review**:
   Human review is not a formality; it is the constitutional foundation of authoritative state. The visualizer enables direct visual inspection of:
   - Extracted pitch timeline vs. quantized rational `Note` durations.
   - Competing machine interpretations with structured uncertainty badges (`LOW`, `MEDIUM`, `HIGH`, `AMBIGUOUS`).
   - Acoustic frequency spectrum across 10 distinct bands from 0 Hz up to >28,000 Hz.
   - Non-musical acoustic anomalies (mains hum, infrasonic rumble, ultrasonic leakage, clipping, DC offset).
   - Generated alternatives with prominent `origin="generated"` provenance badges.
3. **Privileged Authority Session Delegation**:
   Mutations (`/api/confirm`, `/api/correct`, `/api/restore`) execute exclusively through a trusted host-held `AuthoritySession` passed directly by the local operator. Network requests without authorized sessions or targeting locked scopes are strictly rejected with standard `MUSICMCP-CORE-*` diagnostics.
4. **Zero External Dependencies**:
   Pure Python 3.11+ standard library only (`http.server`, `json`, `urllib.parse`, `dataclasses`, `pathlib`, `threading`). Zero third-party web frameworks, zero external node dependencies, zero CDN reliance.

---

## 2. API Endpoints Specification

| Method | Endpoint | Description | Expected Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Single-Page Application | None | `text/html; charset=utf-8` |
| `GET` | `/api/project` | Project snapshot & metadata | None | JSON: `{ ok: true, revision: int, phrases: [...], locks: [...], capabilities: [...] }` |
| `GET` | `/api/proposals` | List uncommitted proposals | Query: `?scope=...` (optional) | JSON: `{ ok: true, proposals: [...] }` |
| `GET` | `/api/spectrum` | 10-band spectrum & anomalies | Query: `?evidence_id=...` | JSON: `{ ok: true, report: SpectrumReport }` |
| `GET` | `/api/alternatives` | Preview generated alternative | Query: `?scope=...&type=...` | JSON: `{ ok: true, notes: [...], type: str }` |
| `POST` | `/api/confirm` | Confirm proposal into revision | JSON: `{ proposal_id: str, expected_revision: int, reason: str }` | JSON: `{ ok: true, revision: Revision }` |
| `POST` | `/api/correct` | Correct proposal with notes | JSON: `{ proposal_id: str, notes: str, expected_revision: int, reason: str }` | JSON: `{ ok: true, revision: Revision }` |
| `POST` | `/api/restore` | Restore historical revision | JSON: `{ revision_number: int, expected_revision: int, reason: str }` | JSON: `{ ok: true, revision: Revision }` |

---

## 3. Error and Diagnostic Mapping

All API errors return standard HTTP status codes (400, 403, 404, 409, 500) and structured JSON bodies complying with `ERRORS.md`:

```json
{
  "ok": false,
  "error": {
    "code": "MUSICMCP-CORE-UNAUTHORIZED",
    "message": "No authority exists for this operation.",
    "action": "Request explicit scoped authorization from the trusted host.",
    "operation": "confirm",
    "scope": "melody"
  }
}
```
