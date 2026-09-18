# Security

Scope: experimental v0.1.0 reference core · 2026-09-18

## Trust boundary

The reference implementation runs inside a trusted Python 3.11+ host. The host identifies authorized humans, controls permission grants, and supplies explicit confirmations and corrections. Model output, analyzer output, imported evidence, metadata, and future transport requests are untrusted data. A field claiming `human` origin does not establish a human identity.

Models must never receive the host's approval or permission-management interface. Exposing a callable that can grant authority as an MCP tool would violate the security model even if its prompt says to ask permission first. Any future transport must authenticate its callers and keep host authority separate from model-visible capabilities.

The core's immutable values and transactional publication protect normal API use. They are **not a sandbox against malicious same-process Python code**, process-memory modification, a compromised operating system, or a malicious trusted host. There is no durable storage, network service, MCP transport, or cryptographic audit ledger in this foundation. Do not deploy it as if those protections exist.

## Authoritative-state protection

Mutations must pass scope and constraint checks and publish complete validated revisions. Denied, stale, or invalid operations must leave authoritative state unchanged. Restore requires current authority and must preserve revision history; it is not a route around locks or grants. Human corrections cannot be silently displaced by new analysis. Original evidence and provenance must remain distinct from machine assertions.

The host is responsible for its approval presentation and for ensuring the person reviewed the specific operation and affected scope. Future remote or multi-user hosts must define identity, authorization lifetime, revocation, replay protection, concurrency, and approval binding before claiming secure operation.

## Data and secrets

Do not commit credentials, private recordings, unpublished compositions, personal metadata, or provider tokens. Use synthetic or explicitly redistributable fixtures. Evidence is retained in process by this reference core; it is not automatically uploaded, persisted, or erased from all memory copies when a Python object is discarded. Hosts must document their own retention and access rules.

Diagnostics must not include secret values or dump raw evidence by default. A useful failure report identifies scope, state safety, transaction outcome, and trace context without exposing an entire musical work. File parsers and network ingestion are future boundaries requiring size limits, format validation, resource limits, and denial-of-service analysis.

## Dependencies and optional capabilities

The initial runtime uses only the Python standard library. This reduces the dependency surface without eliminating interpreter or host vulnerabilities. Use a maintained Python release and review security changes before upgrading.

Before adding a provider, parser, analyzer, or application adapter, document its license, data flows, network access, retention, trust assumptions, failure modes, and replacement route. Execute untrusted code behind an appropriate process or service boundary; a Python package directory does not provide security isolation. Optional components must be disableable without corrupting state or disabling unrelated capabilities. An unavailable or security-blocked capability must report that condition explicitly.

External providers may retain data or change their terms. No provider integration or rights adjudication is included here. Policy decisions must remain separate from technical capability and human authorization.

## Reporting vulnerabilities

No private reporting channel or response-time commitment has been established for this experimental project. If the canonical repository's Security tab offers private vulnerability reporting, use that verified channel. Otherwise, open a minimal public issue requesting a private reporting route **without** exploit details, sensitive material, or credentials; wait for the maintainer to supply a verified route before sharing them. Do not guess a private email address.

A private report should identify affected version/commit, boundary crossed, minimal synthetic reproduction, expected versus actual behavior, authoritative-state impact, and possible mitigation. Maintainers should reproduce the issue, contain the affected capability, add a regression test, document the fix and migration impact, and coordinate publication. Security-driven retirement follows [DEPRECATION.md](DEPRECATION.md).

See [ERRORS.md](ERRORS.md) for accurate state-safety reporting and [CONFORMANCE.md](CONFORMANCE.md) for the current tested contract. No independent security audit or production readiness is claimed.
