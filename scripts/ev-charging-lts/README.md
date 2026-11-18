# EV charging examples: rc → Beckn 2.0 LTS

Tools that produced `examples/ev-charging/v2` and `devkits/ev-charging/uc1-ev-charging/examples` from the earlier `core-2.0.0-rc-eos-release` set (now in `examples/ev-charging/v2-rc`), and that check them.

| Tool | What it does |
|---|---|
| `rc2lts.py` | Converts each rc example to LTS. The mapping rules are in its header and in `examples/ev-charging/v2/README.md`; it also fixes the rc data errors listed there. `--profile devkit` writes the devkit copy (registered test participant ids). |
| `variants.py` | Adds the use-case variants the rc set lacked (slot unavailable, outstanding dues, start rejected, undercharge refund, overcharge, early completion, invoice ready, cancel preview, CPO cancellation, support resolved, track, catalog publish), derived from the same flow so ids and amounts stay consistent. |
| `correlate.py` | Gives each request and the callback(s) answering it one `messageId`, gives every other interaction its own, and keeps callbacks timestamped after their request. |
| `build-examples.sh` | Runs the converter, the variants and the correlation pass, for the canonical and devkit sets. Only generated JSON is replaced. |
| `core-lint.py` | Closed-world lint: reports any field the LTS core schema does not declare (ONIX accepts them because several core objects are open). |
| `onix-check.py` | POSTs every example through a running devkit (BAP caller for requests, BPP caller for callbacks) and reports ACK/NACK, i.e. signature, registry, LTS core and attribute-pack validation. |

```bash
# from the repo root
scripts/ev-charging-lts/build-examples.sh examples/ev-charging/v2-rc examples/ev-charging/v2 devkits/ev-charging/uc1-ev-charging/examples
python3 scripts/ev-charging-lts/core-lint.py <path to core-v2.0.0-lts beckn.yaml> examples/ev-charging/v2
# with the devkit running (devkits/ev-charging/install):
python3 scripts/ev-charging-lts/onix-check.py examples/ev-charging/v2
```

The generated examples are the source of truth from here on; edit them directly and keep both checks passing. The tools stay for review and for regenerating if the mapping changes.
