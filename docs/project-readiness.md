# keep-mcp: reliable local integration and portfolio release

Status: proposed implementation spec, 5 October 2026. This cleanup does not implement the roadmap. Primary endpoint: a dependable local MCP integration plus an evidence-backed portfolio case study. Secondary endpoint: validate paid integration/setup help; no hosted consumer-account service is planned.

## Existing system and cleanup

Python package (`src/server`), stdio MCP entry point, gkeepapi authentication, serialized access through an RLock and reconnect after failed operations. Tools cover reading, note/checklist mutations, labels, collaborators and media. Guarded note writes depend on the `keep-mcp` label, which is not proof of origin. Tests and CI already exist; CI includes a 70% coverage floor. Package metadata says beta. Repository interest: 103 GitHub stars in the review snapshot, not a user count.

Cleanup corrects the README's safety scope, adds an honest project-status section and includes pytest-cov in the local dev tools so contributors can reproduce the documented CI coverage command. No authentication behavior or tool schemas change. Existing Docker/secret-file PR #12 must be reviewed before work in that area.

## User and outcome

A Google Keep user who already uses an MCP-capable desktop/CLI client wants to find notes and manage a dedicated assistant checklist without silently altering unrelated notes. First-run success means install → initialize/list tools → find → create a disposable checklist → update checked state → confirm actual Keep state → cleanup, with no credential in logs.

Non-goals: hosted token custody, team admin/CASB product, full multi-account sync, replacing Keep, or claiming an official Google consumer API integration. The [official Keep API](https://developers.google.com/workspace/keep/api/guides) addresses enterprise administration; [gkeepapi](https://gkeepapi.readthedocs.io/en/latest/) is unofficial. A local setup service is a business hypothesis, not a reliability guarantee for Google's private endpoints.

## Required behavior and technical design

| Requirement | Implementation direction | Acceptance evidence |
| --- | --- | --- |
| Reproducible install | Record supported Python/MCP versions; tested package-install instructions and dependency compatibility matrix | Fresh PyPI install in an isolated environment initializes MCP and lists tools on each claimed supported version |
| First-run diagnosis | Centralized credential/config validation; actionable, redacted authentication/network errors on stderr; preserve stdio protocol on stdout | Missing token, invalid token and unreachable API give distinct outcomes; captured stdout remains valid MCP traffic |
| Reliable mutations | Preserve serialized sync/guard semantics; exercise failed sync then retry/reload | Regression proves failed writes do not appear as confirmed successes or replay onto unrelated notes |
| Clear write scope | Document per-tool guard/side effects; keep UNSAFE_MODE explicit | Existing unlabelled note denied; labelled note works; unsafe override tested independently |
| Media boundaries | Review download path/size/timeout/overwrite behavior; define explicit user-controlled destination policy before changing API | Malformed IDs, existing filename, failed download and large body covered; no credential in error/output |
| Stable compatibility | Test minimum/latest allowed dependencies; decide MCP 2.x support from actual runs rather than widening ranges by assumption | Install, tool-schema discovery and unit tests green for every version claimed supported |
| Credible demo | Dedicated disposable account, CLI client prompt/tool result and corresponding actual Keep screenshots | Evidence follows CONTRIBUTING.md; captures redacted, fixtures removed, server/client versions recorded |

Model-facing tool results should remain documented JSON with stable IDs/field types. Future error changes must preserve compatible shapes or be explicitly versioned. Do not change the origin-label policy silently; a new allowlist/read-only mode needs a separate spec and tests.

## Ordered work packages

1. **K1 — compatibility and onboarding (1–2 days).** Reproduce the released package and checkout installs; record client/version matrix; improve setup/troubleshooting only from observed failures. Coordinate with PR #12. Done when a second person can complete the first-run checklist from README alone.
2. **K2 — reliability edges (1–2 days).** Add meaningful failed-sync/reconnect and concurrent mutation coverage where gaps remain; review media boundaries and output redaction. Do not add new broad tools. Done when unit tests, lint, CI coverage and negative cases pass.
3. **K3 — release evidence and case study (1–2 days).** Follow the repository evidence skill for actual account scenarios, record safe/unsafe outcomes, screenshots and cleanup. Explain the label-based policy, private-API constraint and serialization tradeoff in a short case study. Done when the draft PR satisfies required real-use evidence; merge/release still requires approval.

Dependencies: Python 3.10+; supported MCP client; dedicated test Google account and credentials supplied through an authorized local setup. These are not required for documentation cleanup or mocked unit checks. No live-account smoke test was authorized through supplied credentials in this review.

## Portfolio and paid validation gates

Portfolio-ready: reproducible install, current CI, one real end-to-end checklist scenario plus guarded negative case, annotated architecture and factual limits. Avoid star-ranking claims unless separately rechecked against competitors.

Commercial experiment: interview five active users about setup failures, desired workflows and paid support; require at least two explicit requests for a paid setup pilot before building billing or a hosted service. Try a fixed-scope local integration engagement first. Suggested EUR 49–99 pilot pricing is an experiment, not market evidence. Track install success/time, repeated workflow use and support minutes without collecting note contents. Halt paid expansion if reliable auth requires ongoing hands-on token repair or support costs exceed what customers accept.

## Verification and rollout

Run `make test`, `make lint`, the README coverage command and a fresh package-install/MCP initialization check. Feature/fix PRs require real MCP transcripts and actual Keep screenshots under CONTRIBUTING.md; keep them draft until evidence exists. Live tests use disposable fixtures, record identifiers for cleanup, and never commit account state. Changes land in small PRs; do not merge or publish during this planning task. Roll back runtime changes with a revert and the last verified package version.
