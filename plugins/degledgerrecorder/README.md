# DEG Ledger Recorder Plugin

A Beckn-ONIX Step plugin that records trade data to the DEG Ledger after `on_confirm` calls.

## Overview

This plugin intercepts `on_confirm` beckn protocol messages and creates corresponding records in the DEG Ledger service by calling the `/ledger/put` API. It operates asynchronously (fire-and-forget) to avoid blocking the main request flow.

## Features

- Automatically detects `on_confirm` actions
- Maps beckn protocol fields to DEG Ledger format
- Creates one ledger record per order item
- Asynchronous operation (non-blocking)
- Configurable role (BUYER, SELLER, BUYER_DISCOM, SELLER_DISCOM)
- Idempotent requests using client reference
- **Beckn-style signature authentication** (same as beckn-onix outgoing messages)
- Detailed request/response logging for debugging

## Building

```bash
# From DEG repository root
./build/build-ledger-plugin.sh
```

This will produce `degledgerrecorder.so` in `testnet/p2p-trading-interdiscom-devkit/plugins/`.

## Configuration

Add to your ONIX handler configuration:

```yaml
plugins:
  steps:
    - id: degledgerrecorder
      config:
        ledgerHost: "https://ledger.example.org"
        role: "BUYER"        # BUYER, SELLER, BUYER_DISCOM, or SELLER_DISCOM
        enabled: "true"      # Enable/disable the plugin
        asyncTimeout: "5000" # Timeout in milliseconds
        retryCount: "0"      # Number of retries (0 = no retry)
steps:
  - validateSign
  - addRoute
  - degledgerrecorder      # Add after addRoute
  - validateSchema
```

### Configuration Options

#### Core Settings

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `ledgerHost` | Yes | - | Base URL of the DEG Ledger service |
| `role` | No | `BUYER` | Role for ledger records (see below) |
| `actions` | No | `on_confirm` | Comma-separated list of actions to trigger recording |
| `enabled` | No | `true` | Enable/disable plugin |
| `asyncTimeout` | No | `5000` | API call timeout (ms) |
| `retryCount` | No | `0` | Retry count for failed calls |
| `debugLogging` | No | `false` | Enable verbose request/response logging |

#### Actions and Roles

| Action | Ledger Endpoint | Supported Roles | Description |
|--------|-----------------|-----------------|-------------|
| `on_confirm` | `/ledger/put` | BUYER, SELLER | Records trade agreement |
| `on_status` | `/ledger/record` | BUYER_DISCOM, SELLER_DISCOM | Records meter readings/validation metrics |

**Role behavior:**
- `BUYER` / `SELLER`: Platform roles, use `/ledger/put` for trade records
- `BUYER_DISCOM` / `SELLER_DISCOM`: Discom roles, use `/ledger/record` for validation metrics
  - `BUYER_DISCOM`: Maps `allocatedEnergy` → `ACTUAL_PULLED`
  - `SELLER_DISCOM`: Maps `allocatedEnergy` → `ACTUAL_PUSHED`

#### Authentication Options

The plugin supports two authentication methods:

**Option 1: Beckn-style Signature Authentication (Recommended)**

Uses the same ed25519 + BLAKE2b-512 signing mechanism as beckn-onix for outgoing messages. This generates an `Authorization` header with a cryptographic signature.

| Option | Alias (simplekeymanager-style) | Required | Default | Description |
|--------|-------------------------------|----------|---------|-------------|
| `signingPrivateKey` | (same) | Yes* | - | Base64-encoded ed25519 private key seed |
| `subscriberId` | `networkParticipant` | Yes* | - | Subscriber ID (e.g., `bap.example.org`) |
| `uniqueKeyId` | `keyId` | Yes* | - | Unique key ID |
| `signatureValiditySeconds` | - | No | `30` | How long the signature is valid |

*Required if using Beckn-style signing. If any signing field is set, all three must be set.

**Config key aliases:** You can use the same config keys as `simplekeymanager` (`networkParticipant`, `keyId`) for easy copy-paste.

**Option 2: Simple API Key Authentication**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `apiKey` | No | - | API key for ledger service authentication |
| `authHeader` | No | `X-API-Key` | Header name for the API key |

### Example 1: Zero-Config with Environment Variables (Recommended)

If you already have environment variables set for `simplekeymanager`, the plugin will **automatically** use them - no additional config needed:

```bash
# Environment variables (same as beckn-onix simplekeymanager)
export SIGNING_PRIVATE_KEY="<base64-encoded-ed25519-seed>"
export SUBSCRIBER_ID="bap.example.org"
export UNIQUE_KEY_ID="bap.example.org.k1"
```

