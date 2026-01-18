# Inter-Energy Retailer P2P Energy Trading (Decentralized Approach)

## Overview

This document describes an alternative approach to inter-energy retailer P2P trading that **eliminates the need for a central trade exchange/ledger**. Instead, each utility maintains its own ledger for its customers, and trust is established through cascading Beckn protocol calls with multi-party digital signatures.

For the original approach using a central ledger, see [Inter_energy_retailer_P2P_trading_draft.md](./Inter_energy_retailer_P2P_trading_draft.md).

For a detailed comparison of both approaches, see [Central_vs_Decentralized_Ledger_Comparison.md](./Central_vs_Decentralized_Ledger_Comparison.md).

---

## Scenario

P2P trading between prosumers belonging to different energy retailers/distribution utilities (discoms). Each discom handles routine activities: providing electricity connections, certifying meters, billing, maintaining grid infrastructure, and ensuring grid resilience within their jurisdiction.

**Example:** Prosumer P1 (Meter ID: M1, Utility A) sells electricity to Prosumer P7 (Meter ID: M7, Utility B).

---

## Key Architectural Difference

| Aspect | Central Ledger Approach | Decentralized Approach |
|--------|------------------------|------------------------|
| Trade records | Single central ledger (Trade Exchange) | Each utility maintains its own ledger |
| Trust model | All parties trust the central ledger | Multi-party signatures create distributed proof |
| Trading limits | Central ledger tracks all limits | Each utility tracks only its own customers' limits |
| Reconciliation | Central ledger allocates actual energy | Each utility allocates for its own customers |
| Privacy | Central entity sees all trade details | Each utility only sees trades involving its customers |

---

## Actors

| # | Actor | Role | Beckn Role |
|---|-------|------|------------|
| 1 | **BuyerTP** | Consumer's trading platform | BAP (Beckn Application Platform) |
| 2 | **SellerTP** | Producer's trading platform | BPP (Beckn Provider Platform) |
| 3 | **BuyerUtility** | Buyer's energy retailer/distribution company | BPP (for limit checks and settlement) |
| 4 | **SellerUtility** | Seller's energy retailer/distribution company | BPP (for limit checks and settlement) |
| 5 | **Buyer** | Energy consumer in P2P trade | End user |
| 6 | **Seller** | Energy producer in P2P trade | End user |

> **Note:** When buyer and seller are with the **same utility**, the flow simplifies naturally - BuyerUtility and SellerUtility collapse into a single entity, reducing the number of hops while maintaining the same protocol structure.

---

## Core Design Principles

1. **BAP-initiated flows**: All transactions start from BuyerTP (BAP), maintaining Beckn protocol symmetry
2. **Cascading calls**: Multi-party flows cascade through SellerTP to both utilities
3. **Optional utility involvement**: Utility participation in init/confirm is optional but recommended for trading limit enforcement
4. **Distributed ledgers**: Each utility maintains its own ledger for its customers only
5. **Multi-party signatures**: Tamper-proof audit trail through sequential signing
6. **Natural collapse**: Same-utility trades collapse to single-discom flow automatically

---

## Overall Process Flow

