#!/usr/bin/env python3
"""Render an approved YAML request into Terraform variables."""
import argparse
import json
import sys
import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.request, encoding="utf-8") as request_file:
        request = yaml.safe_load(request_file)

    if request["environment"] != args.environment:
        print(
            f"Request targets {request['environment']}, not {args.environment}; "
            "skipping deployment."
        )
        sys.exit(2)

    resource_groups = [r for r in request["resources"] if r["type"] == "resource-group"]
    if len(resource_groups) != 1:
        raise ValueError("A request must contain exactly one resource-group resource")

    storage_accounts = [
        {"name": r["name"], "tier": r["tier"]}
        for r in request["resources"]
        if r["type"] == "storage-account"
    ]
    key_vaults = [
        {
            "name": r["name"],
            "soft_delete_retention_days": r["softDeleteRetentionDays"],
        }
        for r in request["resources"]
        if r["type"] == "key-vault"
    ]

    with open(args.output, "w", encoding="utf-8") as output_file:
        output_file.write(f'environment = "{request["environment"]}"\n')
        output_file.write(f'resource_group_name = "{resource_groups[0]["name"]}"\n')
        output_file.write(f'cost_center = "{request["costCenter"]}"\n')
        output_file.write('location = "eastus"\n')
        output_file.write(f"storage_accounts = {json.dumps(storage_accounts)}\n")
        output_file.write(f"key_vaults = {json.dumps(key_vaults)}\n")


if __name__ == "__main__":
    main()