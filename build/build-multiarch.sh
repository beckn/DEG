#!/bin/bash

# Multi-Architecture Docker Build Script for DEG Ledger Recorder Plugin
# ======================================================================
# Builds onix-adapter with DEG plugins for linux/amd64 and linux/arm64
#
# Prerequisites:
#   - Docker Desktop or Docker Engine with buildx support
#   - QEMU user-static binaries (for cross-arch emulation)
#
# Usage:
#   ./build-multiarch.sh                    # Build and load to local Docker (current arch only)
#   ./build-multiarch.sh --push             # Build multi-arch and push to registry
#   ./build-multiarch.sh --platform amd64   # Build specific platform only
#
# Environment Variables:
#   BECKN_ONIX_ROOT - Path to beckn-onix repo (will prompt if not set and default not found)
#   IMAGE_NAME      - Image name (default: onix-adapter-deg)
#   IMAGE_TAG       - Image tag (default: p2p-multiarch-v3)
#   REGISTRY        - Registry prefix (default: none, local build)
#   PLATFORMS       - Platforms to build (default: linux/amd64,linux/arm64)
#   BUILDER_NAME    - Buildx builder name (default: deg-multiarch)

set -e

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEG_ROOT="$(dirname "$SCRIPT_DIR")"

# Resolve beckn-onix path
if [ -n "$BECKN_ONIX_ROOT" ] && [ -d "$BECKN_ONIX_ROOT" ]; then
    # Use environment variable if set and valid
    :
else
    # Prompt user for path
    echo ""
    read -p "Enter path to beckn-onix repository: " USER_BECKN_ONIX_PATH

    if [ -z "$USER_BECKN_ONIX_PATH" ]; then
        echo "ERROR: beckn-onix path is required"
        exit 1
    fi

    # Expand ~ to home directory
    USER_BECKN_ONIX_PATH="${USER_BECKN_ONIX_PATH/#\~/$HOME}"

    if [ ! -d "$USER_BECKN_ONIX_PATH" ]; then
        echo "ERROR: Directory not found: $USER_BECKN_ONIX_PATH"
        exit 1
    fi

    BECKN_ONIX_ROOT="$USER_BECKN_ONIX_PATH"
fi

# Configuration with defaults
IMAGE_NAME="${IMAGE_NAME:-onix-adapter-deg}"
IMAGE_TAG="${IMAGE_TAG:-p2p-multiarch-v3}"
REGISTRY="${REGISTRY:-}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILDER_NAME="${BUILDER_NAME:-deg-multiarch}"
DOCKERFILE="$SCRIPT_DIR/Dockerfile.onix-adapter-deg"

# Parse arguments
PUSH_FLAG=""
LOAD_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH_FLAG="--push"
            shift
            ;;
        --load)
            LOAD_FLAG="--load"
            shift
            ;;
        --platform)
            PLATFORMS="linux/$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --push              Push to registry after build"
            echo "  --load              Load into local Docker (single arch only)"
            echo "  --platform ARCH     Build for specific platform (amd64, arm64)"
            echo "  --tag TAG           Image tag (default: p2p-multiarch-v3)"
            echo "  --registry REG      Registry prefix (e.g., docker.io/myuser)"
            echo "  --help              Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  BECKN_ONIX_ROOT     Path to beckn-onix repo (prompts if not set)"
            echo "  IMAGE_NAME          Image name (default: onix-adapter-deg)"
            echo "  IMAGE_TAG           Image tag (default: p2p-multiarch-v3)"
            echo "  REGISTRY            Registry prefix"
            echo "  PLATFORMS           Platforms (default: linux/amd64,linux/arm64)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Construct full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "============================================"
echo "Multi-Arch Build: DEG Ledger Recorder"
echo "============================================"
echo "DEG Root:        $DEG_ROOT"
echo "Beckn-ONIX Root: $BECKN_ONIX_ROOT"
echo "Dockerfile:      $DOCKERFILE"
echo "Image:           $FULL_IMAGE"
echo "Platforms:       $PLATFORMS"
echo "Builder:         $BUILDER_NAME"
echo "============================================"

