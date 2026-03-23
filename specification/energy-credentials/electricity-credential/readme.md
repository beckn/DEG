# Electricity Credential

## Overview

The **Electricity Credential** is a unified W3C Verifiable Credential (VC Data Model 2.0) that combines five equal-level profile sections into a single `credentialSubject` object. The customer's DID (`id`) is optional per the W3C VC Data Model, and the five profiles sit as equal-level sibling properties. The same credential can be used for different purposes - to present information regarding consumption profile, generation profile or storage profile or all of it by omitting or adding relevant sections.

This credential is issued per meter — each meter will have its own credential.

## Credential Structure

```
credentialSubject
├── id                    (optional customer DID)
├── customerProfile       (required — identity: meter, customer number, masked ID)
├── customerDetails       (optional — name, address, connection date)
├── consumptionProfile    (optional — premises, connection type, load, tariff)
├── generationProfile     (optional — DER type, capacity, commissioning)
└── storageProfile        (optional — battery capacity, power rating, type)
```

## Validity Period

Per the [W3C VC Data Model 2.0 validity period](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/#validity-period), this credential uses:

- **`validFrom`** (required) — date and time from which the credential is valid
- **`validUntil`** (optional) — date and time until which the credential is valid

### customerProfile
Core customer identity fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customerNumber` | string | Yes | Full customer account number assigned by the utility |
| `meterNumber` | string | Yes | Unique meter serial number |
| `meterType` | enum | Yes | Smart, Conventional, or Prepaid |
| `maskedIdType` | string | No | Type of government-issued ID (e.g., SSN, Passport, NationalID) |
| `maskedIdNumber` | string | No | Masked government ID for privacy-preserving verification |

### customerDetails
Personal and address information:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fullName` | string | Yes | Full name of the customer as per ID proof |
| `installationAddress` | object | Yes | Address of the installation (fullAddress, city, district, stateProvince, postalCode, country) |
| `serviceConnectionDate` | date | Yes | Date when the electricity connection was activated |

### consumptionProfile
Connection and consumption characteristics:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `premisesType` | enum | Yes | Residential, Commercial, Industrial, or Agricultural |
| `connectionType` | enum | Yes | Single-phase or Three-phase |
| `sanctionedLoadKW` | number | Yes | Sanctioned electrical load in kW |
| `tariffCategoryCode` | string | Yes | Billing/tariff category code |

### generationProfile
DER generation capability:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | string | No | Unique identifier for the generation asset |
| `generationType` | enum | Yes | Solar, Wind, MicroHydro, or Other |
| `capacityKW` | number | Yes | Installed generation capacity in kW |
| `commissioningDate` | date | Yes | Date when the system was activated |
| `manufacturer` | string | No | Equipment manufacturer |
| `modelNumber` | string | No | Equipment model number |

### storageProfile
Battery/energy storage capability:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | string | No | Unique identifier for the storage asset |
| `storageCapacityKWh` | number | Yes | Storage capacity in kWh |
| `powerRatingKW` | number | Yes | Charge/discharge power rating in kW |
| `commissioningDate` | date | Yes | Date when the system was activated |
| `storageType` | enum | No | LithiumIon, LeadAcid, FlowBattery, or Other |

## Files

| File | Description |
|------|-------------|
| `context.jsonld` | JSON-LD context defining semantic mappings for all five profile sections |
| `schema.json` | JSON Schema (draft 2020-12) for credential validation |
| `example.json` | Sample credential with all five profiles populated |

## Issuer

This credential is issued by electricity distribution utilities identified by their URL and regulatory license number. Per the [W3C VC Data Model 2.0 issuer specification](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/#issuer), the issuer `id` is a URL (e.g., `https://example-utility.com/issuers/energy-dept`).

## Revocation

Credential revocation is managed via the DeDi Registry (`dediregistry` status type).
