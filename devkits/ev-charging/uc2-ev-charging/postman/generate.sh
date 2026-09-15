#!/usr/bin/env bash
# Generate the Postman collections for ev-charging uc2-ev-charging.
# Run from any directory — paths are resolved relative to this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../" && pwd)"
GENERATOR="$REPO_ROOT/scripts/generate_postman_collection.py"
OUTPUT_DIR="devkits/ev-charging/uc2-ev-charging/postman"

for ROLE in BAP BPP; do
  echo "Generating $ROLE..."
  python3 "$GENERATOR" \
    --devkit ev-charging-uc2-ev-charging \
    --role "$ROLE" \
    --output-dir "$OUTPUT_DIR"
done

echo "Done. Collections written to $REPO_ROOT/$OUTPUT_DIR/"
