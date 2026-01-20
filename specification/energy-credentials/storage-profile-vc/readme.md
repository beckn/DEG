# Storage Profile Credential

A credential for battery/energy storage capability.

## Purpose

This credential captures the energy storage capability of a prosumer, including:
- Storage capacity in kilowatt-hours
- Charge/discharge power rating in kilowatts
- Commissioning date
- Optional storage technology type

This information is useful for grid management, virtual power plant programs, demand response, and energy arbitrage applications.

## Fields

| Field | Description | Required |
|-------|-------------|----------|
| id | Customer DID (links to customer) | Yes |
| consumerNumber | Consumer account number | Yes |
| fullName | Consumer name | No |
| meterNumber | Meter serial number associated with this asset | No |
| assetId | Unique identifier for this storage asset | No |
| storageCapacityKWh | Battery storage capacity in kWh | Yes |
| powerRatingKW | Charge/discharge power rating in kW | Yes |
| commissioningDate | Date when storage was activated | Yes |
| storageType | LithiumIon / LeadAcid / FlowBattery / Other | No |

### Storage Types

- **LithiumIon**: Lithium-ion batteries (most common for residential)
- **LeadAcid**: Traditional lead-acid batteries
- **FlowBattery**: Flow batteries (vanadium, zinc-bromine, etc.)
- **Other**: Other storage technologies (sodium-ion, solid-state, etc.)

## Credential Linkage

This credential links to the base identity credential (Utility Customer Credential) via the customer DID in the `credentialSubject.id` field. A customer may have multiple storage profile credentials for different battery installations.

## Files

- `schema.json` - JSON Schema for validation
- `context.jsonld` - JSON-LD context for semantic interoperability
- `example.json` - Sample credential (lithium-ion battery)
- `readme.md` - This documentation

## Usage

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org/",
    "https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/storage-profile-vc/context.jsonld"
  ],
  "type": ["VerifiableCredential", "StorageProfileCredential"],
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "consumerNumber": "UTIL-2025-001234567",
    "storageCapacityKWh": 10,
    "powerRatingKW": 5,
    "commissioningDate": "2025-01-12",
    "storageType": "LithiumIon"
  }
}
```

## Multiple Storage Systems

A prosumer may have multiple storage credentials. For example, a customer with both a home battery and an EV-to-grid capable electric vehicle would have two separate Storage Profile Credentials, each with its own capacity and power rating.
