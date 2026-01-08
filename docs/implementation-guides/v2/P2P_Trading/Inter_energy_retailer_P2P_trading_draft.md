# Inter-Energy Retailer P2P Energy Trading 

## Scenario

P2P trading between prosumers belonging to different energy retailers. Each energy retailer and energy distribution utility handles routine activities: providing electricity connections, certifying meters, billing, maintaining grid infrastructure, and ensuring grid resilience within their jurisdiction.

**Example:** Prosumer P1 (Meter ID: M1, Retailer A) sells electricity to Prosumer P7 (Meter ID: M7, Retailer B).

---

## Present World Reality / Constraints[^1]

1. **Physical delivery is guaranteed by the grid.** Unlike other commodity exchanges, electrons flow based on physics. If P1 produces 10 kWh and P7 consumes 10 kWh on connected grids, energy "settles" physically regardless of any contract. The settlement problem is therefore purely financial: who owes whom, based on metered production and consumption.

2. **Energy Retailers face bill collection challenges.** Inter-energy retailer P2P trading must not worsen this problem.

3. **Fewer actors is better.** Requiring many systems or institutions to participate will slow market innovation and adoption.

---

## User Journey

### Model I - Direct Settlement and Contracting

*Energy distribution companies/Energy retailers provide infrastructure and have visibility but are not in the payment flow.*

---

## Actors

| # | Actor | Role |
|---|-------|------|
| 1 | **Energy retailers** | Consumer facing role |
| 2 | **Energy distribution companies** | Wire role / physical infra operator |
| 3 | **Buyer** | Energy consumer in P2P trade |
| 4 | **Seller** | Energy producer in P2P trade |
| 5 | **Trade platform(s)** | Consumer-facing applications that: |
|   |                     | - Allow prosumers to interact with the trade exchange |
|   |                     | - Handle user interfaces for trade placement and management (Energy retailer may also have a consumer interface) |
|   |                     | - Are a separate entity from the trade exchange itself |
| 6 | **Trade exchange(s)** | A logical entity (like NYSE/NSE/LSE in stock markets) that: |
|   |                       | - Runs the permissioned transaction ledger |
|   |                       | - Establishes relationships with Energy distribution companies/Energy retailers (and is trusted by them) |
|   |                       | - Provides regulatory backing and trust assurance |
|   |                       | - May be implemented using various technologies (blockchain, database, etc.) |

> **Assumption:** Whoever is running the permissioned ledger IS the trade exchange. This is a necessary logical construct. Whoever (regulators or other operators) runs this, that entity becomes the trade exchange.

---

## Overall Process Flow

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant B as Buyer (P7)
    participant TP as Trade Platform
    participant TE as Trade Exchange/Ledger
    participant RA as Retailer A
    participant RB as Retailer B
    participant DU_A as Distribution Utility A
    participant DU_B as Distribution Utility B

    rect rgb(230, 245, 255)
    note over S,TE: Phase 1: Trade Placement
    S->>TP: Initiate trade
    B->>TP: Accept trade
    TP->>TE: Submit signed contract
    TE->>TE: Record on ledger
    Note right of TE: Ledger: Discom A, Discom B, seller, buyer, <br/>Trade Time, Delivery Start/End,<br/>Trade Qty, Actual pushed, Actual pulled Qty
    DU_A-->>TE: Visibility into upcoming trades
    DU_B-->>TE: Visibility into upcoming trades
    end

    rect rgb(230, 255, 230)
    note over S,DU_B: Phase 2: Trade Delivery
    S->>DU_A: Inject energy at scheduled time
    DU_A->>DU_A: Grid security check
    B->>B: Consume energy
    end

    rect rgb(255, 245, 230)
    note over TE,RB: Phase 3: Trade Verification
    DU_A->>TE: Add actual pushed signed meter data to ledger (P1)
    DU_B->>TE: Add actual pulled signed meter data to ledger (P7)
    TE->>TE: Mark trade complete
    end

    rect rgb(255, 230, 230)
    note over S,B: Phase 4: Financial Settlement
    Note right of TE: Settlement via chosen<br/>mechanism (Options A-D)
    B->>S: Payment (via settlement mechanism)
    end

    rect rgb(245, 230, 255)
    note over RA,RB: Phase 5: Wheeling & Declaration
    TE->>RA: Declare P2P trades
    TE->>RB: Declare P2P trades
    RA->>S: Bill (excl. P2P + wheeling)
    RB->>B: Bill (excl. P2P + wheeling)
    S->>RA: Pay bill
    B->>RB: Pay bill
    RA->>DU_A: Remit wheeling charges
    RB->>DU_B: Remit wheeling charges
    end

    rect rgb(255, 240, 245)
    note over RA,RB: Phase 6: Enforcement (if default)
    TE->>RA: Notify of default
    TE->>RB: Notify of default
    RA->>S: Enforcement action
    RB->>B: Enforcement action
    end
