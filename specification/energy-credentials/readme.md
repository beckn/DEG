# Energy Credentials

Schemas for Verifiable Credentials in the energy sector.

## Overview

This collection provides schemas for credentials issued by electricity distribution utilities to consumers and prosumers. The credentials are designed to be modular and privacy-preserving, allowing for selective disclosure of customer information.

## Available Credentials

| Credential | Description | Purpose |
|------------|-------------|---------|
| [Utility Customer Credential](./utility-customer-vc/) | Barebones identity credential | Privacy-preserving customer identification |
| [Consumption Profile Credential](./consumption-profile-vc/) | Connection and load characteristics | Load management, tariff determination |
| [Generation Profile Credential](./generation-profile-vc/) | DER generation capability | Grid management, net metering, renewable tracking |
| [Storage Profile Credential](./storage-profile-vc/) | Battery/energy storage capability | Virtual power plants, demand response |
| [Program Enrollment Credential](./program-enrollment-vc/) | Energy program participation | Demand response, ToU programs |

## Credential Relationships

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
```

All profile credentials link to the customer via the `credentialSubject.id` field (customer DID).

## Credential Issuance Scenarios

### Pure Consumer
- **Has**: Utility Customer Credential, Consumption Profile Credential
- **Does not have**: Generation Profile, Storage Profile

### Solar Prosumer
- **Has**: Utility Customer Credential, Consumption Profile, Generation Profile (Solar)
- **May have**: Storage Profile (if battery installed)

### Full Prosumer
- **Has**: All credential types
- **May have**: Multiple Generation Profiles (e.g., solar + wind)
- **May have**: Multiple Storage Profiles (e.g., home battery + EV)

## Directory Structure

```
energy-credentials/
├── utility-customer-vc/       # Base identity credential
│   ├── schema.json
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
├── consumption-profile-vc/    # Connection/load characteristics
│   ├── schema.json
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
├── generation-profile-vc/     # DER generation capability
│   ├── schema.json
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
├── storage-profile-vc/        # Battery storage capability
│   ├── schema.json
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
├── program-enrollment-vc/     # Program participation
│   ├── schema.json
│   ├── context.jsonld
│   ├── example.json
│   └── readme.md
└── readme.md                  # This file
```

## Privacy Considerations

The modular design allows for selective disclosure:

- **Utility Customer Credential** uses a masked consumer number to protect the full account number
- **Consumption Profile** can be shared for load management without revealing identity
- **Generation/Storage Profiles** enable participation in energy programs without exposing personal details

## Schema Standards

All schemas follow:
- W3C Verifiable Credentials Data Model 1.1
- JSON-LD 1.1 for semantic interoperability
- JSON Schema (draft 2020-12) for validation
- Schema.org vocabulary where applicable
