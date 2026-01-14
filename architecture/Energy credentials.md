# Energy Credentials

## Definition

Energy Credentials are attestations (tied to Energy Resource Addresses) that provide verifiable claims about energy resources. These credentials convey trustworthy information such as green-energy certification, maintenance logs, ownership status, subsidy eligibility, safety compliance, and transactional history.

Implemented using W3C Verifiable Credentials standard, energy credentials enable cryptographically secure, privacy-preserving, and machine-verifiable claims that can be issued by trusted authorities, held by resource owners, and presented to verifiers during transactions. Embedded in intents, catalogues, and contracts, these credentials establish trust and enable efficient verification in decentralized energy markets.

## The Trust Challenge

As energy markets decentralize and the cost curve for DERs (solar panels, batteries, etc.) continues to fall, small-scale producers can join the formal energy ecosystem - but face a challenge of trust:

### Traditional vs. Decentralized Verification

**Large-scale generators** benefit from established trust mechanisms:
- Fuel sources and production volumes audited at scale
- Regulatory oversight and periodic inspections
- Established track records and credit ratings
- Physical infrastructure visible and verifiable

**Small-scale producers** (rooftop solar owners, community battery operators) face barriers:
- Costly or impossible to audit at individual scale
- Difficult to prove energy source authenticity
- Hard to demonstrate ownership or operational rights
- Challenging to verify maintenance and safety compliance

### Critical Verification Needs

- **Green energy authenticity**: Is the seller actually feeding solar energy into the grid?
- **Subsidy eligibility**: Do EV-charging incentives reach intended recipients?
- **Safety compliance**: Is the charging station properly certified and maintained?
- **Ownership verification**: Does the prosumer have rights to sell excess generation?
- **Grid connection approval**: Is the resource authorized to interconnect?
- **Payment eligibility**: Can the consumer be trusted for post-paid transactions?

Energy credentials provide a solution: **faster, more efficient source authentication** that scales to millions of distributed participants.

## W3C Verifiable Credentials for Energy

