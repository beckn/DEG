# Energy Intent

## Definition

An Energy Intent is a digital representation of energy demand or requirements, expressing what an energy consumer needs, along with preferred conditions, constraints, and acceptable terms. Intents articulate the "ask" side of energy transactions - enabling consumers to specify their needs in a structured, machine-readable format that can be matched against provider catalogues.

Energy intents range from simple expressions ("charge my EV") to detailed specifications with quantity, timing, location, price limits, source preferences, and quality requirements.

## Why Energy Intents Matter

In traditional energy systems, consumers have limited ability to express preferences:
- **Utility service**: You get whatever power is available, when it's available
- **Limited choice**: No ability to specify renewable sources, price caps, or delivery timing
- **Opaque matching**: No visibility into how demand meets supply

In decentralized energy markets with multiple providers, diverse resources, and varied service offerings, consumers need a standardized way to:
- **Discover relevant services**: Find providers that can meet their specific needs
- **Express preferences**: Specify renewable energy, time windows, location constraints
- **Set boundaries**: Define maximum prices, minimum service levels, required credentials
- **Enable automation**: Allow apps/agents to transact on their behalf

Energy Intents solve this by providing a structured format for expressing demand that can be automatically matched with supply catalogues across distributed networks.

## Structure of Energy Intents

Energy intents are expressed through Beckn Protocol API calls, primarily the `discover` and `select` actions:

### Discovery Intent (discover)

The initial expression of need, often broad, to find available services:

```json
{
  "context": {
    "action": "discover",
    "domain": "beckn.one:deg:ev-charging:*",
    "bap_id": "app.example.com",
    "transaction_id": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002"
  },
  "message": {
    "spatial": [{
      "op": "s_dwithin",
      "targets": "$['beckn:availableAt'][*]['geo']",
      "geometry": {
        "type": "Point",
        "coordinates": [77.59, 12.94]
      },
      "distanceMeters": 10000
    }],
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.connectorType == 'CCS2' && @.beckn:itemAttributes.maxPowerKW >= 50)]"
    }
  }
}
```

**Intent Components**:
- **Context**: Who is asking (BAP ID), what domain (EV charging), when
- **Spatial filters**: Geographic constraints (point + radius, along route)
- **Attribute filters**: JSONPath expressions for resource specifications (connector type, power rating, availability windows)

### Selection Intent (select)

A refined intent specifying exactly what is desired from discovered options:

```json
{
  "context": {
    "action": "select",
    "domain": "beckn.one:deg:ev-charging:*"
  },
  "message": {
    "order": {
      "beckn:orderItems": [{
        "beckn:orderedItem": "ev-charger-ccs2-001",
        "beckn:quantity": 2.5,
        "beckn:acceptedOffer": {
          "beckn:price": {
            "value": 18.0,
            "applicableQuantity": {
              "unitCode": "KWH"
            }
          }
        }
      }],
      "beckn:fulfillment": {
        "beckn:mode": "RESERVATION"
      }
    }
  }
}
```

**Refined Intent Components**:
- **Specific resource**: Exact item/service selected (eg: EVSE ID or ERA)
- **Quantity**: Amount of energy (kWh) or duration
- **Accepted offer**: Specific pricing terms agreed to
- **Fulfillment mode**: Immediate, reservation, scheduled delivery

## Types of Energy Intents

### Simple Intents

High-level expressions of need without detailed constraints:

**Examples**:
- "As a consumer, I want to charge my electric scooter"
- "As a utility, I need energy consumption data from households in sector XYZ"
- "I require solar rooftop installation and financing"
- "Find charging stations near me"

### Detailed Intents

Specific requirements with multiple constraints and preferences:

**Examples**:
- "I need 20 kWh between 6 PM and 9 PM, preferably sourced from solar power, and will pay no more than ₹7 per kWh"
- "Reserve a CCS2 fast charger within 5km, available in next 30 minutes, accepting UPI payment"
- "Buy 10 kWh solar energy from verified prosumers in my neighborhood, delivery between 2-4 PM, price ≤ ₹5.50/kWh"

## Energy Intents in Practice

### From EV Charging Implementation Guide

#### Discovery Intent: Find Chargers Within Boundary with Specifications

**Intent**: "Find CCS2 chargers with 50kW+ power within 10km of my location"

```json
{
  "message": {
    "spatial": [{
      "op": "s_dwithin",
      "targets": "$['beckn:availableAt'][*]['geo']",
      "geometry": {
        "type": "Point",
        "coordinates": [77.59, 12.94]
      },
      "distanceMeters": 10000
    }],
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.connectorType == 'CCS2' && @.beckn:itemAttributes.maxPowerKW >= 50)]"
    }
  }
}
```

#### Discovery Intent: Find Available in Time Range

**Intent**: "Find CCS2 chargers available between 12:30 PM and 2:30 PM"

```json
{
  "message": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.connectorType == 'CCS2' && @.beckn:availabilityWindow.schema:startTime <= '12:30:00' && @.beckn:availabilityWindow.schema:endTime >= '14:30:00')]"
    }
  }
}
```

#### Discovery Intent: Find Specific EVSE by ID

**Intent**: "Find charger IN*ECO*BTM*01*CCS2*A" (after scanning QR code)

```json
{
  "message": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.evseId == 'IN*ECO*BTM*01*CCS2*A')]"
    }
  }
}
```

#### Selection Intent: Reserve Charging Slot

**Intent**: "Reserve 2.5 kWh at charger ev-charger-ccs2-001, accepting ₹18/kWh rate, total ₹100"