```mermaid
sequenceDiagram
    autonumber
    participant B as Buyer (P7)
    participant BuyerTP as BuyerTP (BAP)
    participant SellerTP as SellerTP (BPP)
    participant S as Seller (P1)
    participant BuyerUtility as BuyerUtility
    participant SellerUtility as SellerUtility

    rect rgb(230, 245, 255)
    note over BuyerTP,SellerTP: Phase 1: Trade Discovery & Selection
    B->>BuyerTP: Search for energy offers
    BuyerTP->>SellerTP: /select (choose offer)
    SellerTP->>BuyerTP: /on_select (offer details)
    end

    rect rgb(255, 250, 230)
    note over BuyerTP,SellerUtility: Phase 2: Trade Initialization
    BuyerTP->>SellerTP: /init (trade details)
    opt Optional Utility Limit Checks
        BuyerTP-->>BuyerUtility: /init (if trading limits unknown OR multi-platform onboarding)
        SellerTP-->>SellerUtility: /init (cascaded)
        SellerUtility-->>SellerTP: /on_init (seller's remaining limit)
        BuyerUtility-->>BuyerTP: /on_init (buyer's remaining limit)
    end
    SellerTP->>BuyerTP: /on_init
    end

    rect rgb(230, 255, 230)
    note over BuyerTP,SellerUtility: Phase 3: Trade Confirmation
    BuyerTP->>SellerTP: /confirm (trade contract)
    alt Non-blocking (Recommended)
        SellerTP->>BuyerTP: /on_confirm (trade confirmed)
        par Inform utilities
            SellerTP->>SellerUtility: /confirm (inform utility)
            SellerUtility->>SellerUtility: Deduct from seller limit, log trade
            SellerUtility-->>SellerTP: /on_confirm (acknowledged)
        and
            SellerTP->>BuyerUtility: /confirm (inform utility)
            BuyerUtility->>BuyerUtility: Deduct from buyer limit, log trade
            BuyerUtility-->>SellerTP: /on_confirm (acknowledged)
        end
    else Blocking
        par Utility confirmations
            SellerTP->>SellerUtility: /confirm
            SellerUtility->>SellerUtility: Deduct from seller limit, log trade
            SellerUtility->>SellerTP: /on_confirm (signed)
        and
            SellerTP->>BuyerUtility: /confirm
            BuyerUtility->>BuyerUtility: Deduct from buyer limit, log trade
            BuyerUtility->>SellerTP: /on_confirm (signed)
        end
        SellerTP->>BuyerTP: /on_confirm (signed sealed order)
    end
    end

    opt Phase 3b: Trade Update (e.g., scheduled outage)
        BuyerUtility->>SellerTP: /update (cancel/curtail trade)
        par Cascade update
            SellerTP->>SellerUtility: /update (notify of change)
            SellerUtility->>SellerUtility: Update trade in ledger
            SellerUtility-->>SellerTP: /on_update (acknowledged)
        and
            SellerTP->>BuyerTP: /update (notify of change)
            BuyerTP->>BuyerTP: Update trade status
            BuyerTP-->>SellerTP: /on_update (acknowledged)
        end
        SellerTP->>BuyerUtility: /on_update (update confirmed)
        BuyerUtility->>BuyerUtility: Update trade in ledger
    end

    rect rgb(255, 230, 230)
    note over S,BuyerUtility: Phase 4: Energy Delivery
    S->>SellerUtility: Request to inject energy
    SellerUtility->>SellerUtility: Grid security check
    alt Grid stable
        SellerUtility->>S: Permit injection
        S->>S: Inject energy into grid
        B->>B: Consume energy
    else Grid unstable
        SellerUtility-->>S: Reject/limit injection
    end
    end

    rect rgb(245, 230, 255)
    note over SellerTP,BuyerUtility: Phase 5: Post-Delivery Allocation
    SellerUtility->>SellerUtility: Allocate actual pushed to trades
    SellerUtility-->>SellerTP: /on_status (allocated quantity)
    BuyerUtility->>BuyerUtility: Allocate actual pulled to trades
    BuyerUtility-->>BuyerTP: /on_status (allocated quantity)
    end

    rect rgb(255, 240, 245)
    note over S,B: Phase 6: Billing & Settlement
    SellerUtility->>S: Monthly bill (excl. P2P sold + wheeling)
    S->>SellerUtility: Pay bill
    BuyerUtility->>B: Monthly bill (excl. P2P bought + wheeling)
    B->>BuyerUtility: Pay bill
    end
```

---

## Phase 1: Trade Discovery and Selection

This phase follows standard Beckn discovery flow. Buyer searches for energy offers and selects one.

```mermaid
sequenceDiagram
    autonumber
    participant B as Buyer
    participant BuyerTP as BuyerTP (BAP)
    participant SellerTP as SellerTP (BPP)
    participant S as Seller

    B->>BuyerTP: Search for energy offers<br/>(delivery window, quantity, location)
    BuyerTP->>SellerTP: /select
    Note right of SellerTP: Offer: 5 kWh, 2-4 PM,<br/>$0.50/kWh
    SellerTP->>BuyerTP: /on_select<br/>(offer details, seller info)
    BuyerTP->>B: Display offer details
```

