# Energy Catalogue

## Definition

An Energy Catalogue is a structured listing of available energy resources, services, or offerings published by providers. Catalogues represent the "offer" side of energy transactions, detailing what is available, in what quantities, at what locations, during which times, at what prices, with what constraints, and through what delivery methods.

Energy catalogues are the supply-side complement to energy intents - when a consumer's intent matches a provider's catalogue offering, the foundation for an energy contract is established.

## Why Energy Catalogues Matter

In traditional centralized energy systems:
- **Limited visibility**: Consumers see only their local utility's offerings
- **Opaque pricing**: Tariffs are complex and not easily comparable
- **No choice**: Single provider per geography, take-it-or-leave-it terms
- **Static offerings**: Limited ability for providers to advertise differentiated services

In decentralized energy markets with multiple providers, diverse resources, and varied service offerings, providers need a standardized way to:
- **Advertise services**: Make offerings discoverable across networks
- **Differentiate**: Highlight unique value propositions (green energy, fast charging, flexible pricing)
- **Update dynamically**: Reflect real-time availability, pricing changes, seasonal variations
- **Reach consumers**: Connect with intent-expressing consumers beyond geographic boundaries

Energy Catalogues solve this by providing a structured format for publishing supply that can be automatically matched with demand intents across distributed networks.

## Structure of Energy Catalogues

Energy catalogues are returned through Beckn Protocol `on_discover` responses:

### Catalogue Response Structure

```json
{
  "context": {
    "action": "on_discover",
    "domain": "beckn.one:deg:ev-charging:*",
    "bpp_id": "bpp.example.com"
  },
  "message": {
    "catalogs": [{
      "beckn:descriptor": {
        "schema:name": "EV Charging Services Network",
        "beckn:shortDesc": "Comprehensive network of fast charging stations"
      },
      "beckn:validity": {
        "schema:startDate": "2024-10-01T00:00:00Z",
        "schema:endDate": "2025-01-15T23:59:59Z"
      },
      "beckn:items": [
        /* Array of available services/resources */
      ],
      "beckn:offers": [
        /* Array of pricing and commercial terms */
      ]
    }]
  }
}
```

**Catalogue Components**:
- **Descriptor**: Catalogue name and description
- **Validity**: Time period for which catalogue is valid
- **Items**: Available resources/services (e.g., charging stations, energy offerings)
- **Offers**: Pricing models and commercial terms

### Item Structure (Energy Resource Listing)

