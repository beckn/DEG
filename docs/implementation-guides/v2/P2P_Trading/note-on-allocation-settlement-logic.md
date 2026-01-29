# P2P Energy Settlement & Allocation

## 1. The Settlement Problem- [P2P Energy Settlement \& Allocation](#p2p-energy-settlement--allocation)
- [P2P Energy Settlement \& Allocation](#p2p-energy-settlement--allocation)
  - [1. The Settlement Problem- P2P Energy Settlement \& Allocation](#1-the-settlement-problem--p2p-energy-settlement--allocation)
  - [2. Design Principles for Fair Settlement](#2-design-principles-for-fair-settlement)
  - [3. The Min-of-Two Settlement Rule](#3-the-min-of-two-settlement-rule)
    - [Why Min-of-Two?](#why-min-of-two)
    - [Simple Case: Single Trade](#simple-case-single-trade)
  - [4. When Allocation Becomes Necessary](#4-when-allocation-becomes-necessary)
    - [Condition 1: Multiple Overlapping Trades](#condition-1-multiple-overlapping-trades)
    - [Condition 2: Shortfall (Actual ≠ Contracted)](#condition-2-shortfall-actual--contracted)
    - [The Allocation Problem](#the-allocation-problem)
  - [5. Distributed Allocation Algorithm](#5-distributed-allocation-algorithm)
    - [Pro-Rata Allocation (Recommended)](#pro-rata-allocation-recommended)
    - [The 3-Round Settlement Flow](#the-3-round-settlement-flow)
    - [Settlement Flow Diagram](#settlement-flow-diagram)
    - [Optimality of the 3-Round Approach](#optimality-of-the-3-round-approach)
  - [6. Billing Calculation](#6-billing-calculation)
    - [For Buyer (Consumer)](#for-buyer-consumer)
    - [For Seller (Prosumer)](#for-seller-prosumer)
  - [7. Ledger API Integration](#7-ledger-api-integration)
    - [Allocation Workflow](#allocation-workflow)
    - [Step 1: Platform Creates Trade Record](#step-1-platform-creates-trade-record)
    - [Step 2: Discoms Record Actuals (Rounds 1 \& 2)](#step-2-discoms-record-actuals-rounds-1--2)
    - [Step 3: Settlement Engine Computes Min-of-Two (Round 3)](#step-3-settlement-engine-computes-min-of-two-round-3)
    - [Step 4: Billing Calculation from Settlement](#step-4-billing-calculation-from-settlement)
    - [Error Handling Patterns](#error-handling-patterns)
    - [Sequence Diagram](#sequence-diagram)
  - [8. Summary](#8-summary)
- [Appendix A: Deviation-Based Settlement (Alternative)](#appendix-a-deviation-based-settlement-alternative)
  - [Overview](#overview)
  - [Settlement Formulas](#settlement-formulas)
  - [Example](#example)
  - [Key Properties](#key-properties)
  - [When to Use Which](#when-to-use-which)
- [Appendix B: Detailed Optimality Analysis](#appendix-b-detailed-optimality-analysis)
  - [The Centralized Optimum](#the-centralized-optimum)
  - [Suboptimality Example: Cross-Linked Trades](#suboptimality-example-cross-linked-trades)
  - [FIFO Can Be Worse](#fifo-can-be-worse)
  - [Theoretical Bounds](#theoretical-bounds)
- [Appendix C: Side-by-Side Method Comparison](#appendix-c-side-by-side-method-comparison)
  - [Scenario](#scenario)
  - [Min-of-Two Result](#min-of-two-result)
  - [Deviation Result](#deviation-result)
  - [Key Insight](#key-insight)
  - [Principles Alignment](#principles-alignment)


In P2P energy trading, settlement answers the question: **"How much energy was actually exchanged, and who pays whom?"**

Unlike traditional retail electricity (where the utility supplies whatever you consume), P2P trades involve forward contracts: a buyer and seller agree to exchange a specific quantity at a specific price for a future time slot. The problem arises because:

1. **Actuals differ from contracts** - A seller with rooftop solar may produce less on a cloudy day; a buyer may consume less than expected
2. **Multiple parties involved** - Each trade involves four entities: Buyer (B), Buyer's Utility (BU), Seller (S), Seller's Utility (SU)
3. **Grid must balance** - Any mismatch is absorbed by the utilities from the open market

**Example:** Seller contracts to deliver 100 kWh but produces only 70 kWh. Buyer expected 100 kWh but received only 70 kWh. Who bears the cost of the 30 kWh shortfall? The buyer's utility had to procure it from the real-time market at potentially higher prices.

A good settlement mechanism must answer these questions fairly, consistently, and without creating perverse incentives.

---

## 2. Design Principles for Fair Settlement

The most important property of any settlement is that it is **dispute-free and agreed by all parties, and verifiable in an audit**. Beyond this foundation, we believe the following principles should guide settlement design in order of decreasing importance:

- **Principle 1: Shortfall responsibility**
  > All else equal, the actor(s) responsible for the shortfall should bear the cost of that shortfall.

  If the seller underproduces, the seller bears the consequence. If the buyer underconsumes, the buyer bears the consequence. If both have shortfalls, they share responsibility proportionally.

  This creates natural alignment and avoids gaming. For P2P trading to grow sustainably, it must reduce costs on the rest of the ecosystem and add positive economic value. **Overpenalizing shortfalls (within reason) is acceptable; underpenalizing is not**, as it creates perverse incentives.

  **Consequence of seller underproduction:** The buyer's utility must procure the energy shortfall from the open market at real-time price ($\text{rtm}_p$).

  **Consequence of buyer underconsumption:** The seller's utility must sell the excess energy in the open market, potentially at a loss compared to the trade price.

- **Principle 2: Independence & scalability**
  > Enable uncoordinated, independent actions between (B, BU) and (S, SU) tuples.

  The buyer's utility should not need to know the seller's meter readings or trades when penalizing buyer underconsumption, and vice versa. This breaks deadlocks and enables scale.

- **Principle 3: Allocation flexibility**
  > Different utilities should be able to use independent allocation logic without violating Principle 1.

  The total penalty for a customer's shortfall should be deterministic, even if individual trade allocations vary.

- **Principle 4: Reuse existing billing flows**
  > Avoid introducing new billing relationships.

  Settlement should work within existing flows:
  - Buyer ↔ Buyer's Utility
  - Seller ↔ Seller's Utility
  - Buyer ↔ Seller (via platform)

  Avoid inter-utility payments if possible.

- **Principle 5: No surprises for compliant parties**
  > If an actor abides by its contract, it should face no penalties or revenue surprises.

  - If a seller produces ≥ contracted quantity, their revenue should be the same regardless of whether the buyer underconsumed
  - If a buyer consumes ≥ contracted quantity, their bill should be the same regardless of whether the seller underproduced

- **Principle 6: Allocation-independent total penalty**
  > A customer's total penalty should depend only on their total shortfall, not on how it's allocated across trades.

  This makes allocation logic less critical—it may affect per-trade penalties, but not the total.

---

## 3. The Min-of-Two Settlement Rule

When allocations to a trade by respective parties differ, a consensus has emerged around the following rule to break the tie. Let's denote it as the **min-of-two** rule:

$$\text{settle}_k = \min(a^B_k, a^S_k)$$

Where:
- $a^B_k$ = Buyer utility's allocation for trade $k$ (capped by buyer's actual consumption)
- $a^S_k$ = Seller utility's allocation for trade $k$ (capped by seller's actual production)
- $\text{settle}_k$ = Final settled quantity for trade $k$

There are also alternate settlement rules which can help ease the friction in trade assurance. One such rule "pay for own deviation" is described in Appendix A.

### Why Min-of-Two?

1. **Dispute-free** - Both parties independently compute allocations; the minimum is unambiguous
2. **Conservative** - In case of disagreement, the lower value prevails, preventing over-billing

### Simple Case: Single Trade

When a buyer has exactly one trade with a seller, settlement is straightforward:

```
Trade: T1 between Buyer B1 and Seller S1
  - Contracted: 10 kWh @ 6 INR/kWh

Actuals:
  - B1 consumed: 15 kWh
  - S1 produced: 8 kWh

Settlement:
  - Buyer allocation: a^B = min(10, 15) = 10 kWh
  - Seller allocation: a^S = min(10, 8) = 8 kWh
  - Settled: settle = min(10, 8) = 8 kWh

Billing:
  - Buyer pays seller: 8 kWh × 6 INR = 48 INR
  - Buyer pays utility for grid import: (15 - 8) = 7 kWh × 10 INR = 70 INR
```

**Analysis:** Seller underproduced by 2 kWh. Buyer's settlement reduced from 10 to 8 kWh, forcing them to import 7 kWh from grid instead of 5 kWh.

---

## 4. When Allocation Becomes Necessary

The single-trade case is simple. However, **allocation** becomes a distinct problem when:

### Condition 1: Multiple Overlapping Trades

A customer may have multiple P2P trades in the same time slot:

```
Buyer B1 has two trades in slot 10:00-10:15:
  - T1: Buy 10 kWh from Seller S1 @ 5 INR
  - T2: Buy 10 kWh from Seller S2 @ 6 INR

B1's actual consumption: 15 kWh (shortfall of 5 kWh)

Question: How much of the 15 kWh came from T1 vs T2?
```

### Condition 2: Shortfall (Actual ≠ Contracted)

If a customer's actual meter reading differs from their total contracted quantity, we must decide how to distribute the actual across trades:

```
Seller S1 has two trades:
  - T1: Sell 10 kWh to Buyer B1
  - T3: Sell 10 kWh to Buyer B2

S1's actual production: 15 kWh (shortfall of 5 kWh)

Question: Which buyer gets shorted? Or is it split proportionally?
```

### The Allocation Problem

When both conditions exist, we have the **allocation problem**: given multiple trades and a meter reading that differs from total contracted quantity, how should the utility allocate the actual reading across trades?

This is a **per-utility** problem. Each utility (buyer's DISCOM, seller's DISCOM) independently allocates their customer's meter reading across that customer's trades. The final settlement for each trade is then the minimum of both allocations.

---

## 5. Distributed Allocation Algorithm

### Pro-Rata Allocation (Recommended)

Each utility allocates proportionally to contracted quantities:

$$a_k = \text{tr}_k \cdot \min\left(1, \frac{\text{meter}}{\sum_{k'} \text{tr}_{k'}}\right)$$

**Example:**
```
Seller S1: Production = 15 kWh, Contracts = T1(10) + T3(10) = 20 kWh
Pro-rata factor: min(1, 15/20) = 0.75
Allocations: T1 = 10 × 0.75 = 7.5 kWh, T3 = 10 × 0.75 = 7.5 kWh
```

**Properties:**
- Deterministic (no timestamp dependency)
- Fair across trades (proportional sharing)
- Simple to implement
- Each utility computes independently

### The 3-Round Settlement Flow

1. **Round 1 - Seller utilities allocate:** Each seller utility computes pro-rata allocations based on seller's production. Records allocated pushed energy to ledger.

2. **Round 2 - Buyer utilities allocate:** Each buyer utility computes pro-rata allocations based on buyer's consumption. Records allocated pulled energy to ledger.

3. **Round 3 - Settlement:** Settlement engine queries ledger, applies min-of-two rule: $\text{settle}_k = \min(a^B_k, a^S_k)$

**Why seller first?** Production (supply) is typically the scarcer constraint. However, with simple pro-rata, each utility allocates independently—the min-of-two at settlement handles any mismatch.

### Settlement Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Post-Delivery Settlement                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. METER READING           2. ALLOCATION              3. BILLING   │
│  ┌─────────────┐           ┌─────────────┐          ┌─────────────┐ │
│  │ m_i = 100   │    →      │ alloc = 80  │    →     │ utility_bill│ │
│  │ (consumed)  │           │ (from P2P)  │          │ = 20 × tariff│
│  └─────────────┘           └─────────────┘          └─────────────┘ │
│                                                                     │
│              Total Consumption = P2P Settled + Utility Import       │
│                     100 kWh     =    80 kWh   +    20 kWh           │
└─────────────────────────────────────────────────────────────────────┘
```

### Optimality of the 3-Round Approach

**When is it optimal?**
- **No shortfalls:** If all parties meet their contracts, settlement equals contract for every trade. Trivially optimal.
- **Single-side shortfall:** If only sellers (or only buyers) have shortfalls, the algorithm is optimal.

**When is it suboptimal?**
- **Both-side shortfalls with cross-linked trades:** When buyers and sellers both have shortfalls, and trades form a bipartite graph with multiple edges, the distributed algorithm can leave energy "stranded."

**Practical performance:** The 3-round pro-rata approach achieves **67-90% of the theoretical optimum** in worst-case scenarios. In typical scenarios (mild, correlated shortfalls), the gap is much smaller (<10%). See Appendix B for detailed analysis.

**Recommendation:** Use pro-rata allocation. It is simple, fair, and adequate for most practical scenarios.

---

## 6. Billing Calculation

### For Buyer (Consumer)

| Component | Formula | Description |
|-----------|---------|-------------|
| Meter Reading | $m_i$ | Actual consumption (kWh) |
| P2P Settled | $\sum_{k: b(k)=i} \text{settle}_k$ | Energy from P2P trades |
| Utility Import | $m_i - \sum \text{settle}_k$ | Remaining from grid |
| P2P Cost | $\sum \text{settle}_k \times p_k$ | Payment to sellers |
| Utility Cost | $(m_i - \sum \text{settle}_k) \times \text{tariff}_{\text{import}}$ | Grid charges |

### For Seller (Prosumer)

| Component | Formula | Description |
|-----------|---------|-------------|
| Meter Reading | $m_j$ | Actual production (kWh) |
| P2P Settled | $\sum_{k: s(k)=j} \text{settle}_k$ | Energy sold via P2P |
| Utility Export | $m_j - \sum \text{settle}_k$ | Remaining to grid |
| P2P Revenue | $\sum \text{settle}_k \times p_k$ | Payment from buyers |
| Utility Revenue | $(m_j - \sum \text{settle}_k) \times \text{tariff}_{\text{export}}$ | Net metering credits |

---

## 7. Ledger API Integration

The DEG Ledger Service provides an immutable, multi-party view of trade lifecycle events. It supports three primary operations:

| Endpoint | Who Uses | Purpose |
|----------|----------|---------|
| `POST /ledger/put` | Platforms only | Create/update trade records |
| `POST /ledger/record` | Discoms only | Record actuals and status |
| `POST /ledger/get` | All parties | Query records (policy-filtered) |

### Allocation Workflow

```
Timeline:
  T+0h   Delivery period ends
  T+1h   Meter readings available
  T+2h   Round 1: Seller discom allocates (ACTUAL_PUSHED)
  T+4h   Round 2: Buyer discom allocates (ACTUAL_PULLED)
  T+6h   Round 3: Settlement engine computes min-of-two
  T+8h   Settlement complete, billing triggered
```

### Step 1: Platform Creates Trade Record

When a trade is confirmed, the platform creates a ledger record via `/ledger/put`.

```python
def create_trade_record(trade: Trade) -> LedgerWriteResponse:
    """
    Platform creates the initial ledger record at trade confirmation.
    Called by: Buyer Platform or Seller Platform
    Endpoint: POST /ledger/put
    """
    payload = {
        "role": "BUYER",  # or "SELLER" depending on calling platform
        "transactionId": trade.transaction_id,
        "orderItemId": trade.order_item_id,

        # Party identifiers
        "platformIdBuyer": trade.bap_id,
        "platformIdSeller": trade.bpp_id,
        "discomIdBuyer": trade.buyer_discom_id,
        "discomIdSeller": trade.seller_discom_id,
        "buyerId": trade.buyer_ca_number,  # Consumer Account number
        "sellerId": trade.seller_der_id,    # DER / prosumer ID

        # Time metadata
        "tradeTime": trade.confirmed_at.isoformat() + "Z",
        "deliveryStartTime": trade.delivery_slot_start.isoformat() + "Z",
        "deliveryEndTime": trade.delivery_slot_end.isoformat() + "Z",

        # Trade details
        "tradeDetails": [{
            "tradeType": "ENERGY",
            "tradeQty": trade.contracted_kwh,
            "tradeUnit": "KWH"
        }],

        # Idempotency token for safe retries
        "clientReference": f"platform-create-{trade.order_item_id}"
    }

    response = requests.post(
        f"{LEDGER_HOST}/ledger/put",
        json=payload,
        headers=get_signed_headers(payload)
    )

    if response.status_code == 200:
        result = response.json()
        # Store recordId for future reference
        trade.ledger_record_id = result["recordId"]
        trade.ledger_row_digest = result["rowDigest"]
        return result
    elif response.status_code == 409:
        # Record already exists - idempotent retry is safe
        raise ConflictError(response.json())
    else:
        raise LedgerAPIError(response.status_code, response.json())
```

### Step 2: Discoms Record Actuals (Rounds 1 & 2)

After the delivery period, discoms compute and record allocations in sequence:
- **Round 1:** Seller discoms allocate based on production (pro-rata)
- **Round 2:** Buyer discoms query seller allocations, then allocate based on consumption, capped at seller's allocation

```python
def compute_pro_rata_allocation(
    customer_id: str,
    meter_reading: float,
    trades: list[Trade]
) -> dict[str, float]:
    """
    Pro-rata allocation algorithm.
    Allocates meter reading proportionally across all trades for a customer.

    Returns: {order_item_id: allocated_qty}
    """
    total_contracted = sum(t.contracted_kwh for t in trades)

    if total_contracted == 0:
        return {t.order_item_id: 0.0 for t in trades}

    # Pro-rata factor: ratio of actual to contracted (capped at 1.0)
    pro_rata_factor = min(1.0, meter_reading / total_contracted)

    allocations = {}
    for trade in trades:
        # Each trade gets proportional share of actual meter reading
        allocated = trade.contracted_kwh * pro_rata_factor
        allocations[trade.order_item_id] = round(allocated, 3)

    return allocations


def record_discom_actuals(
    role: str,  # "BUYER_DISCOM" or "SELLER_DISCOM"
    trade: Trade,
    allocated_qty: float,
    status: str = "COMPLETED"
) -> LedgerWriteResponse:
    """
    Discom records fulfillment actuals for a trade.
    Called by: Buyer Discom or Seller Discom
    Endpoint: POST /ledger/record

    Validation metric types:
      - ACTUAL_PUSHED: Energy pushed by seller (seller discom records)
      - ACTUAL_PULLED: Energy pulled by buyer (buyer discom records)
    """
    payload = {
        "role": role,
        "transactionId": trade.transaction_id,
        "orderItemId": trade.order_item_id,
        "clientReference": f"{role.lower()}-actuals-{trade.order_item_id}-{uuid4()}"
    }

    if role == "SELLER_DISCOM":
        payload["sellerFulfillmentValidationMetrics"] = [{
            "validationMetricType": "ACTUAL_PUSHED",
            "validationMetricValue": allocated_qty
        }]
        payload["statusSellerDiscom"] = status
    elif role == "BUYER_DISCOM":
        payload["buyerFulfillmentValidationMetrics"] = [{
            "validationMetricType": "ACTUAL_PULLED",
            "validationMetricValue": allocated_qty
        }]
        payload["statusBuyerDiscom"] = status
    else:
        raise ValueError(f"Invalid role: {role}")

    response = requests.post(
        f"{LEDGER_HOST}/ledger/record",
        json=payload,
        headers=get_signed_headers(payload)
    )

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        # Record doesn't exist - platform must create first
        raise RecordNotFoundError(
            f"Ledger record not found for {trade.transaction_id}/{trade.order_item_id}"
        )
    elif response.status_code == 403:
        # Role not authorized to write these fields
        raise AuthorizationError(response.json())
    else:
        raise LedgerAPIError(response.status_code, response.json())


def seller_discom_allocation_job(
    delivery_slot: TimeSlot,
    discom_id: str
):
    """
    Round 1: Batch job run by seller discom after delivery period.

    Computes pro-rata allocations based on seller production and records to ledger.
    This runs FIRST - buyer discoms will query these allocations in Round 2.
    """
    # Get all trades for this discom in the delivery slot
    trades = get_trades_by_seller_discom(discom_id, delivery_slot)

    # Group trades by seller
    trades_by_seller = group_by(trades, key=lambda t: t.seller_id)

    for seller_id, seller_trades in trades_by_seller.items():
        # Get meter reading for this seller (production)
        meter_reading = get_meter_reading(seller_id, delivery_slot, type="GENERATION")

        # Compute pro-rata allocation
        allocations = compute_pro_rata_allocation(seller_id, meter_reading, seller_trades)

        # Record each allocation to ledger
        for trade in seller_trades:
            allocated_qty = allocations[trade.order_item_id]
            record_discom_actuals(
                role="SELLER_DISCOM",
                trade=trade,
                allocated_qty=allocated_qty
            )
            log.info(f"Seller allocation recorded: {trade.order_item_id} = {allocated_qty} kWh")


def get_seller_allocations_from_ledger(
    delivery_slot: TimeSlot,
    discom_id: str
) -> dict[str, float]:
    """
    Query ledger to get seller allocations recorded in Round 1.
    Returns: {order_item_id: seller_allocated_qty}
    """
    records = query_ledger_records(delivery_slot, discom_id=discom_id)

    seller_allocations = {}
    for record in records:
        seller_alloc = extract_allocation(record, "SELLER")
        if seller_alloc is not None:
            seller_allocations[record["orderItemId"]] = seller_alloc

    return seller_allocations


def compute_pro_rata_allocation_with_cap(
    customer_id: str,
    meter_reading: float,
    trades: list[Trade],
    other_party_allocations: dict[str, float]
) -> dict[str, float]:
    """
    Pro-rata allocation capped at other party's allocation.

    Round 2: Buyer allocates pro-rata based on consumption,
    but caps each trade at seller's Round 1 allocation.

    Returns: {order_item_id: allocated_qty}
    """
    total_contracted = sum(t.contracted_kwh for t in trades)

    if total_contracted == 0:
        return {t.order_item_id: 0.0 for t in trades}

    # Pro-rata factor: ratio of actual to contracted (capped at 1.0)
    pro_rata_factor = min(1.0, meter_reading / total_contracted)

    allocations = {}
    for trade in trades:
        # Base pro-rata share
        pro_rata_share = trade.contracted_kwh * pro_rata_factor

        # Cap at seller's allocation from Round 1 (if available)
        seller_alloc = other_party_allocations.get(trade.order_item_id)
        if seller_alloc is not None:
            capped = min(pro_rata_share, seller_alloc)
        else:
            # Seller hasn't recorded yet - use pro-rata only
            capped = pro_rata_share

        allocations[trade.order_item_id] = round(capped, 3)

    return allocations


def buyer_discom_allocation_job(
    delivery_slot: TimeSlot,
    discom_id: str
):
    """
    Round 2: Batch job run by buyer discom after seller discoms have allocated.

    1. Queries ledger to get seller allocations from Round 1
    2. Computes pro-rata allocations based on buyer consumption
    3. Caps each allocation at seller's allocation (can't pull more than pushed)
    4. Records to ledger
    """
    # Get all trades for this discom in the delivery slot
    trades = get_trades_by_buyer_discom(discom_id, delivery_slot)

    # Query seller allocations from Round 1
    seller_allocations = get_seller_allocations_from_ledger(delivery_slot, discom_id)
    log.info(f"Retrieved {len(seller_allocations)} seller allocations from Round 1")

    # Group trades by buyer
    trades_by_buyer = group_by(trades, key=lambda t: t.buyer_id)

    for buyer_id, buyer_trades in trades_by_buyer.items():
        # Get meter reading for this buyer (consumption)
        meter_reading = get_meter_reading(buyer_id, delivery_slot, type="CONSUMPTION")

        # Compute pro-rata allocation, capped at seller's allocation
        allocations = compute_pro_rata_allocation_with_cap(
            buyer_id,
            meter_reading,
            buyer_trades,
            seller_allocations
        )

        # Record each allocation to ledger
        for trade in buyer_trades:
            allocated_qty = allocations[trade.order_item_id]
            seller_alloc = seller_allocations.get(trade.order_item_id, "N/A")
            record_discom_actuals(
                role="BUYER_DISCOM",
                trade=trade,
                allocated_qty=allocated_qty
            )
            log.info(
                f"Buyer allocation recorded: {trade.order_item_id} = {allocated_qty} kWh "
                f"(capped at seller's {seller_alloc} kWh)"
            )
```

### Step 3: Settlement Engine Computes Min-of-Two (Round 3)

After both discoms have recorded their allocations (Rounds 1 & 2), the settlement engine queries the ledger and applies the min-of-two rule.

```python
def query_ledger_records(
    delivery_slot: TimeSlot,
    discom_id: str = None,
    buyer_id: str = None,
    seller_id: str = None
) -> list[LedgerRecord]:
    """
    Query ledger records by filters.
    Endpoint: POST /ledger/get

    Access control: Server enforces record-level and field-level visibility
    based on caller identity.
    """
    payload = {
        "deliveryStartFrom": delivery_slot.start.isoformat() + "Z",
        "deliveryStartTo": delivery_slot.end.isoformat() + "Z",
        "limit": 500,
        "offset": 0,
        "sort": "deliveryStartTime",
        "sortOrder": "asc"
    }

    # Add optional filters
    if discom_id:
        payload["discomIdBuyer"] = discom_id  # or discomIdSeller
    if buyer_id:
        payload["buyerId"] = buyer_id
    if seller_id:
        payload["sellerId"] = seller_id

    response = requests.post(
        f"{LEDGER_HOST}/ledger/get",
        json=payload,
        headers=get_signed_headers(payload)
    )

    if response.status_code == 200:
        result = response.json()
        return result["records"]
    else:
        raise LedgerAPIError(response.status_code, response.json())


def extract_allocation(record: LedgerRecord, role: str) -> float | None:
    """
    Extract allocated quantity from ledger record for a given role.
    """
    if role == "SELLER":
        metrics = record.get("sellerFulfillmentValidationMetrics", [])
        for m in metrics:
            if m["validationMetricType"] == "ACTUAL_PUSHED":
                return m["validationMetricValue"]
    elif role == "BUYER":
        metrics = record.get("buyerFulfillmentValidationMetrics", [])
        for m in metrics:
            if m["validationMetricType"] == "ACTUAL_PULLED":
                return m["validationMetricValue"]
    return None


def compute_settlement(record: LedgerRecord) -> SettlementResult:
    """
    Apply min-of-two settlement rule to a ledger record.

    settle_k = min(buyer_allocation, seller_allocation)
    """
    trade_qty = record["tradeDetails"][0]["tradeQty"]  # Contracted quantity

    # Extract allocations from both discoms
    seller_alloc = extract_allocation(record, "SELLER")
    buyer_alloc = extract_allocation(record, "BUYER")

    # Handle missing allocations
    if seller_alloc is None:
        raise SettlementError(
            f"Missing seller allocation for {record['recordId']}"
        )
    if buyer_alloc is None:
        raise SettlementError(
            f"Missing buyer allocation for {record['recordId']}"
        )

    # Min-of-two rule
    settled_qty = min(seller_alloc, buyer_alloc)

    return SettlementResult(
        record_id=record["recordId"],
        transaction_id=record["transactionId"],
        order_item_id=record["orderItemId"],
        contracted_qty=trade_qty,
        seller_allocation=seller_alloc,
        buyer_allocation=buyer_alloc,
        settled_qty=settled_qty,
        seller_shortfall=trade_qty - seller_alloc,
        buyer_shortfall=trade_qty - buyer_alloc
    )


def settlement_batch_job(delivery_slot: TimeSlot):
    """
    Main settlement job run after both discoms have recorded allocations.
    Queries ledger, computes min-of-two, generates billing records.
    """
    # Query all records for the delivery slot
    records = query_ledger_records(delivery_slot)

    settlements = []
    errors = []

    for record in records:
        try:
            # Verify both discoms have recorded
            if (record.get("statusSellerDiscom") not in ["COMPLETED", "CURTAILED_OUTAGE"] or
                record.get("statusBuyerDiscom") not in ["COMPLETED", "CURTAILED_OUTAGE"]):
                log.warning(f"Skipping {record['recordId']}: awaiting discom status")
                continue

            settlement = compute_settlement(record)
            settlements.append(settlement)

            log.info(
                f"Settlement computed: {settlement.order_item_id} "
                f"contracted={settlement.contracted_qty} "
                f"seller_alloc={settlement.seller_allocation} "
                f"buyer_alloc={settlement.buyer_allocation} "
                f"settled={settlement.settled_qty}"
            )

        except SettlementError as e:
            errors.append((record["recordId"], str(e)))
            log.error(f"Settlement error for {record['recordId']}: {e}")

    # Generate billing records from settlements
    generate_billing_records(settlements)

    return SettlementBatchResult(
        delivery_slot=delivery_slot,
        total_records=len(records),
        settled_count=len(settlements),
        error_count=len(errors),
        errors=errors
    )
```

### Step 4: Billing Calculation from Settlement

```python
@dataclass
class BillingRecord:
    buyer_id: str
    seller_id: str
    settled_qty: float
    p2p_cost: float       # settled_qty × trade_price
    wheeling_cost: float  # settled_qty × wheeling_rate
    grid_import: float    # buyer_consumption - settled_qty
    grid_cost: float      # grid_import × grid_tariff


def generate_billing_records(settlements: list[SettlementResult]):
    """
    Convert settlement results into billing line items.
    """
    for s in settlements:
        trade = get_trade(s.transaction_id, s.order_item_id)

        billing = BillingRecord(
            buyer_id=trade.buyer_id,
            seller_id=trade.seller_id,
            settled_qty=s.settled_qty,
            p2p_cost=s.settled_qty * trade.price_per_kwh,
            wheeling_cost=s.settled_qty * trade.wheeling_rate,
            grid_import=trade.buyer_meter_reading - s.settled_qty,
            grid_cost=(trade.buyer_meter_reading - s.settled_qty) * get_grid_tariff()
        )

        # Persist billing record
        save_billing_record(billing)

        # Trigger payment flows
        initiate_buyer_to_seller_payment(billing)
        initiate_buyer_to_utility_payment(billing)
```

### Error Handling Patterns

```python
# Status codes and their meanings
LEDGER_ERROR_CODES = {
    "SCH_FIELD_NOT_ALLOWED": "Field not allowed in request schema",
    "SCH_MISSING_REQUIRED": "Required field missing",
    "AUT_SIGNATURE_INVALID": "Request signature verification failed",
    "AUT_NOT_AUTHORIZED": "Caller not authorized for this operation",
    "PRC_CONFLICT": "Immutable field conflict on existing record",
    "PRC_NOT_FOUND": "Target record not found",
    "SRV_INTERNAL_ERROR": "Internal server error"
}

def handle_ledger_error(response: requests.Response):
    """
    Standard error handling for ledger API responses.
    """
    error = response.json()
    code = error.get("code")
    message = error.get("message")

    if response.status_code == 400:
        # Schema/validation error - fix request and retry
        raise ValidationError(f"{code}: {message}")

    elif response.status_code == 401:
        # Signature invalid - check signing key
        raise AuthenticationError(f"{code}: {message}")

    elif response.status_code == 403:
        # Not authorized - role cannot perform this action
        raise AuthorizationError(f"{code}: {message}")

    elif response.status_code == 404:
        # Record not found - platform must create first
        raise RecordNotFoundError(f"{code}: {message}")

    elif response.status_code == 409:
        # Conflict - immutable field mismatch
        raise ConflictError(f"{code}: {message}")

    else:
        raise LedgerAPIError(response.status_code, f"{code}: {message}")
```

### Sequence Diagram

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
│ Buyer   │  │ Seller  │  │ Ledger  │  │ Seller   │  │ Buyer    │  │Settle- │
│ Platform│  │ Platform│  │ Service │  │ Discom   │  │ Discom   │  │ment    │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘  └───┬────┘
     │            │            │            │             │            │
     │  Trade Confirmed        │            │             │            │
     │─────────────────────────>            │             │            │
     │  POST /ledger/put       │            │             │            │
     │  (create record)        │            │             │            │
     │            │            │            │             │            │
     │            │<───────────│            │             │            │
     │            │  recordId  │            │             │            │
     │            │            │            │             │            │
     │            │            │                                       │
     │            │            │  ══════ ROUND 1: Seller Allocates ══════
     │            │            │   T+2h: Meter readings available      │
     │            │            │            │             │            │
     │            │            │<───────────│             │            │
     │            │            │  POST /ledger/record     │            │
     │            │            │  ACTUAL_PUSHED=70 kWh   │            │
     │            │            │───────────>│             │            │
     │            │            │     OK     │             │            │
     │            │            │            │             │            │
     │            │            │  ══════ ROUND 2: Buyer Allocates ══════
     │            │            │   T+4h: Buyer queries seller allocs   │
     │            │            │            │             │            │
     │            │            │<──────────────────────────            │
     │            │            │  POST /ledger/get                     │
     │            │            │  (get seller allocations)             │
     │            │            │──────────────────────────>            │
     │            │            │  ACTUAL_PUSHED=70 kWh                 │
     │            │            │            │             │            │
     │            │            │            │  Buyer computes pro-rata │
     │            │            │            │  consumption=80, cap at 70│
     │            │            │            │             │            │
     │            │            │<──────────────────────────            │
     │            │            │  POST /ledger/record                  │
     │            │            │  ACTUAL_PULLED=70 kWh (capped)        │
     │            │            │──────────────────────────>            │
     │            │            │     OK     │             │            │
     │            │            │            │             │            │
     │            │            │  ══════ ROUND 3: Settlement ══════════
     │            │            │   T+6h: Settlement window             │
     │            │            │            │             │            │
     │            │            │<─────────────────────────────────────│
     │            │            │  POST /ledger/get                    │
     │            │            │  (query by delivery slot)            │
     │            │            │─────────────────────────────────────>│
     │            │            │  seller=70, buyer=70                 │
     │            │            │            │             │            │
     │            │            │            │             │  settle_k = min(70, 70) = 70 kWh
     │            │            │            │             │  → Generate billing
```

**Key insight:** In Round 2, buyer discom queries seller's allocation (70 kWh) and caps its allocation at that value. Even though buyer consumed 80 kWh, the allocation is capped at 70 kWh because seller only pushed 70 kWh. The min-of-two in Round 3 becomes `min(70, 70) = 70`.

---

## 8. Summary

| Aspect | Min-of-Two Settlement |
|--------|----------------------|
| Settlement rule | $\text{settle}_k = \min(a^B_k, a^S_k)$ |
| Allocation method | Pro-rata (recommended) |
| Flow | Seller allocates → Buyer allocates → Min-of-two settlement |
| Optimality | 67-90% of global optimum in worst case |
| Complexity | Simple, no optimization solvers needed |

The min-of-two approach satisfies our design principles:
- **Dispute-free:** Minimum is unambiguous
- **Shortfall accountability:** Underproduce/underconsume → reduced settlement
- **Independence:** Each utility allocates based only on its customers' meters
- **Existing flows:** No inter-utility payments required

---

# Appendix A: Deviation-Based Settlement (Alternative)

This appendix describes an alternative settlement method based on **explicit deviation penalties** rather than reduced settlement quantities.

## Overview

| Aspect | Min-of-Two | Deviation Method |
|--------|------------|------------------|
| Inter-utility coordination | Required (3 rounds) | **Not required** |
| Penalty mechanism | Implicit (reduced settlement) | Explicit (deviation charges) |
| Revenue for compliant party | Depends on other party | **Guaranteed if you comply** |
| Complexity | Simpler billing | More line items |

## Settlement Formulas

**Buyer pays:**
$$\text{Buyer Payment} = \text{tr}_q \times \text{tr}_p - (\text{tr}_q - \text{load}_q) \times \text{exportBU}_p$$

- Pays full contract value
- Minus: credit for underconsumption (utility sells surplus at spot)

**Seller receives:**
$$\text{Seller Revenue} = \text{tr}_q \times \text{tr}_p - (\text{tr}_q - \text{gen}_q) \times \text{importSU}_p$$

- Receives full contract value
- Minus: penalty for underproduction (utility procures shortfall)

**Utility flows:**
- Seller utility receives: $(\text{tr}_q - \text{gen}_q) \times \text{importSU}_p$
- Buyer utility pays: $(\text{tr}_q - \text{load}_q) \times \text{exportBU}_p$

**Zero-sum verification:** All flows balance to zero.

## Example

```
Trade: 10 kWh @ 6 INR/kWh
Actuals: load_q = 8 kWh, gen_q = 7 kWh
Rates: exportBU_p = 4 INR, importSU_p = 8 INR

Buyer pays:   10×6 - (10-8)×4 = 60 - 8 = 52 INR
Seller gets:  10×6 - (10-7)×8 = 60 - 24 = 36 INR
SU receives:  (10-7)×8 = 24 INR
BU pays:      (10-8)×4 = 8 INR

Verify: 52 - 36 - 24 + 8 = 0 ✓
```

## Key Properties

**1. No coordination needed**
Each utility computes penalties independently based only on its customer's meter.

**2. Contract compliance guarantees revenue**
If seller produces ≥ contract: receives full $\text{tr}_q \times \text{tr}_p$ regardless of buyer behavior.

**3. Allocation doesn't affect total penalty**
Total penalty = (total contract - total meter) × rate. Independent of per-trade allocation.

**4. Utility margin for risk**
Utilities can set $\text{importSU}_p > \text{rtm}_p$ and $\text{exportBU}_p < \text{rtm}_p$ to ensure no loss.

## When to Use Which

| Scenario | Recommended |
|----------|-------------|
| Intra-utility P2P (same DISCOM) | Min-of-two (simpler) |
| Inter-utility P2P (different DISCOMs) | **Deviation** (no coordination) |
| Regulatory requirement for energy tracing | Min-of-two |
| Revenue certainty for compliant parties | **Deviation** |

---

# Appendix B: Detailed Optimality Analysis

This appendix provides formal analysis of when the 3-round min-of-two allocation is suboptimal.

## The Centralized Optimum

If a central coordinator had all information, the optimal allocation maximizes total settlement:

$$
\begin{align}
\max_{a^B, a^S, z} \quad & \sum_{k \in \mathcal{T}} z_k \\
\text{s.t.} \quad & z_k \leq a^B_k, \quad z_k \leq a^S_k & \forall k \\
& \sum_{k: b(k)=i} a^B_k \leq m_i & \forall i \\
& \sum_{k: s(k)=j} a^S_k \leq m_j & \forall j \\
& 0 \leq a^B_k, a^S_k \leq \text{tr}_k & \forall k
\end{align}
$$

This is a **Linear Program (LP)** solvable in polynomial time.

## Suboptimality Example: Cross-Linked Trades

Consider this scenario with both-side shortfalls:

```
Trades:
  T1: Buyer B1 ↔ Seller S1, quantity = 10
  T2: Buyer B1 ↔ Seller S2, quantity = 10
  T3: Buyer B2 ↔ Seller S1, quantity = 10

Meter readings:
  B1 consumed = 15, B2 consumed = 10
  S1 produced = 15, S2 produced = 10
```

**Pro-Rata Algorithm Result:**
- Seller allocations: S1 → T1=7.5, T3=7.5; S2 → T2=10
- Buyer allocations: B1 → T1=7.5, T2=7.5; B2 → T3=10
- Settlements: T1=min(7.5,7.5)=7.5, T2=min(10,7.5)=7.5, T3=min(7.5,10)=7.5
- **Total settled: 22.5 kWh**

**Optimal (LP Solution):**
- T1=5, T2=10, T3=10
- Check: B1 uses 15 (5+10), B2 uses 10, S1 produces 15 (5+10), S2 produces 10
- **Total settled: 25 kWh**

**Gap:** 22.5/25 = 90% of optimal.

## FIFO Can Be Worse

With timestamp-based FIFO allocation (T1 < T2 < T3):

- Round 1 (Sellers): S1 allocates T1=10, T3=5; S2 allocates T2=10
- Round 2 (Buyers): B1 allocates T1=10, T2=5; B2 allocates T3=5
- **Total settled: 20 kWh** (only 80% of optimal)

## Theoretical Bounds

**Worst-case approximation ratio:** The distributed algorithm achieves at least **67%** of optimal.

**Tight example:**
```
T1: B1 ↔ S1, quantity = 100
T2: B1 ↔ S2, quantity = 100
T3: B2 ↔ S1, quantity = 100
Meters: B1=100, B2=100, S1=100, S2=100

FIFO (T1 first): T1=100, T2=0, T3=0 → 100 kWh
Optimal: T1=50, T2=50, T3=50 → 150 kWh
Ratio: 100/150 = 67%
```

**Practical performance:** In typical scenarios with mild, correlated shortfalls, the gap is much smaller (<10%). The 67% bound is a pathological worst case requiring:
- Both-side shortfalls
- Cross-linked bipartite trade graph
- Adversarial allocation order

---

# Appendix C: Side-by-Side Method Comparison

## Scenario

```
Trade: B1 (DISCOM-A) ↔ S1 (DISCOM-B)
  - Contract: 100 kWh @ 6 INR/kWh = 600 INR

Actuals:
  - B1 consumed: 80 kWh (20 kWh underconsumption)
  - S1 produced: 70 kWh (30 kWh underproduction)

Rates:
  - exportBU_p = 4 INR/kWh
  - importSU_p = 8 INR/kWh
  - Grid import = 10 INR/kWh
```

## Min-of-Two Result

```
Settlement = min(80, 70) = 70 kWh

Buyer pays:
  - P2P: 70 × 6 = 420 INR
  - Grid: (80-70) × 10 = 100 INR
  - Total: 520 INR for 80 kWh (6.50 INR/kWh effective)

Seller receives:
  - P2P: 70 × 6 = 420 INR
  - Total: 420 INR for 70 kWh (6.00 INR/kWh effective)
```

## Deviation Result

```
Buyer pays:
  - 100×6 - 20×4 = 520 INR (same)

Seller receives:
  - 100×6 - 30×8 = 360 INR (60 INR less)

SU receives: 240 INR
BU pays: 80 INR
```

## Key Insight

- **Buyer outcome:** Identical (520 INR)
- **Seller outcome:** Different
  - Min-of-two: 420 INR
  - Deviation: 360 INR (explicit penalty for 30 kWh shortfall)

The deviation method penalizes the non-compliant party more explicitly, while min-of-two implicitly reduces settlement without explicit penalty attribution.

## Principles Alignment

| Principle | Min-of-Two | Deviation |
|-----------|------------|-----------|
| Shortfall responsibility | ✓ Implicit | ✓ Explicit |
| Independence | Partial (needs 3 rounds) | ✓ Full |
| Existing billing flows | ✓ | ✓ |
| No surprise for compliant | Partial | ✓ Full |
| Allocation-independent total | Partial | ✓ Full |

Both methods satisfy the core principles; deviation provides stronger guarantees for independence and compliant-party protection at the cost of more explicit penalty accounting.