```

---

## Phase 1: Trade Placement

### 1. Trade Placement

- P1 (Energy Retailer A) logs into a trading app and initiates a trade with P7 (Energy Retailer B)
- Trade contract specifies: fulfillment terms (delivery window, energy quantity), agreed price, meter IDs for both parties, destination energy retailer details
- Contract is digitally signed by P1 and P7 using certificates issued by the trade exchange
- **Example:** P1-A agrees to deliver 5 kWh between 2–4 PM at USD 5/kWh to P7-B

> **Note:** As trading volumes grow, matching individual buyers to individual sellers might become impractical. A stock-exchange-style approach, where supply and demand are aggregated and matched algorithmically, may be more viable at scale.

### 2. Ledger Recording

- The trade is recorded on the trade exchange
- Energy distribution utilities gain visibility into scheduled trades for grid security management, capacity planning and financial reconciliation

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)<br/>Retailer A
    participant B as Buyer (P7)<br/>Retailer B
    participant TP as Trade Platform
    participant TE as Trade Exchange/Ledger
    participant DU as Distribution Utility

    S->>TP: Login & initiate trade
    TP->>S: Request trade details
    S->>TP: Submit trade details<br/>(delivery window, quantity,<br/>price, meter IDs)
    TP->>B: Trade invitation
    B->>TP: Accept trade terms

    TP->>TE: Request signing certificates
    TE-->>TP: Issue certificates

    S->>TP: Digital signature
    B->>TP: Digital signature
    TP->>TE: Submit signed contract

    TE->>TE: Validate signatures
    TE->>TE: Record on permissioned ledger
    TE-->>TP: Confirmation
    TP-->>S: Trade confirmed
    TP-->>B: Trade confirmed

    DU-->>TE: Visibility into scheduled trades<br/>(for grid planning)
```

---

## Phase 2: Trade Delivery

*(Could be anywhere from a few hours to a few days later)*

### 3. Energy Injection

- At scheduled time, seller injects energy into the grid
- Corresponding energy distribution utility performs grid security checks and permits injection only if grid stability is maintained

### 4. Energy Consumption

- Buyer consumes energy as usual during the delivery window

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant SM_S as Seller's<br/>Smart Meter
    participant DU_A as Distribution<br/>Utility A
    participant DU_B as Distribution<br/>Utility B
    participant SM_B as Buyer's<br/>Smart Meter
    participant B as Buyer (P7)

    Note over S,B: Scheduled Delivery Window Begins

    S->>SM_S: Generate/inject energy
    SM_S->>DU_A: Report injection request

    DU_A->>DU_A: Grid security check
    alt Grid stable
        DU_A->>DU_A: Permit injection
        SM_S->>SM_S: Energy injected into grid

        SM_B->>B: Energy consumed

        SM_S->>SM_S: Record injection (kWh, timestamp)
        SM_B->>SM_B: Record consumption (kWh, timestamp)
    else Grid unstable
        DU_A-->>SM_S: Reject/limit injection
        Note over DU_A: Grid stability<br/>takes priority
    end

    Note over S,B: Scheduled Delivery Window Ends
