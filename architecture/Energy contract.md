# Energy Contract

## Definition

An Energy Contract is a formalized agreement that emerges when an energy intent successfully matches with a catalogue offering. Contracts define the boundaries of interactions between two or more parties in an energy ecosystem, specifying who is transacting, what is being exchanged, under what terms, and how fulfillment will occur.

In every interaction, one party seeks something, and another party provides it. An energy contract comprises two fundamental components: **Energy intent** (the ask) and **Energy catalogue** (the offer). When these match, a contract is formed.

**The cycle of intent matched with catalogue, forming a contract, is the fundamental interaction loop in the Digital Energy Grid.**

## Why Energy Contracts Matter

Traditional energy transactions operate under rigid, pre-defined contracts:
- **Utility service agreements**: One-size-fits-all terms, limited customization
- **Long-term PPAs**: Complex, legally-heavy agreements requiring extensive negotiation
- **High transaction costs**: Legal overhead makes small-scale contracts impractical

In decentralized energy markets, there's a need for:
- **Automated contract formation**: Match intent with catalogue, confirm terms automatically
- **Flexible scope**: From simple acknowledgments to complex multi-party arrangements
- **Layered complexity**: Basic contracts for simple transactions, detailed terms when needed
- **Digital enforceability**: Machine-readable contracts that can be verified programmatically

## Contract Scope - Layered Framework

Energy contracts operate as layered frameworks, where the basic requirement is simply mutual acknowledgment by all involved parties that they are entering into an agreement. Other conditions are optional and can be included as needed.

### Layer 1: Basic Acknowledgment
**Minimum requirement**: Mutual acknowledgment of engagement.

**Examples**:
- A home automation system interacting with devices like smart bulbs, thermostats
- Device-to-device communication in smart homes

### Layer 2: Service Agreement
**Adds**: Purpose of interaction, basic service terms.

**Examples**:
- A utility monitoring energy generation and consumption data from connected households
- Data sharing with specific frequency and privacy terms

### Layer 3: Commercial Transaction
**Adds**: Pricing, payment terms, quantities, delivery specifications.

**Examples**:
- EV charging sessions with per-kWh pricing
- P2P energy trading with delivery windows

### Layer 4: Complex Multi-Party Agreement
**Adds**: Multiple parties, SLAs, legal enforceability, dispute resolution.

**Examples**:
- Long-term power purchase agreements
- Multi-party energy trading with settlement and penalties

The legal enforceability of energy contracts can vary widely. Some contracts may not require legal enforceability or specific business requirements such as Service Level Agreements (SLAs).

## Contract Formation in Beckn Protocol

Energy contracts are established through the `confirm` and `on_confirm` actions:

### Confirmation Request (confirm)

```json
{
  "context": {
    "action": "confirm",
    "domain": "beckn.one:deg:ev-charging:*"
  },
  "message": {
    "order": {
      "beckn:id": "order-ev-charging-001",
      "beckn:orderStatus": "QUOTE_ACCEPTED",
      "beckn:seller": "ecopower-charging",
      "beckn:buyer": "user-12345",
      "beckn:orderItems": [{
        "beckn:orderedItem": "ev-charger-ccs2-001",
        "beckn:quantity": 2.5
      }],
      "beckn:payment": {
        "beckn:paymentMethod": "UPI"
      }
    }
  }
}
```

### Confirmation Response (on_confirm)

```json
{
  "message": {
    "order": {
      "beckn:id": "order-bpp-789012",
      "beckn:orderStatus": "CONFIRMED",
      "beckn:orderNumber": "ORD-2025-001",
      "beckn:seller": "ecopower-charging",
      "beckn:buyer": {
        "beckn:id": "user-123",
        "beckn:name": "John Doe"
      },
      "beckn:orderValue": {
        "currency": "INR",
        "value": 128.64
      },
      "beckn:fulfillment": {
        "beckn:status": "PENDING"
      }
    }
  }
}
```

## Contract Lifecycle

### Phase 1: Formation (discover → confirm)
```
Intent (discover) ↔ Catalogue (on_discover)
  ↓
Selection (select) ↔ Quote (on_select)
  ↓
Initialize (init) ↔ Terms (on_init)
  ↓
Confirm (confirm) ↔ CONTRACT ESTABLISHED (on_confirm)
```

### Phase 2: Execution
```
Fulfillment initiated (update)
  ↓
Progress tracking (track, on_status)
  ↓
Completion (update: stop)
```

### Phase 3: Settlement
```
Final verification
  ↓
Payment settlement
  ↓
Transaction receipt
```

## Examples from EV Charging

### Confirmed Charging Session Contract

**Parties**: Ravi Kumar ↔ CPO (ecopower-charging)
**Service**: 5 kWh EV charging
**Pricing**: ₹128.64 total (base + surge + tax + fees)
**Payment**: UPI, authorized
**Fulfillment**: Reservation mode, CCS2 connector

Contract ID: ORD-2025-001
Reservation: RESV-789012

## Relationship with Other Primitives

Energy Contracts culminate all primitives:

1. **Energy Resource**: Contracts bind resources in transactions
2. **Energy Resource Address**: Contract parties identified by ERAs
3. **Energy Credentials**: Verified during contract formation
4. **Energy Intent**: Forms one input to contract
5. **Energy Catalogue**: Forms the other input to contract

## Summary

Energy Contracts formalize energy transactions in the Digital Energy Grid. Emerging from intent-catalogue matching, contracts define who transacts, what is exchanged, under what terms, and how fulfillment occurs. From simple acknowledgments to complex multi-party arrangements, energy contracts enable the full spectrum of energy interactions.

## See Also

- [Energy Intent](./Energy%20intent.md) - Consumer demand forming contracts
- [Energy Catalogue](./Energy%20catalogue.md) - Provider supply forming contracts
- [Energy Resource](./Energy%20resource.md) - Resources bound by contracts
- [EV Charging Implementation Guide](../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) - Contract examples
