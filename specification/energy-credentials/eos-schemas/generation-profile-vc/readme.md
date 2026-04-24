# Generation Profile Credential

A credential for DER (Distributed Energy Resource) generation capability.

## Purpose

This credential captures the generation capability of a prosumer, including:
- Type of generation (solar, wind, micro-hydro, etc.)
- Installed capacity in kilowatts
- Commissioning date
- Optional equipment details (manufacturer, model)

This information is useful for grid management, net metering programs, and renewable energy certificate tracking.

## Fields

| Field | Description | Required |
|-------|-------------|----------|
| id | Customer DID (links to customer) | Yes |
| consumerNumber | Consumer account number | Yes |
| fullName | Consumer name | No |
| meterNumber | Meter serial number associated with this asset | No |
| assetId | Unique identifier for this generation asset | No |
| generationType | Solar / Wind / MicroHydro / Other | Yes |
| capacityKW | Installed generation capacity in kW | Yes |
| commissioningDate | Date when generation was activated | Yes |
| manufacturer | Equipment manufacturer | No |
| modelNumber | Equipment model | No |

### Generation Types

- **Solar**: Photovoltaic (PV) solar panels
- **Wind**: Small/micro wind turbines
- **MicroHydro**: Small-scale hydroelectric generators
- **Other**: Other DER generation types (fuel cells, biogas, etc.)

## Credential Linkage

This credential links to the base identity credential (Utility Customer Credential) via the customer DID in the `credentialSubject.id` field. A customer may have multiple generation profile credentials for different DER installations.

## Files

- `schema.json` - JSON Schema for validation
- `context.jsonld` - JSON-LD context for semantic interoperability
- `example.json` - Sample credential (solar installation)
- `readme.md` - This documentation

## Usage

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org/",
    "https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/generation-profile-vc/context.jsonld"
  ],
  "type": ["VerifiableCredential", "GenerationProfileCredential"],
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "consumerNumber": "UTIL-2025-001234567",
    "generationType": "Solar",
    "capacityKW": 3,
    "commissioningDate": "2025-01-12",
    "manufacturer": "SunPower Corporation",
    "modelNumber": "SPR-X22-360"
  }
}
```

## Multiple DERs

A prosumer may have multiple generation credentials. For example, a customer with both rooftop solar and a small wind turbine would have two separate Generation Profile Credentials, each with its own generation type and capacity.