---

## Phase 2: Trade Initialization

The initialization phase optionally checks trading limits with both utilities. This is optional but recommended to prevent trade failures at confirmation time.

### Why Check Limits?

Each utility may impose trading limits on its customers to:
- Manage grid capacity
- Control financial exposure
- Comply with regulatory requirements

### Initialization Flow

```mermaid
sequenceDiagram
    autonumber
    participant BuyerTP as BuyerTP (BAP)
    participant BuyerUtility as BuyerUtility
    participant SellerTP as SellerTP (BPP)
    participant SellerUtility as SellerUtility

    Note over BuyerTP,SellerUtility: Trade: 5 kWh, 2-4 PM, $0.50/kWh

    BuyerTP->>SellerTP: /init (trade details)

    opt Optional Utility Limit Checks
        par Parallel limit checks
            BuyerTP->>BuyerUtility: /init (buyer limit check)
            BuyerUtility->>BuyerUtility: Look up buyer's<br/>remaining trading limit
            BuyerUtility-->>BuyerTP: /on_init<br/>(remaining limit: 20 kWh)
        and
            SellerTP->>SellerUtility: /init (seller limit check)
            SellerUtility->>SellerUtility: Look up seller's<br/>remaining trading limit
            SellerUtility-->>SellerTP: /on_init<br/>(remaining limit: 15 kWh)
        end
    end

    SellerTP->>BuyerTP: /on_init<br/>(trade initialized, limits OK)
```

### What Each Utility Tracks in Its Own Ledger

| Data Element | Owner | Description |
|--------------|-------|-------------|
| Customer's trading limit | Customer's utility | Max energy that customer can trade in a period |
| Customer's confirmed trades | Customer's utility | All confirmed trades for the customer |
| Customer's actual delivery/consumption | Customer's utility | Metered data for the customer |
| Customer's allocated trade quantities | Customer's utility | Post-delivery allocation of actuals to trades |

---

## Phase 3: Trade Confirmation

This is the critical phase that establishes trust without a central ledger. SellerTP coordinates with both utilities in parallel, and each utility logs the trade and (optionally) signs the order.

Two modes are supported:

| Mode | When to Use | Trade Confirmed |
|------|-------------|-----------------|
| **Non-blocking (Recommended)** | Utilities cannot block trades; they are informed for record-keeping | Immediately after SellerTP receives `/confirm` |
| **Blocking** | Utilities must approve before trade is confirmed | After both utilities respond with `/on_confirm` |

### Confirmation Flow

```mermaid
sequenceDiagram
    autonumber
    participant BuyerTP as BuyerTP (BAP)
    participant SellerTP as SellerTP (BPP)
    participant SellerUtility as SellerUtility
    participant BuyerUtility as BuyerUtility

    Note over BuyerTP,BuyerUtility: Trade: 5 kWh, 2-4 PM, $0.50/kWh

    BuyerTP->>SellerTP: /confirm (trade contract)

    alt Non-blocking (Recommended)
        SellerTP->>BuyerTP: /on_confirm (trade confirmed)
        par Inform utilities
            SellerTP->>SellerUtility: /confirm (inform utility)
            SellerUtility->>SellerUtility: Deduct from seller limit, log trade
            SellerUtility-->>SellerTP: /on_confirm (acknowledged)
        and
            SellerTP->>BuyerUtility: /confirm (inform utility)
            BuyerUtility->>BuyerUtility: Deduct from buyer limit, log trade
            BuyerUtility-->>SellerTP: /on_confirm (acknowledged)
        end
    else Blocking
        par Utility confirmations
            SellerTP->>SellerUtility: /confirm
            SellerUtility->>SellerUtility: Deduct from seller limit, log trade
            SellerUtility->>SellerTP: /on_confirm (signed)
        and
            SellerTP->>BuyerUtility: /confirm
            BuyerUtility->>BuyerUtility: Deduct from buyer limit, log trade
            BuyerUtility->>SellerTP: /on_confirm (signed)
        end
        SellerTP->>BuyerTP: /on_confirm (signed sealed order)
    end
```

