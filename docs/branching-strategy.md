# Branching Strategy — Self-Service Platform Repo

Trunk-based, short-lived branches. Chosen because requests are small,
independent, and reviewed fast — long-lived feature branches would just
create merge conflicts between unrelated data-source/infra requests.

## Branches

| Branch | Purpose | Protection |
|---|---|---|
| `main` | Source of truth. Every merge here can trigger Dev deployment automatically. | Protected — see policies below |
| `feature/<request-name>` | One branch per onboarding/infra request. Deleted after merge. | None — disposable |
| `release/<yyyy-mm-dd>` | Cut only when promoting a batch of Dev-validated changes to Test/Prod. | Protected, short-lived |

## Branch policies on `main` (enforced as code — see `scripts/apply_branch_policies.py`)

- Minimum 1 reviewer from `platform-team`
- Build validation: `pipelines/intake-pipeline.yml` must pass (schema + security gate)
- No direct pushes — PR only
- Comment resolution required before merge
- Linked work item required (ties every infra change back to a tracked request)

Deployment approvals are configured on the pipeline environments, not bypassed
in a request file: `self-service-test` requires `platform-team`, and
`self-service-prod` requires both `platform-team` and `data-owner`. The full
request and gate flow is documented in `docs/self-service-workflow.md`.

## Why this matters for self-service

Self-service only works if `main` can be trusted to always be deployable —
otherwise every merge needs manual sanity-checking, which defeats the point.
Short-lived branches + mandatory automated gates keep that guarantee without
a human bottleneck.
