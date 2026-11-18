#!/usr/bin/env bash
# Regenerate the LTS EV examples (canonical + devkit copies) from the rc set.
# Usage: build-examples.sh <rc examples dir> <canonical out> <devkit out>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
rc="$1"; canon="$2"; devkit="$3"
# replace only the generated JSON; README and other hand-written files stay
for d in "$canon" "$devkit"; do [ -d "$d" ] && find "$d" -name '*.json' -delete; done
python3 "$HERE/rc2lts.py" "$rc" "$canon" >/dev/null
python3 "$HERE/variants.py" "$canon" >/dev/null
python3 "$HERE/rc2lts.py" "$rc" "$devkit" --profile devkit >/dev/null
python3 "$HERE/variants.py" "$devkit" >/dev/null
# variants copy ids from their source files; normalise the few literals they add
find "$devkit" -name '*.json' -exec sed -i '' -e 's/example-bpp\.com/bpp.example.com/g' -e 's/example-bap\.com/bap.example.com/g' {} +
echo "canonical: $(find "$canon" -name '*.json' | wc -l | tr -d ' ') files; devkit: $(find "$devkit" -name '*.json' | wc -l | tr -d ' ') files"
