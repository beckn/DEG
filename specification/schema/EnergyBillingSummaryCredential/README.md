# EnergyBillingSummaryCredential

Verifiable Credential containing aggregated billing period data using ESPI/Green Button types. Issued by distribution utilities to consumers. Combines customer identity with billing summary data within a W3C VC 2.0 envelope.

**Canonical IRI:** `https://schema.beckn.io/EnergyBillingSummaryCredential/v1.0`

**Namespace prefix:** `deg:` → `https://schema.beckn.io/deg/`

**Tags:** `energy` · `credential` · `verifiable-credential` · `billing` · `green-button` · `espi`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| [v1.0](./v1.0/) | Current | Migrated from energy-credentials/billingSummaryVC |

---

## Inheritance

```
beckn:Credential
  └── EnergyCredential
        └── EnergyBillingSummaryCredential  ← this schema
```

---

## credentialSubject Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string` (URI) | | DID of the customer/credential subject |
| `customerProfile` | [`EnergyCustomerProfile`](../EnergyCustomerProfile/) | ✅ | Customer identity linking utility account to meter |
| `billingSummary` | [`EnergyBillingSummary`](../EnergyBillingSummary/) | ✅ | ESPI/Green Button billing summary data |

---

## Linked Data

| Term | IRI |
|------|-----|
| `EnergyBillingSummaryCredential` | `deg:EnergyBillingSummaryCredential` |
| `customerProfile` | `deg:customerProfile` |
| `billingSummary` | `deg:billingSummary` |

---

## Usage

Issued by electricity distribution utilities to consumers. Used for:
- Billing verification and dispute resolution
- Tariff analysis and comparison
- Energy cost tracking and forecasting