```json
{
  "message": {
    "order": {
      "beckn:orderValue": {
        "currency": "INR",
        "value": 100.0
      },
      "beckn:orderItems": [{
        "beckn:orderedItem": "ev-charger-ccs2-001",
        "beckn:quantity": 2.5,
        "beckn:acceptedOffer": {
          "beckn:id": "offer-ccs2-60kw-kwh",
          "beckn:price": {
            "value": 18.0,
            "applicableQuantity": {
              "unitCode": "KWH"
            }
          }
        }
      }],
      "beckn:fulfillment": {
        "beckn:mode": "RESERVATION",
        "beckn:deliveryAttributes": {
          "connectorType": "CCS2",
          "reservationId": "RESV-984532",
          "gracePeriodMinutes": 10
        }
      }
    }
  }
}
```

### P2P Energy Trading Intents (Conceptual)

#### Discovery Intent: Buy Solar Energy from Neighbors

**Intent**: "Buy 10 kWh solar energy from prosumers within 2km, delivery 2-4 PM, max ₹6/kWh, certified sellers only"

```json
{
  "context": {
    "action": "discover",
    "domain": "beckn.one:deg:p2p-trading:*"
  },
  "message": {
    "spatial": [{
      "op": "s_dwithin",
      "geometry": {
        "type": "Point",
        "coordinates": [12.9716, 77.5946]
      },
      "distanceMeters": 2000
    }],
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.energyType == 'solar' && @.price.value <= 6.0 && @.credentials[?(@.type == 'GreenCertification')])]"
    },
    "temporal": {
      "deliveryWindow": {
        "startTime": "14:00:00",
        "endTime": "16:00:00"
      }
    }
  }
}
```

#### Selection Intent: Accept Prosumer Offer

**Intent**: "Accept offer from household-solar-001 to buy 10 kWh at ₹5.50/kWh, delivery Nov 12 2-4 PM"

```json
{
  "message": {
    "order": {
      "seller": "household-solar-001.prosumer.example.com",
      "buyer": "apartment-complex-456.example.com",
      "orderItems": [{
        "orderedItem": "excess-solar-export-afternoon",
        "quantity": 10,
        "acceptedOffer": {
          "price": {
            "value": 5.50,
            "currency": "INR",
            "applicableQuantity": {
              "unitCode": "KWH"
            }
          }
        }
      }],
      "fulfillment": {
        "deliveryWindow": {
          "startTime": "2024-11-12T14:00:00Z",
          "endTime": "2024-11-12T16:00:00Z"
        },
        "meterReading": {
          "meteringAuthority": "SmartMeterCo",
          "attestationRequired": true
        }
      }
    }
  }
}
```

## Intent Lifecycle in Transactions

### Phase 1: Initial Discovery

**Actor**: Consumer (via BAP)
**Action**: `discover`
**Purpose**: Express broad need, find available services

```
User opens app → Expresses intent → BAP sends discover → CDS routes to BPPs
```

**Example**: EV user searches for "charging stations near me"

### Phase 2: Catalogue Matching

**Actors**: Catalogue Discovery Service, BPPs
**Process**: Route intent to relevant providers, filter catalogues

```
CDS receives intent → Identifies relevant BPPs based on domain/location
  ↓
BPPs filter their catalogues based on intent constraints
  ↓
Return matching items in on_discover
```

**Example**: Only chargers within radius, with CCS2 connector, ≥50kW power, currently available

### Phase 3: Refinement and Selection

**Actor**: Consumer (via BAP)
**Action**: `select`
**Purpose**: Specify exact choice from discovered options

```
User reviews catalogue results → Selects specific service → BAP sends select
  ↓
BPP generates detailed quote with pricing
  ↓
Returns on_select with quote
```

**Example**: User chooses specific charger, requests 20 kWh at quoted ₹18/kWh

### Phase 4: Initialization and Confirmation

**Actions**: `init`, `confirm`
**Purpose**: Finalize terms, establish contract

```
User provides billing details (init) → BPP returns payment terms (on_init)
  ↓
User reviews final terms → Confirms order (confirm)
  ↓
BPP confirms reservation (on_confirm) → Contract established
```

**Example**: User confirms charging session with UPI payment, receives booking confirmation

## Relationship with Other Primitives

1. **Energy Resource**: Intent originates from a consumer resource (ERA of requester)
2. **Energy Resource Address**: Intent targets resources addressable by ERA
3. **Energy Credentials**: Intent may require specific credentials from providers
4. **Energy Catalogue**: Intent is matched against catalogues to find suitable offerings
5. **Energy Contract**: Successful intent-catalogue match leads to contract formation

## Summary

Energy Intents are the consumer's voice in the Digital Energy Grid - enabling structured, machine-readable expression of energy needs that can be automatically matched with provider offerings across distributed networks. From simple discovery ("find nearby chargers") to complex specifications ("CCS2, 50kW+, available 12:30-2:30 PM, within 10km"), intents empower consumers with choice, transparency, and control in decentralized energy markets.

By combining intents with catalogues through the Beckn Protocol's discover-select-init-confirm flow, DEG creates a dynamic, responsive marketplace where demand finds supply efficiently.

## See Also

- [Energy Catalogue](./Energy%20catalogue.md) - The supply side that matches with intents
- [Energy Contract](./Energy%20contract.md) - What emerges when intent meets catalogue
- [Energy Resource](./Energy%20resource.md) - Resources that express intents
- [Energy Credentials](./Energy%20credentials.md) - Credentials required in intents
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - Intent examples in practice
