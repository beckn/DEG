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

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `ledgerHost` | Yes | - | Base URL of the DEG Ledger service |
| `role` | No | `BUYER` | Role for ledger records |
| `enabled` | No | `true` | Enable/disable plugin |
| `asyncTimeout` | No | `5000` | API call timeout (ms) |
| `retryCount` | No | `0` | Retry count for failed calls |

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