### What Each Utility Does on `/confirm`

1. Verify customer identity
2. Check customer's remaining trading limit
3. Deduct trade quantity from limit
4. Log trade in own ledger
5. (Blocking mode only) Sign the order

### Multi-Party Signature Chain (Blocking Mode)

In blocking mode, the sealed trade order contains signatures from all parties:

| Signature | Attests To |
|-----------|-----------|
| BuyerTP | Buyer's intent to purchase |
| SellerTP | Seller's agreement to supply |
| BuyerUtility | Trade is within buyer's limits, logged in buyer's utility ledger |
| SellerUtility | Trade is within seller's limits, logged in seller's utility ledger |

This creates a **tamper-proof, distributed proof of trade commitment** without requiring a central ledger.

### Non-blocking vs Blocking Trade-offs

| Aspect | Non-blocking | Blocking |
|--------|--------------|----------|
| **Latency** | Lower (immediate confirmation) | Higher (waits for utilities) |
| **Utility control** | Utilities informed, cannot block | Utilities can reject trades |
| **Trust model** | Trust SellerTP to inform utilities | Full multi-party consensus |
| **Use case** | High-frequency trading, trusted platforms | Regulatory requirement for utility approval |

---

## Phase 3b: Trade Update (Optional)

After a trade is confirmed but before energy delivery, a utility may need to modify or cancel the trade due to operational reasons (e.g., scheduled outage, grid constraints, regulatory intervention).

### Why Trade Updates?

- **Scheduled outages:** Utility plans maintenance that affects the delivery window
- **Grid constraints:** Forecasted congestion or stability issues
- **Regulatory intervention:** Compliance requirements or emergency orders
- **Meter issues:** Problems detected with buyer's or seller's metering equipment

### Update Flow

The initiating utility (in this example, BuyerUtility) sends `/update` to SellerTP, which coordinates the update across all parties.

```mermaid
sequenceDiagram
    autonumber
    participant BuyerUtility as BuyerUtility
    participant SellerTP as SellerTP (BPP)
    participant SellerUtility as SellerUtility
    participant BuyerTP as BuyerTP (BAP)

    Note over BuyerUtility,BuyerTP: Trade update triggered (e.g., scheduled outage)

    BuyerUtility->>SellerTP: /update (cancel/curtail trade)
    Note right of SellerTP: Update reason: scheduled outage<br/>Action: cancel OR curtail to X kWh

    par Cascade update to all parties
        SellerTP->>SellerUtility: /update (notify of change)
        SellerUtility->>SellerUtility: Update trade in ledger
        SellerUtility-->>SellerTP: /on_update (acknowledged)
    and
        SellerTP->>BuyerTP: /update (notify of change)
        BuyerTP->>BuyerTP: Update trade status
        BuyerTP-->>SellerTP: /on_update (acknowledged)
    end

    SellerTP->>BuyerUtility: /on_update (update confirmed)
    BuyerUtility->>BuyerUtility: Update trade in ledger

    Note over BuyerUtility,BuyerTP: All parties now have consistent view of modified trade
```

### Update Types

| Update Type | Description | Effect on Trade |
|-------------|-------------|-----------------|
| **Cancel** | Full cancellation of the trade | Trade marked as cancelled; limits restored |
| **Curtail** | Reduce contracted quantity | Trade quantity reduced; partial limits restored |
| **Reschedule** | Change delivery window | New delivery window; same quantity |

### What Each Party Does on `/update`

| Party | Actions |
|-------|---------|
| **SellerUtility** | Update trade in ledger; adjust seller's trading limit if cancelled/curtailed |
| **BuyerTP** | Notify buyer of change; update local trade status |
| **BuyerUtility** | Update trade in ledger; adjust buyer's trading limit if cancelled/curtailed |

### Update Initiation

While this example shows BuyerUtility initiating, updates can also be initiated by:

| Initiator | Route | Use Case |
|-----------|-------|----------|
| **BuyerUtility** | BuyerUtility → SellerTP → (SellerUtility, BuyerTP) | Outage on buyer's side |
| **SellerUtility** | SellerUtility → SellerTP → (BuyerUtility, BuyerTP) | Outage on seller's side |
| **BuyerTP** | BuyerTP → SellerTP → (SellerUtility, BuyerUtility) | Buyer requests cancellation |

