# Utility Program Enrollment Credential

This credential is issued by energy providers when a consumer enrolls in an energy program. Programs can include peer-to-peer trading, demand flexibility, virtual power plants, and other grid services.

## Use Cases

- **P2P Energy Trading**: Consumer is authorized to trade excess solar energy with neighbors
- **Demand Flexibility**: Consumer agrees to reduce consumption during peak hours for incentives
- **Virtual Power Plant**: Consumer's DER assets are aggregated for grid services
- **Time of Use**: Consumer opts into time-based pricing programs
- **Net Metering**: Consumer is enrolled in net metering for solar exports

## Credential Structure

```
credentialSubject
├── id                    (optional customer DID)
├── customerProfile       (optional: customer number, meter, idRef)
├── customerDetails       (optional: name, address, connection date)
├── programName           (required)
├── programCode           (required)
├── enrollmentDate        (required)
└── enrollmentValidUntil  (optional)
```

## Issuer

The credential is issued by energy providers. The issuer object contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | URI | Yes | DID or URL of the issuing provider |
| `name` | string | Yes | Name of the provider |
| `idRef` | object | No | Regulatory identity reference — see [idRef](../../schema/ElectricityCredential/v1.0/README.md#idref) |

## Validity Period

Per the [W3C VC Data Model 2.0 validity period](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/#validity-period), this credential uses:

- **`validFrom`** (required) — date-time from which the credential is valid
- **`validUntil`** (optional) — date-time until which the credential is valid

All date-time values include an explicit timezone offset (e.g., `2025-01-13T11:00:00-05:00`).

## Revocation

Credential revocation is managed via DeDi. See [credentialStatus](../readme.md#credentialstatus) in the top-level readme.

## Profile Sections

### customerProfile (optional)

Core customer identity fields — same structure as [Customer Credential](../../schema/ElectricityCredential/v1.0/README.md#customerprofile):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customerNumber` | string | Yes | Full customer account number assigned by the utility |
| `meterNumber` | string | No | Unique meter serial number |
| `meterType` | enum | No | Type of meter — see [meterType enum](../../schema/ElectricityCredential/v1.0/README.md#metertype-enum) |
| `idRef` | object | No | External identity reference — see [idRef](../../schema/ElectricityCredential/v1.0/README.md#idref) |

### customerDetails (optional)

Personal and address information — same structure as [Customer Credential](../../schema/ElectricityCredential/v1.0/README.md#customerdetails):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fullName` | string | Yes | Full name of the customer as per ID proof |
| `installationAddress` | object | No | Address of the installation (includes optional `geo` and `openLocationCode`) |
| `serviceConnectionDate` | date-time | No | Date and time when the electricity connection was activated |

### Enrollment Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `programName` | string | Yes | Human-readable program name |
| `programCode` | string | Yes | Unique program identifier |
| `enrollmentDate` | date-time | Yes | Date and time of enrollment |
| `enrollmentValidUntil` | date-time | No | End date and time when enrollment expires |

## Files

| File | Description |
|------|-------------|
| `context.jsonld` | JSON-LD context defining semantic mappings |
| `schema.json` | JSON Schema (draft 2020-12) for credential validation |
| `example.json` | Sample P2P trading enrollment credential |
