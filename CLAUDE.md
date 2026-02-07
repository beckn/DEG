# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Digital Energy Grid (DEG)** specification repository - a decentralized digital infrastructure for energy transactions built on the Beckn protocol. DEG enables interoperable energy contracts, transactions, and fulfillment across diverse stakeholders (EVs, charging stations, prosumers, utilities, etc.).

**Current Version:** 0.4.0

## Related Repository: protocol-specifications-new

**IMPORTANT:** This DEG repository is co-developed with the **Beckn Protocol v2.0 specification repository** located at `../protocol-specifications-new/`. The two repositories work together:

- **protocol-specifications-new** - Contains the core Beckn Protocol v2.0 schemas, JSON-LD contexts, and vocabulary definitions that DEG implementations use
- **DEG (this repo)** - Contains energy-specific implementation guides, examples, and devkits built on top of Beckn Protocol v2.0

### Key Protocol Specification Files

@../protocol-specifications-new/README.md

**Schema Structure:**
- Core schemas: @../protocol-specifications-new/schema/core/v2/
  - `attributes.yaml` - Core Beckn entities (Order, Offer, Item, Provider, etc.)
  - `context.jsonld` - JSON-LD context mapping to schema.org
  - `vocab.jsonld` - Beckn vocabulary definitions
- Domain schemas: @../protocol-specifications-new/schema/
  - `EvChargingOffer/v1/` - EV charging attribute schemas
  - `EvChargingSession/v1/` - Charging session schemas
  - `EnergyTradeOffer/v1/` - P2P energy trading schemas
  - `EnergyEnrollment/v1/` - Enrollment/onboarding schemas

### Schema Development Workflow

When working across both repositories:

1. **Schema changes** happen in `protocol-specifications-new`
2. **Example JSONs** in this repo reference those schemas via `@context` URLs
3. **Validation** ensures examples comply with schemas
4. Use `@../protocol-specifications-new/schema/...` to reference schema files when needed

### Beckn Protocol v2.0 Key Changes

DEG is built on Beckn Protocol v2.0, which introduced major architectural changes from v1.x:

1. **JSON-LD + schema.org alignment** - All entities use `@context` and `@type` for global semantic interoperability
2. **Core + Attributes model** - Core schemas (Order, Offer, Item) are extended via composable `*Attributes` fields containing domain-specific schemas
3. **CDS (Catalog Discovery Service)** - Replaces Beckn Gateway; BPPs push catalogs to CDS, BAPs query CDS for discovery
4. **DeDi-compliant Registry** - Network registries now use Decentralized Directory protocol instead of Beckn-specific lookup/subscribe
5. **Modular schema packs** - Domain schemas (EvChargingOffer, EnergyTradeOffer) are independent, versioned bundles

**Impact on DEG:**
- All JSON examples use JSON-LD format with `@context` and `@type`
- Energy-specific fields live in `*Attributes` objects (e.g., `offerAttributes`, `itemAttributes`)
- Schemas loaded from `@context` URLs determine validation rules

## Core Architecture

DEG is built on six fundamental primitives (see `architecture/` directory):

1. **Energy Resource** - Physical/logical entities (solar panels, EVs, batteries, utilities)
2. **Energy Resource Address (ERA)** - Globally unique identifiers for resources
3. **Energy Credentials** - Digital attestations for trust and verification
4. **Energy Intent** - Consumer demand specifications
5. **Energy Catalogue** - Provider supply listings
6. **Energy Contract** - Formalized agreements when intent matches catalogue

**Transaction Flow:** Resources → ERAs → Credentials → Intents/Catalogues → Contract → Fulfillment

## Key Technologies

- **Language:** Python 3.14+
- **Protocol:** Beckn Protocol v2.0 (JSON-LD based)
- **Schema Validation:** jsonschema, referencing library, YAML schemas
- **Testing:** Postman collections, Docker-based devkits

## Repository Structure

```
architecture/           - Core primitive documentation
docs/implementation-guides/v2/  - Implementation guides for use cases
  ├── EV_Charging_V0.8-draft.md
  └── P2P_Trading/
examples/              - JSON example flows for each use case
  ├── ev-charging/v2/
  ├── p2p-trading/v2/
  └── enrollment/v2/
scripts/               - Validation and generation tools
testnet/               - Devkit configurations and testing
  ├── ev-charging-devkit/
  └── p2p-energy-trading-devkit/
```

