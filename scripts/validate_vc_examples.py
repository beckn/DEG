#!/usr/bin/env python3
"""Validate JSON / NDJSON example files against an attributes.yaml schema.

Pipeline:
  1. Run `npx @redocly/cli bundle --dereferenced` to inline all $refs
     (local and remote) into a single self-contained YAML document.
  2. Pick the target schema by name (or the sole entry in
     `components.schemas`, or the one matching `info.title`).
  3. Validate each example with `jsonschema.Draft202012Validator`. Any
     residual remote $refs that Redocly left unresolved are fetched on
     demand through a `referencing.Registry` — outbound HTTPS required.

Usage:
    python3 scripts/validate_vc_examples.py \\
        specification/schema/EnergyMeterDataCredential/v1.0/attributes.yaml

    python3 scripts/validate_vc_examples.py \\
        specification/schema/EnergyMeterDataCredential/v1.0/attributes.yaml \\
        path/to/example.json path/to/stream.ndjson

    python3 scripts/validate_vc_examples.py attributes.yaml --schema MySchema
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


def bundle(attributes_path: Path) -> dict:
    """Dereference attributes.yaml via Redocly CLI and return the bundled doc."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        out_path = Path(tmp.name)
    cmd = [
        "npx", "--yes", "@redocly/cli@latest", "bundle",
        str(attributes_path), "--dereferenced", "--ext", "yaml",
        "-o", str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("npx not found. Install Node.js to run @redocly/cli.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"redocly bundle failed:\n{e.stderr}")
    with open(out_path) as f:
        return yaml.safe_load(f)


def pick_schema(bundled: dict, name: str | None) -> tuple[str, dict]:
    """Return (schema_name, schema_obj) from components.schemas."""
    schemas = (bundled.get("components") or {}).get("schemas") or {}
    if not schemas:
        sys.exit("bundle has no components.schemas — cannot validate")
    if name:
        if name not in schemas:
            sys.exit(f"schema {name!r} not found; available: {sorted(schemas)}")
        return name, schemas[name]
    if len(schemas) == 1:
        key = next(iter(schemas))
        return key, schemas[key]
    title = (bundled.get("info") or {}).get("title")
    if title and title in schemas:
        return title, schemas[title]
    sys.exit(
        f"multiple schemas in bundle; pass --schema NAME. "
        f"available: {sorted(schemas)}"
    )


def build_registry() -> Registry:
    """Registry that lazily fetches residual remote $refs over HTTPS."""
    def retrieve(uri: str) -> Resource:
        resp = requests.get(uri, timeout=15)
        resp.raise_for_status()
        return Resource(contents=yaml.safe_load(resp.text), specification=DRAFT202012)
    return Registry(retrieve=retrieve)


def discover_examples(attributes_path: Path) -> list[Path]:
    ex_dir = attributes_path.parent / "examples"
    if not ex_dir.is_dir():
        return []
    return sorted([*ex_dir.glob("*.json"), *ex_dir.glob("*.ndjson")])


def iter_instances(path: Path):
    """Yield (label, instance) for each JSON or NDJSON entry in `path`."""
    if path.suffix == ".ndjson":
        with open(path) as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    yield f"{path.name}:line{lineno}", json.loads(line)
    else:
        with open(path) as f:
            yield path.name, json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate VC examples against an attributes.yaml schema."
    )
    ap.add_argument("attributes", type=Path, help="Path to attributes.yaml")
    ap.add_argument(
        "examples", nargs="*", type=Path,
        help="Example JSON/NDJSON files (default: <attributes-dir>/examples/*)",
    )
    ap.add_argument(
        "--schema",
        help="Schema name in components.schemas (default: single entry or info.title)",
    )
    args = ap.parse_args()

    if not args.attributes.is_file():
        sys.exit(f"attributes.yaml not found: {args.attributes}")

    bundled = bundle(args.attributes)
    schema_name, schema = pick_schema(bundled, args.schema)

    examples = args.examples or discover_examples(args.attributes)
    if not examples:
        sys.exit(
            "no example files found; pass paths explicitly "
            "or create <attributes-dir>/examples/"
        )

    validator = Draft202012Validator(schema, registry=build_registry())

    print(f"Validating against components.schemas.{schema_name} from {args.attributes}")
    fail = 0
    for path in examples:
        for label, instance in iter_instances(path):
            errors = list(validator.iter_errors(instance))
            if errors:
                fail += 1
                print(f"FAIL  {label}")
                for e in errors:
                    print(f"      {e.json_path}: {e.message}")
            else:
                print(f"PASS  {label}")
    if fail:
        print(f"\n{fail} example(s) failed validation.")
        return 1
    print("\nAll examples valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
