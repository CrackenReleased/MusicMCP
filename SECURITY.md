# Security

Scope: experimental v0.1.01 reference core · 2026-09-18

## Trust boundary

The reference implementation runs inside a trusted Python 3.11+ host. The host identifies authorized humans, controls permission grants, and supplies explicit confirmations and corrections. Model output, analyzer output, imported evidence, metadata, and future transport requests are untrusted data. A field claiming `human` origin does not establish a human identity.

Models must never receive the host's approval or permission-management interface. Exposing a callable that can grant authority as an MCP tool would violate the security model even if its prompt says to ask permission first. Any future transport must authenticate its callers and keep host authority separate from model-visible capabilities.

The core's immutable values and transactional publication protect normal API use. They are **not a sandbox against malicious same-process Python code**, process-memory modification, a compromised operating system, or a malicious trusted host. There is no durable storage, network service, MCP transport, or cryptographic audit ledger in this foundation. Do not deploy it as if those protections exist.

## Authoritative-state protection

Mutations must pass scope and constraint checks and publish complete validated revisions. Denied, stale, or invalid operations must leave authoritative state unchanged. Restore requires current authority and must preserve revision history; it is not a route around locks or grants. Human corrections cannot be silently displaced by new analysis. Original evidence and provenance must remain distinct from machine assertions.

The host must present the exact workspace and current workspace-wide revision, operation, affected scope, proposal or historical restore target, resulting notes, source producer identity/version, material origin and uncertainty, active constraints with origins/reasons, and the reason for the change. It must obtain explicit human action through a trusted route before invoking the session with the reviewed immutable values and expected revision. Session possession is not authentication or per-operation consent; a model's claim that approval happened is insufficient. A stale revision rejection requires fresh review and consent, never an automatic retry with a newer expected revision.

Producer attribution belongs to each observation and proposal separately, and constraints retain their origin and reason. The host supplies that metadata; it is not cryptographic authenticity. Display differing observer/interpreter identities and distinguish source-proposal uncertainty from a human correction or restored human result. HIGH support never grants permission or justifies skipping review. The kernel cannot establish whether a person saw or approved the values: these duties remain part of the trusted-host boundary, with no UI or approval-token subsystem added in v0.1.01.

Future remote or multi-user hosts must define identity, authorization lifetime, revocation, replay protection, concurrency, and approval binding before claiming secure operation.

## Data and secrets

Do not commit credentials, private recordings, unpublished compositions, personal metadata, or provider tokens. Use synthetic or explicitly redistributable fixtures. Evidence is retained in process by this reference core; it is not automatically uploaded, persisted, or erased from all memory copies when a Python object is discarded. Hosts must document their own retention and access rules.

Diagnostics must not include secret values or dump raw evidence by default. A useful failure report identifies scope, state safety, transaction outcome, and trace context without exposing an entire musical work. File parsers and network ingestion are future boundaries requiring size limits, format validation, resource limits, and denial-of-service analysis.

## Dependencies and optional capabilities

The initial runtime uses only the Python standard library. This reduces the dependency surface without eliminating interpreter or host vulnerabilities. Use a maintained Python release and review security changes before upgrading.

Before adding a provider, parser, analyzer, or application adapter, document its license, data flows, network access, retention, trust assumptions, failure modes, and replacement route. Execute untrusted code behind an appropriate process or service boundary; a Python package directory does not provide security isolation. Optional components must be disableable without corrupting state or disabling unrelated capabilities. An unavailable or security-blocked capability must report that condition explicitly.

External providers may retain data or change their terms. No provider integration or rights adjudication is included here. Policy decisions must remain separate from technical capability and human authorization.


## Evaluation Provider Security & Credential Isolation (v0.1.02)

The evaluation silo introduces support for optional external evaluators (such as TypeSafe Jev) under strict credential isolation:

1. **Bring Your Own Key (BYOK):** Hosted evaluation providers require user-supplied credentials (e.g. `TYPESAFE_API_KEY`) loaded from the environment or explicit parameter injection. Shared maintainer keys MUST NOT be checked into source repositories, configuration files, test fixtures, documentation, or handoff logs.
2. **Secret Redaction Invariant:** Adapters MUST sanitize sensitive tokens and API keys, replacing them with `[REDACTED_SECRET]` in all explanations, user-facing error messages, and technical diagnostics. Automated tests enforce that keys never leak into evaluation outputs.
3. **Privilege & Mutation Isolation:** Evaluation providers are strictly advisory. Evaluators do NOT receive `AuthoritySession` tokens and have no access to internal workspace commit machinery. Evaluator judgments cannot mutate Authoritative Musical State.
4. **Absence of Credentials is Safe:** When credentials are absent, adapters degrade immediately to status `CAPABILITY_UNAVAILABLE` without network activity, unhandled exceptions, or side effects on core musical state.

## Reporting vulnerabilities

No private reporting channel or response-time commitment has been established for this experimental project. If the canonical repository's Security tab offers private vulnerability reporting, use that verified channel. Otherwise, open a minimal public issue requesting a private reporting route **without** exploit details, sensitive material, or credentials; wait for the maintainer to supply a verified route before sharing them. Do not guess a private email address.

A private report should identify affected version/commit, boundary crossed, minimal synthetic reproduction, expected versus actual behavior, authoritative-state impact, and possible mitigation. Maintainers should reproduce the issue, contain the affected capability, add a regression test, document the fix and migration impact, and coordinate publication. Security-driven retirement follows [DEPRECATION.md](DEPRECATION.md).

See [ERRORS.md](ERRORS.md) for accurate state-safety reporting and [CONFORMANCE.md](CONFORMANCE.md) for the current tested contract. No independent security audit or production readiness is claimed.