## Common Commands

### Schema Validation

Validate JSON payloads against Beckn protocol schemas:

```bash
# Validate a single file
python3 scripts/validate_schema.py examples/ev-charging/v2/03_select/time-based-ev-charging-slot-select.json

# Validate multiple files (glob patterns)
python3 scripts/validate_schema.py examples/ev-charging/v2/**/*.json

# Validate only core Beckn objects (skip domain-specific attributes)
python3 scripts/validate_schema.py --core-only examples/ev-charging/v2/03_select/time-based-ev-charging-slot-select.json
```

**How validation works:**
- Schemas are auto-discovered from `@context` URLs in JSON-LD objects
- Core Beckn objects (beckn:Order, beckn:Offer) use `core/v2/attributes.yaml`
- Domain-specific attributes (ChargingOffer, ChargingSession) use domain schemas (e.g., `EvChargingOffer/v1/attributes.yaml`)
- Schemas are loaded on-demand from GitHub URLs and cached
- Uses `referencing` library for $ref resolution across schema files

### Generate Postman Collections

Build Postman collections from example JSON flows for testing:

```bash
python3 scripts/generate_postman_collection.py \
  --devkit ev-charging \
  --role BAP \
  --output-dir testnet/ev-charging-devkit/postman \
  --examples examples/ev-charging/v2 \
  --name ev-charging:BAP-DEG \
  --description "EV Charging BAP flows" \
  --validate
```

**Arguments:**
- `--devkit`: Devkit key (ev-charging, p2p-trading)
- `--role`: BAP (Beckn Application Platform) or BPP (Beckn Provider Platform)
- `--output-dir`: Where to write the collection
- `--validate`: Run schema validation on generated collection

### Embed Example JSONs in Documentation

Automatically populate `<details>` blocks in markdown files with referenced JSON contents:

```bash
python3 scripts/embed_example_json.py path/to/markdown_file.md
```

Markdown should contain:
```markdown
<details>
  <summary><a href="path/to/example.json">Example</a></summary>
  <!-- Content auto-populated -->
</details>
```

## JSON-LD Schema Structure

All DEG payloads are JSON-LD documents with:

- **@context**: Schema URL (determines which schema to validate against)
- **@type**: Object type (beckn:Order, beckn:Offer, ChargingOffer, etc.)
- **beckn: prefix**: Core Beckn protocol fields
- **schema: prefix**: Schema.org fields
- **Domain-specific objects**: Embedded in `*Attributes` fields

Example structure (PURE architecture — DEGContract is the direct `@type`):
```json
{
  "context": { "domain": "beckn.one:deg:ev-charging:2.0.0", ... },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/.../core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:buyerAttributes": { "@type": "EnergyBuyer", "vehicle": { ... } },
      "beckn:orderAttributes": { "@type": "DEGContract", "contractState": "ACTIVE", ... },
      "beckn:fulfillment": {
        "beckn:deliveryAttributes": { "@type": "EnergyDelivery", "status": "ACTIVE", ... }
      }
    }
  }
}
```

## Use Case Implementations

Three primary use cases are implemented:

1. **EV Charging** - Charge point discovery, reservation, session management
   - Guide: `docs/implementation-guides/v2/EV_Charging/EV_Charging.md`
   - Examples: `examples/ev-charging/v2/`
   - Devkit: `testnet/ev-charging-devkit/`

2. **P2P Energy Trading** - Prosumer-to-consumer energy marketplace
   - Guide: `docs/implementation-guides/v2/P2P_Trading/P2P_Trading_implementation_guide_draft.md`
   - Examples: `examples/p2p-trading/v2/`
   - Devkit: `testnet/p2p-energy-trading-devkit/`

3. **Enrollment/Onboarding** - User and resource registration
   - Examples: `examples/enrollment/v2/`

## Beckn Protocol Actions

Core protocol flow (applies to all use cases):

1. **discover** - Search for available resources/services
2. **on_discover** - Return catalogue of offerings
3. **select** - Choose specific offer
4. **on_select** - Confirm selection with updated pricing
5. **init** - Initialize order (billing, customer details)
6. **on_init** - Return order draft with payment terms
7. **confirm** - Confirm the order
8. **on_confirm** - Order confirmation
9. **status** - Query order status
10. **on_status** - Status updates (can be asynchronous)
11. **update** - Modify order (e.g., start/stop charging)
12. **on_update** - Update acknowledgment
13. **track** - Track fulfillment progress
14. **on_track** - Real-time tracking data
15. **cancel** - Cancel order
16. **on_cancel** - Cancellation confirmation
17. **rating** - Submit feedback
18. **on_rating** - Rating acknowledgment
19. **support** - Get support info
20. **on_support** - Support details

