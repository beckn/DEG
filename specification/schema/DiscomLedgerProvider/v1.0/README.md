# DiscomLedgerProvider — v1.0

Identity attributes for a regulated discom ledger Technical Service Provider (TSP). Attached to `Contract.participants[*].participantAttributes` for entries with role `buyerDiscom` or `sellerDiscom`, and carries the `ledgerUri` that platforms use to write trade records after `on_confirm`.

Part of the [DEG Schema](../../../specification/schema/) · [DiscomLedgerProvider](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | JSON Schema 2020-12 definition for `DiscomLedgerProvider` |
| [context.jsonld](./context.jsonld) | JSON-LD context (namespace: `https://schema.beckn.io/deg/DiscomLedgerProvider/v1.0/`) |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary for `DiscomLedgerProvider` terms |

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `ledgerUri` | `string` (uri) | ✅ | Base URL of the discom ledger TSP |
| `utilityId` | `string` | | Utility/DISCOM identifier the TSP serves (e.g., `BRPL-DL`) |

## Usage

Two discoms MAY point at the same `ledgerUri` if they share a TSP. Each platform still calls only its own side's discom URI: BAP → `buyerDiscom.ledgerUri`, BPP → `sellerDiscom.ledgerUri`.

The `degledgerrecorder` plugin reads `ledgerUri` from the payload when configured with `ledgerUriSource: payload`.
