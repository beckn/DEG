# P2P Energy Settlement & Allocation

## 1. The Settlement Problem

In P2P energy trading, settlement answers the question: **"How much energy was actually exchanged, and who pays whom?"**

Unlike traditional retail electricity (where the utility supplies whatever you consume), P2P trades involve forward contracts: a buyer and seller agree to exchange a specific quantity at a specific price for a future time slot. The problem arises because:

1. **Actuals differ from contracts** - A seller with rooftop solar may produce less on a cloudy day; a buyer may consume less than expected
2. **Multiple parties involved** - Each trade involves four entities: Buyer (B), Buyer's Utility (BU), Seller (S), Seller's Utility (SU)
3. **Grid must balance** - Any mismatch is absorbed by the utilities from the open market

**Example:** Seller contracts to deliver 100 kWh but produces only 70 kWh. Buyer expected 100 kWh but received only 70 kWh. Who bears the cost of the 30 kWh shortfall? The buyer's utility had to procure it from the real-time market at potentially higher prices.

A good settlement mechanism must answer these questions fairly, consistently, and without creating perverse incentives.

---

## 2. Design Principles for Fair Settlement

The most important property of any settlement is that it is **dispute-free and agreed by all parties**. Beyond this foundation, we believe the following principles should guide settlement design:

### Must Have

**Principle 1: Shortfall responsibility**
> All else equal, the actor(s) responsible for the shortfall should bear the cost of that shortfall.

If the seller underproduces, the seller bears the consequence. If the buyer underconsumes, the buyer bears the consequence. If both have shortfalls, they share responsibility proportionally.

This creates natural alignment and avoids gaming. For P2P trading to grow sustainably, it must reduce costs on the rest of the ecosystem and add positive economic value. **Overpenalizing shortfalls (within reason) is acceptable; underpenalizing is not**, as it creates perverse incentives.

**Consequence of seller underproduction:** The buyer's utility must procure the energy shortfall from the open market at real-time price ($\text{rtm}_p$).

**Consequence of buyer underconsumption:** The seller's utility must sell the excess energy in the open market, potentially at a loss compared to the trade price.

### Good to Have

**Principle 2: Independence & scalability**
> Enable uncoordinated, independent actions between (B, BU) and (S, SU) tuples.

The buyer's utility should not need to know the seller's meter readings or trades when penalizing buyer underconsumption, and vice versa. This breaks deadlocks and enables scale.

**Principle 3: Allocation flexibility**
> Different utilities should be able to use independent allocation logic without violating Principle 1.

The total penalty for a customer's shortfall should be deterministic, even if individual trade allocations vary.

**Principle 4: Reuse existing billing flows**
> Avoid introducing new billing relationships.

Settlement should work within existing flows:
- Buyer ↔ Buyer's Utility
- Seller ↔ Seller's Utility
- Buyer ↔ Seller (via platform)

Avoid inter-utility payments if possible.

**Principle 5: No surprises for compliant parties**
> If an actor abides by its contract, it should face no penalties or revenue surprises.

- If a seller produces ≥ contracted quantity, their revenue should be the same regardless of whether the buyer underconsumed
- If a buyer consumes ≥ contracted quantity, their bill should be the same regardless of whether the seller underproduced

**Principle 6: Allocation-independent total penalty**
> A customer's total penalty should depend only on their total shortfall, not on how it's allocated across trades.

This makes allocation logic less critical—it may affect per-trade penalties, but not the total.

---

## 3. The Min-of-Two Settlement Rule

Given the principles above, we propose the **min-of-two** rule:

$$\text{settle}_k = \min(a^B_k, a^S_k)$$

Where:
- $a^B_k$ = Buyer utility's allocation for trade $k$ (capped by buyer's actual consumption)
- $a^S_k$ = Seller utility's allocation for trade $k$ (capped by seller's actual production)
- $\text{settle}_k$ = Final settled quantity for trade $k$

### Why Min-of-Two?

