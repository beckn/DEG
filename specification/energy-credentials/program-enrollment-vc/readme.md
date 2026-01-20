# Utility Program Enrollment Credential

This credential is issued by electricity distribution utilities when a consumer enrolls in an energy program. Programs can include peer-to-peer trading, demand flexibility, virtual power plants, and other grid services.

## Use Cases

- **P2P Energy Trading**: Consumer is authorized to trade excess solar energy with neighbors
- **Demand Flexibility**: Consumer agrees to reduce consumption during peak hours for incentives
- **Virtual Power Plant**: Consumer's DER assets are aggregated for grid services
- **Time of Use**: Consumer opts into time-based pricing programs
- **Net Metering**: Consumer is enrolled in net metering for solar exports

## Fields

| Field | Description | Required |
| :---- | :---- | :----: |
| consumerNumber | Unique consumer account number | Yes |
| fullName | Consumer name | No |
| programName | Human-readable program name | Yes |
| programCode | Unique program identifier | Yes |
| enrollmentDate | Date of enrollment | Yes |
| validUntil | End date when enrollment expires | No |

## Files

- `schema.json` - JSON Schema for validation
- `context.jsonld` - JSON-LD context for semantic interoperability
- `example.json` - Sample P2P trading enrollment credential

## Usage

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://schema.org/",
    "https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/program-enrollment-vc/context.jsonld"
  ],
  "type": ["VerifiableCredential", "UtilityProgramEnrollmentCredential"],
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "consumerNumber": "UTIL-2025-001234567",
    "programName": "Peer-to-Peer Energy Trading",
    "programCode": "P2P-2025",
    "enrollmentDate": "2025-01-13"
  }
}
```

Context URL:
```
https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/program-enrollment-vc/context.jsonld
```

Schema URL:
```
https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/program-enrollment-vc/schema.json
```
