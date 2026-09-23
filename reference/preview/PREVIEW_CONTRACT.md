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


## Persistence failure recovery

Preview requests serialize mutation, persistence, and recovery under a host lock, with reads using the same lock. Upload evidence/observation/proposal creation and generated-alternative observation/proposal creation occur inside the same mutation boundary; a failed analysis or save must not retain only their first records. A failed mutation restores its prior in-memory records. A failed save attempts a consistent disk reload with the original policy, validator, and only the grants held by preview sessions. Successful reload reports the recovered disk state, which may include another writer's changes; it does not claim the disk was rolled back.

If reload fails, the response reports unknown state safety and transaction outcome, restores pre-mutation memory, and blocks further mutations until the project is reopened. Read access to that memory is not proof of current disk state. These guarantees cover preview requests; unrelated direct in-process callers are outside the host request lock.


## Correction editor source and draft lifetime

For a selected proposal, the clean editor loads the current confirmed phrase only when its scope and proposal ID both match. Otherwise it loads that proposal's original interpretation. A visible source label identifies the confirmed revision or original proposal and explains that Submit Correction saves edited notes while Confirm Proposal still publishes the original proposal. This does not mutate or replace the original proposal.

Project state is fetched before proposal rendering so the editor can resolve that source on reload. Polling, manual Refresh and reselection of the same proposal preserve a dirty draft. Selecting a different proposal intentionally loads its source; unsaved drafts are not persisted across page reload. On successful correction, draft dirtiness is cleared only if the selected proposal and input still match the submitted values, preserving newer edits made during the request.

Regression: tests/test_preview.py::TestCorrectionEditor.test_editor_uses_confirmed_notes_and_preserves_new_drafts executes the shipped inline JavaScript with a minimal DOM/fetch harness via installed Node.js. It skips explicitly when Node is absent; Python-only test passes with that skip do not verify browser-script behavior. Node is a test prerequisite only, not an application runtime dependency. Browser visual/tactile verification is recorded separately in the why-log.


## Proposal review status

A proposal is labeled Reviewed when its ID appears in the workspace's revision history, including a correction derived from it. Other proposals are Pending. Reviewed describes a recorded publication action, not independent musical validation or a claim that the unchanged original was accepted. Status uses history, not only current phrases, so replacement/restoration does not reset review status. Counts refer to the displayed proposal list. All original proposals remain selectable and visible for provenance; no storage field, deletion or authority change is introduced.

## Pitch-aware staff canvas bounds

`drawStaff()` derives vertical canvas height from the highest and lowest supported note steps in the rendered phrase. The backing bitmap and CSS height must contain staff lines, ledger lines, noteheads, stems, accidentals, and pitch labels; the renderer must not alter note pitches to fit. Keep a default minimum height for ordinary phrases. The regression in `tests/test_preview.py::TestCorrectionEditor.test_editor_uses_confirmed_notes_and_preserves_new_drafts` executes the shipped drawing function with C#8 and C3 and asserts every emitted drawing coordinate remains inside the expanded canvas. This is a rendering-bound guarantee, not a full responsive-layout guarantee.

## Page width and staff scrolling

The review deck's grid columns may shrink below a staff canvas's intrinsic width. Grid sections and cards must fit the viewport; each fixed-width staff canvas remains scrollable inside its own wrapper. Header controls and proposal badges wrap when space is limited. The document should not acquire a horizontal scrollbar at the conformance widths, while the notation itself keeps its drawing width and pitch positions. See the browser width regression in `CONFORMANCE.md`.