1. **Grounded in physical reality** - You cannot settle more energy than was actually produced AND consumed
2. **Dispute-free** - Both parties independently compute allocations; the minimum is unambiguous
3. **Conservative** - In case of disagreement, the lower value prevails, preventing over-billing

### Settlement Flow

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

### Billing Calculation

**For Buyer (Consumer):**

| Component | Formula | Description |
|-----------|---------|-------------|
| Meter Reading | $m_i$ | Actual consumption (kWh) |
| P2P Settled | $\sum_{k: b(k)=i} \text{settle}_k$ | Energy from P2P trades |
| Utility Import | $m_i - \sum \text{settle}_k$ | Remaining from grid |
| P2P Cost | $\sum \text{settle}_k \times p_k$ | Payment to sellers |
| Utility Cost | $(m_i - \sum \text{settle}_k) \times \text{tariff}_{\text{import}}$ | Grid charges |

**For Seller (Prosumer):**

| Component | Formula | Description |
|-----------|---------|-------------|
| Meter Reading | $m_j$ | Actual production (kWh) |
| P2P Settled | $\sum_{k: s(k)=j} \text{settle}_k$ | Energy sold via P2P |
| Utility Export | $m_j - \sum \text{settle}_k$ | Remaining to grid |
| P2P Revenue | $\sum \text{settle}_k \times p_k$ | Payment from buyers |
| Utility Revenue | $(m_j - \sum \text{settle}_k) \times \text{tariff}_{\text{export}}$ | Net metering credits |

### Example

```
Trade: T1 between Buyer B1 and Seller S1
  - Contracted: 10 kWh @ 6 INR/kWh
  - Wheeling: 1 INR/kWh

Actuals:
  - B1 consumed: 15 kWh
  - S1 produced: 8 kWh

Allocation:
  - Buyer utility: a^B = min(10, 15) = 10 kWh
  - Seller utility: a^S = min(10, 8) = 8 kWh
  - Settlement: settle = min(10, 8) = 8 kWh

Buyer B1's Bill:
  - P2P: 8 kWh × 6 INR = 48 INR
  - Wheeling: 8 kWh × 1 INR = 8 INR
  - Grid import: (15 - 8) = 7 kWh × 10 INR = 70 INR
  - Total: 126 INR

Seller S1's Revenue:
  - P2P: 8 kWh × 6 INR = 48 INR
  - Grid export: 0 kWh (all production went to P2P)
  - Total: 48 INR
```

**Analysis:** Seller underproduced by 2 kWh. Buyer's settlement reduced from 10 to 8 kWh, forcing them to import 7 kWh from grid instead of 5 kWh. The shortfall cost is implicit—buyer pays grid rate for the extra 2 kWh.

---

## 4. The Allocation Problem

When a customer has **multiple trades** in a time slot, and their actual meter reading differs from total contracted quantity, we must decide how to allocate the meter reading across trades. This is the **allocation problem**.

### Problem Statement

Given:
- Multiple P2P trades in a time slot
- Actual meter readings that may differ from contracted quantities
- Two utilities (buyer's and seller's) that must independently allocate

Find allocations $a^B_k$ and $a^S_k$ for each trade such that:
1. Each utility can compute its allocations independently
2. The allocations converge to a stable settlement
3. Total settled energy is maximized (waste minimized)

### Notation

| Symbol | Description |
|--------|-------------|
| $\mathcal{B}$ | Set of buyers |
| $\mathcal{S}$ | Set of sellers |
| $\mathcal{T}$ | Set of trades in time slot |
| $m_i$ | Meter reading for buyer $i$ |
| $m_j$ | Meter reading for seller $j$ |
| $\text{tr}_k$ | Contracted quantity for trade $k$ |
| $b(k), s(k)$ | Buyer and seller in trade $k$ |

### Constraints

**Trade bounds:** Allocation cannot exceed contract
$$0 \leq a^B_k \leq \text{tr}_k \quad \text{and} \quad 0 \leq a^S_k \leq \text{tr}_k$$

