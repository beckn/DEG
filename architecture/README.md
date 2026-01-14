# Architecture

## Introduction

The Digital Energy Grid (DEG) is built on a decentralized, open architecture that enables seamless interactions between diverse energy stakeholders - from individual consumers and distributed energy resources (DERs) to utilities, aggregators, and service providers. At its core, DEG provides a standardized framework for energy transactions, data exchange, and service delivery across a fragmented ecosystem.

As energy markets evolve toward decentralization, the proliferation of small-scale producers (rooftop solar, community batteries), distributed resources (EVs, smart appliances), and new energy services creates a pressing need for interoperability. Traditional centralized systems struggle to accommodate this complexity, leading to siloed networks, proprietary platforms, and limited consumer choice.

DEG addresses these challenges through a set of fundamental primitives that work together to create a universal language for energy interactions - enabling discovery, negotiation, contracting, and fulfillment across any compliant platform or network.

## The Six Core Primitives

The DEG architecture is built on six fundamental primitives that together enable trustworthy, efficient energy transactions:

### 1. [Energy Resource](./Energy%20resource.md)
Physical or logical entities in the energy ecosystem - including generation assets (solar panels, wind turbines, VPPs), storage systems (batteries), consumption devices (EVs, appliances), infrastructure (transformers, meters), and service providers. Energy resources can act as consumers, providers, or both (prosumers), depending on the context and transaction.

### 2. [Energy Resource Address (ERA)](./Energy%20resource%20address.md)
A globally or locally unique digital identifier assigned to any energy resource, enabling seamless addressability and discovery. ERAs function like internet domain names, allowing systems to uniformly recognize and interact with energy resources across platforms and contexts.

### 3. [Energy Credentials](./Energy%20credentials.md)
Digital attestations tied to Energy Resource Addresses that provide verifiable claims about resources - such as green energy certification, ownership status, maintenance logs, subsidy eligibility, and transaction history. Credentials establish trust in decentralized energy markets where traditional audit mechanisms are cost-prohibitive.

### 4. [Energy Intent](./Energy%20intent.md)
A digital representation of energy demand or requirements, detailing what is needed, preferred conditions, constraints, and acceptable terms. Intents express the "ask" side of any energy transaction - from simple needs ("charge my EV") to complex requirements ("20 kWh solar energy between 6-9 PM at ₹7/kWh or less").

### 5. [Energy Catalogue](./Energy%20catalogue.md)
Structured listings of available energy resources, services, or offerings - including quantities, locations, timing, pricing, constraints, and delivery methods. Catalogues represent the "offer" side of transactions, published by providers to match against consumer intents.

### 6. [Energy Contract](./Energy%20contract.md)
The formalized agreement that emerges when an energy intent successfully matches with a catalogue offering. Contracts define the boundaries of interactions between parties, encompassing everything from simple acknowledgments to complex multi-party agreements with detailed terms, conditions, and fulfillment requirements.

## How the Primitives Work Together

The DEG primitives form a cohesive interaction model:

```
         Energy Resources
                ↓
        Assigned ERAs
                ↓
        Carry Credentials
           ↙         ↘
    Express         Publish
    Intents         Catalogues
       ↓                ↓
       └────(Match)─────┘
                ↓
         Energy Contract
                ↓
         Contract Execution
           (Fulfillment)
```

**The Transaction Cycle(in no particular order):**

1. **Resources are identified**: Every participating entity (consumer, producer, prosumer, device, service) has an Energy Resource Address
2. **Trust is established**: Energy Credentials verify claims about resources (capacity, certification, ownership)
3. **Demand is expressed**: Resources acting as consumers publish Energy Intents describing their needs
4. **Supply is advertised**: Resources acting as providers publish Energy Catalogues listing available offerings
5. **Matching occurs**: When an intent aligns with a catalogue entry, negotiation begins
6. **Contracts are formed**: Agreements are confirmed and formalized (may vary in degree of formality) as Energy Contracts
7. **Fulfillment happens**: Energy is delivered or services rendered according to contract terms

This cycle - **intent matched with catalogue, forming a contract** - is the fundamental interaction loop in the Digital Energy Grid.

A single Energy Resource can simultaneously express intents (as a consumer) and publish catalogues (as a provider). For example, a home with rooftop solar and battery storage might publish a catalogue selling excess solar energy while expressing an intent to buy grid power during peak demand hours.

## Real-World Application

These primitives map to practical energy scenarios:

**EV Charging Example:**
- **Energy Resource**: Charging station (EVSE), Electric vehicle, EV user
- **ERA**: Unique identifier for each charging station and user
- **Credentials**: CPO verification, charger safety certification, user payment eligibility
- **Intent**: "Need 20 kWh charge for my EV near location X between 6-9 PM"
- **Catalogue**: "DC Fast Charger available, 60kW, ₹18/kWh, location Y, slots available"
- **Contract**: Confirmed charging session with specific terms, pricing, and duration

**P2P Energy Trading Example:**
- **Energy Resource**: Rooftop solar installation, Home battery, Prosumer household
- **ERA**: Unique identifiers for producer and consumer households
- **Credentials**: Green energy certification, grid connection approval, ownership proof
- **Intent**: "Buy 10 kWh solar energy between 2-4 PM at ₹6/kWh or less"
- **Catalogue**: "Selling 15 kWh excess solar, 2-5 PM available, ₹5.50/kWh"
- **Contract**: P2P energy transfer agreement with delivery terms and settlement

## Navigation

Explore each primitive in detail:

- [Energy Resource](./Energy%20resource.md) - Understanding energy ecosystem entities
- [Energy Resource Address](./Energy%20resource%20address.md) - Digital addressing for energy
- [Energy Credentials](./Energy%20credentials.md) - Establishing trust and verification
- [Energy Intent](./Energy%20intent.md) - Expressing energy demand
- [Energy Catalogue](./Energy%20catalogue.md) - Publishing energy supply
- [Energy Contract](./Energy%20contract.md) - Formalizing energy agreements

For implementation examples, see:
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md)
- [P2P Energy Trading Implementation Guide](../docs/implementation-guides/v2/P2P_Trading) (coming soon)