Energy credentials are based on the [W3C Verifiable Credentials Data Model](https://www.w3.org/TR/vc-data-model/), which provides:

### Core Components

1. **Credential**: A set of claims made by an issuer about a subject
2. **Issuer**: Trusted authority that creates and signs credentials (e.g., certification body, utility, government)
3. **Holder/Subject**: Entity described by the credential (energy resource identified by ERA)
4. **Verifier**: Party that checks credential validity during transactions (e.g., marketplace, consumer app)

### Key Properties

- **Cryptographically secure**: Digital signatures prevent tampering
- **Privacy-preserving**: Selective disclosure of only necessary claims
- **Machine-verifiable**: Automated verification without manual processes
- **Decentralized**: No single point of control or failure
- **Interoperable**: Standard format works across platforms and systems
- **Revocable**: Credentials can be invalidated if circumstances change

### Verifiable Credential Structure

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://deg.energy/credentials/v1"
  ],
  "id": "https://certification.example.com/credentials/solar-cert-123",
  "type": ["VerifiableCredential", "GreenEnergyCertificate"],
  "issuer": {
    "id": "did:example:renewable-certification-authority",
    "name": "Renewable Energy Certification Authority"
  },
  "issuanceDate": "2024-01-15T00:00:00Z",
  "expirationDate": "2029-01-15T23:59:59Z",
  "credentialSubject": {
    "id": "did:deg:household-solar-battery-001",
    "era": "household-solar-battery-001.greenenergy.example.com",
    "energySource": "solar",
    "installedCapacity": "5kW",
    "annualGeneration": "6000kWh",
    "certificationStandard": "ISO 50001:2018"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2024-01-15T00:00:00Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:example:renewable-certification-authority#key-1",
    "proofValue": "z3FXQjecWh...signature...kKJh6vW3"
  }
}
```

## Types of Energy Credentials

### Resource Certification Credentials

Attestations about resource capabilities and compliance:

**Green Energy Certification**
```json
{
  "type": ["VerifiableCredential", "GreenEnergyCertificate"],
  "credentialSubject": {
    "energySource": "solar",
    "renewableEnergyType": "photovoltaic",
    "carbonIntensity": "0gCO2/kWh",
    "rec Link": "REC-2024-XYZ"
  }
}
```

**Safety and Standards Compliance**
```json
{
  "type": ["VerifiableCredential", "SafetyCertificate"],
  "credentialSubject": {
    "standard": "IEC 62196",
    "connectorType": "CCS2",
    "safetyRating": "UL Listed",
    "fireRetardant": true,
    "lastInspection": "2024-06-01"
  }
}
```

**Performance and Capacity**
```json
{
  "type": ["VerifiableCredential", "CapacityAttestation"],
  "credentialSubject": {
    "ratedPowerKW": 60,
    "efficiency": 0.95,
    "warrantyValid": true,
    "warrantyExpiry": "2027-12-31"
  }
}
```

### Ownership and Authorization Credentials

Attestations about control and rights:

**Grid Connection Approval**
```json
{
  "type": ["VerifiableCredential", "GridInterconnectionApproval"],
  "issuer": {
    "id": "did:utility:bangalore-electricity",
    "name": "Bangalore Electricity Supply Company"
  },
  "credentialSubject": {
    "era": "household-solar-battery-001.greenenergy.example.com",
    "approvalId": "IC-APPROVAL-789",
    "exportLimit": "5kW",
    "bidirectionalMeter": true,
    "netMeteringEnabled": true
  }
}
```

**Ownership Proof**
```json
{
  "type": ["VerifiableCredential", "AssetOwnership"],
  "issuer": {
    "id": "did:gov:land-registry",
    "name": "Land Registry Department"
  },
  "credentialSubject": {
    "propertyId": "DEED-123456",
    "ownerName": "Jane Smith",
    "ownerDID": "did:deg:jane-smith-001",
    "assetType": "residential-solar-installation"
  }
}
```

### Financial and Eligibility Credentials

Attestations enabling transactions and subsidies:

**Subsidy Eligibility**
```json
{
  "type": ["VerifiableCredential", "SubsidyEligibility"],
  "issuer": {
    "id": "did:gov:ministry-renewable-energy",
    "name": "Ministry of New and Renewable Energy"
  },
  "credentialSubject": {
    "program": "RooftopSolarIncentive2024",
    "eligibilityId": "SUBSIDY-2024-ABC",
    "benefitAmount": {
      "value": 50000,
      "currency": "INR"
    },
    "claimStatus": "disbursed",
    "dbtAccountLinked": true
  }
}
```

## Energy Credentials in Practice

### From EV Charging Implementation Guide

While credentials may not always be explicitly represented in current schemas, they underpin trust in EV charging transactions:

#### CPO Provider Credentials

**Implicit VC Representation**:
```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  "type": ["VerifiableCredential", "CPOBusinessLicense"],
  "issuer": "did:gov:business-registry",
  "credentialSubject": {
    "id": "did:deg:ecopower-charging",
    "era": "ecopower-charging.cpo.example.com",
    "businessName": "EcoPower Charging Pvt Ltd",
    "licenseNumber": "BL-2024-XYZ",
    "operationalRegions": ["Karnataka", "Tamil Nadu"],
    "insuranceCoverage": "₹1 crore liability"
  }
}
```

#### EVSE Safety Credential

**Implicit VC Representation**:
```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  "type": ["VerifiableCredential", "EVSESafetyCertification"],
  "issuer": "did:certification:electrical-safety-authority",
  "credentialSubject": {
    "id": "did:deg:evse-IN-ECO-BTM-01-CCS2-A",
    "era": "IN*ECO*BTM*01*CCS2*A",
    "connectorType": "CCS2",
    "maxPowerKW": 60,
    "safetyStandard": "IEC 62196",
    "certificationDate": "2024-01-10",
    "nextInspectionDue": "2025-01-10"
  }
}
```

### P2P Energy Trading Credentials

#### Comprehensive Prosumer Credential Bundle

A prosumer would hold multiple VCs issued by different authorities:

1. **Green Energy Certification VC** (from Renewable Energy Authority)
2. **Grid Interconnection Approval VC** (from Utility)
3. **Property Ownership VC** (from Land Registry)
4. **Subsidy Eligibility VC** (from Government)
5. **Transaction History VC** (from Marketplace Platform)

When publishing a catalogue to sell excess solar energy, the prosumer presents selected VCs to prove:
- Authority to export energy (Grid Interconnection VC)
- Green energy source (Certification VC)
- Eligibility for preferential pricing (Subsidy VC)

## Verifiable Presentation in Transactions

When a credential holder needs to prove claims during a transaction, they create a **Verifiable Presentation**:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://www.w3.org/2018/credentials/examples/v1"
  ],
  "type": "VerifiablePresentation",
  "verifiableCredential": [
    {
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      "type": ["VerifiableCredential", "GreenEnergyCertificate"],
      "issuer": "did:example:renewable-authority",
      "credentialSubject": {
        "id": "did:deg:household-solar-001",
        "energySource": "solar"
      },
      "proof": { "...": "issuer signature" }
    }
  ],
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2024-11-12T14:00:00Z",
    "proofPurpose": "authentication",
    "verificationMethod": "did:deg:household-solar-001#key-1",
    "challenge": "transaction-challenge-xyz",
    "proofValue": "z3Abc...holder signature...xyz"
  }
}
```