**Meter constraint:** Total allocations cannot exceed actual reading
$$\sum_{k: b(k)=i} a^B_k \leq m_i \quad \text{(buyer)}$$
$$\sum_{k: s(k)=j} a^S_k \leq m_j \quad \text{(seller)}$$

### Centralized Optimum (For Reference)

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

This is a **Linear Program (LP)** solvable in polynomial time. However, we need a **distributed** algorithm where each utility acts independently.

---

## 5. Distributed Allocation Algorithms

### Algorithm 1: Pro-Rata Allocation (Recommended)

Each utility allocates proportionally to contracted quantities:

$$a^S_k = \text{tr}_k \cdot \min\left(1, \frac{m_j}{\sum_{k': s(k')=j} \text{tr}_{k'}}\right)$$

**Properties:**
- Deterministic (no timestamp dependency)
- Fair across trades
- Simple to implement
- Works independently at each utility

**Iterative Convergence:**

1. **Round 1 - Seller utilities allocate:** Pro-rata based on production
2. **Round 2 - Buyer utilities allocate:** Pro-rata, capped at seller allocation
3. **Round 3 - Final:** $\text{settle}_k = \min(a^B_k, a^S_k)$

Converges in 2-3 rounds.

### Algorithm 2: FIFO Allocation

Allocate to trades in timestamp order:

```
For each customer:
    Sort trades by timestamp
    remaining = meter_reading
    For each trade in order:
        allocation = min(trade_qty, remaining, other_party_allocation)
        remaining -= allocation
```

**Properties:**
- Rewards early trades
- May be suboptimal in some scenarios
- Depends on consistent timestamp ordering

### Optimality Analysis

**When algorithms are optimal:**
- No shortfalls: Both parties meet all contracts → settle = contract
- Single-side shortfall: Non-constrained party matches constrained party exactly

**When algorithms are suboptimal:**
Both-side shortfalls with cross-linked trades can cause inefficiency.

**Example:**
```
Trades: T1 (B1↔S1, 10), T2 (B1↔S2, 10), T3 (B2↔S1, 10)
Meters: B1=15, B2=10, S1=15, S2=10

FIFO Result: 20 kWh settled
Optimal LP: 25 kWh settled (T1=5, T2=10, T3=10)
```

**Practical impact:** In most scenarios, shortfalls are mild and correlated (weather affects all solar). The approximation gap is typically <10%.

### Recommendation

Use **Pro-Rata** allocation:
- Simple, deterministic, fair
- Adequate for most practical scenarios
- 67-90% of optimal in worst cases

For high-shortfall scenarios (cloudy days with solar portfolios), consider iterative LP refinement.

---

## 6. Ledger API Integration

### Allocation Workflow

```
Timeline:
  T+0h   Delivery period ends
  T+1h   Meter readings available
  T+2h   Round 1: Seller utility allocates
  T+4h   Round 2: Buyer utility allocates
  T+6h   Round 3: Finalize
  T+8h   Settlement complete
```

### Recording Allocations

```python
def record_allocation(trade_id: str, role: str, allocated_qty: float):
    payload = {
        "role": role,
        "transactionId": trade.transaction_id,
        "orderItemId": trade.order_item_id,
    }

    if role == "SELLER_DISCOM":
        payload["sellerFulfillmentValidationMetrics"] = [{
            "validationMetricType": "ACTUAL_PUSHED",
            "validationMetricValue": allocated_qty
        }]
    else:
        payload["buyerFulfillmentValidationMetrics"] = [{
            "validationMetricType": "ACTUAL_PULLED",
            "validationMetricValue": allocated_qty
        }]

    return requests.post(f"{LEDGER_HOST}/ledger/record", json=payload)
```

---

## 7. Summary

| Aspect | Min-of-Two Settlement |
|--------|----------------------|
| Settlement rule | $\text{settle}_k = \min(a^B_k, a^S_k)$ |
| Allocation method | Pro-rata (recommended) or FIFO |
| Coordination | 2-3 rounds between utilities |
| Optimality | 67-90% of global optimum |
| Complexity | Simple, no LP solvers needed |

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

# Appendix B: Side-by-Side Comparison

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
