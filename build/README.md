# DEG Build Scripts

This directory contains build scripts and Docker configurations for the DEG Ledger Recorder plugin and onix-adapter-deg image.

## Files

| File | Description |
|------|-------------|
| `Dockerfile.onix-adapter-deg` | Dockerfile for building onix-adapter with DEG plugins |
| `build-multiarch.sh` | Build multi-arch Docker image (amd64 + arm64) |

## Multi-Architecture Builds

The `build-multiarch.sh` script builds Docker images for multiple architectures (linux/amd64 and linux/arm64) using Docker Buildx and QEMU emulation.

### Prerequisites

1. **Docker with Buildx support**
   - Docker Desktop (macOS/Windows): Buildx is included
   - Linux: Install Docker Engine 19.03+ with buildx plugin

2. **QEMU** (for cross-architecture emulation)
   - The script automatically installs QEMU user-mode emulation
   - Or install manually:
     ```bash
     docker run --privileged --rm tonistiigi/binfmt --install all
     ```

3. **beckn-onix repository**
   - Script will prompt for path if not found at default location (`../beckn-onix`)
   - Or set `BECKN_ONIX_ROOT` environment variable to skip prompt

### Usage

```bash
# Build and load to local Docker (current architecture only)
./build/build-multiarch.sh --load

# Build for specific platform
./build/build-multiarch.sh --platform amd64 --load
./build/build-multiarch.sh --platform arm64 --load

# Build and push to registry (multi-arch)
./build/build-multiarch.sh --push --registry docker.io/myuser

# Build with custom tag
./build/build-multiarch.sh --push --registry ghcr.io/myorg --tag v1.0.0

# Show help
./build/build-multiarch.sh --help
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BECKN_ONIX_ROOT` | (prompts if not found) | Path to beckn-onix repo |
| `IMAGE_NAME` | `onix-adapter-deg` | Docker image name |
| `IMAGE_TAG` | `p2p-multiarch-v3` | Docker image tag |
| `REGISTRY` | (none) | Registry prefix (e.g., `docker.io/user`) |
| `PLATFORMS` | `linux/amd64,linux/arm64` | Target platforms |
| `BUILDER_NAME` | `deg-multiarch` | Buildx builder name |

### Examples

**Local development (macOS Apple Silicon)**
```bash
# Build for your Mac's ARM64 architecture
./build/build-multiarch.sh --platform arm64 --load

# Run locally
docker run -it --rm \
  -v $(pwd)/config:/app/config \
  -e CONFIG_FILE=/app/config/local.yaml \
  -p 8081:8081 \
  onix-adapter-deg:latest
```

**Build for production deployment**
```bash
# Build multi-arch and push to Docker Hub
export REGISTRY=docker.io/mycompany
export IMAGE_TAG=v1.2.3
./build/build-multiarch.sh --push

# Verify multi-arch manifest
docker buildx imagetools inspect docker.io/mycompany/onix-adapter-deg:v1.2.3
```

**GitHub Actions CI/CD**

See `.github/workflows/build-multiarch.yml` for automated multi-arch builds.

## Go Plugin Compatibility

**Important:** Go plugins require exact version matching:
- The plugin and host binary must be built with the **same Go version**
- The plugin and host must use the **same dependency versions**
- CGO must be enabled (`CGO_ENABLED=1`)

The Dockerfile ensures compatibility by building both the adapter and plugins in the same build stage with the same Go version.

## Troubleshooting

### "exec format error"
You're trying to run an image built for a different architecture. Either:
- Build for your architecture: `--platform amd64` or `--platform arm64`
- Enable QEMU: `docker run --privileged --rm tonistiigi/binfmt --install all`

### "plugin was built with a different version of package"
The plugin was built with a different Go version or dependency versions than the adapter. Rebuild both together using the Dockerfile.

### "builder not found"
Create the buildx builder manually:
```bash
docker buildx create --name deg-multiarch --driver docker-container --bootstrap
docker buildx use deg-multiarch
```

### Slow builds on non-native architecture
QEMU emulation is slower than native builds. For faster CI:
- Use native runners when available (e.g., GitHub's `ubuntu-latest` for amd64)
- Consider using arm64 runners for arm64 builds
- Use build caching (`--cache-from type=gha`)

## Architecture Notes

The image supports:
- **linux/amd64**: Standard x86-64 servers (AWS EC2, GCP, most cloud VMs)
- **linux/arm64**: ARM64 servers (AWS Graviton, Apple Silicon Macs, Raspberry Pi 4+)

The base image (`cgr.dev/chainguard/wolfi-base`) and Go image (`golang:1.24-bullseye`) both provide multi-arch support.