## Git Workflow

- **Main branch:** `main`
- **Current working branch:** `p2p-trading` (as of conversation start)
- Use conventional commit messages following existing patterns
- Recent commits focus on schema improvements, implementation guides, and Postman collection updates

## Working with Schemas

**Schema Location:** Schemas are defined in the sister repository `../protocol-specifications-new/schema/`

When modifying or adding schemas:

1. **Schema definitions** are in `../protocol-specifications-new/schema/`
   - Core: `../protocol-specifications-new/schema/core/v2/attributes.yaml`
   - Domain-specific: `../protocol-specifications-new/schema/{DomainName}/v1/attributes.yaml`
2. **Example JSONs** in this repo (`examples/`) reference schemas via `@context` URLs pointing to GitHub
3. **Validation workflow:**
   - Make schema changes in `../protocol-specifications-new/`
   - Update/create example JSONs in this repo
   - Run `python3 scripts/validate_schema.py` to validate examples against schemas
4. The `fix_schema.py` script can help migrate old schema formats to new ones (fixes `beckn:items` → `beckn:orderItems`, etc.)

**Schema Development Pattern:**
- Use `@../protocol-specifications-new/schema/core/v2/attributes.yaml` to view/edit core schemas
- Use `@../protocol-specifications-new/schema/EvChargingOffer/v1/` for EV charging schemas
- Use `@../protocol-specifications-new/schema/EnergyTradeOffer/v1/` for P2P trading schemas

## Important Files

**In this repository (DEG):**
- `architecture/README.md` - Core primitives overview
- `docs/implementation-guides/v2/EV_Charging/EV_Charging.md` - Comprehensive EV charging guide
- `docs/implementation-guides/v2/P2P_Trading/` - P2P energy trading documentation
- `scripts/validate_schema.py` - Primary validation tool
- `scripts/generate_postman_collection.py` - Collection generator
- `examples/*/v2/` - Reference implementations
- `fix_schema.py` - Schema migration utility

**In protocol-specifications-new:**
- `../protocol-specifications-new/README.md` - Beckn Protocol v2.0 overview
- `../protocol-specifications-new/schema/README.md` - Schema registry documentation
- `../protocol-specifications-new/schema/core/v2/attributes.yaml` - Core Beckn schemas
- `../protocol-specifications-new/schema/{Domain}/v1/` - Domain-specific attribute schemas

## DEGContract-as-Code (Generalized Energy Contracts)

**Status:** Active development (Feb 2026)
**Architecture:** PURE — DEGContract is the top-level `@type` in offerAttributes/orderAttributes

### Concept

DEGContract is a **composable, multi-party contract schema** that unifies EV charging, P2P trading, and demand flexibility into a single structure. Instead of separate domain schemas per use case, a DEGContract defines **roles**, **terms**, **energy specs**, and **revenue flows** — allowing composite contracts (e.g., EV charging + V2G demand flexibility in one transaction).

Key idea: **Contract-as-Code** — contract terms reference executable OPA/Rego policies for complex business logic (pricing, eligibility, penalties), while simple conditions use inline expressions or structured rule trees.

### Pure Beckn Slot Mapping

DEGContract is the **primary `@type`** in `offerAttributes` and `orderAttributes` (no wrapper schemas). Domain-specific data lives in dedicated Beckn attribute slots using 4 first-principles schemas.

| Beckn Slot | `@type` | Purpose | First Appears |
|------------|---------|---------|--------------|
| `itemAttributes` | **EnergyResource** | Physical resource description (charger, solar, battery) | `on_discover` |
| `offerAttributes` | **DEGContract** (TEMPLATE) | Contract template with open role slots | `on_discover` |
| `providerAttributes` | **EnergyProvider** | Provider identity, registration, grid account | `on_discover` |
| `buyerAttributes` | **EnergyBuyer** | Buyer vehicle info or grid account | `select` |
| `orderAttributes` | **DEGContract** (NEGOTIATED→SETTLED) | Contract through full lifecycle | `select` onwards |
| `deliveryAttributes` | **EnergyDelivery** | Runtime telemetry, session state, V2G events | `on_confirm` |
| `paymentAttributes` | **PaymentSettlement** | Settlement accounts & reconciliation | `init` |

