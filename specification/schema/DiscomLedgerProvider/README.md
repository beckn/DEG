# DiscomLedgerProvider

Identity attributes for a regulated discom ledger Technical Service Provider (TSP), used on `buyerDiscom` and `sellerDiscom` participants in a DEG contract.

**Canonical IRI:** `https://schema.beckn.io/DiscomLedgerProvider/v1.0`

**Namespace prefix:** `deg:` → `https://schema.beckn.io/deg/DiscomLedgerProvider/v1.0/`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| [v1.0](./v1.0/) | Current | Initial version. Identity and endpoint for a discom ledger TSP. |

---

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `utilityId` | `string` | ✓ | Utility / DISCOM identifier the ledger TSP serves (e.g. `BRPL-DL`). |
| `ledgerUri` | `URI` | ✓ | Base URL of the discom ledger TSP endpoint. |