```

---

## Phase 3: Trade Verification

*(Will happen at a time gap from execution - verification frequency can be pre-determined, like every x hours)*

### 5. Trade Verification

- Distribution utilities update the ledger with digitally signed meter data for both parties
- For overlapping trades (same delivery window), actual energy is allocated FIFO by trade time; reconciled quantity = min(trade qty, actual pushed)
- Trade exchange/ledger marks trade as complete

```mermaid
sequenceDiagram
    autonumber
    participant TE as Trade Exchange/Ledger
    participant DU_A as Distribution Utility A
    participant DU_B as Distribution Utility B

    Note over TE: Verification cycle triggered<br/>(e.g., every X hours)

    DU_A->>TE: Update ledger with signed meter data<br/>(Meter M1, P1 injection: X kWh)
    DU_B->>TE: Update ledger with signed meter data<br/>(Meter M7, P7 consumption: Y kWh)

    Note over TE: Anti-double-dipping: For overlapping trades,<br/>actual kWh allocated FIFO by trade time.<br/>Recon Qty = min(Trade Qty, Actual Pushed).<br/>(See Overlapping Trade Reconciliation)

    TE->>TE: Validate digital signatures
    TE->>TE: Compare actuals vs contract

    alt Delivery matches contract
        TE->>TE: Mark trade COMPLETE
        Note over TE: Proceed to settlement
    else Partial delivery
        TE->>TE: Record actual delivery
        Note over TE: Apply settlement rules<br/>(see Contract Modification)
    else No delivery
        TE->>TE: Mark trade FAILED
        Note over TE: Trigger penalty/<br/>enforcement
    end
```

---

## Phase 4: Financial Settlement

### Settlement Options (Open for Group Discussion)

---

### Option A: Clearing House Model

- Central clearing house holds funds from the buyer (at the time of trade placement or at a later date for trades happening much later)
- Releases to seller upon delivery confirmation
- Similar to stock exchange settlement

| Pros | Cons |
|------|------|
| Familiar pattern, trusted intermediary, proven at scale | Requires new infrastructure; problematic for long-horizon trades (when does money go to the clearing house for a T+60 trade - day 1 or day 59?) |

```mermaid
sequenceDiagram
    autonumber
    participant B as Buyer (P7)
    participant CH as Clearing House
    participant TE as Trade Exchange
    participant S as Seller (P1)

    Note over B,S: At Trade Placement (or later for future trades)
    B->>CH: Deposit funds
    CH->>CH: Hold funds in escrow
    CH-->>B: Deposit confirmed

    Note over B,S: After Trade Verification
    TE->>CH: Trade verified<br/>(delivery confirmed)
    CH->>CH: Release funds
    CH->>S: Transfer payment
    S-->>CH: Payment received

    CH->>TE: Settlement complete
```

---

### Option B: Money Block / Escrow Model

- Funds blocked at trade placement
- Released on delivery confirmation
- Many payment rails like credit cards already support blocking

| Pros | Cons |
|------|------|
| Real-time assurance, works for immediate trades | Complex for future trades - how will we block money for 15, 30, 60 days? |

```mermaid
sequenceDiagram
    autonumber
    participant B as Buyer (P7)
    participant Bank as Buyer's Bank/<br/>Payment Rail
    participant TE as Trade Exchange
    participant S as Seller (P1)

    Note over B,S: At Trade Placement
    TE->>Bank: Request fund block<br/>(amount, duration)
    Bank->>Bank: Block funds in<br/>buyer's account
    Bank-->>TE: Block confirmed
    Bank-->>B: Funds blocked notification

    Note over B,S: After Trade Verification
    TE->>Bank: Release blocked funds<br/>to seller
    Bank->>Bank: Unblock & transfer
    Bank->>S: Payment credited
    Bank-->>B: Funds released notification

    Note over Bank: Challenge: How to maintain<br/>block for 15-60 days?