### 4 Domain Schemas (First Principles)

**EnergyResource** (`itemAttributes`) — One unified schema for ALL energy resources. Uses `resourceType` as discriminator:
- `resourceType`: EV_CHARGER | GENERATION_PLANT | BATTERY_STORAGE | GRID_CONNECTION
- `sourceType`: GRID | SOLAR | WIND | BATTERY | HYBRID
- `deliveryMode`: EV_CHARGING | GRID_INJECTION | V2G | BATTERY_SWAP
- `capacity`, `connector`, `metering`, `capabilities`, `location`, `amenities`, `certification`, `rating`

**EnergyDelivery** (`deliveryAttributes`) — One unified schema for ALL runtime fulfillment. Uses sparse sub-objects:
- `status`: PENDING | ACTIVE | PAUSED | COMPLETED | FAILED
- `deliveryMode`: EV_CHARGING | GRID_INJECTION | V2G
- `energyFlow` (direction, delivered, discharged, net, curtailed)
- `telemetry[]`, `meterReadings[]` (P2P), `v2g` (V2G events), `vehicle`, `grid`, `summary`

**EnergyProvider** (`providerAttributes`) — Unified provider identity (CPO, prosumer, utility):
- `operatorName`, `operatorCode`, `identifier`, `contact`, `registration`
- `gridAccount` (for prosumers: meterId, utilityId, sanctionedLoad, connectionType)

**EnergyBuyer** (`buyerAttributes`) — Sparse, domain-specific buyer info (core identity stays in `beckn:Buyer`):
- `vehicle` (registration, makeModel, batteryKwh, connectorType) — for EV use cases
- `gridAccount` (meterId, utilityId, sanctionedLoad) — for P2P use cases

### Core Design Patterns

1. **Progressive Role Filling** — In the catalog (TEMPLATE), provider roles are pre-filled; consumer roles have `party: null` and unfilled inputs. As the Beckn transaction progresses (select → init → confirm), buyer fills negotiation-phase inputs, then commitment-phase inputs, until all roles are complete.

2. **3-Tier Policy Expressions** — Contract terms use `condition` and `obligation` fields with three escalation levels:
   - `expr`: Simple string expression (`"deliveredKwh > 0"`)
   - `rule`: Structured operator tree (`{ operator: "AND", operands: [...] }`)
   - `policyRef`: External OPA/Rego policy (`{ type: "REGO", package: "deg.contracts.ev_charging", entrypoint: "total_charge" }`)

3. **Multi-Party Revenue Model with Net-Zero Invariant** — Every contract has a `revenueModel` with directed `flows[]` (from → to). At discovery, flows show formulas; at settlement, flows show `computedAmount`. For every party, `sum(inflows) - sum(outflows)` across ALL parties = 0.

4. **Composite Contracts** — `contractType: "COMPOSITE"` with `composedOf: ["EV_CHARGING", "DEMAND_FLEXIBILITY"]` allows combining multiple use case logics in one contract.

### DEGContract Schema Components

- **DEGContract** — Top-level: contractType, contractState, roles[], terms[], energySpec, fulfillmentSpec, settlementSpec, revenueModel
- **DEGRole** — roleId, roleType, party (simplified: partyId, partyType, platformId), inputs[], obligations[]
- **RoleInput** — inputId, inputType, providedAt (TEMPLATE|NEGOTIATION|COMMITMENT|FULFILLMENT), value
- **DEGTerm** — termId, termType, condition (PolicyExpression), obligation, appliesTo[]
- **RevenueModel** — flows[] (RevenueFlow), netZeroCheck
- **RevenueFlow** — flowId, from, to, flowType, formula, computedAmount, currency

### File Layout

