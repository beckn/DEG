"""Generate message-only templates for beckn/sandbox BPP webhook (PERSONA=bpp)."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
EXAMPLES = ROOT.parent.parent.parent / "examples" / "demand-flex" / "v2"
BDR = EXAMPLES / "bdr-e2e"
OUT = ROOT / "bpp-response"
OUT.mkdir(parents=True, exist_ok=True)

# (source under examples/demand-flex/v2 or bdr-e2e, dest filename under bpp-response)
PAIRS: list[tuple[pathlib.Path, str]] = [
    (EXAMPLES / "on-select-response.json", "on_select.json"),
    (EXAMPLES / "on-init-response.json", "on_init.json"),
    (EXAMPLES / "on-confirm-response.json", "on_confirm.json"),
    (BDR / "02-on-status-bdr-baselines.json", "on_status.json"),
]

for src, dst in PAIRS:
    data = json.loads(src.read_text(encoding="utf-8"))
    (OUT / dst).write_text(
        json.dumps({"message": data["message"]}, indent=2) + "\n",
        encoding="utf-8",
    )

# BDR-capable on_update / on_cancel (full contract slots; sandbox merges request context)
for src_name, dst in (
    ("on-update-response-bdr.json", "on_update.json"),
    ("on-cancel-callback-example.json", "on_cancel.json"),
):
    src = BDR / src_name
    data = json.loads(src.read_text(encoding="utf-8"))
    (OUT / dst).write_text(
        json.dumps({"message": data["message"]}, indent=2) + "\n",
        encoding="utf-8",
    )

print("Wrote:", sorted(p.name for p in OUT.iterdir()))
