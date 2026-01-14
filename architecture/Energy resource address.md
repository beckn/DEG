# Energy Resource Address (ERA)

## Definition

An Energy Resource Address (ERA) is a unique digital identifier assigned to any energy resource, enabling seamless addressability and discovery across the energy ecosystem. ERAs function similarly to internet domain names or URLs, allowing any system or platform to uniformly recognize, reference, and interact with energy resources in a standardized manner.

## Why ERAs Are Essential

For energy transactions to occur in a decentralized, interoperable network, all participants need a mechanism to be addressed. Without standardized addressing:

- **Discovery becomes impossible**: How would an EV find nearby charging stations?
- **Transactions cannot be routed**: How does a catalogue response reach the right consumer?
- **Coordination fails**: How can aggregators manage distributed resources?

ERAs solve these problems by providing universal addressability - ensuring that every resource, from utility-scale generators to individual smart appliances, can be uniquely identified and interacted with.

## Global vs Local ERAs

ERAs can operate at different scopes depending on the resource's operational context:

### Global ERAs
Universally recognizable identifiers for resources that participate in broad energy markets or cross-platform interactions.

**Examples**:
- **Utilities and energy producers**: Need global recognition for wholesale markets
- **Public charging networks**: CPOs operating across regions
- **Service providers**: Aggregators, ESCOs, financial institutions
- **Individual consumers**: Households participating in P2P trading or demand response programs
- **Network participants**: BAPs (Beckn Application Platforms) and BPPs (Beckn Provider Platforms)

**Characteristics**:
- Globally unique across all networks
- Registered in public or federated registries
- Discoverable by any compliant platform
- Typically tied to verified namespaces (e.g., domain names)

### Local ERAs
Identifiers relevant within a specific context or environment, useful for resources that operate in constrained scopes.

**Examples**:
- **Home appliances**: Smart thermostats, bulbs, HVAC systems within a household
- **Building devices**: Floor-level meters, zone controllers in a commercial building
- **Microgrid components**: Individual solar panels, batteries within a community microgrid
- **Sub-metered devices**: Department-level loads in an industrial facility

**Characteristics**:
- Unique within a specific context (home, building, microgrid)
- May not be globally discoverable
- Managed by a local coordinator or gateway
- Can be more lightweight and flexible

**Example Hierarchy**:
```
Global ERA: household-solar-001.prosumer@example.com
  Local ERA: battery-inverter-01
  Local ERA: panel-array-rooftop
  Local ERA: smart-meter-main
```

## ERA Structure and Examples

### From EV Charging Implementation Guide

ERAs in the EV charging ecosystem take various forms:

#### EVSE (Charging Station) Identifiers

```json
{
  "beckn:id": "ev-charger-ccs2-001",
  "evseId": "IN*ECO*BTM*01*CCS2*A",
  "ocppId": "IN-ECO-BTM-01"
}
```

- **`beckn:id`**: Platform-specific resource identifier used in DEG transactions
- **`evseId`**: International EVSE identifier following ISO 15118/OCPI standards
  - Format: `{Country}*{CPO}*{Location}*{Unit}*{Connector}*{Instance}`
  - Example: `IN*ECO*BTM*01*CCS2*A` → India, EcoPower, BTM location, unit 01, CCS2 connector, instance A
- **`ocppId`**: Open Charge Point Protocol identifier for backend communication

#### CPO (Provider) Identifiers

```json
{
  "beckn:id": "ecopower-charging",
  "beckn:descriptor": {
    "schema:name": "EcoPower Charging Pvt Ltd"
  }
}
```

- **`beckn:id`**: Unique provider identifier
- Used across multiple charging locations
- Associated with namespace in registry

#### BAP/BPP Network Identifiers

From the registry setup section:

```json
{
  "subscriber_id": "example-company.com",
  "url": "https://.dedi.global/dedi/lookup/example-company/subscription-details"
}
```

- **`subscriber_id`**: Network participant's unique identifier (often domain-based)
- **Registry URL**: Discovery endpoint for participant details
- **Namespace**: Claimed and verified on DeDi.global

### P2P Energy Trading Examples (Conceptual)

#### Prosumer Household ERA

```
Global ERA: household-solar-battery-001.greenenergy.example.com
Premises ID: GRID-CONN-2024-001
Smart Meter ID: METER-BLR-SEC5-123
```

#### Distributed Solar Array

```
Global ERA: community-solar-array.localenergy.coop
Site ID: SOLAR-SITE-COMMUNITY-01
Individual Panel IDs:
  - Local: PANEL-ROW-A-01
  - Local: PANEL-ROW-A-02
  ...
```

## ERA in Transaction Flow

ERAs are used throughout the energy transaction lifecycle:

### Discovery Phase
```
EV User App (BAP) → discover(location, filters)
  ↓
CDS routes to relevant CPOs (BPPs) based on location
  ↓
CPO responds with catalogue including EVSE ERAs:
  - beckn:id: "ev-charger-ccs2-001"
  - evseId: "IN*ECO*BTM*01*CCS2*A"
```

### Order Phase
```
User selects specific EVSE by ERA
  ↓
select/init/confirm actions reference:
  - Item ID: "ev-charger-ccs2-001"
  - Provider ID: "ecopower-charging"
```

### Fulfillment Phase
```
Contract established for specific EVSE ERA
  ↓
update/track actions target same ERA
  ↓
EVSE backend receives commands via OCPP ID
```

## Relationship with Other Primitives

ERAs enable all other primitives to function:

1. **Energy Resource**: Every resource must have an ERA to participate
2. **Energy Credentials**: Tied to ERAs to establish verifiable claims
3. **Energy Intent**: Includes ERA of the consumer expressing the intent
4. **Energy Catalogue**: Lists ERAs of available provider resources
5. **Energy Contract**: Binds ERAs of all participating parties

Without ERAs, there is no way to identify who is transacting with whom - they are the foundation of trust and interoperability in DEG.

## Summary

Energy Resource Addresses (ERAs) provide the addressing infrastructure that makes the Digital Energy Grid possible. Like the Domain Name System (DNS) enables the internet, ERAs enable energy resources to discover, reference, and transact with each other in a standardized, secure, and scalable manner.

Whether global or local, ERAs ensure that every participant - from massive utilities to individual smart bulbs - has a unique, verifiable identity in the energy ecosystem.

## See Also

- [Energy Resource](./Energy%20resource.md) - What gets addressed by ERAs
- [Energy Credentials](./Energy%20credentials.md) - Trust attestations tied to ERAs
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - ERA usage in practice
- [DeDi.global](https://publish.dedi.global/) - Registry platform for namespace and ERA management
