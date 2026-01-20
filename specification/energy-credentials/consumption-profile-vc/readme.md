# Consumption Profile Credential

A credential for connection and consumption characteristics for load management and tariff purposes.

## Purpose

This credential captures the electrical connection profile of a customer, including:
- Premises classification (residential, commercial, etc.)
- Connection type (single-phase or three-phase)
- Sanctioned/approved load capacity
- Tariff category for billing

This information is useful for load management, demand response programs, and tariff calculations.

## Fields

| Field | Description | Required |
|-------|-------------|----------|
| id | Customer DID (links to customer) | Yes |
| consumerNumber | Full consumer account number | Yes |
| fullName | Consumer name | Yes |
| premisesType | Residential/Commercial/Industrial/Agricultural | Yes |
| connectionType | Single-phase/Three-phase | Yes |
| sanctionedLoadKW | Allotted/approved electrical load in kW | Yes |
| tariffCategoryCode | Billing category code | Yes |
| meterNumber | Meter serial number (for linking to specific meter) | No |

### Premises Types

- **Residential**: Domestic household connections
- **Commercial**: Business and office connections
- **Industrial**: Manufacturing and industrial facilities
- **Agricultural**: Farm and agricultural connections

### Connection Types

- **Single-phase**: Standard residential/small commercial (typically up to 10kW)
- **Three-phase**: Higher capacity for larger loads

## Credential Linkage

This credential links to the base identity credential (Utility Customer Credential) via the customer DID in the `credentialSubject.id` field. A customer may have multiple consumption profile credentials if their connection details change over time.

## Files

- `schema.json` - JSON Schema for validation
- `context.jsonld` - JSON-LD context for semantic interoperability
- `example.json` - Sample credential
- `readme.md` - This documentation

## Usage

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org/",
    "https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/consumption-profile-vc/context.jsonld"
  ],
  "type": ["VerifiableCredential", "ConsumptionProfileCredential"],
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "consumerNumber": "UTIL-2025-001234567",
    "fullName": "Jane Doe",
    "premisesType": "Residential",
    "connectionType": "Single-phase",
    "sanctionedLoadKW": 5,
    "tariffCategoryCode": "RES-01"
  }
}
```
