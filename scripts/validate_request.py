#!/usr/bin/env python3
"""Validate a self-service basic infrastructure request."""
import sys
import glob
import yaml
from jsonschema import validate, ValidationError

SCHEMA = {
    "type": "object",
    "required": ["requestName", "owner", "costCenter", "environment",
                  "resources", "network", "approvals", "securityGates"],
    "properties": {
        "requestName": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "owner": {"type": "string", "format": "email"},
        "costCenter": {"type": "string", "pattern": "^CC-[0-9]+$"},
        "environment": {"enum": ["dev", "test", "prod"]},
        "resources": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type", "name"],
                "properties": {
                    "type": {"enum": ["resource-group", "storage-account", "key-vault"]},
                    "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
                    "tier": {"enum": ["Standard_LRS", "Standard_GRS", "Standard_ZRS"]},
                    "resourceGroup": {"type": "string"},
                    "softDeleteRetentionDays": {"type": "integer", "minimum": 7},
                },
            },
        },
        "network": {
            "type": "object",
            "required": ["vnetName", "subnetName"],
            "properties": {
                "vnetName": {"type": "string", "pattern": "^vnet-[a-z0-9-]+$"},
                "subnetName": {"type": "string", "pattern": "^snet-[a-z0-9-]+$"},
            },
        },
        "approvals": {
            "type": "object",
            "required": ["test", "prod"],
            "properties": {
                "test": {"type": "string", "minLength": 1},
                "prod": {"type": "string", "minLength": 1},
            },
        },
        "securityGates": {
            "type": "object",
            "required": ["requireTfsecPass", "requireNoPublicNetworkAccess",
                          "requireTaggedCostCenter"],
            "properties": {
                "requireTfsecPass": {"const": True},
                "requireNoPublicNetworkAccess": {"const": True},
                "requireTaggedCostCenter": {"const": True},
            },
        },
    },
}


def validate_file(path: str) -> list[str]:
    errors = []
    with open(path) as f:
        request = yaml.safe_load(f)

    try:
        validate(instance=request, schema=SCHEMA)
    except ValidationError as e:
        errors.append(f"{path}: {e.message}")
        return errors

    # Extra guardrails beyond plain schema shape.
    if request["environment"] == "prod" and not request["approvals"].get("prod"):
        errors.append(f"{path}: production requests require a prod approval group")

    if request["network"]["vnetName"].startswith("new-"):
        errors.append(
            f"{path}: network.vnetName looks self-provisioned. "
            "Self-service only consumes Infra-owned VNets — request one from Infra first."
        )

    return errors


def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else glob.glob(
        "onboarding/infra-requests/*.yaml"
    )
    all_errors = []
    for path in glob.glob(f"{paths[0]}*.yaml") if len(paths) == 1 else paths:
        all_errors.extend(validate_file(path))

    if all_errors:
        print("Validation failed:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)

    print("All onboarding requests valid.")


if __name__ == "__main__":
    main()
