# Developer Guide

This repository provides a guarded self-service path for basic Azure infrastructure. A developer submits a YAML request; the pipeline validates it, runs infrastructure security checks, and applies the approved Terraform catalog through Azure DevOps environment gates.

## Repository layout

```text
onboarding/infra-requests/       Self-service YAML requests
terraform/                       Terraform root module and approved catalog
terraform/modules/basic-infra/   Resource-group, storage, and Key Vault module
scripts/validate_request.py      Request schema and policy validation
scripts/check_request_guardrails.py
                                  Required security declarations
scripts/render_request_tfvars.py YAML-to-Terraform variable conversion
pipelines/intake-pipeline.yml    Validation and deployment pipeline
docs/                            Platform and developer documentation
```

## Prerequisites

Install the following locally:

- Python 3.11 or newer
- Python packages `pyyaml` and `jsonschema`
- Terraform 1.9.x or newer, compatible with the repository constraint
- Azure CLI, when testing authenticated Terraform operations
- Access to the Azure DevOps project and repository

Install Python dependencies:

```powershell
py -m pip install pyyaml jsonschema
```

## Create a request

Copy [the sample request](../onboarding/infra-requests/sales-analytics-basics.yaml) to a new file under `onboarding/infra-requests/`:

```powershell
Copy-Item onboarding\infra-requests\sales-analytics-basics.yaml onboarding\infra-requests\my-request.yaml
```

Set these fields:

| Field | Rule |
|---|---|
| `requestName` | Lowercase letters, numbers, and hyphens only |
| `owner` | Request owner email address |
| `costCenter` | Format `CC-1234` |
| `environment` | Exactly `dev`, `test`, or `prod` |
| `resources` | Only `resource-group`, `storage-account`, and `key-vault` |
| `network` | Existing infrastructure-owned VNet and subnet |
| `approvals` | Non-empty `test` and `prod` approver groups |
| `securityGates` | All required values must remain `true` |

The request can only consume an existing private VNet and subnet. It cannot create networking or introduce a new resource type. Adding a new catalog resource is a platform-team change in `terraform/modules/basic-infra/`.

## Validate locally

Run from the repository root:

```powershell
py scripts\validate_request.py onboarding\infra-requests\my-request.yaml
py scripts\check_request_guardrails.py onboarding\infra-requests\my-request.yaml
```

Validate Terraform formatting and configuration:

```powershell
terraform fmt -check -recursive terraform
terraform init -backend=false terraform
terraform validate terraform
```

Render a request into Terraform variables without applying it:

```powershell
py scripts\render_request_tfvars.py onboarding\infra-requests\my-request.yaml --environment dev --output terraform\dev.auto.tfvars
```

The renderer exits without deployment when the request environment does not match `--environment`. Remove generated `*.auto.tfvars` files after local testing if they are not ignored by Git.

## Branch and pull request flow

Use one short-lived branch per request:

```powershell
git checkout -b feature/my-request
git add onboarding/infra-requests/my-request.yaml
git commit -m "Add my self-service infrastructure request"
git push -u origin feature/my-request
```

Open a pull request into `main`. The `main` branch requires:

- At least one platform-team reviewer
- Successful `pipelines/intake-pipeline.yml` validation
- Resolved comments
- A linked work item
- No direct pushes

## Azure DevOps setup

Before enabling deployment, configure these pipeline variables in the Azure DevOps UI or a variable group. Do not commit credentials or secrets.

| Variable | Value |
|---|---|
| `azureServiceConnection` | Azure Resource Manager service connection name |
| `terraformStateResourceGroup` | Existing resource group for Terraform state |
| `terraformStateStorageAccount` | Existing state storage account |
| `terraformStateContainer` | State blob container, normally `tfstate` |
| `terraformStateKey` | Base state key for this platform |
| `requestFile` | Request YAML path being promoted |
| `requestEnvironment` | Matching `dev`, `test`, or `prod` value |

The pipeline identity needs `Contributor` on the target deployment scope and `Storage Blob Data Contributor` on the Terraform state container. Prefer a user-assigned or project-managed identity with least-privilege scope.

The state storage account should use private access, encryption, soft delete, and RBAC. The state resource group and storage account are prerequisites; this repository does not create them.

## Approval environments

Create Azure DevOps environments with these exact names:

| Environment | Approval configuration |
|---|---|
| `self-service-dev` | No manual approval; validation must pass |
| `self-service-test` | Approval from `platform-team` |
| `self-service-prod` | Approval from `platform-team` and `data-owner` |

The pipeline runs only the stage matching `requestEnvironment`. The request's `approvals` section documents the expected groups, while Azure DevOps environments enforce the approval gate.

## What gets created

The approved Terraform catalog creates:

- One resource group
- Zero or more approved storage accounts with public network access disabled, TLS 1.2, and HTTPS-only traffic
- Zero or more standard Key Vaults with public network access disabled and soft-delete retention
- Cost-center and `managedBy=self-service-platform` tags

Terraform authenticates through the Azure DevOps service connection. The Azure subscription ID is read from the authenticated Azure CLI session and passed explicitly to the AzureRM provider.

## Pipeline stages

`Validate` runs on pull requests and `main`:

1. Installs Python validation dependencies.
2. Validates all request YAML files.
3. Enforces required security declarations.
4. Checks Terraform formatting and validity.
5. Runs the Trivy infrastructure scan.

The matching deployment stage runs after validation on `main`:

1. Checks out the repository.
2. Installs the pinned Terraform version.
3. Converts the selected request to Terraform variables.
4. Initializes the AzureRM remote backend.
5. Creates a Terraform plan.
6. Applies the approved plan after the Azure DevOps environment gate.

## Adding a new catalog resource

A new resource type requires a platform-team change:

1. Extend the Terraform module with fixed security defaults.
2. Extend the request schema's allowed resource types.
3. Extend `render_request_tfvars.py`.
4. Add or update security tests and the sample request.
5. Run request and Terraform validation locally.
6. Submit the module change through the normal protected pull request process.

Do not allow request YAML to control security-sensitive Terraform settings such as public network access, TLS minimums, or required tags.

## Troubleshooting

- **Request validation fails:** Check the required fields and allowed values in `scripts/validate_request.py`.
- **Guardrail validation fails:** Keep all required `securityGates` values set to `true` and provide `costCenter`.
- **Terraform backend fails:** Verify the state resource group, storage account, container, service connection, and RBAC role.
- **Azure authorization fails:** Confirm the pipeline identity has `Contributor` at the intended target scope.
- **The deployment stage is skipped:** Confirm `requestEnvironment` matches the request's `environment` and that the build ran from `main`.
- **Security scan fails:** Inspect the Terraform resource settings and resolve HIGH or CRITICAL findings before requesting approval.

## Current boundaries

This implementation is intentionally limited to the approved basic-infrastructure catalog. It does not create VNets, subnets, private endpoints, Terraform state storage, Azure DevOps environments, or service connections. Those are platform prerequisites and should be provisioned and governed separately.
