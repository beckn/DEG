# Energy Credentials

Schemas for Verifiable Credentials in the energy sector.

## Overview

This collection provides schemas for credentials issued by energy providers to consumers and prosumers. The credentials are designed to be privacy-preserving and follow the W3C VC Data Model 2.0.

## Available Credentials

| Credential | Description | Purpose |
|------------|-------------|---------|
| [Customer Credential](../schema/ElectricityCredential/v1.0/) | Unified credential combining customer identity, consumption, generation, and storage profiles | Single credential per meter for consumer/prosumer identity |
| [Program Enrollment Credential](./program-enrollment-vc/) | Energy program participation | P2P trading, demand response, virtual power plants, ToU programs |
| [Meter Data Credential](./meterDataVC/v1.0/) | Historical interval meter readings | Demand forecasting, P2P trading |
| [Billing Summary Credential](./billingSummaryVC/v1.0/) | Aggregated billing period costs and consumption | Credit checks, program eligibility, cost analytics |

## Shared Data Objects

Both credentials share the same `customerProfile` and `customerDetails` object structures:

- **customerProfile** — customer number, meter number, meter type, external identity reference (`idRef`)
- **customerDetails** — full name, installation address (with optional geo tagging and Open Location Code), service connection date

In the Customer Credential these are required; in the Program Enrollment Credential they are optional.

## Shared Patterns

### idRef

A reusable identity reference pattern used wherever one entity's identity is issued by another authority. It appears in two places:

- **`issuer.idRef`** — the utility's regulatory registration (issued by the energy regulator)
- **`customerProfile.idRef`** — the customer's identity (issued by a government body or other authority)

Structure:

```json
"idRef": {
  "issuedBy": "did:web:kerc.karnataka.gov.in",
  "subjectId": "kerc.karnataka.gov.in:AABPC12345"
}
```
┌─────────────────────────────┐
│  Utility Customer Credential │  (Base identity - required)
│  - Masked consumer number    │
│  - Name, address, meter      │
└──────────────┬──────────────┘
               │
               │ Links via customer DID
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Optional Profile Credentials               │
├────────────────────┬─────────────────────┬───────────────────┤
│ Consumption Profile│ Generation Profile  │ Storage Profile   │
│ - Load/tariff info │ - Solar/Wind/etc.   │ - Battery capacity│
│ - Connection type  │ - Capacity (kW)     │ - Power rating    │
└────────────────────┴─────────────────────┴───────────────────┘
               │
               │ Links via customer DID + meterNumber
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Data Credentials                            │
├─────────────────────────────┬────────────────────────────────┤
│ Meter Data Credential       │ Billing Summary Credential     │
│ - 15-min interval readings  │ - Monthly billing totals       │
│ - Green Button / ESPI       │ - Cost + consumption per period│
│ - Demand forecasting        │ - Credit checks, eligibility   │
└─────────────────────────────┴────────────────────────────────┘
```

| Field | Type | Description |
|-------|------|-------------|
| `issuedBy` | URI (DID) | DID of the authority that issued the identity |
| `subjectId` | string | Identifier in the format `authority-domain:id-value` |

### credentialStatus

All credentials use the DeDi registry for revocation. The `credentialStatus` object contains:

```json
"credentialStatus": {
  "id": "https://dedi.global/dedi/lookup/{issuer-domain}/vc-revocation-registry/{credential-uuid}",
  "type": "dedi",
  "statusPurpose": "revocation",
  "statusListCredential": "https://dedi.global/dedi/query/{issuer-domain}/vc-revocation-registry"
}
```

### Pure Consumer
- **Has**: Utility Customer Credential, Consumption Profile Credential
- **May have**: Meter Data Credential (for sharing history with trading apps)
- **Does not have**: Generation Profile, Storage Profile

### Solar Prosumer
- **Has**: Utility Customer Credential, Consumption Profile, Generation Profile (Solar)
- **May have**: Storage Profile (if battery installed)
- **May have**: Meter Data Credential (for demand forecasting)

### Full Prosumer
- **Has**: All credential types
- **May have**: Multiple Generation Profiles (e.g., solar + wind)
- **May have**: Multiple Storage Profiles (e.g., home battery + EV)
- **May have**: Meter Data Credentials covering different time periods
| Field | Type | Description |
|-------|------|-------------|
| `id` | URI | Lookup URL for this specific credential's revocation status |
| `type` | string | Always `dedi` |
| `statusPurpose` | enum | `revocation` or `suspension` |
| `statusListCredential` | URI | URL to the issuer's revocation registry |

### DateTime Format

All date and time fields use ISO 8601 `date-time` format with an explicit timezone offset (not UTC/GMT). This ensures unambiguous interpretation across jurisdictions.

Example: `"2025-01-15T10:30:00+05:30"` (IST) or `"2025-01-13T10:30:00-05:00"` (EST)

## Directory Structure

```
energy-credentials/
├── program-enrollment-vc/        # Program participation
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
├── eos-schemas/                  # Archived: original per-profile schemas (pre-unification)
│   ├── consumption-profile-vc/
│   ├── generation-profile-vc/
│   ├── storage-profile-vc/
│   ├── utility-customer-vc/
│   └── examples/
└── readme.md                     # This file

# Customer Credential moved to versioned schema folder:
# specification/schema/ElectricityCredential/v1.0/
```

## Schema Standards

All schemas follow:
- W3C Verifiable Credentials Data Model 2.0
- JSON-LD 1.1 for semantic interoperability
- JSON Schema (draft 2020-12) for validation
- Schema.org vocabulary where applicable

## @context Resolution

Each credential's `@context` array lists the W3C VC context, Schema.org, and individual `schema.beckn.io` URLs for each object type used:

```json
"@context": [
  "https://www.w3.org/ns/credentials/v2",
  "https://schema.org/",
  "https://schema.beckn.io/customerCredential",
  "https://schema.beckn.io/customerProfile",
  "https://schema.beckn.io/customerDetails",
  "https://schema.beckn.io/consumptionProfile",
  "https://schema.beckn.io/generationProfile",
  "https://schema.beckn.io/storageProfile"
]
```
