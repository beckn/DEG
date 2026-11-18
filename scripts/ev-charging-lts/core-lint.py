#!/usr/bin/env python3
"""Closed-world lint for Beckn 2.0 LTS payloads.

ONIX validates against beckn.yaml, where several core objects (Offer, Resource,
Commitment, Participant, Settlement, Consideration) leave additionalProperties open,
so fields the spec never declares pass validation. This lint walks each payload
against the LTS schema and reports every key that no core schema declares. Objects
in *Attributes slots (JSON-LD packs) are skipped: their packs are validated by ONIX.

Usage: core-lint.py <beckn.yaml> <examples dir>
"""
import json, pathlib, sys, yaml

spec = yaml.safe_load(open(sys.argv[1]))
paths = spec["paths"]


def resolve(sch):
    """Return (properties, items_schema, is_open_attributes) for a schema node."""
    if not isinstance(sch, dict):
        return {}, None, False
    if "$ref" in sch:
        ref = sch["$ref"]
        if ref.endswith("/Attributes"):
            return {}, None, True
        node = spec
        for part in ref.lstrip("#/").split("/"):
            node = node[part]
        props, items, open_ = resolve(node)
        extra = {k: v for k, v in sch.items() if k != "$ref"}
        if extra:
            p2, i2, _ = resolve(extra)
            props = {**props, **p2}
            items = items or i2
        return props, items, open_
    props, items, open_ = dict(sch.get("properties", {})), sch.get("items"), False
    # A name listed in `required` counts as declared even without a property entry
    # (LTS Commitment.resources requires `quantity`, which Resource never declares).
    if isinstance(sch.get("required"), list):
        for name in sch["required"]:
            props.setdefault(name, {})
    for key in ("allOf", "oneOf", "anyOf"):
        for part in sch.get(key, []):
            p, i, o = resolve(part)
            for k, v in p.items():
                props[k] = {"allOf": [props[k], v]} if k in props else v
            items = items or i
            open_ = open_ or o
    return props, items, open_


def walk(obj, sch, path, out):
    props, items, open_ = resolve(sch)
    if open_:
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, items or {}, f"{path}[{i}]", out)
        return
    if not isinstance(obj, dict) or not props:
        return
    for k, v in obj.items():
        if path == "$" and k == "error":
            continue  # async business error beside message (NFH-008 draft)
        if k not in props:
            out.append(f"{path}.{k}")
        else:
            walk(v, props[k], f"{path}.{k}", out)


total = 0
for f in sorted(pathlib.Path(sys.argv[2]).rglob("*.json")):
    d = json.load(open(f))
    if "context" not in d:
        continue
    body = paths[f"/{d['context']['action']}"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    out = []
    walk(d, body, "$", out)
    total += len(out)
    print(f"{'ok  ' if not out else 'WARN'} {f.relative_to(sys.argv[2])}"
          + ("" if not out else "  undeclared: " + ", ".join(out[:8]) + (" …" if len(out) > 8 else "")))
print(f"\n{total} undeclared fields")
sys.exit(1 if total else 0)
