#!/bin/bash

# Build script for DEG Ledger Recorder plugin
# This script builds the plugin as a Go shared object (.so) file
#
# Usage:
#   ./build-ledger-plugin.sh          # Build for current OS/arch (local development)
#   ./build-ledger-plugin.sh docker   # Build for linux/amd64 using Docker (for deployment)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEG_ROOT="$(dirname "$SCRIPT_DIR")"
PLUGINS_DIR="$DEG_ROOT/plugins"
OUTPUT_DIR="${OUTPUT_DIR:-$DEG_ROOT/testnet/p2p-trading-interdiscom-devkit/plugins}"

PLUGIN_NAME="degledgerrecorder"
BUILD_MODE="${1:-local}"

echo "============================================"
echo "Building DEG Ledger Recorder Plugin"
echo "============================================"
echo "DEG Root:    $DEG_ROOT"
echo "Plugins Dir: $PLUGINS_DIR"
echo "Output Dir:  $OUTPUT_DIR"
echo "Plugin:      $PLUGIN_NAME"
echo "Build Mode:  $BUILD_MODE"
echo "============================================"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

if [ "$BUILD_MODE" = "docker" ]; then
    echo "Building for linux/amd64 using Docker..."

    # IMPORTANT: Must use exact same Go version as onix-adapter (1.24.6)
    # Go plugins require exact version match between plugin and host
    GO_VERSION="1.24.6"

    docker run --rm --platform linux/amd64 \
        -v "$DEG_ROOT:/workspace" \
        -v "$DEG_ROOT/../beckn-onix:/beckn-onix" \
        -w /workspace/plugins \
        -e CGO_ENABLED=1 \
        -e GOOS=linux \
        -e GOARCH=amd64 \
        golang:${GO_VERSION} \
        bash -c "
            # Update go.mod replace directive to use container path
            # Use specific pattern to avoid corrupting module path
            sed -i 's|=> ../../beckn-onix|=> /beckn-onix|g' go.mod
            go mod tidy
            go build -buildmode=plugin -o /workspace/testnet/p2p-trading-interdiscom-devkit/plugins/$PLUGIN_NAME.so ./degledgerrecorder/cmd/plugin.go
            # Restore original go.mod replace directive
            sed -i 's|=> /beckn-onix|=> ../../beckn-onix|g' go.mod
        "
else
    echo "Building for local OS/arch..."

    # Navigate to plugins directory (where go.mod is)
    cd "$PLUGINS_DIR"

    # Tidy up dependencies
    echo "Running go mod tidy..."
    go mod tidy

    # Build the plugin
    echo "Building plugin..."
    go build -buildmode=plugin \
        -o "$OUTPUT_DIR/$PLUGIN_NAME.so" \
        "./degledgerrecorder/cmd/plugin.go"
fi

echo "============================================"
echo "Build complete!"
echo "Plugin: $OUTPUT_DIR/$PLUGIN_NAME.so"
echo "============================================"

# Verify the build
if [ -f "$OUTPUT_DIR/$PLUGIN_NAME.so" ]; then
    echo "Plugin file size: $(ls -lh "$OUTPUT_DIR/$PLUGIN_NAME.so" | awk '{print $5}')"
    file "$OUTPUT_DIR/$PLUGIN_NAME.so" 2>/dev/null || true
    echo "Build successful!"
else
    echo "ERROR: Plugin file not found after build"
    exit 1
fi