The presentation includes:
- The credential(s) being presented
- Issuer's signature (proof in credential)
- Holder's signature (proof in presentation) proving they control the DID

## Selective Disclosure and Privacy

VCs support privacy-preserving credential presentation:

**Zero-Knowledge Proofs**: Prove eligibility without revealing sensitive data
```
Claim: "User is eligible for low-income subsidy"
VC Presented: Proof of eligibility (YES/NO)
VC NOT Presented: Actual income amount
```

**Minimal Disclosure**: Present only required claims
```
Catalogue requires: Green energy source
VC Presented: { "energySource": "solar" }
VC NOT Presented: Capacity, location, owner details
```

**Pseudonymous Credentials**: Bind to DIDs rather than real identities
```
Subject: did:deg:prosumer-anonymous-12345 (pseudonymous)
NOT: Jane Smith, 123 Main Street (identity)
```

## Credential Lifecycle with VCs

### Issuance

1. **Request**: Resource owner requests credential from issuer
2. **Verification**: Issuer verifies claims (inspection, audit, document check)
3. **Issuance**: Issuer creates VC, signs with private key
4. **Delivery**: VC delivered to holder's digital wallet
5. **Storage**: Holder stores VC securely (encrypted wallet, hardware device)

### Verification

1. **Presentation**: Holder presents VC (or verifiable presentation) to verifier
2. **Signature Check**: Verifier cryptographically validates issuer's signature
3. **Status Check**: Verifier checks if credential is revoked (status list, registry)
4. **Binding Check**: Verifier confirms holder controls the DID in credential subject
5. **Acceptance**: Verifier accepts claims if all checks pass

### Revocation

**Status List 2021** (W3C standard):
```json
{
  "credentialStatus": {
    "id": "https://issuer.example.com/status/1#94567",
    "type": "StatusList2021Entry",
    "statusPurpose": "revocation",
    "statusListIndex": "94567",
    "statusListCredential": "https://issuer.example.com/status/1"
  }
}
```

Verifiers check the status list to see if credential at index 94567 has been revoked.

## Decentralized Identifiers (DIDs)

VCs use DIDs to identify issuers, subjects, and holders:

**Example DIDs in Energy Context**:
- `did:deg:household-solar-001` - Prosumer household
- `did:deg:ecopower-charging` - CPO provider
- `did:gov:renewable-authority` - Certification body
- `did:utility:bangalore-electricity` - Grid operator

DIDs provide:
- **Decentralized**: No central authority controls identity
- **Persistent**: IDs remain valid even if domains change
- **Cryptographically verifiable**: Associated with public/private key pairs
- **Resolvable**: DID documents provide public keys and service endpoints

## Relationship with Other Primitives

1. **Energy Resource**: Resources hold VCs as digital attestations
2. **Energy Resource Address (ERA)**: DIDs and ERAs both identify resources; VCs bind to DIDs
3. **Energy Intent**: Intent may require specific VCs ("must present green certification VC")
4. **Energy Catalogue**: Catalogues include or reference VCs to establish trust
5. **Energy Contract**: Contracts reference presented VCs as terms/conditions

## Summary

Energy Credentials, implemented using W3C Verifiable Credentials, are the trust infrastructure of the Digital Energy Grid. They enable millions of distributed participants to transact with confidence through cryptographically secure, privacy-preserving, and machine-verifiable attestations.

By combining VCs with Energy Resource Addresses and Decentralized Identifiers, DEG creates a robust trust framework that solves the verification challenge inherent in decentralized energy markets - making green energy claims verifiable, subsidies trackable, and safety compliance provable at scale.

## See Also

- [Energy Resource](./Energy%20resource.md) - What holds and presents credentials
- [Energy Resource Address](./Energy%20resource%20address.md) - Addressable identifiers for resources
- [Energy Catalogue](./Energy%20catalogue.md) - How credentials affect service offerings
- [Energy Contract](./Energy%20contract.md) - How credentials shape agreements
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - Credential usage in practice
- [W3C Verifiable Credentials Data Model](https://www.w3.org/TR/vc-data-model/) - Standard specification
- [W3C Decentralized Identifiers](https://www.w3.org/TR/did-core/) - DID specification
