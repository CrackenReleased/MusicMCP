# Model-facing MCP transport contract — 0.1.01

Owner: Music MCP transport maintainers. Implementation: `reference/mcp_server.py`. Consumer: external Ai models, IDE agents, MCP client hosts, and conformance tests. Dependencies: Python 3.11+ standard library only (`json`, `sys`, `io`, `base64`, `dataclasses`, `uuid`). Standard JSON-RPC 2.0 stdio protocol. Experimental reference silo.

## 1. Boundary and constitutional authority isolation

Per Founding Directive §1 and §4:
> **Human intent is authoritative. Machine inference is provisional. Machine creation is identifiable. Machine modification is authorized.**
> **No model directly controls authoritative musical state.**

The Model Context Protocol (MCP) server is strictly a **read and proposal gateway**. It connects external models to musical evidence, spectrum checks, and proposal mechanisms.
1. **Absolute Mutation Ban on Model Transport:** The MCP transport MUST NOT expose `confirm`, `correct`, `restore`, or session acquisition capabilities to the model.
2. **Host-Held Authority:** The privileged `AuthoritySession` remains exclusively in the custody of the trusted host application. The host presents machine proposals to the human artist for explicit review and confirmation.
3. **Attribution and Origin:** Any proposal submitted through MCP is permanently stamped with `origin="interpreted"` or `origin="generated"`, and attributed to the model's declared producer identity. It can never claim `origin="human"`.
4. **Denial on Tampering:** Any attempt by an external client or model to invoke mutation methods, forge authority tokens, or alter locked scopes via JSON-RPC is immediately rejected with an explicit authority violation diagnostic.

## 2. Protocol and transport specification

- **Protocol Version:** MCP protocol version `2024-11-05` over standard input / standard output (`stdio`).
- **Framing:** Line-delimited UTF-8 JSON-RPC 2.0 messages.
- **Server Identity:** `name: "music-mcp-reference"`, `version: "0.1.01"`.
- **Capabilities Advertised:**
  - `tools`: Read, analysis, spectrum inspection, and proposal tools.
  - `resources`: Read-only dynamic URIs for workspace state, phrases, revisions, and spectrum reports.
  - `prompts`: Guided review workflows for human artists.

## 3. Tool inventory (model-accessible)

External models and agents are permitted to invoke the following tools:

### `get_workspace_summary`
- **Description:** Read overall workspace status: current revision, registered scopes, active lock constraints, and evidence count.
- **Input:** `{}`
- **Returns:** JSON representation of workspace state.

### `list_scopes`
- **Description:** List all registered musical phrase scopes with their note count and last modified revision.
- **Input:** `{}`
- **Returns:** Array of scope metadata objects.

### `get_phrase`
- **Description:** Retrieve the current authoritative notes and revision history for a named scope.
- **Input:** `{"scope": "string"}`
- **Returns:** Ordered phrase notes, current revision, and material origin.

### `inspect_spectrum`
- **Description:** Execute full 10 Hz – 28,000 Hz (28 kHz) spectrum inspection and non-musical anomaly checks on evidence audio.
- **Input:** `{"evidence_id": "string"}` OR `{"wav_base64": "string"}`
- **Returns:** `SpectrumReport` JSON including peak, RMS, SNR, DC offset, 10-band energy decomposition, and detected anomalies (`CLIPPING`, `DC_OFFSET`, `CLICK_DISCONTINUITY`, `MAINS_HUM`, `INFRASONIC_RUMBLE`, `ULTRASONIC_LEAK`).

### `analyze_audio`
- **Description:** Run monophonic pitch analysis and quantization on WAV audio evidence.
- **Input:** `{"evidence_id": "string"}` OR `{"wav_base64": "string"}`, optional `tempo_bpm` (int, default 120), `tuning_a4` (float, default 440.0).
- **Returns:** Notes array, quantized durations, uncertainty label, and spectrum report.

### `propose_phrase`
- **Description:** Submit a provisional machine proposal for human consideration. Does NOT alter authoritative state.
- **Input:**
  - `observation_id`: string
  - `scope`: string
  - `notes`: array of `{"pitch": "string", "duration": "string"}` (e.g. `{"pitch": "C4", "duration": "1/4"}`)
  - `mode`: `"intended"` | `"literal"`
  - `uncertainty`: `"HIGH"` | `"MEDIUM"` | `"LOW"` | `"AMBIGUOUS"` | `"INSUFFICIENT_EVIDENCE"` | `"UNRESOLVED"`
  - `reason`: string
  - `producer_name`: string (optional, defaults to model client)
  - `producer_version`: string (optional)
- **Returns:** Proposal metadata, proposal ID, and review link.

### Explicitly Forbidden Tools (Denied at Gate)
- `confirm_phrase` -> Error -32601 / `PERMISSION_DENIED`
- `correct_phrase` -> Error -32601 / `PERMISSION_DENIED`
- `restore_phrase` -> Error -32601 / `PERMISSION_DENIED`
- `acquire_session` -> Error -32601 / `PERMISSION_DENIED`

## 4. Resource inventory (read-only URIs)

The transport exposes the following dynamic resource URIs:
- `music://workspace/summary`: Current revision, scope list, and lock constraints.
- `music://workspace/scopes/{scope}/phrase`: Current authoritative phrase notes for `{scope}`.
- `music://workspace/scopes/{scope}/history`: Revision history for `{scope}`.
- `music://workspace/evidence/{id}`: Metadata and observation records for evidence `{id}`.
- `music://workspace/evidence/{id}/spectrum`: 10 Hz – 28 kHz spectrum report for evidence `{id}`.

## 5. Prompts

- `review_musical_proposal`: Formats a machine proposal side-by-side with the current authoritative phrase, spectrum anomalies, and uncertainty rating for host presentation to the musician.
