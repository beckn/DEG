#!/usr/bin/env python3
"""
Demand Flex Settlement Evaluator

Runs the demand_flex.rego policy against an on_status JSON payload and either
prints a formatted settlement report or generates a settled JSON with
consideration blocks injected.

Usage:
    # Print report
    python3 scripts/evaluate_demand_flex_settlement.py \\
        examples/demand-flex/v2/on-status-response-settled.json

    # Generate settled JSON from actuals (must include offerAttributes)
    python3 scripts/evaluate_demand_flex_settlement.py \\
        examples/demand-flex/v2/on-status-response-settled.json \\
        --generate examples/demand-flex/v2/on-status-response-settled.json

Requirements:
    OPA CLI installed (brew install opa)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_POLICY = REPO_ROOT / "specification" / "policies" / "demand_flex_revenue.rego"
QUERY = "data.deg.contracts.demand_flex"

CONTRACT_POLICY_CONTEXT = "https://raw.githubusercontent.com/beckn/DEG/refs/heads/p2p-trading-becknv2/specification/schema/DEGContractPolicy/v2.0/context.jsonld"


def run_opa_eval(policy_path: Path, input_path: Path) -> dict:
    """Run OPA eval and return the result dict."""
    cmd = [
        "opa", "eval",
        "-d", str(policy_path),
        "--input", str(input_path),
        "--format", "json",
        QUERY,
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


def build_revenue_flows(rego_result: dict) -> list:
    """Extract revenue_flows from rego result."""
    return rego_result.get("revenue_flows", [])


def generate_settled_json(input_path: Path, output_path: Path, rego_result: dict):
    """Read input payload, inject revenueFlows into contractAttributes, write settled JSON."""
    with open(input_path) as f:
        payload = json.load(f)

    contract = payload["message"]["contract"]

    # Inject revenueFlows into contractAttributes
    ca = contract.get("contractAttributes", {})
    ca["revenueFlows"] = build_revenue_flows(rego_result)
    contract["contractAttributes"] = ca

    # Remove consideration if present (replaced by revenueFlows)
    contract.pop("consideration", None)

    # Update performance status to SETTLED
    for perf in contract.get("performance", []):
        perf["status"] = {
            "code": "SETTLED",
            "name": "Event completed, M&V verified, settlement computed",
        }

    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated: {output_path}")


def print_report(data: dict):
    """Print a formatted settlement report."""
    event_hours = data.get("event_hours", "?")
    components = data.get("settlement_components", [])
    total = data.get("total_settlement", 0)
    net_zero = data.get("net_zero_ok", False)
    violations = data.get("violations", [])
    flows = data.get("revenue_flows", [])

    print()
    print("=" * 60)
    print("  Demand Flex Settlement Report")
    print("=" * 60)
    print(f"  Event duration : {event_hours}h")
    print()

    if components:
        print("  Per-meter breakdown:")
        for c in components:
            print(f"    {c['lineId']:<35} {c['value']:>10.2f} {c['currency']}")
        print(f"    {'':─<35} {'':─>10}──────")
        print(f"    {'TOTAL':<35} {total:>10.2f} INR")
    else:
        print("  No settlement components computed.")

    print()
    print("  Revenue flows:")
    flow_sum = 0
    for f in flows:
        sign = "+" if f["value"] >= 0 else ""
        print(f"    {f['role']:<10} {sign}{f['value']:>10.2f} {f['currency']}")
        flow_sum += f["value"]
    print(f"    {'SUM':<10} {'':>10}{flow_sum:+.2f}")
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
        description="Evaluate demand-flex settlement via OPA/Rego policy"
    )
    parser.add_argument(
        "input",
        help="Path to on_status JSON payload (must include offerAttributes and performance actuals)"
    )
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY),
        help=f"Path to demand_flex.rego (default: {DEFAULT_POLICY.relative_to(REPO_ROOT)})"
    )
    parser.add_argument(
        "--generate", "-g",
        metavar="OUTPUT",
        help="Generate settled JSON with consideration injected and write to OUTPUT path"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    policy_path = Path(args.policy)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
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

    data = run_opa_eval(policy_path, input_path)

    if args.generate:
        generate_settled_json(input_path, Path(args.generate), data)

    print_report(data)


if __name__ == "__main__":
    main()
