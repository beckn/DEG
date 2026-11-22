# EV charging examples — Beckn 2.0 LTS

These examples use the Beckn 2.0 LTS core specification (`beckn/protocol-specifications-v2`, tag `core-v2.0.0-lts`, `api/v2.0.0/beckn.yaml`), which is what Beckn ONIX validates against by default from v1.7.1 onwards. The earlier examples, written for the `core-2.0.0-rc-eos-release` draft (`message.order`), are in [`../v2-rc`](../v2-rc) for implementations still on that shape; [`devkits/ev-charging-migration-kit`](../../../devkits/ev-charging-migration-kit) maps between the two for discover to on_confirm.

Every file here is checked in two ways:
- **Through ONIX 1.9.4:** signature, DeDi registry lookup, LTS core schema and the attribute packs.
- **By a closed-world lint** that rejects any field the LTS core does not declare.

The discover requests were also run against the fabric discovery service code (`beckn/beckn-discovr`, the image the hosted service runs) with these catalogs ingested; see Discovery below.

The [EV devkit](../../../devkits/ev-charging) carries the same set with the devkit's registered test participants, and its Arazzo workflows run the flows below through ONIX. The tools that produced and check these files are in [`scripts/ev-charging-lts`](../../../scripts/ev-charging-lts).

## Use cases

The [implementation guide](../../../docs/implementation-guides/v2/EV_Charging/EV_Charging.md) describes two journeys; the remaining rows are the operational cases a production consumer app or CPO platform has to handle.