From the EV Charging Implementation Guide:

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
      "postalCode": "560076"
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
    "evseId": "IN*ECO*BTM*01*CCS2*A",
    "stationStatus": "Available"
  }
}
```

### Offer Structure (Pricing and Terms)

```json
{
  "beckn:id": "offer-ccs2-60kw-kwh",
  "beckn:descriptor": {
    "schema:name": "Per-kWh Tariff - CCS2 60kW"
  },
  "beckn:items": ["ev-charger-ccs2-001"],
  "beckn:price": {
    "currency": "INR",
    "value": 18.0,
    "applicableQuantity": {
      "unitText": "Kilowatt Hour",
      "unitCode": "KWH",
      "unitQuantity": 1
    }
  },
  "beckn:validity": {
    "schema:startDate": "2025-10-10T00:00:00Z",
    "schema:endDate": "2026-04-10T23:59:59Z"
  },
  "beckn:acceptedPaymentMethod": ["UPI", "CreditCard", "Wallet"],
  "beckn:offerAttributes": {
    "buyerFinderFee": {
      "feeType": "PERCENTAGE",
      "feeValue": 2.5
    },
    "idleFeePolicy": "₹2/min after 10 min post-charge"
  }
}
```

## Types of Energy Catalogue Offerings

### Infrastructure Services

Catalogues listing physical infrastructure available for energy transactions:

**EV Charging Stations**:
- Location and accessibility
- Connector types and power ratings
- Availability windows
- Amenities (restroom, Wi-Fi, food)
- Real-time status

**Grid Connection Services**:
- Interconnection capacity available
- Connection approval processing
- Technical requirements
- Installation services

### Energy Supply

Catalogues listing energy available for purchase:

**Utility Grid Power**:
- Time-of-use tariffs
- Demand response programs
- Interruptible vs. firm power
- Voltage and phase specifications

**Distributed Generation (DER)**:
- Rooftop solar excess capacity
- Battery storage discharge windows
- Combined heat and power (CHP) availability
- Wind farm allocations

**Peer-to-Peer (P2P) Trading**:
- Prosumer excess energy
- Community solar shares
- Virtual power plant (VPP) aggregated capacity
- Time-based availability windows

### Data and Analytics Services

Catalogues for energy-related data offerings:

**Consumption Data**:
- Anonymized household/sector consumption patterns
- Peak demand analytics
- Load forecasting datasets

**Market Information**:
- Real-time pricing signals
- Forecast prices and availability
- Carbon intensity data
- Renewable generation forecasts

### Financial and Support Services

Catalogues for energy-adjacent services:

**Financing**:
- Solar installation loans
- EV purchase financing
- Energy efficiency retrofit funding

**Insurance and Guarantees**:
- Performance guarantees for solar installations
- Demand guarantee insurance
- Price hedging products

**Installation and Maintenance**:
- Solar panel installation services
- EV charger setup
- Battery storage commissioning
- Ongoing maintenance contracts

## Energy Catalogues in Practice

### From EV Charging Implementation Guide

#### Complete Catalogue Response

**Provider**: EcoPower Charging Pvt Ltd
**Catalogue**: EV Charging Services Network

```json
{
  "message": {
    "catalogs": [{
      "beckn:descriptor": {
        "schema:name": "EV Charging Services Network"
      },
      "beckn:items": [{
        "beckn:id": "ev-charger-ccs2-001",
        "beckn:descriptor": {
          "schema:name": "DC Fast Charger - CCS2 (60kW)"
        },
        "beckn:availableAt": [{
          "geo": {"coordinates": [77.5946, 12.9716]},
          "address": {
            "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
            "addressLocality": "Bengaluru"
          }
        }],
        "beckn:availabilityWindow": {
          "schema:startTime": "06:00:00",
          "schema:endTime": "22:00:00"
        },
        "beckn:itemAttributes": {
          "connectorType": "CCS2",
          "maxPowerKW": 60,
          "minPowerKW": 5,
          "socketCount": 2,
          "evseId": "IN*ECO*BTM*01*CCS2*A",
          "stationStatus": "Available",
          "amenityFeature": ["Restaurant", "Restroom", "Wi-Fi"]
        },
        "beckn:rating": {
          "beckn:ratingValue": 4.5,
          "beckn:ratingCount": 128
        }
      }],
      "beckn:offers": [{
        "beckn:id": "offer-ccs2-60kw-kwh",
        "beckn:descriptor": {
          "schema:name": "Per-kWh Tariff - CCS2 60kW"
        },
        "beckn:items": ["ev-charger-ccs2-001"],
        "beckn:price": {
          "currency": "INR",
          "value": 18.0,
          "applicableQuantity": {
            "unitText": "Kilowatt Hour",
            "unitCode": "KWH"
          }
        },
        "beckn:acceptedPaymentMethod": ["UPI", "CreditCard", "Wallet"],
        "beckn:offerAttributes": {
          "buyerFinderFee": {
            "feeType": "PERCENTAGE",
            "feeValue": 2.5
          },
          "idleFeePolicy": "₹2/min after 10 min post-charge"
        }
      }]
    }]
  }
}
```

**Key Catalogue Elements**:
1. **Service Identity**: EVSE ID, provider ID, location
2. **Technical Specifications**: Connector type, power range, socket count
3. **Availability**: Operating hours 6 AM - 10 PM
4. **Status**: Real-time "Available" status
5. **Amenities**: Restaurant, restroom, Wi-Fi on-site
6. **Pricing**: ₹18/kWh
7. **Payment**: UPI, Credit Card, Wallet accepted
8. **Fees**: 2.5% finder fee, ₹2/min idle fee after 10 min grace
9. **Reputation**: 4.5 star rating from 128 users

### P2P Energy Trading Catalogue (Conceptual)

#### Prosumer Solar Export Catalogue

**Provider**: Household Solar Battery 001
**Catalogue**: Excess Solar Energy Available

```json
{
  "message": {
    "catalogs": [{
      "beckn:descriptor": {
        "schema:name": "Excess Solar Energy - Afternoon Export"
      },
      "beckn:items": [{
        "beckn:id": "excess-solar-export-afternoon",
        "beckn:descriptor": {
          "schema:name": "Rooftop Solar Excess Capacity",
          "beckn:longDesc": "Clean solar energy from certified 5kW rooftop installation"
        },
        "beckn:category": {
          "schema:codeValue": "solar-export",
          "schema:name": "Peer-to-Peer Solar Trading"
        },
        "beckn:availableAt": [{
          "address": {
            "addressLocality": "Sector 5, Bengaluru",
            "postalCode": "560001"
          }
        }],
        "beckn:availabilityWindow": {
          "schema:startTime": "10:00:00",
          "schema:endTime": "16:00:00"
        },
        "beckn:itemAttributes": {
          "energySource": "solar",
          "installedCapacity": "5kW",
          "averageExportCapacity": "3kW",
          "greenCertified": true,
          "certificateId": "SOLAR-CERT-2024-XYZ",
          "gridInterconnected": true
        }
      }],
      "beckn:offers": [{
        "beckn:id": "solar-export-rate-afternoon",
        "beckn:items": ["excess-solar-export-afternoon"],
        "beckn:price": {
          "currency": "INR",
          "value": 5.50,
          "applicableQuantity": {
            "unitCode": "KWH"
          }
        },
        "beckn:validity": {
          "schema:startDate": "2024-11-01T00:00:00Z",
          "schema:endDate": "2024-12-31T23:59:59Z"
        },
        "beckn:offerAttributes": {
          "minimumPurchase": "5kWh",
          "maximumPurchase": "15kWh",
          "deliveryMethod": "grid-injection",
          "meteringAttestation": true
        }
      }]
    }]
  }
}
```

**Key Catalogue Elements**:
1. **Energy Source**: Solar, green certified
2. **Capacity**: 5kW installation, ~3kW average export
3. **Availability**: 10 AM - 4 PM daily (peak solar hours)
4. **Location**: Sector 5, Bengaluru (local P2P)
5. **Credentials**: Green certificate SOLAR-CERT-2024-XYZ
6. **Pricing**: ₹5.50/kWh
7. **Constraints**: Min 5 kWh, max 15 kWh per transaction
8. **Delivery**: Grid injection with smart meter attestation

## Catalogue Lifecycle in Transactions

### Phase 1: Publishing

**Actor**: Provider (via BPP)
**Process**: Create and maintain catalogue

```
Provider defines services → BPP structures catalogue → Registers with CDS
  ↓