# Verify Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo "ERROR: Dockerfile not found at $DOCKERFILE"
    exit 1
fi

# Step 1: Setup QEMU for cross-platform emulation
echo ""
echo ">>> Step 1: Setting up QEMU for cross-platform builds..."
docker run --privileged --rm tonistiigi/binfmt --install all 2>/dev/null || {
    echo "Note: QEMU setup may already be configured or not needed"
}

# Step 2: Create/use buildx builder
echo ""
echo ">>> Step 2: Setting up buildx builder..."
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    echo "Creating new buildx builder: $BUILDER_NAME"
    docker buildx create \
        --name "$BUILDER_NAME" \
        --driver docker-container \
        --driver-opt network=host \
        --bootstrap
else
    echo "Using existing builder: $BUILDER_NAME"
fi

docker buildx use "$BUILDER_NAME"

# Step 3: Verify builder supports requested platforms
echo ""
echo ">>> Step 3: Verifying builder capabilities..."
docker buildx inspect --bootstrap

# Step 4: Determine output mode
# - If pushing to registry: use --push (supports multi-arch)
# - If loading locally: use --load (single arch only)
# - If neither: outputs are kept in build cache

OUTPUT_FLAG=""
if [ -n "$PUSH_FLAG" ]; then
    OUTPUT_FLAG="$PUSH_FLAG"
    echo ""
    echo ">>> Mode: Build and push to registry"
elif [ -n "$LOAD_FLAG" ]; then
    OUTPUT_FLAG="$LOAD_FLAG"
    # --load only works with single platform
    if [[ "$PLATFORMS" == *","* ]]; then
        echo "WARNING: --load only supports single platform. Using current platform."
        PLATFORMS="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
    fi
    echo ""
    echo ">>> Mode: Build and load to local Docker (platform: $PLATFORMS)"
else
    echo ""
    echo ">>> Mode: Build only (use --push or --load to export)"
    echo "    Note: Images will be in build cache. Use --push to push to registry"
    echo "          or --load to load single-arch image to local Docker."
fi

# Step 5: Build the image
echo ""
echo ">>> Step 4: Building multi-arch image..."
echo "Command:"
echo "  docker buildx build \\"
echo "    --platform $PLATFORMS \\"
echo "    --file $DOCKERFILE \\"
echo "    --build-context beckn-onix=$BECKN_ONIX_ROOT \\"
echo "    --tag $FULL_IMAGE \\"
echo "    $OUTPUT_FLAG \\"
echo "    $DEG_ROOT"
echo ""

docker buildx build \
    --platform "$PLATFORMS" \
    --file "$DOCKERFILE" \
    --build-context beckn-onix="$BECKN_ONIX_ROOT" \
    --tag "$FULL_IMAGE" \
    $OUTPUT_FLAG \
    "$DEG_ROOT"

# Step 6: Report results
echo ""
echo "============================================"
echo "Build Complete!"
echo "============================================"
echo "Image: $FULL_IMAGE"
echo "Platforms: $PLATFORMS"

if [ -n "$PUSH_FLAG" ]; then
    echo ""
    echo "Image pushed to registry. Verify with:"
    echo "  docker buildx imagetools inspect $FULL_IMAGE"
elif [ -n "$LOAD_FLAG" ]; then
    echo ""
    echo "Image loaded to local Docker. Verify with:"
    echo "  docker images $IMAGE_NAME"
    echo "  docker inspect $FULL_IMAGE | jq '.[0].Architecture'"
else
    echo ""
    echo "Image built in cache. To use:"
    echo "  - Push to registry:  $0 --push --registry <your-registry>"
    echo "  - Load locally:      $0 --load"
fi

echo "============================================"
