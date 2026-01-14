# Energy Resource

## Definition

An Energy Resource is any physical, virtual or logical entity within the energy ecosystem that participates in energy generation, storage, consumption, transmission, distribution, or service delivery. Energy resources form the foundational building blocks of the Digital Energy Grid, representing the diverse actors and assets that create, move, store, or use energy.

## Why Energy Resources Matter

Traditional energy systems treat most participants as passive endpoints - consumers simply receive energy, and only large generators are recognized as active participants. As the energy landscape decentralizes, this model breaks down:

- **Distributed generation** means households and small businesses become producers
- **Storage systems** (batteries, EVs) both consume and supply energy at different times
- **Smart devices** actively manage their consumption patterns
- **Aggregators and intermediaries** coordinate distributed resources
- **Infrastructure elements** (transformers, meters, grids) enable energy flow more actively

Each of these entities needs to be recognized, addressed, and capable of participating in energy transactions. Energy Resources provide a unified representation for this diversity.

## Types of Energy Resources

Energy resources span a wide spectrum of physical, virtual and logical entities:

### Generation Assets
Resources that produce energy:
- **Utility-scale generators**: Thermal plants, large solar farms, wind farms
- **Distributed Energy Resources (DERs)**: Rooftop solar panels, small wind turbines
- **Microgrids**: Community or campus-level generation systems
- **Backup generators**: Diesel generators, combined heat and power (CHP) systems

### Storage Systems
Resources that store and release energy:
- **Stationary batteries**: Home battery systems, utility-scale battery storage
- **Electric Vehicles (EVs)**: Mobile storage that can charge and potentially discharge (V2G) (are also consumption devices)
- **Pumped hydro**: Large-scale energy storage through water elevation
- **Thermal storage**: Hot water tanks, phase-change materials

### Consumption Devices
Resources that use energy:
- **Smart appliances**: Thermostats, HVAC systems, water heaters, washing machines
- **Industrial equipment**: Manufacturing machinery, data centers
- **Electric Vehicles**: Cars, buses, scooters during charging
- **Building management systems**: Integrated controls for commercial buildings

### Infrastructure
Resources that enable energy delivery:
- **Transformers**: Step-up and step-down voltage converters
- **Smart meters**: Measurement and monitoring devices
- **Grid connections**: Substations, distribution lines
- **Charging stations (EVSE)**: Public and private EV charging infrastructure

### Service Providers
Logical resources that facilitate transactions:
- **Utilities**: Energy distribution companies
- **Aggregators**: Entities that pool distributed resources
- **Energy Service Companies (ESCOs)**: Efficiency and management service providers
- **Demand Response Providers**: Services that coordinate load management
- **Financial institutions**: Banks, payment processors enabling settlements

### Prosumers
Resources that act as both consumers and producers:
- **Households with solar + storage**: Buy from grid during night, sell during day
- **Commercial buildings with solar**: Self-consume during business hours, export excess
- **EV fleets**: Charge during off-peak, potentially provide grid services during peak

## Resource Characteristics

Energy Resources are described by various attributes:

### Identity and Addressability
- **Energy Resource Address (ERA)**: Unique identifier (global or local scope)
- **Type**: Category of resource (generation, storage, consumption, etc.)
- **Owner/Operator**: Entity controlling the resource

### Capacity and Performance
- **Rated capacity**: Maximum generation, storage, or consumption capacity
- **Current availability**: Real-time operational status
- **Efficiency metrics**: Conversion efficiency, round-trip efficiency
- **Response time**: How quickly resource can adjust output/consumption

### Location and Context
- **Geographic location**: Physical coordinates or address
- **Network location**: Connection point in the electrical grid
- **Local/Global scope**: Whether resource operates in constrained context or broader market

### Operational Constraints
- **Operating hours**: Availability windows (e.g., solar only during daylight)
- **Minimum/maximum thresholds**: Operational limits
- **Ramp rates**: Speed of changing output or consumption
- **Maintenance schedules**: Planned downtime

### Credentials and Verification
- **Certifications**: Green energy certification, safety standards compliance
- **Ownership proof**: Legal rights to operate resource
- **Grid connection approval**: Permission to interconnect
- **Transaction history**: Past performance and reliability records

## Energy Resources in Practice

### EV Charging Example

In the EV charging ecosystem, multiple energy resources interact:

#### Charging Station (EVSE) Resource

From the [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md), a charging station is represented with these attributes:

