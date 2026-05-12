# ElectricityCredential

Unified W3C Verifiable Credential (VC Data Model 2.0) issued per meter by electricity distribution utilities. Combines customer identity with optional consumption, generation, and storage profiles in a single credential.

**Canonical IRI:** `https://schema.beckn.io/ElectricityCredential/v1.0`

**Namespace prefix:** `deg:` → `https://schema.beckn.io/deg/`

**Tags:** `energy` · `credential` · `verifiable-credential` · `electricity` · `customer` · `deg`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| [v1.0](./v1.0/) | Current | Unified credential replacing separate per-profile VCs |

---

## Inheritance

```
beckn:Credential
  └── EnergyCredential
        └── ElectricityCredential  ← this schema
```

---

## credentialSubject Properties

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `id` | `string` (URI) | | Optional DID of the customer/credential subject |
| `customerProfile` | object | ✅ | Customer number, meter number, meter type, identity reference |
| `customerDetails` | object | | Full name, installation address, service connection date |
| `consumptionProfile` | object | | Premises type, connection type, sanctioned load, tariff |
| `generationProfile` | object | | DER type, capacity, commissioning date, manufacturer |
| `storageProfile` | object | | Battery capacity, power rating, storage type |

---

## Linked Data

| Term | IRI |
|------|-----|
| `ElectricityCredential` | `deg:ElectricityCredential` |
| `customerProfile` | `deg:customerProfile` |
| `customerDetails` | `deg:customerDetails` |
| `consumptionProfile` | `deg:consumptionProfile` |
| `generationProfile` | `deg:generationProfile` |
| `storageProfile` | `deg:storageProfile` |

---

## Usage

Issued by electricity distribution utilities to consumers and prosumers. Used for:
- P2P energy trading eligibility and identity verification
- Demand response and virtual power plant enrollment
- DER asset registration and grid service qualification
- Program enrollment and tariff management