Catalogue indexed for discovery
  ↓
Real-time updates (availability, pricing)
```

### Phase 2: Discovery Matching

**Actors**: CDS, BPP
**Process**: Filter catalogue based on consumer intent

```
CDS receives discover intent → Routes to relevant BPPs
  ↓
BPP filters catalogue based on intent constraints
  ↓
Returns matching items in on_discover
```

**Example**: Intent for "CCS2, 50kW+, within 10km" → Catalogue filtered to matching chargers only

### Phase 3: Selection Response

**Actor**: BPP
**Process**: Generate detailed quote for selected item

```
BPP receives select → Validates selection → Generates quote (on_select)
```

### Phase 4: Contract Formation

**Process**: Catalogue offering + accepted intent → Energy Contract

```
Init/Confirm flow → Catalogue terms finalized → Contract established
```

## Catalogue Composition

Catalogues can include multiple dimensions:

### Resource Attributes
- **Identity**: Unique IDs (EVSE ID, resource ERA)
- **Type**: Category, subcategory, classification
- **Specifications**: Technical parameters (power, capacity, connector type)
- **Location**: Geographic coordinates, address, accessibility

### Availability
- **Operating hours**: Start/end times, days of week
- **Real-time status**: Available, occupied, offline, reserved
- **Capacity**: Current vs. total capacity
- **Scheduling**: Future availability windows

### Commercial Terms
- **Pricing**: Per-unit rates, subscription models, time-of-use tariffs
- **Payment**: Accepted methods, prepaid vs. postpaid
- **Fees**: Platform fees, idle fees, cancellation fees
- **Minimums/maximums**: Minimum purchase, maximum capacity

### Service Quality
- **Ratings**: User reviews and average ratings
- **Reliability**: Uptime percentage, historical performance
- **Support**: Customer service availability, response times
- **Amenities**: Additional services or features

### Credentials and Compliance
- **Certifications**: Safety standards, green energy attestations
- **Licenses**: Operational permits, regulatory compliance
- **Insurance**: Liability coverage, performance guarantees
- **Attestations**: Third-party verifications

## Relationship with Other Primitives

1. **Energy Resource**: Catalogues list available resources (with ERAs)
2. **Energy Resource Address**: Each catalogue item has an ERA for addressability
3. **Energy Credentials**: Catalogue includes or references resource credentials
4. **Energy Intent**: Catalogues are filtered/matched against consumer intents
5. **Energy Contract**: Catalogue offering + matched intent = contract formation

## Summary

Energy Catalogues are the supply-side voice in the Digital Energy Grid - enabling structured, machine-readable publication of energy offerings that can be automatically matched with consumer intents across distributed networks. From charging station listings to prosumer solar exports, catalogues make diverse energy services discoverable, comparable, and accessible.

Together with intents, catalogues form the complementary sides of a digital handshake. When an energy intent matches an energy catalogue offering, an energy contract is established - **this cycle of intent matched with catalogue, forming a contract, is the fundamental interaction loop in the Digital Energy Grid**.

## See Also

- [Energy Intent](./Energy%20intent.md) - The demand side that matches with catalogues
- [Energy Contract](./Energy%20contract.md) - What emerges when catalogue meets intent
- [Energy Resource](./Energy%20resource.md) - Resources listed in catalogues
- [Energy Credentials](./Energy%20credentials.md) - Credentials referenced in catalogues
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - Catalogue examples in practice