```yaml
# Plugin config - no signing config needed!
plugins:
  steps:
    - id: degledgerrecorder
      config:
        ledgerHost: "https://ledger.example.org"
        role: "BUYER"
        # Signing config automatically loaded from env vars
```

This approach is **compatible with**:
- **HashiCorp Vault** - secrets injected via Vault Agent
- **Kubernetes Secrets** - mounted as env vars
- **Docker Secrets** - exposed as env vars
- **AWS Secrets Manager** - via ECS/Lambda env injection
- **Azure Key Vault** - via env injection

### Example 2: Platform Recording (on_confirm only)

```yaml
plugins:
  steps:
    - id: degledgerrecorder
      config:
        ledgerHost: "https://ledger.example.org"
        role: "BUYER"                    # Platform role
        actions: "on_confirm"            # Default, records trade agreements
        signingPrivateKey: "${SIGNING_PRIVATE_KEY}"
        networkParticipant: "bap.example.org"
        keyId: "bap.example.org.k1"
```

### Example 3: Discom Recording (on_status with meter readings)

```yaml
plugins:
  steps:
    - id: degledgerrecorder
      config:
        ledgerHost: "https://ledger.example.org"
        role: "BUYER_DISCOM"             # Discom role for validation metrics
        actions: "on_status"             # Record meter readings
        signingPrivateKey: "${SIGNING_PRIVATE_KEY}"
        networkParticipant: "discom-buyer.example.org"
        keyId: "discom-buyer.example.org.k1"
```

### Example 4: Both Actions (Platform + Discom in same instance)

```yaml
plugins:
  steps:
    - id: degledgerrecorder
      config:
        ledgerHost: "https://ledger.example.org"
        role: "BUYER_DISCOM"             # Use discom role if handling both
        actions: "on_confirm,on_status"  # Handle both actions
        signingPrivateKey: "${SIGNING_PRIVATE_KEY}"
        networkParticipant: "example.org"
        keyId: "example.org.k1"
```

**Note:** When `on_status` is enabled, the role must be `BUYER_DISCOM` or `SELLER_DISCOM`.

### Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `SIGNING_PRIVATE_KEY` | Base64-encoded ed25519 private key seed |
| `SUBSCRIBER_ID` | Subscriber ID (e.g., `bap.example.org`) |
| `UNIQUE_KEY_ID` | Unique key ID (e.g., `bap.example.org.k1`) |

### Generated Authorization Header

```
Authorization: Signature keyId="bap.example.org|bap.example.org.k1|ed25519",algorithm="ed25519",created="1706547600",expires="1706547630",headers="(created) (expires) digest",signature="<base64_signature>"
```

### Vault Integration Example

```hcl
# Vault Agent template
template {
  contents = <<EOF
SIGNING_PRIVATE_KEY={{ with secret "secret/beckn/signing" }}{{ .Data.data.private_key }}{{ end }}
SUBSCRIBER_ID={{ with secret "secret/beckn/identity" }}{{ .Data.data.subscriber_id }}{{ end }}
UNIQUE_KEY_ID={{ with secret "secret/beckn/identity" }}{{ .Data.data.key_id }}{{ end }}
EOF
  destination = "/app/.env"
}
```

## Field Mapping

| Ledger Field | Source |
|--------------|--------|
| `transactionId` | `context.transaction_id` |
| `orderItemId` | `beckn:acceptedOffer.beckn:id` |
| `platformIdBuyer` | `context.bap_id` |
| `platformIdSeller` | `context.bpp_id` |
| `discomIdBuyer` | `beckn:orderAttributes.utilityIdBuyer` |
| `discomIdSeller` | `beckn:orderAttributes.utilityIdSeller` |
| `buyerId` | `beckn:buyer.beckn:id` |
| `sellerId` | `beckn:seller` |
| `tradeTime` | `context.timestamp` |
| `deliveryStartTime` | `beckn:timeWindow.schema:startTime` |
| `deliveryEndTime` | `beckn:timeWindow.schema:endTime` |

## Requirements

- Go 1.24+
- Beckn-ONIX (for plugin interface)
- DEG Ledger service accessible from ONIX instance

## Development

### Project Structure

```
plugins/degledgerrecorder/
├── cmd/
│   └── plugin.go     # Plugin entry point
├── config.go         # Configuration handling
├── mapper.go         # Payload mapping logic
├── client.go         # HTTP client for ledger API
├── signer.go         # Beckn-style signature generation
├── recorder.go       # Main step implementation
└── README.md
```

### Testing

```bash
cd plugins
go test ./degledgerrecorder/...
```

## License

See repository LICENSE file.