```

---

### Option C: Prepaid Model

- Every consumer/prosumer pre-pays their smart meter with x amount
- All purchases are directly addressed by respective retailers' bill collection and payments infra against the bill using the data from trade exchange

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant B as Buyer (P7)
    participant SM_B as Buyer's<br/>Smart Meter
    participant RA as Retailer A
    participant RB as Retailer B
    participant TE as Trade Exchange

    Note over B: Pre-funding Phase
    B->>SM_B: Pre-pay smart meter<br/>(top-up balance)
    SM_B-->>B: Balance: $X

    Note over S,B: After Trade Verification
    TE->>RB: P2P trade data<br/>(P7 owes P1 $Y)

    RB->>SM_B: Debit P2P purchase
    SM_B->>SM_B: Deduct from balance

    RB->>RA: Inter-retailer settlement<br/>(P7's payment for P1)
    RA->>S: Credit to seller<br/>(via regular bill credit)

    Note over B: Next bill cycle
    RB->>B: Regular bill<br/>(reflects P2P debits)
```

---

### Option D: Country Specific Bill Presentation Rails

**Example: BBPS in India**

Settlement via BBPS with either seller or seller's platform as registered biller.

---

#### Sub-option C1: Seller as Bill Presenter

- Seller (with platform support for KYC/registration) registers as biller on BBPS
- Trade verified → Seller raises invoice to buyer via BBPS
- Buyer pays within stipulated window
- Payment flows directly to seller
- If buyer defaults → Seller's discom notified → Buyer's discom notified for enforcement

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant TP as Trade Platform
    participant BBPS as BBPS
    participant B as Buyer (P7)
    participant RA as Retailer A<br/>(Seller's Discom)
    participant RB as Retailer B<br/>(Buyer's Discom)

    Note over S: One-time Registration
    S->>TP: Request BBPS registration
    TP->>TP: KYC verification
    TP->>BBPS: Register seller as biller
    BBPS-->>S: Biller ID assigned

    Note over S,B: After Trade Verification
    S->>BBPS: Raise invoice to P7<br/>(amount, due date)
    BBPS->>B: Bill notification

    alt Buyer pays
        B->>BBPS: Pay invoice
        BBPS->>S: Direct payment
        BBPS-->>B: Payment confirmed
    else Buyer defaults
        BBPS->>S: Payment overdue
        S->>RA: Notify default
        RA->>RB: Cross-retailer notification
        RB->>B: Enforcement action
    end
```

---

#### Sub-option C2: Platform as Bill Presenter

- Platform registers as BBPS biller
- Trade verified → Platform presents invoice to buyer
- Buyer pays via BBPS
- Platform credits seller (minus platform fee, if any)
- If buyer defaults → Platform notifies buyer's discom for enforcement

```mermaid
sequenceDiagram
    autonumber
    participant S as Seller (P1)
    participant TP as Trade Platform<br/>(BBPS Biller)
    participant BBPS as BBPS
    participant B as Buyer (P7)
    participant RB as Retailer B<br/>(Buyer's Discom)

    Note over TP: Platform is registered<br/>BBPS biller

    Note over S,B: After Trade Verification
    TP->>BBPS: Present invoice to P7<br/>(amount, due date)
    BBPS->>B: Bill notification

    alt Buyer pays
        B->>BBPS: Pay invoice
        BBPS->>TP: Payment received
        TP->>TP: Deduct platform fee<br/>(if any)
        TP->>S: Credit seller
    else Buyer defaults
        BBPS->>TP: Payment overdue
        TP->>RB: Notify default
        RB->>B: Enforcement action
    end
```

| Pros | Cons |
|------|------|
| Existing infrastructure, no new rails needed, familiar UX for consumers, handles small ticket sizes well, enforcement can piggyback on discom relationship | "Bill" framing may not fit P2P trade semantics, settlement timing tied to buyer action (not automatic), need to verify BBPS allows this use case |

---

## Phase 5: Wheeling Charges and Declaration

This phase ensures accurate billing by preventing double-counting and collecting grid usage (wheeling) fees for P2P energy transfers.

### Step-by-Step Flow

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Trade Exchange declares P2P trades to Retailers | Retailers learn which energy was traded peer-to-peer |
| 2 | Retailers verify against ledger | Ensures no double billing for P2P-traded energy |
| 3 | Retailers prepare bills (excl. P2P energy, incl. wheeling charges) | Customers only pay retailer for non-P2P energy; wheeling fees added |
| 4 | Customers pay Retailers | Single consolidated bill payment |
| 5 | Retailers remit wheeling charges to Distribution Utility | Grid usage fees flow to infrastructure operator |

### Anti-Double-Billing Rules

- **Buyer (P7):** Not charged by retailer for energy already purchased via P2P
- **Seller (P1):** Not credited by retailer for energy already sold via P2P

```mermaid
sequenceDiagram
    autonumber
    participant TE as Trade Exchange/Ledger
    participant RA as Retailer A
    participant RB as Retailer B
    participant S as Seller (P1)
    participant B as Buyer (P7)
    participant DU as Distribution Utility

    rect rgb(230, 245, 255)
    Note over TE,RB: Step 1: Trade Declaration
    TE->>RA: Declare P2P trades<br/>(P1 sold X kWh, time slot T)
    TE->>RB: Declare P2P trades<br/>(P7 bought X kWh, time slot T)
    end

    rect rgb(255, 245, 230)
    Note over RA,RB: Step 2-3: Retailer Billing Cycle
    RA->>RA: Verify: Exclude P2P energy<br/>from retailer settlement
    RA->>RA: Add wheeling charges<br/>for P2P transfers
    RA->>S: Bill (non-P2P energy +<br/>wheeling charges)

    RB->>RB: Verify: Exclude P2P energy<br/>from retailer charges
    RB->>RB: Add wheeling charges<br/>for P2P transfers
    RB->>B: Bill (non-P2P energy +<br/>wheeling charges)
    end

    rect rgb(230, 255, 230)
    Note over S,B: Step 4: Customer Payment
    S->>RA: Pay bill
    B->>RB: Pay bill
    end

    rect rgb(245, 230, 255)
    Note over RA,DU: Step 5: Wheeling Remittance
    RA->>DU: Remit wheeling charges (P1)
    RB->>DU: Remit wheeling charges (P7)
    end
```

---

## Phase 6: Enforcement

*(Open for Group Discussion)*

When a prosumer registers for P2P trading, they sign an agreement consenting to energy retailer/distribution utility enforcement in case of payment default. Enforcement actions may include fines, suspension of P2P trading privileges or service disconnection in case of non-fulfilment.

```mermaid
sequenceDiagram
    autonumber
    participant B as Buyer (P7)<br/>[Defaulter]
    participant TE as Trade Exchange
    participant RB as Retailer B<br/>(Buyer's Discom)
    participant RA as Retailer A<br/>(Seller's Discom)
    participant S as Seller (P1)

    Note over B: Payment default detected

    TE->>TE: Record default on ledger
    TE->>RB: Notify: P7 defaulted<br/>on P2P payment
    TE->>RA: Notify: P1's payment<br/>not received

    RB->>RB: Check enforcement<br/>agreement

    alt Level 1: Warning
        RB->>B: Warning notice
    else Level 2: Fine
        RB->>B: Fine added to bill
    else Level 3: Suspension
        RB->>TE: Suspend P7's<br/>trading privileges
        TE->>TE: Update status
        TE-->>B: Trading suspended
    else Level 4: Disconnection
        RB->>B: Service disconnection<br/>notice
        Note over B: Severe cases only
    end

    Note over RA,S: Seller compensation
    RA->>S: Credit from enforcement<br/>recovery (if any)
```

---

## Contract Modification and Partial Fulfillment

### Pre-delivery Modification

Either party can request changes (quantity, time, cancellation) via trading platform. The other party accepts/rejects. Trade exchange records modified contract with a small penalty to the requester. Energy retailers verify against modified contract.

### Settlement on Actuals

Regardless of contract, settlement = actual verified delivery × agreed price. Deviations handled as:

| Scenario | Settlement |
|----------|------------|
| **Seller under-delivers** | Buyer pays for actual; seller penalized |
| **Buyer under-consumes** | Open question: Pay for actual or contracted? |
| **Over-delivery/consumption** | Excess settles with respective energy retailer at standard rates |

**Example - Tolerance band:** Minor deviations (±10%?) settle at actuals without penalty.

### Overlapping Trade Reconciliation (Anti-Double-Dipping)

When a prosumer has multiple trades within the same delivery window, actual meter readings must be allocated carefully to prevent double-counting:

1. **FIFO Allocation:** Actual energy is allocated to trades in order of trade placement time (earliest first)
2. **Per-Trade Cap:** Each trade receives at most its contracted quantity
3. **Reconciled Qty:** `Recon Qty = min(Trade Qty, Remaining Actual)`

**Example:**

| Trade | Trade Time | Delivery Window | Trade Qty | Actual Injected | Recon Qty |
|-------|------------|-----------------|-----------|-----------------|-----------|
| T1 | 9:00 AM | 2–4 PM | 5 kWh | — | 5 kWh |
| T2 | 9:30 AM | 2–4 PM | 4 kWh | — | 3 kWh |
| **Total** | — | — | 9 kWh | **8 kWh** | 8 kWh |

*P1 contracted 9 kWh across two trades but only injected 8 kWh. T1 (earlier trade) gets full 5 kWh; T2 gets remaining 3 kWh. T2 buyer may claim shortfall penalty.*

---

```mermaid
sequenceDiagram
    autonumber
    participant P as Requesting Party
    participant TP as Trade Platform
    participant TE as Trade Exchange
    participant O as Other Party
    participant L as Ledger

    Note over P,O: Pre-Delivery Modification

    P->>TP: Request modification<br/>(quantity/time/cancel)
    TP->>TE: Submit modification request
    TE->>O: Notify: Modification requested

    alt Other party accepts
        O->>TE: Accept modification
        TE->>L: Record modified contract
        TE->>L: Apply penalty to requester
        TE-->>P: Modification confirmed<br/>(penalty applied)
        TE-->>O: Modification confirmed
    else Other party rejects
        O->>TE: Reject modification
        TE-->>P: Modification rejected<br/>(original contract stands)
    end

    Note over TE: Settlement Phase

    TE->>TE: Compare actuals vs contract

    alt Within tolerance (±10%)
        TE->>L: Settle at actuals<br/>(no penalty)
    else Seller under-delivers
        TE->>L: Buyer pays actuals
        TE->>L: Seller penalized
    else Over-delivery/consumption
        TE->>L: Contract amount via P2P
        Note over TE: Excess settles with<br/>retailer at standard rates
    end
```

---

## Open Questions

1. **Settlement Mechanism:** Which approach (clearing house, money block, hybrid, prepaid) and why?

2. **Smart Meter Data Latency:** How quickly can energy retailers release meter data to trade exchanges? This is the binding constraint on settlement timelines.

3. **Inter-institution Enforcement:** If buyer defaults and buyer's energy retailer needs to act, what compels retailer B to enforce on behalf of a seller in retailer A's territory? What's the contractual or regulatory mechanism?

4. **Future Trade Horizon:** Should v1 allow long-horizon trades (T+30, T+60)? If yes, we need the full futures/options complexity.

5. **Regulatory Structure:** If multiple trade exchanges exist, who regulates them? How do we ensure interoperability (or do we)?

6. **Partial Fulfillment:** How do we deal with partial fulfilment of contract? Is it an all or none model?

---

[^1]: Non-exhaustive
