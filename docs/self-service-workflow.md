# Self-Service Workflow

The platform exposes a small approved catalog in `terraform/modules/basic-infra`.
Requesters create or copy a YAML file in `onboarding/infra-requests/` and open a
short-lived feature branch and pull request to `main`.

## Request flow

1. Copy `onboarding/infra-requests/sales-analytics-basics.yaml` and use a unique `requestName`.
2. Set the owner, `CC-` cost center, target environment, and only catalog resource types.
3. Reference an existing private VNet and subnet owned by the infrastructure team.
4. Keep all `securityGates` values set to `true` and provide test and production approval groups.
5. Open a pull request from `feature/<request-name>` to `main`.
6. The intake pipeline validates the request, Terraform catalog, formatting, and security scan.
7. After the required platform reviewer approves, merge to `main`. Direct pushes are blocked.

## Approval gates

Configure these Azure DevOps environments before enabling deployment:

| Environment | Approval gate | Deployment trigger |
|---|---|---|
| `self-service-dev` | No manual approval; validation stage must pass | Merge to `main` |
| `self-service-test` | `platform-team` | Successful validation |
| `self-service-prod` | `platform-team` and `data-owner` | Successful validation |

Before running the pipeline, replace the `REPLACE_WITH_*` variables in
`pipelines/intake-pipeline.yml` with an Azure service connection and an existing
Azure Storage account/container for Terraform state. The state account should
use private access and RBAC; the pipeline identity needs `Storage Blob Data
Contributor` on the state container and `Contributor` on the target scope.

Set `requestFile` and `requestEnvironment` for the request being promoted. Only
the matching environment stage runs, so a development request cannot be applied
to test or production accidentally.

Approvals belong to the environment, not the YAML request. The request declares
which groups are expected, while the environment remains the enforcement point.

## Security gates

The intake pipeline blocks a request unless schema validation, Terraform
validation, formatting, and the infrastructure security scan pass. The catalog
also enforces private network access, TLS 1.2, HTTPS-only storage traffic, and
cost-center tags so a requester cannot weaken those controls in YAML.