In all cases, SellerTP acts as the coordination hub, ensuring all parties receive the update and acknowledge it.

---

## Phase 4: Energy Delivery

*(Could be anywhere from a few hours to a few days later)*

Energy delivery follows the same physical process as the central ledger approach. The key difference is that each utility records meter data in its own ledger.

### Energy Injection

- At scheduled time, seller injects energy into the grid
- Seller's utility performs grid security checks and permits injection only if grid stability is maintained

### Energy Consumption

- Buyer consumes energy as usual during the delivery window

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant SM_S as Seller's<br/>Smart Meter
    participant SellerUtility as SellerUtility
    participant BuyerUtility as BuyerUtility
    participant SM_B as Buyer's<br/>Smart Meter
    participant B as Buyer (P7)

    Note over S,B: Scheduled Delivery Window Begins

    S->>SM_S: Generate/inject energy
    SM_S->>SellerUtility: Report injection request

    SellerUtility->>SellerUtility: Grid security check
    alt Grid stable
        SellerUtility->>SellerUtility: Permit injection
        SM_S->>SM_S: Energy injected into grid

        SM_B->>B: Energy consumed

        SM_S->>SM_S: Record injection (kWh, timestamp)
        SM_B->>SM_B: Record consumption (kWh, timestamp)
    else Grid unstable
        SellerUtility-->>SM_S: Reject/limit injection
        Note over SellerUtility: Grid stability<br/>takes priority
    end

    Note over S,B: Scheduled Delivery Window Ends