| Use case | Files (in order) |
|---|---|
| **Walk-in** (scan the charger QR, pay through the CPO's payment link) | `01_discover/discovery-by-EVSE` → `02_on_discover/ev-charging-specific-evse-catalog` → `03_select` → `04_on_select/ev-charging-on-select` → `05_init/ev-charging-bpp-payment-init` → `06_on_init/ev-charging-bpp-payment-on-init` → `06_on_status_1` (payment received) → `07_confirm/ev-charging-confirm` → `08_00_on_confirm` → `08_01_status` / `08_02_on_status` (connector) → `09_update` / `10_on_update` (start) → `11_status` / `12_on_status` (live telemetry) → `14_01_update` / `14_02_on_update/…-complete` (stop, final bill) → `14_03_on_update` (invoice) → `15_rating` / `16_on_rating` → `17_support/ev-charging-session-support` / `18_on_support/ev-charging-session-on-support` |
| **Reservation** (area search, consumer app collects payment, slot) | `01_discover/discovery-within-a-circular-boundary` (and the other search variants) → `02_on_discover/ev-charging-discovery-catalog` → `03_select` → `04_on_select` → `05_init/ev-charging-bap-payment-init` → `06_on_init/ev-charging-bap-payment-on-init` → `07_confirm/ev-charging-bap-payment-confirm` → `08_00_on_confirm` → start / status / stop as above |
| Search variants | `01_discover/*`: by EVSE, by CPO, by station, within a radius, opening hours, connector spec, vehicle spec |
| Slot already booked | `04_on_select/ev-charging-on-select-slot-unavailable` (`BIZ_FULFILLMENT_UNAVAILABLE`) |
| Outstanding balance on the next quote | `04_on_select/ev-charging-on-select-outstanding-dues` |
| Start refused, EVSE inoperative | `10_on_update/ev-charging-session-start-rejected-on-update` (error with an OCPI cause) |
| Connection interrupted | `13_on_status/ev-charging-session-interrupt-on-status` |
| Power cut: bill energy delivered, refund the rest | `13_on_status/ev-charging-session-undercharge-refund-on-status` |
| Charger offline, kept dispensing (overcharge billed against the overcharge estimate) | `14_02_on_update/ev-charging-session-overcharge-on-update` |
| Battery full early (undercharge, refund) | `14_02_on_update/ev-charging-session-undercharge-on-update` |
| Invoice ready | `14_03_on_update/ev-charging-invoice-ready-on-update` |
| Cancellation terms before cancelling (`context.try`) | `19_cancel/ev-charging-cancel-preview` → `20_on_cancel/ev-charging-cancel-preview-on-cancel` |
| Consumer cancels | `19_cancel/ev-charging-cancel-reserved-slot` → `20_on_cancel/ev-charging-bpp-reservation-on-cancel` |
| CPO cancels (unsolicited) | `20_on_cancel/ev-charging-cpo-initiated-on-cancel` |
| Live tracking handle | `21_track` → `22_on_track` |
| Support ticket opened, then resolved | `17_support/ev-charging-connector-fault-support` → `18_on_support/ev-charging-support-resolved-on-support` |
| CPO publishes its catalog to the discovery service | `23_catalog_publish` → `24_catalog_on_publish` |

## Conventions

- **Context.** camelCase (`bapId`, `bapUri`, `bppId`, `bppUri`, `transactionId`, `messageId`, `networkId`, `ttl`, `try`). `networkId` is `nfh.global/testnet-evcharging`, the test network the devkit's example participants are registered on. A `discover` carries no BPP fields: it goes to the discovery service. Each discover example has its own `messageId`, because the discovery service drops a repeated one for 60 s.
- **The order is a `contract`.**
  - `commitments[]` say what is bought: the charger (`resources[].id`) with the energy booked (`resources[].quantity`, required by LTS) and the tariff (`offer`, with `id` and `resourceIds`).
  - `consideration[]` is the price, `settlements[]` the payments and refunds, `performance[]` the charging session, and `participants[]` the CPO and the driver.
- **Status codes.**
  - `contract.status.code`: `DRAFT` (quote), `ACTIVE` (booked or charging), `COMPLETE`, `CANCELLED`.
  - `commitments[].status.descriptor.code`: `DRAFT`, `ACTIVE`, `CLOSED`.
  - `settlements[].status`: `DRAFT`, `COMMITTED`, `COMPLETE`.
  - The session state is in `performance[].performanceAttributes.sessionStatus`.
- **Attribute packs** (all on schema.nfh.global):

  | Slot | Pack | `@type` |
  |---|---|---|
  | `resources[].resourceAttributes` | `EvChargingService/v2.0` | `ChargingService` |
  | `offers[].offerAttributes` | `EvChargingOffer/v2.0` | `ChargingOffer` |
  | `performance[].performanceAttributes`, `contractAttributes`, `trackingAttributes` | `EvChargingSession/v2.0` | `ChargingSession` |
  | `consideration[].considerationAttributes`, `offers[].considerations[]` | `PriceSpecification/v2.1` | `PriceSpecification` |
  | `settlements[].settlementAttributes` | `Payment/v2.0` | `Payment` |
  | `participants[].participantAttributes` (driver) | `Consumer/v2.0` | `Consumer` |
  | `support.channels[]` | `SupportInfo/v2.1` | `SupportInfo` |

- **Prices.** An offer's unit price is in `offers[].considerations[]`. A quote or bill is one `consideration` whose `PriceSpecification.components[]` (`UNIT`, `SURCHARGE`, `DISCOUNT`, `FEE`, …) add up to `value`.
- **Payment.** Who collects is `beckn:beneficiary` in the settlement:
  - `BPP`: the CPO sends a `beckn:paymentURL` and reports `COMPLETED` in an unsolicited `on_status`.
  - `BAP`: the consumer app collects and sends `COMPLETED` in `confirm`.
  - Refunds are further settlements with `beckn:paymentStatus: REFUNDED` and `beckn:beneficiary: BUYER`.
  - An amount the buyer still owes is a `DRAFT` settlement with `PENDING` and `beckn:beneficiary: BPP`.
- **One catalog per CPO.** An LTS `Catalog` has a single `provider`, so a multi-CPO answer is several catalogs. Each CPO's station locations are in `provider.availableAt`.
- **Business errors** in a callback go in `error` beside `message`. `code` comes from the LTS `ErrorCode` list, with a `details.cause` chain where useful (draft NFH-008, Handling Exceptions and Errors). `message` still carries the contract, because `beckn.yaml` requires it.
- **Preview before commit.** `context.try: true` on `cancel` returns the cancellation terms and the refund without cancelling.

## Discovery

Checked against `beckn/beckn-discovr` v1.7.1, and against the 1.7.0 image the hosted service pins, with these catalogs ingested.

- **Filters are RFC 9535 JSONPath, absolute from the catalog root, filtering the arrays themselves:**
  - `$.catalogs[*].resources[?(@.resourceAttributes.connectorType == 'CCS2' && @.resourceAttributes.maxPowerKW >= 50)]`
  - `$.catalogs[*].offers[?(@.validity.startTime <= '11:30:00' && @.validity.endTime >= '14:30:00')]`
  - `$.catalogs[?(@.provider.id == 'ecopower-charging')]`
  - A charger by its QR code is `resources[?(@.resourceAttributes.evseId == '…')]`; a station is `resources[?(@.resourceAttributes.chargingStation.id == '…')]`.
- **"Within N metres" is `S_DWITHIN` with `distanceMeters`.** Its `targets` must be an indexed geometry path: `$.catalogs[*].provider.availableAt[*].geo`, or `$.catalogs[*].resources[*].resourceAttributes.chargingStation.serviceLocation.geo`. Any other path (including bracket notation) returns nothing, without an error. `S_WITHIN` is containment: it ignores `distanceMeters` and never matches a point.
- **Status on the current discovery service:**
  - Filter-only, radius-only and text searches return the expected chargers.
  - Two examples combine a filter with a radius: `discovery-within-boundary-with-connection-spec` and `…-vehicle-spec`. They return HTTP 500 on discovr 1.7.x, which sends combined filter + spatial queries to PostgreSQL `jsonpath` without converting RFC 9535 first. The payloads are correct; the fix belongs in discovr.

## rc → LTS field map

| rc (`core-2.0.0-rc-eos-release`) | LTS (`core-v2.0.0-lts`) |
|---|---|
| `context.domain`, `bap_id`, `transaction_id`, … | `context.networkId`, `bapId`, `transactionId`, … |
| `message.order` (`beckn:Order`) | `message.contract` |
| `beckn:orderStatus` | `contract.status.code` (+ `commitments[].status.descriptor.code`) |
| `beckn:seller` / `beckn:buyer` | `contract.participants[]` (driver: `Consumer` pack with `person`) |
| `beckn:orderItems[].beckn:orderedItem` / `beckn:quantity` | `commitments[].resources[].id` / `.quantity` |
| `beckn:orderItems[].beckn:acceptedOffer` | `commitments[].offer` |
| `beckn:orderValue` | `consideration[0].considerationAttributes` (`PriceSpecification`) |
| `beckn:payment` | `settlements[].settlementAttributes` (`Payment`) |
| `beckn:fulfillment` + `beckn:deliveryAttributes` | `performance[]` + `performanceAttributes` (`ChargingSession`) |
| `beckn:orderAttributes` | `contract.contractAttributes` |
| `beckn:items[]` + `beckn:itemAttributes` | `catalogs[].resources[]` + `resourceAttributes` (`ChargingService`) |
| `beckn:offers[].beckn:price` | `offers[].considerations[].considerationAttributes` |
| `beckn:offers[].beckn:acceptedPaymentMethod` | `offerAttributes.acceptedPaymentMethods` |
| `beckn:availabilityWindow` (item) | `offers[].validity.startTime` / `endTime` |
| item-relative filter `$[?(@.beckn:itemAttributes.x …)]` | `$.catalogs[*].resources[?(@.resourceAttributes.x …)]` |
| `rating` / `on_rating`, `ratings[]` | `rate` / `on_rate`, `ratingInputs[]` / `ratings[]` (`range.bestRating`/`worstRating`/`ratingValue`) |
| `support` (`refId`, `support`) | `support.orderId`, `support.descriptor`, `support.channels[]` (`SupportInfo`) |
| tracking URL inside `beckn:fulfillment.trackingAction` | `track` / `on_track` (`tracking.url`) |

## Corrections made while converting

The rc set had data errors. The LTS set fixes them so the files form one consistent flow:

- **Pricing:** the quote's lines did not match their labels (a "20%" surge of 20.00 on 112.50, a "15%" discount of 15.00). The quote is now recomputed to **144.43**:
  - 20% surge, 15% discount, 10 INR service fee, a 0.3 kWh overcharge estimate (refunded if unused) and a 2.5% buyer finder fee;
  - lines are rounded, and the total is their sum;
  - the completed session bills **130.93** and refunds the unused 13.50;
  - every variant uses the same pricing.
- **messageIds:** each callback carries its request's `messageId`, and every other interaction has its own. In the rc set, unrelated requests shared ids, and some callbacks predated their request.
- **Seller id:** it switched from `ecopower-charging` to `cpo1.com` from `05_init` onwards.
- **Charger id:** `20_on_cancel` referred to a truncated id (`pe-charging-01`).
- **Units:** in `12_on_status`, the POWER and ENERGY units were swapped (`KWH`/`KW`).
- **Specific-EVSE catalog:**
  - EcoPower's offer was declared under the GoGreen provider;
  - GoGreen's connector B carried connector A's EVSE id;
  - the answer to the by-EVSE search listed a second CPO. It now holds only the scanned charger.
- **Discover filters:**
  - The by-EVSE and by-station examples filtered on ids found in no catalog; they now use `evseId` and `chargingStation.id`.
  - The vehicle filter (Tata Nexon EV) is expressed as what a charger can serve: `vehicleType == '4-WHEELER'` and `connectorType == 'CCS2'`.
  - All seven discover examples shared one `messageId`; each now has its own.
  - **Time-range example:** the rc version also required `connectorType == 'Type2'`. One LTS filter expression addresses one array (resources *or* offers), and opening hours live on offers, so the example filters on opening hours only. Check the connector type client-side from the returned resources. A nested RFC 9535 filter on `$.catalogs[?(…)]` could combine the two where the discovery service supports it.

Data with no LTS home was dropped: item `category`, `rateable` and aggregate `rating`; the driver's GSTIN (`taxID`); the fulfillment `mode`.

## Open points in the specifications (found while building these)

- `Commitment.resources[]` requires `quantity`, but `Resource` does not declare it.
- `Tracking` requires `url` and `status`, so a `/track` request must send a URL the consumer does not have yet.
- `beckn.yaml` requires `message` in every callback, while draft NFH-008 shows error callbacks with `context` and `error` only.
- The `Intent.filters` example in `beckn.yaml` (`$[?(@.rating.value >= 4.0 …)]`) and the `SpatialConstraint.targets` examples (relative bracket pointers) are shapes the discovery service rejects or ignores.
- There is no published `PaymentSettlement` pack on schema.nfh.global; settlement accounts still reference the rc-tag pack.
- `EvChargingService/v2.0` and `EvChargingOffer/v2.0` had `$ref`s to bare pack URLs (an HTML page), fixed in this change; other DEG packs still have the same pattern.
