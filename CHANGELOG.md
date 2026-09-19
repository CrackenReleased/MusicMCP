# Changelog

## 0.1.01 — 2026-09-18 — local experimental foundation refinement

- Define monophonic audio analyzer contract in reference/ANALYZER_CONTRACT.md.
- Implement dependency-free reference monophonic audio analyzer in reference/analyzer.py with normalized autocorrelation pitch tracking, duration quantization to exact Fraction units, and qualitative uncertainty classification.
- Add audio fixtures generator in tests/audio_fixtures.py and 9 conformance/architecture tests (total 36 passing tests).
- Add executable monophonic audio analysis demonstration in reference/demo_analyzer.py.
- Require immutable producer identity/version on each observation and proposal; missing or invalid attribution is rejected.
- Replace bare `locked_scopes` with attributed `LockConstraint(scope, origin, reason)` records retained in candidates and revisions; reject duplicate lock scopes.
- Define all six uncertainty labels and their non-authorizing semantics.
- Specify exact human review and fresh-consent obligations for trusted hosts; no UI, authentication or approval-token subsystem is claimed.
- Add six provenance/uncertainty conformance cases; all 27 tests pass. Source migration is documented in DEPRECATION.md.
- Experimental source API changes are intentionally incompatible with 0.1.0. No dependency, durable data format, network capability or musical representation expansion was introduced.

## 0.1.0 — 2026-09-18 — local experimental foundation

- Preserved the existing Apache-2.0 license and founding directive; established governing documentation, contracts, error semantics and continuation records.
- Added a dependency-free Python reference core retaining original evidence, provisional interpretations and structured uncertainty.
- Added host-held scoped authority for confirmation, correction and historical phrase restoration; immutable provenance and workspace revision checks protect publication.
- Added lock/policy/post-validation denial paths and bounded in-memory retention.
- Added adversarial conformance tests, architecture checks and an executable synthetic demonstration.
- No MCP transport, actual transcription, durable storage, adapters, GUI, deployment or published package is included.