```

---

## Phase 5: Post-Delivery Allocation and Status

After the delivery window, each utility performs allocation independently for its own customers and notifies the relevant trading platforms.

### Why Allocation Matters

A prosumer may have multiple trades in the same delivery window but inject/consume less than the total contracted amount. Each utility must allocate actual meter readings to specific trades to determine:
- What quantity was actually delivered/received for each trade
- What to include in billing adjustments
- Whether penalties apply for under-delivery

### Allocation Flow

```mermaid
sequenceDiagram
    autonumber
    participant SellerTP as SellerTP (BPP)
    participant SellerUtility as SellerUtility
    participant BuyerUtility as BuyerUtility
    participant BuyerTP as BuyerTP (BAP)

    Note over SellerUtility: Verification Cycle (e.g., every X hours)

    rect rgb(255, 245, 230)
    Note over SellerUtility: Seller-Side Allocation
    SellerUtility->>SellerUtility: Get all confirmed trades for<br/>seller in delivery period
    SellerUtility->>SellerUtility: Get actual meter injection data
    SellerUtility->>SellerUtility: Allocate actuals to trades<br/>(FIFO or pro-rata)
    SellerUtility-->>SellerTP: /on_status<br/>(allocated qty per trade)
    Note right of SellerTP: Seller knows what to expect<br/>in discom bill adjustment
    end

    opt Cross-Utility Visibility
        SellerUtility-->>BuyerUtility: /on_status<br/>(seller's allocated quantities)
    end

    rect rgb(230, 245, 255)
    Note over BuyerUtility: Buyer-Side Allocation
    BuyerUtility->>BuyerUtility: Get all confirmed trades for<br/>buyer in delivery period
    BuyerUtility->>BuyerUtility: Get actual meter consumption data
    BuyerUtility->>BuyerUtility: Allocate actuals to trades<br/>(FIFO or pro-rata)
    BuyerUtility-->>BuyerTP: /on_status<br/>(allocated qty per trade)
    Note right of BuyerTP: Buyer knows what to expect<br/>in discom bill adjustment
    end

    opt Cross-Utility Visibility
        BuyerUtility-->>SellerUtility: /on_status<br/>(buyer's allocated quantities)
    end
```

### Allocation Example (FIFO)

**Seller P1's trades for delivery window 2-4 PM:**

| Trade | Trade Time | Contracted Qty | Priority |
|-------|------------|----------------|----------|
| T1 (with P7) | 9:00 AM | 5 kWh | 1st |
| T2 (with P8) | 9:30 AM | 4 kWh | 2nd |
| **Total** | | **9 kWh** | |

**Actual injection: 7 kWh**

**SellerUtility allocation (FIFO):**

| Trade | Contracted | Allocated | Status |
|-------|------------|-----------|--------|
| T1 | 5 kWh | 5 kWh | Full delivery |
| T2 | 4 kWh | 2 kWh | Partial delivery |

SellerUtility sends `/on_status` to SellerTP with these allocated quantities.

---

## Phase 6: Billing and Settlement

Each utility handles billing for its own customers, using only its own ledger data.

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant SellerUtility as SellerUtility
    participant BuyerUtility as BuyerUtility
    participant B as Buyer (P7)

    Note over SellerUtility,BuyerUtility: Monthly Billing Cycle

    rect rgb(255, 245, 230)
    Note over SellerUtility: Seller's Bill
    SellerUtility->>SellerUtility: Look up P2P trades from own ledger
    SellerUtility->>SellerUtility: Calculate: Regular bill<br/>- P2P sold energy credit<br/>+ Wheeling charges
    SellerUtility->>S: Monthly bill
    S->>SellerUtility: Pay bill
    end

    rect rgb(230, 245, 255)
    Note over BuyerUtility: Buyer's Bill
    BuyerUtility->>BuyerUtility: Look up P2P trades from own ledger
    BuyerUtility->>BuyerUtility: Calculate: Regular bill<br/>- P2P purchased energy<br/>+ Wheeling charges
    BuyerUtility->>B: Monthly bill
    B->>BuyerUtility: Pay bill
    end
```

### Anti-Double-Billing

- **Buyer (P7):** BuyerUtility excludes P2P energy from regular charges (buyer already paid seller directly)
- **Seller (P1):** SellerUtility excludes P2P energy from injection credit (seller already received payment from buyer)

---

## Same-Utility Collapse

When buyer and seller are with the **same utility**, the flow simplifies naturally:

```mermaid
sequenceDiagram
    autonumber
    participant BuyerTP as BuyerTP (BAP)
    participant SellerTP as SellerTP (BPP)
    participant Utility as Utility<br/>(same for both)

    BuyerTP->>SellerTP: /confirm (trade contract)
    SellerTP->>Utility: /confirm (single utility call)

    Utility->>Utility: Check both limits
    Utility->>Utility: Log single trade entry
    Utility->>Utility: Sign and seal order

    Utility-->>SellerTP: /on_confirm
    SellerTP-->>BuyerTP: /on_confirm

    Note over BuyerTP,Utility: Same protocol, fewer hops
```

The protocol structure remains identical, but:
- Only one utility is involved
- No cross-utility confirm/on_confirm
- Single ledger entry (but from same utility's perspective for both parties)

---

## Comparison with Central Ledger Approach

| Aspect | Central Ledger | Decentralized (This Approach) |
|--------|---------------|------------------------------|
| **Trust model** | All trust central exchange | Multi-party signatures |
| **Privacy** | Central entity sees all trades | Each utility sees only its customers' trades |
| **Single point of failure** | Yes (central ledger) | No |
| **Cross-utility coordination** | Via central ledger queries | Via cascading Beckn calls |
| **Regulatory complexity** | Central exchange needs regulation | Each utility self-regulates |
| **Deployment** | Requires new central infrastructure | Builds on existing utility systems |
| **Dispute resolution** | Central ledger is arbiter | Multi-party signatures provide evidence |

---

## Open Questions

1. **Signature Format:** What cryptographic format for multi-party signatures? (JWS, EdDSA, etc.)

2. **Allocation Consistency:** If FIFO allocation differs between utilities for the same trade (due to data timing), how to reconcile?

3. **Cross-Utility Trust:** What compels SellerUtility to forward `/confirm` to BuyerUtility honestly?

4. **Offline Handling:** If a utility is temporarily unavailable during confirmation cascade, how to handle?

5. **Audit Trail Access:** How do trading platforms access the full signature chain for disputes?

---

[^1]: Non-exhaustive
