# Utility Customer Credential

A barebones identity credential for privacy-preserving customer identification issued by electricity distribution utilities.

## Purpose

This credential provides a minimal set of identity fields needed to:
- Identify a utility customer without exposing full account details
- Link the customer to their service address and meter
- Enable privacy-preserving verification of customer status

## Fields

| Field | Description | Required |
|-------|-------------|----------|
| id | Customer DID | Yes |
| consumerNumber | Full consumer account number assigned by the utility | Yes |
| maskedIdNumber | Optional masked government ID (e.g., driving license, national ID) | No |
| fullName | Full name as per ID proof | Yes |
| installationAddress | Full address object | Yes |
| meterNumber | Meter serial number | Yes |
| serviceConnectionDate | Connection activation date | Yes |

### Installation Address Object

| Field | Description | Required |
|-------|-------------|----------|
| fullAddress | Complete street address | Yes |
| city | City name | No |
| district | District or county name | No |
| stateProvince | State, province, or region | No |
| postalCode | Postal or ZIP code | Yes |
| country | ISO 3166-1 alpha-2 country code | Yes |

## Credential Linkage

This credential serves as the base identity credential. Other profile credentials (consumption, generation, storage) link to this credential via the customer DID in the `credentialSubject.id` field.

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
    "https://nfh-trust-labs.github.io/vc-schemas/energy-credentials/utility-customer-vc/context.jsonld"
  ],
  "type": ["VerifiableCredential", "UtilityCustomerCredential"],
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "consumerNumber": "UTIL-2025-001234567",
    "maskedIdNumber": "XXXX-XXXX-1234",
    "fullName": "Jane Doe",
    "installationAddress": { ... },
    "meterNumber": "MET2025789456123",
    "serviceConnectionDate": "2025-01-10"
  }
}
```