```
specification/
├── schema/
│   └── deg_contract_schema.yaml          # OpenAPI 3.1.1 formal schema
├── policies/                              # OPA/Rego policy packages
│   ├── ev_charging.rego                   # Connector compat, pricing, cancellation
│   ├── p2p_trade.rego                     # Delivery compliance, deviation penalty
│   ├── demand_flex.rego                   # Trigger conditions, curtailment, incentives
│   ├── v2g.rego                           # V2G eligibility, discharge decisions
│   └── revenue.rego                       # Generic net-zero revenue computation
└── deg_contract_beckn_flow.arazzo.yaml    # Arazzo spec: 3 workflows

examples/deg_contract/
├── README.md                              # Overview + Pure Beckn slot mapping
├── ev_charging/                           # 9 files: discover → settlement
│   ├── on_discover.json                   #   EnergyResource + EnergyProvider + DEGContract
│   └── on_update_complete.json            #   EnergyDelivery (COMPLETED) + DEGContract (SETTLED)
├── p2p-trading-interdiscom/               # 11 files: discover → settlement (incl. cascaded)
│   ├── on_discover.json                   #   GENERATION_PLANT resource, 4 roles + 6 revenue flows
│   ├── cascaded_init.json                 #   P2P BPP acts as BAP to utility BPP
│   └── on_status_completed.json           #   Full settlement with net-zero verified
└── smart_ev_charging/                     # 10 files: discover → V2G event → settlement
    ├── on_discover.json                   #   V2G-capable EV_CHARGER, COMPOSITE contract, 3 roles
    ├── on_update_v2g_event.json           #   Grid stress V2G activation with Rego eval
    └── on_status_complete.json            #   4-party revenue: ev_owner, CPO, grid_operator, platform
```

### Three Implemented Use Cases

**1. EV Charging** (`ev_charging/`)
- 2 roles: `cpo` (CPO) + `ev_driver` (CONSUMER)
- Revenue: charging_payment + platform_fee + GST + idle_fee - refund_overcharge
- Rego: `deg.contracts.ev_charging` (connector compat, time-of-day pricing, cancellation)

**2. P2P Inter-Discom Trading** (`p2p-trading-interdiscom/`)
- 4 roles: `seller` (PRODUCER) + `buyer` (CONSUMER) + `source_utility` (DISCOM) + `destination_utility` (DISCOM)
- Revenue: energy_payment + wheeling_charge(×2) + platform_fee(×2) + deviation_penalty
- Cascaded init: P2P BPP acts as BAP to utility BPP for wheeling/open-access approval
- Rego: `deg.contracts.p2p_trade` (delivery compliance, deviation penalty, sanctioned load)

**3. Smart EV Charging + V2G** (`smart_ev_charging/`)
- 3 roles: `ev_owner` (PROSUMER) + `cpo_aggregator` (AGGREGATOR) + `grid_operator` (GRID_OPERATOR)
- Revenue: charging_payment - v2g_earnings + grid_v2g_payment + platform_fee
- V2G triggers on grid frequency < 49.5 Hz, evaluates `deg.contracts.v2g` Rego policy
- Composite: `composedOf: ["EV_CHARGING", "DEMAND_FLEXIBILITY"]`

### Working with DEGContract Examples

- All 30 JSON files validated with `python3 -c "import json; json.load(open(f))"`
- **PURE architecture**: DEGContract is the direct `@type` in offerAttributes/orderAttributes — no wrapper schemas (ChargingOffer, EnergyTradeOffer etc. are NOT used)
- Domain data in dedicated Beckn slots: EnergyResource in itemAttributes, EnergyDelivery in deliveryAttributes, EnergyProvider in providerAttributes, EnergyBuyer in buyerAttributes
- Revenue model `computedAmount` values only appear in SETTLED state; TEMPLATE state has `computedAmount: null`
- Net-zero verified: `sum(all per-party net positions) == 0` in all 3 settled examples

### Reference Files (Original Working Docs)

The original generalization work lives in `ref_docs/generalize_deg_shcemas/`:
- `prompt_generalize_deg_schemas.md` — Original prompt/requirements
- `deg_contract_schema.yaml` — Original schema (copied to specification/schema/)
- `DEG_Contract_Specification.md` — Original spec (copied to docs/)
- `Mapping_Existing_Schemas.md` — Original mapping (copied to docs/)
- `example_rego_policies.rego` — Original combined Rego (split into specification/policies/)

## Development Notes

- All Python scripts use Python 3.14+ (system has 3.14.0b3)
- Required Python packages: json, yaml, jsonschema, referencing, requests
- JSON files follow strict JSON-LD format with @context and @type fields
- Schema validation is critical - always validate before committing examples
- Postman collections use environment variables: `{{bap_id}}`, `{{bap_uri}}`, `{{bpp_id}}`, `{{bpp_uri}}`
