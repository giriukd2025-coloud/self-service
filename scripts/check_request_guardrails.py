#!/usr/bin/env python3
"""Enforce security and ownership declarations on a self-service request."""
import sys

import yaml


REQUIRED_GATES = {
    "requireTfsecPass": True,
    "requireNoPublicNetworkAccess": True,
    "requireTaggedCostCenter": True,
}


def main(path: str) -> int:
    with open(path, encoding="utf-8") as request_file:
        request = yaml.safe_load(request_file)

    failures = []
    gates = request.get("securityGates", {})
    for key, expected in REQUIRED_GATES.items():
        if gates.get(key) != expected:
            failures.append(f"securityGates.{key} must be {expected}")

    if not request.get("costCenter"):
        failures.append("costCenter is required for all infra requests")

    if failures:
        print(f"Guardrail check failed for {path}:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"Guardrail check passed for {path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} REQUEST.yaml", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))#!/usr/bin/env python3
"""
Checks a request's declared securityGates against the platform's non-negotiables.
This is deliberately separate from tfsec/checkov: those catch what the
Terraform *would create*; this catches what the requester *asked for* — so a
bad request fails fast, before a plan is even generated.
"""
import sys
import yaml

REQUIRED_GATES = {
    "requireNoPublicNetworkAccess": True,
    "requireTaggedCostCenter": True,
}


def main(path: str):
    with open(path) as f:
        request = yaml.safe_load(f)

    gates = request.get("securityGates", {})
    failures = []

    for key, expected in REQUIRED_GATES.items():
        if gates.get(key) != expected:
            failures.append(f"securityGates.{key} must be {expected}")

    if not request.get("costCenter"):
        failures.append("costCenter is required for all infra requests")

    if failures:
        print(f"Guardrail check failed for {path}:")
        for f_ in failures:
            print(f"  - {f_}")
        sys.exit(1)

    print(f"Guardrail check passed for {path}")


if __name__ == "__main__":
    main(sys.argv[1])