```json
{
  "beckn:id": "ev-charger-ccs2-001",
  "beckn:descriptor": {
    "schema:name": "DC Fast Charger - CCS2 (60kW)",
    "beckn:shortDesc": "High-speed DC charging station with CCS2 connector"
  },
  "beckn:category": {
    "schema:codeValue": "ev-charging",
    "schema:name": "EV Charging"
  },
  "beckn:availableAt": [{
    "geo": {
      "type": "Point",
      "coordinates": [77.5946, 12.9716]
    },
    "address": {
      "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
      "addressLocality": "Bengaluru",
      "addressRegion": "Karnataka",
      "postalCode": "560076",
      "addressCountry": "IN"
    }
  }],
  "beckn:availabilityWindow": {
    "schema:startTime": "06:00:00",
    "schema:endTime": "22:00:00"
  },
  "beckn:rating": {
    "beckn:ratingValue": 4.5,
    "beckn:ratingCount": 128
  },
  "beckn:itemAttributes": {
    "connectorType": "CCS2",
    "maxPowerKW": 60,
    "minPowerKW": 5,
    "socketCount": 2,
    "evseId": "IN*ECO*BTM*01*CCS2*A",
    "ocppId": "IN-ECO-BTM-01",
    "powerType": "DC",
    "chargingSpeed": "FAST",
    "stationStatus": "Available",
    "amenityFeature": ["Restaurant", "Restroom", "Wi-Fi"]
  }
}
```

**Key Resource Attributes**:
- **Identity**: `beckn:id`, `evseId`, `ocppId`
- **Capacity**: `maxPowerKW: 60`, `minPowerKW: 5`, `socketCount: 2`
- **Location**: GPS coordinates, full address
- **Operating Hours**: 06:00-22:00
- **Status**: Real-time availability (`stationStatus: "Available"`)
- **Specifications**: Connector type (CCS2), power type (DC), charging speed classification
- **Additional Services**: Amenities at location

#### Charge Point Operator (CPO) Resource

```json
{
  "beckn:id": "ecopower-charging",
  "beckn:descriptor": {
    "schema:name": "EcoPower Charging Pvt Ltd"
  }
}
```

**Key Resource Attributes**:
- **Identity**: Provider ID
- **Manages**: Multiple EVSE resources across locations
- **Publishes**: Service catalogues with pricing and availability

#### EV User/Vehicle Resource

From transaction examples, represented through:
- Subscriber ID (BAP identifier)
- Vehicle specifications (for filtering compatible chargers)
- Payment credentials
- Contact information for notifications

### P2P Energy Trading Example (Conceptual)

#### Prosumer Household Resource

A household acting as both energy consumer and provider:

**As Generation/Storage Resource**:
```
{
  "resourceId": "household-solar-battery-001",
  "descriptor": {
    "name": "Residential Solar + Battery System",
    "location": {
      "address": "123 Green Street, Sector 5",
      "gpsCoordinates": [77.1234, 12.5678]
    }
  },
  "generationCapacity": {
    "solarArrayKW": 5,
    "peakGenerationKW": 5
  },
  "storageCapacity": {
    "batteryKWh": 10,
    "inverterKW": 5
  },
  "gridConnection": {
    "meterType": "Bidirectional Smart Meter",
    "netMeteringEnabled": true,
    "approvalId": "GRID-CONN-2024-001"
  },
  "credentials": {
    "greenCertification": "SOLAR-CERT-2024-XYZ",
    "ownershipProof": "DEED-123456",
    "interconnectionApproval": "IC-APPROVAL-789"
  },
  "availability": {
    "exportWindow": "10:00:00 to 16:00:00",
    "exportCapacityKW": 3
  }
}
```

**Dual Role**:
- **Morning**: Acts as consumer (charging battery from solar)
- **Afternoon**: Acts as provider (exporting excess solar to neighbors)
- **Evening**: Acts as consumer (drawing from battery and grid)

## Relationship with Other Primitives

Energy Resources are central to all DEG interactions:

1. **Energy Resource Address (ERA)**: Every resource must have an ERA to be discoverable and addressable
2. **Energy Credentials**: Resources carry credentials that attest to their capabilities, certifications, and trustworthiness
3. **Energy Intent**: Resources can express intents describing their energy needs
4. **Energy Catalogue**: Resources can publish catalogues listing available energy or services
5. **Energy Contract**: Resources enter into contracts when their intents and catalogues match

The same resource can play multiple roles across different transactions - a battery storage system might express an intent to charge during off-peak hours while simultaneously publishing a catalogue offering grid services during peak demand.

## Summary

Energy Resources are the foundational entities in DEG - representing everything from massive power plants to individual smart appliances. By providing a unified framework to identify, describe, and interact with diverse energy assets and actors, Energy Resources enable the decentralized, interoperable energy ecosystem that DEG envisions.

Every transaction begins with resources: they receive ERAs, carry credentials, express intents or publish catalogues, and enter into contracts. Understanding Energy Resources is essential to understanding how the Digital Energy Grid operates.

## See Also

- [Energy Resource Address](./Energy%20resource%20address.md) - How resources are uniquely identified
- [Energy Credentials](./Energy%20credentials.md) - How resources establish trust
- [Energy Catalogue](./Energy%20catalogue.md) - How provider resources advertise services
- [Energy Intent](./Energy%20intent.md) - How consumer resources express needs
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - Real-world examples
