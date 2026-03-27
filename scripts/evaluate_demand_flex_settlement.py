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
DEFAULT_POLICY = REPO_ROOT / "specification" / "policies" / "demand_flex.rego"
QUERY = "data.deg.contracts.demand_flex"

PRICE_SPEC_CONTEXT = "https://schema.beckn.io/PriceSpecification/2.1/context.jsonld"


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


def build_consideration(payload: dict, rego_result: dict) -> list:
    """Build consideration array from rego settlement result and payload participants."""
    total = rego_result.get("total_settlement", 0)
    components = rego_result.get("settlement_components", [])
    currency = rego_result.get("_currency", "INR")

    # Extract participant IDs from the contract
    contract = payload["message"]["contract"]
    participants = contract.get("participants", [])

    # Try to identify BPP (utility) and BAP (aggregator) from participants
    bpp_id = None
    bap_id = None
    for p in participants:
        pid = p.get("id", "")
        if pid:
            # First participant is typically the BPP (utility), second is BAP (aggregator)
            if bpp_id is None:
                bpp_id = pid
            elif bap_id is None:
                bap_id = pid

    # Fall back to context if participants not available
    if not bpp_id:
        bpp_id = payload.get("context", {}).get("bppId", "unknown-bpp")
    if not bap_id:
        bap_id = payload.get("context", {}).get("bapId", "unknown-bap")

    # Build per-meter components for the payer's breakdown
    price_components = []
    for c in components:
        price_components.append({
            "type": "FEE",
            "value": c["value"],
            "currency": c["currency"],
            "description": c["lineSummary"],
        })

    return [
        {
            "id": bpp_id,
            "status": {"code": "PAYABLE"},
            "considerationAttributes": {
                "@context": PRICE_SPEC_CONTEXT,
                "@type": "PriceSpecification",
                "value": total,
                "currency": currency,
                "components": price_components,
            },
        },
        {
            "id": bap_id,
            "status": {"code": "RECEIVABLE"},
            "considerationAttributes": {
                "@context": PRICE_SPEC_CONTEXT,
                "@type": "PriceSpecification",
                "value": total,
                "currency": currency,
            },
        },
    ]


def generate_settled_json(input_path: Path, output_path: Path, rego_result: dict):
    """Read the input payload, inject consideration, write settled JSON."""
    with open(input_path) as f:
        payload = json.load(f)

    contract = payload["message"]["contract"]

    # Inject consideration
    contract["consideration"] = build_consideration(payload, rego_result)

    # Add PriceSpecification context to schemaContext if not present
    schema_ctx = payload.get("context", {}).get("schemaContext", [])
    if PRICE_SPEC_CONTEXT not in schema_ctx:
        schema_ctx.append(PRICE_SPEC_CONTEXT)
        payload["context"]["schemaContext"] = schema_ctx

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
    utility_out = data.get("utility_outflow", 0)
    aggregator_in = data.get("aggregator_inflow", 0)

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
    print(f"  Utility outflow   : {utility_out:,.2f}")
    print(f"  Aggregator inflow : {aggregator_in:,.2f}")
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
