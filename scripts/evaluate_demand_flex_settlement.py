#!/usr/bin/env python3
"""
DEG Contract Settlement Evaluator

Runs any OPA/Rego policy against a beckn contract payload, prints a settlement
report, and optionally generates a settled JSON with revenueFlows injected
into contractAttributes.

Works with any DEG contract type (demand-flex, P2P trade, EV charging, etc.)
as long as the rego exports: revenue_flows, violations, and optionally
settlement_components / total_settlement.

The policy path and query path are read from the payload's
contractAttributes.policy — no hardcoded defaults needed.

Usage:
    # Print report (reads policy from contractAttributes.policy)
    python3 scripts/evaluate_deg_settlement.py <payload.json>

    # Override policy file
    python3 scripts/evaluate_deg_settlement.py <payload.json> --policy path/to/custom.rego

    # Generate settled JSON
    python3 scripts/evaluate_deg_settlement.py <payload.json> -g <output.json>

Requirements:
    OPA CLI installed (brew install opa)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _extract_policy_info(payload: dict) -> tuple:
    """Extract policy queryPath from contractAttributes, or from offer's contractTerms."""
    ca = payload.get("message", {}).get("contract", {}).get("contractAttributes", {})
    policy = ca.get("policy", {})
    if policy.get("queryPath"):
        return policy["queryPath"]

    # Fallback: look in offer's contractTerms
    for c in payload.get("message", {}).get("contract", {}).get("commitments", []):
        ct = c.get("offer", {}).get("offerAttributes", {}).get("contractTerms", {})
        p = ct.get("policy", {})
        if p.get("queryPath"):
            return p["queryPath"]

    return None


def run_opa_eval(policy_path: Path, input_path: Path, query: str) -> dict:
    """Run OPA eval and return the result dict."""
    cmd = [
        "opa", "eval",
        "-d", str(policy_path),
        "--input", str(input_path),
        "--format", "json",
        query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"OPA error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    output = json.loads(result.stdout)
    try:
        return output["result"][0]["expressions"][0]["value"]
    except (KeyError, IndexError):
        print(f"Unexpected OPA output:\n{json.dumps(output, indent=2)}", file=sys.stderr)
        sys.exit(1)


def generate_settled_json(input_path: Path, output_path: Path, rego_result: dict):
    """Read input payload, inject revenueFlows into contractAttributes, write settled JSON."""
    with open(input_path) as f:
        payload = json.load(f)

    contract = payload["message"]["contract"]

    ca = contract.get("contractAttributes", {})
    ca["revenueFlows"] = rego_result.get("revenue_flows", [])
    contract["contractAttributes"] = ca

    contract.pop("consideration", None)

    for perf in contract.get("performance", []):
        perf["status"] = {
            "code": "SETTLED",
            "name": "Settlement computed from policy evaluation",
        }

    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated: {output_path}")


def print_report(data: dict):
    """Print a settlement report from rego output. Only assumes revenue_flows and violations."""
    flows = data.get("revenue_flows", [])
    violations = data.get("violations", [])
    net_zero = data.get("net_zero_ok", None)

    # Optional domain-specific fields
    components = data.get("settlement_components", [])
    total = data.get("total_settlement", None)

    print()
    print("=" * 60)
    print("  DEG Contract Settlement Report")
    print("=" * 60)

    # Print any domain-specific breakdown if present
    if components:
        currency = components[0].get("currency", "") if components else ""
        print()
        print("  Line items:")
        for c in components:
            print(f"    {c.get('lineId', '?'):<35} {c['value']:>10.2f} {c.get('currency', '')}")
        if total is not None:
            print(f"    {'':─<35} {'':─>10}──────")
            print(f"    {'TOTAL':<35} {total:>10.2f} {currency}")

    # Revenue flows — the standard output
    print()
    print("  Revenue flows:")
    flow_sum = 0
    for f in flows:
        sign = "+" if f["value"] >= 0 else ""
        print(f"    {f['role']:<12} {sign}{f['value']:>10.2f} {f.get('currency', '')}")
        flow_sum += f["value"]
    print(f"    {'SUM':<12} {'':>10}{flow_sum:+.2f}")

    if net_zero is not None:
        print(f"  Net-zero verified : {'YES' if net_zero else 'NO'}")

    if violations:
        print()
        print(f"  Violations ({len(violations)}):")
        for v in sorted(violations):
            print(f"    - {v}")
    else:
        print(f"  Violations        : none")

    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate DEG contract settlement via OPA/Rego policy"
    )
    parser.add_argument(
        "input",
        help="Path to beckn contract JSON payload"
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to .rego file (default: read from contractAttributes.policy in payload)"
    )
    parser.add_argument(
        "--query",
        default=None,
        help="OPA query path (default: read from contractAttributes.policy.queryPath in payload)"
    )
    parser.add_argument(
        "--generate", "-g",
        metavar="OUTPUT",
        help="Generate settled JSON with revenueFlows injected and write to OUTPUT path"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read payload to extract policy info
    with open(input_path) as f:
        payload = json.load(f)

    # Resolve query path
    query = args.query or _extract_policy_info(payload)
    if not query:
        print("No queryPath found in contractAttributes.policy or --query flag", file=sys.stderr)
        sys.exit(1)

    # Resolve policy file
    if args.policy:
        policy_path = Path(args.policy)
    else:
        # Try to find policy file relative to repo root based on policyUrl
        ca = payload.get("message", {}).get("contract", {}).get("contractAttributes", {})
        policy_url = ca.get("policy", {}).get("url", "")
        # Extract path after /specification/ or /policies/
        for marker in ["/specification/policies/", "/policies/"]:
            if marker in policy_url:
                relative = policy_url.split(marker)[-1]
                repo_root = Path(__file__).parent.parent
                candidate = repo_root / "specification" / "policies" / relative
                if candidate.exists():
                    policy_path = candidate
                    break
        else:
            print("Cannot resolve policy file. Use --policy flag.", file=sys.stderr)
            sys.exit(1)

    if not policy_path.exists():
        print(f"Policy file not found: {policy_path}", file=sys.stderr)
        sys.exit(1)

    # Check OPA is installed
    try:
        subprocess.run(["opa", "version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("OPA CLI not found. Install with: brew install opa", file=sys.stderr)
        sys.exit(1)

    data = run_opa_eval(policy_path, input_path, query)

    if args.generate:
        generate_settled_json(input_path, Path(args.generate), data)

    print_report(data)


if __name__ == "__main__":
    main()
