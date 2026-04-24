# EnergyMeterDataCredential

Verifiable Credential containing historical time-series interval meter readings using ESPI/Green Button types. Issued by distribution utilities to consumers. Combines customer identity with meter data within a W3C VC 2.0 envelope.

**Canonical IRI:** `https://schema.beckn.io/EnergyMeterDataCredential/v1.0`

**Namespace prefix:** `deg:` → `https://schema.beckn.io/deg/`

**Tags:** `energy` · `credential` · `verifiable-credential` · `metering` · `green-button` · `espi`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| [v1.0](./v1.0/) | Current | Migrated from energy-credentials/meterDataVC |

---

## Inheritance

```
beckn:Credential
  └── EnergyCredential
        └── EnergyMeterDataCredential  ← this schema
```

---

## credentialSubject Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | `string` (URI) | | DID of the customer/credential subject |
| `customerProfile` | [`EnergyCustomerProfile`](../EnergyCustomerProfile/) | ✅ | Customer identity linking utility account to meter |
| `meterDataGB` | [`EnergyMeterDataGB`](../EnergyMeterDataGB/) | ✅ | ESPI/Green Button meter reading data |

---

## Linked Data

| Term | IRI |
|------|-----|
| `EnergyMeterDataCredential` | `deg:EnergyMeterDataCredential` |
| `customerProfile` | `deg:customerProfile` |
| `meterDataGB` | `deg:meterDataGB` |

---

## Usage

Issued by electricity distribution utilities to consumers. Used for:
- Demand response and load management
- P2P energy trading with verified consumption data
- Energy forecasting and optimization
