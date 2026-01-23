# P2P Energy Trading Implementation Guide <!-- omit from toc -->

Version 0.1 (Non-Normative)

## Table of Contents  <!-- omit from toc -->

- [1. Introduction](#1-introduction)
- [2. Scope](#2-scope)
- [3. Intended Audience](#3-intended-audience)
- [4. Conventions and Terminology](#4-conventions-and-terminology)
- [5. Terminology](#5-terminology)
- [6. Example User Journey](#6-example-user-journey)
  - [6.1. Sequence diagram of a P2P transaction](#61-sequence-diagram-of-a-p2p-transaction)
- [7. Reference Architecture](#7-reference-architecture)
  - [7.1. Architecture Diagram](#71-architecture-diagram)
  - [7.2. Actors](#72-actors)
- [8. Creating an Open Network for Peer to Peer Energy Trading](#8-creating-an-open-network-for-peer-to-peer-energy-trading)
  - [8.1. Setting up a Registry](#81-setting-up-a-registry)
    - [8.1.1. For a Network Participant](#811-for-a-network-participant)
      - [8.1.1.1. Step 1 :  Claiming a Namespace](#8111-step-1---claiming-a-namespace)
      - [8.1.1.2. Step 2 :  Setting up a Registry](#8112-step-2---setting-up-a-registry)
      - [8.1.1.3. Step 3 :  Publishing subscriber details](#8113-step-3---publishing-subscriber-details)
    - [8.1.2. Step 4 :  Share details of the registry created with the Beckn One team](#812-step-4---share-details-of-the-registry-created-with-the-beckn-one-team)
    - [8.1.3. For a Network facilitator organization](#813-for-a-network-facilitator-organization)
      - [8.1.3.1. Step 1 :  Claiming a Namespace](#8131-step-1---claiming-a-namespace)
      - [8.1.3.2. Step 2 :  Setting up a Registry](#8132-step-2---setting-up-a-registry)
      - [8.1.3.3. Step 3 :  Publishing subscriber details](#8133-step-3---publishing-subscriber-details)
      - [8.1.3.4. Step 4 :  Share details of the registry created with the Beckn One team](#8134-step-4---share-details-of-the-registry-created-with-the-beckn-one-team)
  - [8.2. Setting up the Protocol Endpoints](#82-setting-up-the-protocol-endpoints)
    - [8.2.1. Installing Beckn ONIX](#821-installing-beckn-onix)
    - [8.2.2. Configuring Beckn ONIX for Peer to Peer Energy Trading](#822-configuring-beckn-onix-for-peer-to-peer-energy-trading)
    - [8.2.3. 10.2.3 Performing a test transaction](#823-1023-performing-a-test-transaction)
- [9. Schema overview](#9-schema-overview)
  - [9.1. v2 Composable Schema Architecture](#91-v2-composable-schema-architecture)
  - [9.2. Schema Composition Points](#92-schema-composition-points)
  - [9.3. EnergyResource (Item.itemAttributes)](#93-energyresource-itemitemattributes)
  - [9.4. EnergyTradeOffer (Offer.offerAttributes)](#94-energytradeoffer-offerofferattributes)
  - [9.5. EnergyTradeContract (Order.orderAttributes)](#95-energytradecontract-orderorderattributes)
  - [9.6. EnergyOrderItem (OrderItem.orderItemAttributes)](#96-energyorderitem-orderitemorderitemattributes)
  - [9.7. EnergyTradeDelivery (EnergyOrderItem.fulfillmentAttributes)](#97-energytradedelivery-energyorderitemfulfillmentattributes)
- [10. API Reference \& examples](#10-api-reference--examples)
  - [10.1. Discover flow](#101-discover-flow)
  - [10.2. Select Flow](#102-select-flow)
  - [10.3. Init Flow](#103-init-flow)
  - [10.4. Confirm Flow](#104-confirm-flow)
    - [10.4.1. Cascaded Init Example (Utility Registration)](#1041-cascaded-init-example-utility-registration)
  - [10.5. Confirm Flow](#105-confirm-flow)
    - [10.5.1. Cascaded Confirm Example (Utility Trade Logging)](#1051-cascaded-confirm-example-utility-trade-logging)
  - [10.6. Status Flow](#106-status-flow)
    - [10.6.1. Curtailed Trade Status](#1061-curtailed-trade-status)
  - [10.7. Update Flow (Provider-Initiated)](#107-update-flow-provider-initiated)
    - [10.7.1. Utility-Initiated Trade Curtailment](#1071-utility-initiated-trade-curtailment)
- [11. Additional Resources](#11-additional-resources)
  - [11.1. Inter energy retailer P2P trading](#111-inter-energy-retailer-p2p-trading)
- [12. Additional Resources](#12-additional-resources)
    - [12.0.1. **Integrating with your software**](#1201-integrating-with-your-software)
      - [12.0.1.1. **Integrating the BAP**](#12011-integrating-the-bap)
      - [12.0.1.2. **Integrating the BPP**](#12012-integrating-the-bpp)
  - [12.1. FAQs](#121-faqs)
  - [12.2. References](#122-references)

Table of contents and section auto-numbering was done using [Markdown-All-In-One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) vscode extension. Specifically `Markdown All in One: Create Table of Contents` and `Markdown All in One: Add/Update section numbers` commands accessible via vs code command pallete.

Example jsons were imported directly from source of truth elsewhere in this repo inline by inserting the pattern below within all json expand blocks, and running this [script](/scripts/embed_example_json.py), e.g. `python3 scripts/embed_example_json.py path_to_markdown_file.md`.

```
<details><summary><a href="/path_to_file_from_root">txt_with_json_keyword</a></summary>

</details>
``` 

---

# 1. Introduction

This document provides an implementation guidance for deploying peer to peer (P2P) energy trading
services using the Beckn Protocol ecosystem. Peer to peer energy trading enables energy producers 
(prosumers) to directly sell excess energy to consumers. 

Peer-to-peer (P2P) energy trading enables decentralized energy exchange that benefits all participants while strengthening the grid. For consumers, P2P markets offer lower prices during periods of abundant renewable supply (such as mid-day solar or nightly wind), creating demand for supply that might otherwise be curtailed. For producers, these markets may provide higher prices incentivizing the renewable energy generation. Grid operators benefit through reduced transmission losses, local supply-demand balancing, and new revenue streams from wheeling charges on P2P transactions. Additionally, prosumers with accumulated net-metering credits can monetize them through P2P trades, converting credits into cash. These benefits extend beyond direct participants, as reduced grid congestion and improved efficiency ultimately lower costs for all ratepayers.

P2P trades are executed virtually before the delivery hour based on estimated load and generation, with actual energy flows potentially deviating from contracts. However, the economic incentives, namely better revenue for adhering to contracts and penalties for deviations, naturally align producer and consumer behavior toward delivering contracted energy. Each trade contract references a real or virtual meter for post-delivery deviation measurement, with utilities maintaining visibility and control through network policies that limit trade volumes based on sanctioned load or generation at each meter. Virtual meters enable aggregators to balance supply and demand across multiple participants, as any net deviation from zero flow through these virtual meters incurs penalties, creating a self-regulating mechanism for grid stability.

---

# 2. Scope

* Architecture patterns for peer-to-peer energy marketplace implementation using Beckn Protocol  
* Discovery of energy trading partners.
* Some recommendations for BAPs, BPPs and NFOs on how to map protocol API calls to 
  internal systems (or vice-versa).  
* Session management and billing coordination between BAP, BPP and the utility BPP.

This document does NOT cover:

* Processes for customer onboarding, meter validation and settlement.
* Fraud prevention: e.g. if a producer strikes a deal with two consumers, 
  settlement mechanics should be aware of total commited trade flows at a meter
  and apportion the shortfall against it.
* Cyber-security and best practices to ensure privacy of market participants by 
  guarding of personally identifiable information data.
* Payment guarantees or ACH hold until fulfillment to cover the cost trade participant reneging or defaulting on payment.

# 3. Intended Audience

* Energy Trading Platforms: Platforms that want to participate in P2P trading on behalf of prosumers and consumers   
* Technology Integrators: Technology providers building adaptors between existing DERs and applications
* System Architects: Designing scalable, interoperable P2P trading ecosystems  
* Business Stakeholders: Understanding technical capabilities and implementation requirements for P2P marketplace strategies  
* Standards Organizations: Evaluating interoperability approaches for future P2P standards development

# 4. Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described [here](https://github.com/beckn/protocol-specifications/blob/draft/docs/BECKN-010-Keyword-Definitions-for-Technical-Specifications.md).

# 5. Terminology

| Acronym | Full Form/Description            | Description                                                                                                           |
| ------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| BAP     | Beckn Application Platform       | Consumer-facing application that initiates transactions.                                                              |
| BPP     | Beckn Provider Platform          | Service provider platform that responds to BAP requests.                                                              |
| NFO     | Network Facilitator Organization | Organization responsible for the adoption and growth of the network. Usually the custodian of the network’s registry. |
| CDS     | Catalog Discovery Service        | Enables discovery of energy services from BPPs in the network by providing a cache service for catalogs.                                                        |
| MDMS     | Meter Data Management System        | Platform that enables collection, storage and processing of smart meter data                                                        |
| RMS     | Revenue Management System        | Platform that enables money flows throughout the transaction and post fulfillment                                                        |


# 6. Example User Journey

This walkthrough demonstrates a complete P2P energy trading transaction: 

Nisha, who has a large rooftop solar is hoping to get better returns than 3 INR/kwh for the surplus energy mid-day and wants to sell it at 6 INR/kwh. She is eligible to participate and is enrolled as a prosumer in a peer to peer trading app (BPP), which publishes the offer to catalog discovery service (CDS).

In parallel, nearby, Swati runs a small mill which has a sanctioned load of 20kw. Anticipating large seasonal demand, she is looking to purchase cheaper energy than the utility import price of of 10 INR/kwh between 10am to 6pm for next week. Swati is eligible to participate and is already enrolled as a consumer on a *different* peer to peer energy trading app (BAP), and declares her intent to buy with above price and time of day filters.

To her delight, the Beckn network helps her *discovers* Nisha's offer of renewable energy at 6 INR/kwh between 12am to 4pm on all days in that week. With wheeling charges of 1 INR/kwh, the total 8 INR/kwh is still 20% cheaper than importing. 

She *initiates* in an order of 20kw. The (BAP) app knows and shares her meter number with the seller's app (BPP), which in turn shares both with the utility BPP which knows the sanctioned import & export for each meter and existing trades. Utility BPP applies a 50% cap policy and replies back saying that upto 10kw of trade is allowed and adds wheeling charges to the quote. It also adds terms & conditions that specify that any underconsumption by Swati will be treated as a spot export by her reimbursed at 3 INR/kwh and any underproduction by solar farm by the farm is treated as a spot import at 10$/kwh. After this Swati *confirms* the 8 INR/kwh final order with her BAP, solar farm BPP in turn cascaded it to utility BPP and utility BPP acknowledges, locks and logs the trade and deducts it from the further trading allowance in those hours for both Swati & Nisha. 

On the delivery day, the floor mill is busy and consumes 400 kwh from the rooftop solar and saves on its 
in energy costs. The solar farm gains additional revenue, and utility gets revenue for the upkeep of transmission & to cover the administration cost. Utility BPP sends the final settlement including the wheeling and deviation charges to Swati & the solar farm. Swati pays the solar farm BPP 
for the trade itself via her BAP.

## 6.1. Sequence diagram of a P2P transaction

**Scenario**: Consumer (BAP: `bap.energy-consumer.com`) buys 10 kWh from Producer (BPP: `bpp.energy-provider.com`) on Oct 4, 2025, 10:00 AM - 6:00 PM. Source meter: `100200300`, Target meter: `98765456`. Transaction ID: `txn-energy-001`.


```mermaid
sequenceDiagram
    participant P2P Trading BAP
    participant CDS
    participant P2P Trading BPP
    participant Utility Company
    P2P Trading BPP-->>CDS: upload(Item/Offer changes)
    Note over P2P Trading BAP, Utility Company: Opening Bell
    P2P Trading BAP->>+CDS: discover
    CDS-->>-P2P Trading BAP: on_discover
    Note over P2P Trading BAP, P2P Trading BPP: Post-discovery, BAP calls BPP directly for transaction APIs
    P2P Trading BAP->>+P2P Trading BPP: select
    P2P Trading BPP-->>-P2P Trading BAP: on_select

    P2P Trading BAP->>+P2P Trading BPP: init (Trading Order)
    P2P Trading BPP->>+Utility Company: cascaded init (Initialze a delivery order)
      Note right of Utility Company: 1. Calculate wheeling charges<br/>2. remaining sanctioned load
    Utility Company-->>-P2P Trading BPP: on_init (Wheeling charges, remaining trading limit etc. )
    P2P Trading BPP-->>-P2P Trading BAP: cascaded_on_init

    P2P Trading BAP->>+P2P Trading BPP: confirm (Trading Order)
    P2P Trading BPP->>+Utility Company: cascaded confirm (Initialize a delivery order)
      Note right of Utility Company: 1. Log trade<br/>2. Deduct from trading limits.
    Utility Company-->>-P2P Trading BPP: on_confirm (remaining sanctioned load etc. )
    P2P Trading BPP-->>-P2P Trading BAP: on_confirm (Trading Order)
    Note over P2P Trading BAP, Utility Company: Closing Bell

    Note over P2P Trading BAP, Utility Company: Fulfillment
     Utility Company->> Utility Company: Calculate total actual energy <br> surplus produced by provider
    alt if total produced energy is less than total traded
        Utility Company->> Utility Company: Calculate penalty charges <br> (Will be adjusted in the provider's monthly bill)
    else if total produced energy is more than total traded
        Utility Company->> Utility Company: Calculate amount to be paid to provider <br> (Total Surplus - Total Traded ) X Grid buying rate"
    end
    Utility Company->> Utility Company: Apportion total actual energy <br> produced in proportion to <br> energy promised across all trades <br> on that day before closing bell
    loop Send on_update to each consumer(P2P Trading BPP) containing updated order details
        Utility Company->>+P2P Trading BPP: on_update (updated Delivery Order details)
    end
    loop Send cascaded on_update to each P2P Trading BAP containing updated order details
       P2P Trading BPP->>+P2P Trading BAP: cascaded on_update (updated Delivery Order details)
    end
```

**1. Discover** - Consumer searches for solar energy with JSONPath filters (`sourceType == 'SOLAR'`, `deliveryMode == 'GRID_INJECTION'`, `availableQuantity >= 10.0`).  
Request: [discover-request.json](../../../../examples/p2p-trading/v2/discover-request.json) | Response: [discover-response.json](../../../../examples/p2p-trading/v2/discover-response.json)  
*Result: Found `energy-resource-solar-001` at $0.15/kWh, 30.5 kWh available*

**2. Select** - Consumer selects item and receives quote breakdown.  
Request: [select-request.json](../../../../examples/p2p-trading/v2/select-request.json) | Response: [select-response.json](../../../../examples/p2p-trading/v2/select-response.json)  
*Result: Quote $4.00 ($1.50 energy + $2.50 wheeling)*

**3. Init** - Consumer provides meter IDs (`100200300` → `98765456`), time window, and payment details. BPP may cascade to Utility for load verification and wheeling charges.  
Request: [init-request.json](../../../../examples/p2p-trading/v2/init-request.json) | Response: [init-response.json](../../../../examples/p2p-trading/v2/init-response.json)  
Cascaded Flow: [cascaded-init-request.json](../../../../examples/p2p-trading/v2/cascaded-init-request.json) | [cascaded-on-init-response.json](../../../../examples/p2p-trading/v2/cascaded-on-init-response.json)  
*Result: Order initialized, contract PENDING. Utility BPP responds with wheeling charges in `orderValue.components` and remaining trading limits in `orderAttributes.remainingTradingLimit`.*

**4. Confirm** - Consumer confirms order to activate contract. BPP may cascade to Utility to log the trade and deduct from trading limits.  
Request: [confirm-request.json](../../../../examples/p2p-trading/v2/confirm-request.json) | Response: [confirm-response.json](../../../../examples/p2p-trading/v2/confirm-response.json)  
Cascaded Flow: [cascaded-confirm-request.json](../../../../examples/p2p-trading/v2/cascaded-confirm-request.json) | [cascaded-on-confirm-response.json](../../../../examples/p2p-trading/v2/cascaded-on-confirm-response.json)  
*Result: Contract ACTIVE, settlement cycle `settle-2024-10-04-001` created. Utility BPP logs trade and responds with updated remaining trading limits in `orderAttributes.remainingTradingLimit`.*

**5. Status (In Progress)** - Consumer monitors delivery progress. BPP updates meter readings and telemetry every 15-30 minutes.  
Request: [status-request.json](../../../../examples/p2p-trading/v2/status-request.json) | Response: [status-response.json](../../../../examples/p2p-trading/v2/status-response.json)  
*Result: Delivery IN_PROGRESS, 9.8 kWh delivered (98%), real-time telemetry*

**6. Status (Completed)** - Consumer checks final status after delivery completion.  
Response: [status-response-completed.json](../../../../examples/p2p-trading/v2/status-response-completed.json)  
*Result: Delivery COMPLETED, 10.0 kWh delivered, settlement SETTLED ($4.00)*

**Summary**: Transaction completed in ~8.5 hours. 10.0 kWh delivered. Total cost $4.00. Daily settlement cycle processed.


# 7. Reference Architecture

The section defines the reference ecosystem architecture that is used for building this implementation guide. 

## 7.1. Architecture Diagram


TBD

## 7.2. Actors

1. Prosumers and consumers with smart meters.
2. Beckn One Global Root Registry  
3. Beckn One Catalog Discovery Service  
4. Beckn Application Platforms  
5. Beckn Provider Platforms  
6. Peer to Peer trading Registry

TODO: Explain the role of each entity in detail for P2P trading, and whether they are required or optional and API interface to them.


# 8. Creating an Open Network for Peer to Peer Energy Trading

TODO: move this section into a seperate `../core_spec/` folder, and reference from there in implementation guides of EV charging, P2P tradig etc. 

To create an open network for energy trading requires all the producers, prosumers and consumers BAPs, BPPs, to be able to discover each other and become part of a common club. This club is manifested in the form of a Registry maintained by an NFO. 

## 8.1. Setting up a Registry

The NP Registry serves as the root of addressability and trust for all network participants. It maintains comprehensive details such as the participant’s globally unique identifier (ID), network address (Beckn API URL), public key, operational domains, and assigned role (e.g., BAP, BPP, CDS). In addition to managing participant registration, authentication, authorization, and permission control, the Registry oversees participant verification, activation, and overall lifecycle management, ensuring that only validated and authorized entities can operate within the network.

![](../assets/registry-arch.png)

You can publish your registries at [DeDi.global](https://publish.dedi.global/).

### 8.1.1. For a Network Participant

#### 8.1.1.1. Step 1 :  Claiming a Namespace

To get started, any platform that has implemented Beckn Protocol MUST create a globally unique namespace for themselves.   
All NPs (BAPs, BPPs, CDS’es) **MUST** register as a user on dedi.global and claim a unique namespace against their FQDN to become globally addressable. As part of the claiming process, the user must prove ownership of the namespace by verifying the ownership of their domain. Namespace would be at an organisation level. You can put your organisation name as the name of the namespace.

#### 8.1.1.2. Step 2 :  Setting up a Registry

Once the namespace is claimed, each NP **MUST** create a Beckn NP registry in the namespace to list their subscriber details. While creating the registry, the user **MUST** configure it with the [subscriber schema](https://gist.githubusercontent.com/nirmalnr/a6e5b17522169ecea4f3ccdd831af7e4/raw/7744f2542034db9675901b61b41c8228ea239074/beckn-subscriber-no-refs.schema.json). Example of a registry name can be `subscription-details`.

#### 8.1.1.3. Step 3 :  Publishing subscriber details

In the registry that is created, NPs **MUST** publish their subscription details including their ID, network endpoints, public keys, operational domains and assigned roles (BAP, BPP) as records.

*Detailed steps to create namespaces and registries in dedi.global can be found [here](https://github.com/dedi-global/docs/blob/0976607aabc6641d330a3d41a3bd89ab8790ea09/user-guides/namespace%20and%20registry%20creation.md).*

### 8.1.2. Step 4 :  Share details of the registry created with the Beckn One team

Once the registry is created and details are published, the namespace and the registry name of the newly created registry should be shared with the beckn one team.

### 8.1.3. For a Network facilitator organization

#### 8.1.3.1. Step 1 :  Claiming a Namespace

An NFO **MAY** register as a user on dedi.global and claim a unique namespace against their FQDN. As part of the claiming process, the user must prove ownership of that namespace by verifying the ownership of that domain. The NFO name can be set as the name of the namespace. 
*Note: A calibrated roll out of this infrastructure is planned and hence before it is open to the general public NFOs are advised to share their own domain and the domains of their NPs to the Beckn One team so that they can be whitelisted which will allow the NPs to verify the same using TXT records in their DNS.*

#### 8.1.3.2. Step 2 :  Setting up a Registry

Network facilitators **MAY** create registries under their own namespace using the [subscriber reference schema](https://gist.githubusercontent.com/nirmalnr/a6e5b17522169ecea4f3ccdd831af7e4/raw/b7cf8a47e6531ef22744b43e6305b8d8cc106e7b/beckn-subscriber-reference.schema.json) to point to either whole registries or records created by the NPs in their own namespaces.  Example of a registry name can be `subscription-details`.

#### 8.1.3.3. Step 3 :  Publishing subscriber details

In the registry that is created, NFOs **MAY** publish records which act as pointers to either whole registries or records created by the NPs records. The URL field in the record would be the lookup URL for a registry or a record as per DeDi protocol.

Example: For referencing another registry created by an NP, the record details created would be:

```json
{
  "url": "https://.dedi.global/dedi/lookup/example-company/subscription-details",
  "type": "Registry",
  "subscriber_id": "example-company.com"
}
```

Here `example-company` is the namespace of the NP, and all records added in the registry is referenced here. 

If only one record in the registry needs to be referenced, then the record details created would be:

```json
{
  "url": "https://.dedi.global/dedi/lookup/example-company/subscription-details/energy-bap",
  "type": "Record",
  "subscriber_id": "example-company.com"
}
```

Here `energy-bap` is the name of the record created by the NP in this registry. Only that record is referenced here.

*Detailed steps to create namespaces and registries in dedi.global can be found [here](https://github.com/dedi-global/docs/blob/0976607aabc6641d330a3d41a3bd89ab8790ea09/user-guides/namespace%20and%20registry%20creation.md).*

#### 8.1.3.4. Step 4 :  Share details of the registry created with the Beckn One team

Once the registry is created and details are published, the namespace and the registry name of the newly created registry should be shared with the beckn one team.

## 8.2. Setting up the Protocol Endpoints

This section contains instructions to set up and test the protocol stack for transactions. 

### 8.2.1. Installing Beckn ONIX

All NPs SHOULD install the Beckn ONIX adapter to quickly get set up and become Beckn Protocol compliant. Click [here](https://github.com/Beckn-One/beckn-onix?tab=readme-ov-file#automated-setup-recommended)) to learn how to set up Beckn ONIX.

### 8.2.2. Configuring Beckn ONIX for Peer to Peer Energy Trading

A detailed Configuration Guide is available [here](https://github.com/Beckn-One/beckn-onix/blob/main/CONFIG.md). A quick read of key concepts from the link is recommended.

Specifically, please use the following configuration:
1. Configure dediregistry plugin instead of registry plugin. Read more [here](https://github.com/Beckn-One/beckn-onix/tree/main/pkg/plugin/implementation/dediregistry).
2. Start with using Simplekeymanager plugin during development, read more [here](https://github.com/Beckn-One/beckn-onix/tree/main/pkg/plugin/implementation/simplekeymanager). For production deployment, you may setup vault.
3. For routing calls to Catalog Discovery Service, refer to routing configuration [here](https://github.com/Beckn-One/beckn-onix/blob/main/config/local-simple-routing-BAPCaller.yaml).

### 8.2.3. 10.2.3 Performing a test transaction

Step 1 : Download the postman collection, from [here](/testnet/p2p-energy-trading-devkit/postman).

Step 2 : Run API calls

If you are a BAP

1. Configure the collection/environment variables to the newly installed Beckn ONIX adapter URL and other variables in the collection.
2. Select the discover example and hit send
3. You should see the service catalog response

If you are a BPP

1. Configure the collection/environment variables to the newly installed Beckn ONIX adapter URL and other variables in the collection.
2. Select the on_status example and hit send
3. You should see the response in your console


# 9. Schema overview

Beckn Protocol v2 provides a composable schema architecture that enables:
- **Modular Attribute Bundles**: Energy-specific attributes attached to core Beckn objects
- **JSON-LD Semantics**: Full semantic interoperability
- **Standards Alignment**: Integration with IEEE 2030.5 (mRID), OCPP, OCPI
- **Flexible Discovery**: Meter-based discovery and filtering

## 9.1. v2 Composable Schema Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Core Beckn Objects                    │
│  Item | Offer | Order | Fulfillment | Provider          │
└─────────────────────────────────────────────────────────┘
                        │
                        │ Attach Attributes
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Energy* Attribute Bundles                    │
│  EnergyResource | EnergyTradeOffer | EnergyTradeContract │
│  EnergyTradeDelivery                                     │
└─────────────────────────────────────────────────────────┘
```

## 9.2. Schema Composition Points

| Attribute Bundle        | Attach To                | Purpose                                                                            |
| ----------------------- | ------------------------ | ---------------------------------------------------------------------------------- |
| **EnergyResource**      | `Item.itemAttributes`    | Energy source characteristics (source type, delivery mode, meter ID, availability) |
| **EnergyTradeOffer**    | `Offer.offerAttributes`  | Pricing models, settlement types, wheeling charges, validity windows               |
| **EnergyTradeContract** | `Order.orderAttributes`  | Contract status, meter IDs, settlement cycles, billing cycles                      |
| **EnergyOrderItem**     | `OrderItem.orderItemAttributes`                       | Wrapper containing customerAttributes and optional fulfillmentAttributes |
| **EnergyTradeDelivery** | `EnergyOrderItem.fulfillmentAttributes`               | Per-orderItem delivery status, meter readings with time windows, energy allocation |


## 9.3. EnergyResource (Item.itemAttributes)

**Purpose**: Describes tradable energy resources

**Key Attributes**:
- `sourceType`: SOLAR, BATTERY, GRID, HYBRID, RENEWABLE
- `deliveryMode`: EV_CHARGING, BATTERY_SWAP, V2G, GRID_INJECTION
- `meterId`: IEEE 2030.5 mRID (e.g., `"100200300"`)
- `availableQuantity`: Available energy in kWh
- `productionWindow`: Time window when energy is available
- `sourceVerification`: Verification status and certificates

**Example**:
```json
{
  "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/EnergyResource/v0.2/context.jsonld",
  "@type": "EnergyResource",
  "sourceType": "SOLAR",
  "deliveryMode": "GRID_INJECTION",
  "meterId": "100200300",
  "availableQuantity": 30.5,
  "productionWindow": {
    "start": "2024-10-04T10:00:00Z",
    "end": "2024-10-04T18:00:00Z"
  }
}
```

## 9.4. EnergyTradeOffer (Offer.offerAttributes)

**Purpose**: Defines pricing and settlement terms for energy trades

**Key Attributes**:
- `pricingModel`: PER_KWH, TIME_OF_DAY, SUBSCRIPTION, FIXED
- `settlementType`: REAL_TIME, HOURLY, DAILY, WEEKLY, MONTHLY
- `wheelingCharges`: Utility transmission charges
- `minimumQuantity` / `maximumQuantity`: Tradable quantity limits
- `validityWindow`: Offer validity period
- `timeOfDayRates`: Time-based pricing (for TIME_OF_DAY model)

**Example**:
```json
{
  "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/EnergyTradeOffer/v0.2/context.jsonld",
  "@type": "EnergyTradeOffer",
  "pricingModel": "PER_KWH",
  "settlementType": "DAILY",
  "wheelingCharges": {
    "amount": 2.5,
    "currency": "USD",
    "description": "PG&E Grid Services wheeling charge"
  },
  "minimumQuantity": 1.0,
  "maximumQuantity": 100.0
}
```

## 9.5. EnergyTradeContract (Order.orderAttributes)

**Purpose**: Tracks commercial agreements and contract lifecycle

**Key Attributes**:
- `contractStatus`: PENDING, ACTIVE, COMPLETED, TERMINATED
- `sourceMeterId` / `targetMeterId`: IEEE 2030.5 mRID
- `contractedQuantity`: Contracted energy in kWh
- `tradeStartTime` / `tradeEndTime`: Contract time window
- `settlementCycles`: Array of settlement periods
- `billingCycles`: Array of billing periods
- `wheelingCharges`: Utility charges breakdown

**Example**:
```json
{
  "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/EnergyTradeContract/v0.2/context.jsonld",
  "@type": "EnergyTradeContract",
  "contractStatus": "ACTIVE",
  "sourceMeterId": "100200300",
  "targetMeterId": "98765456",
  "contractedQuantity": 10.0,
  "settlementCycles": [...],
  "billingCycles": [...]
}
```

## 9.6. EnergyOrderItem (OrderItem.orderItemAttributes)

**Purpose**: Wrapper schema for per-orderItem attributes containing customer information and optional fulfillment tracking

**Location**: `beckn:orderItemAttributes`

**Key Attributes**:
- `customerAttributes`: Contains EnergyCustomer schema with customer meter and utility info (always required)
- `fulfillmentAttributes`: Contains EnergyTradeDelivery schema with delivery tracking (only in on_status/on_update)

**Example**:
```json
{
  "beckn:orderItemAttributes": {
    "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
    "@type": "EnergyOrderItem",
    "customerAttributes": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
      "@type": "EnergyCustomer",
      "meterId": "der://meter/98765456",
      "utilityCustomerId": "UTIL-CUST-123456"
    },
    "fulfillmentAttributes": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
      "@type": "EnergyTradeDelivery",
      "deliveryStatus": "IN_PROGRESS",
      "deliveryMode": "GRID_INJECTION",
      "deliveredQuantity": 7.5,
      "meterReadings": [...],
      "lastUpdated": "2024-10-04T15:00:00Z"
    }
  }
}
```

## 9.7. EnergyTradeDelivery (EnergyOrderItem.fulfillmentAttributes)

**Purpose**: Tracks physical energy transfer and delivery status per orderItem

**Location**: Nested within `beckn:orderItemAttributes.fulfillmentAttributes` (not at top-level Order)

**When Populated**: Only in `on_status` and `on_update` responses. NOT present in init/confirm flows.

**Key Attributes**:
- `deliveryStatus`: PENDING, IN_PROGRESS, COMPLETED, FAILED
- `deliveryMode`: EV_CHARGING, BATTERY_SWAP, V2G, GRID_INJECTION
- `deliveredQuantity`: Total quantity delivered so far in kWh
- `meterReadings`: Array of meter readings with time windows (see below)
- `curtailedQuantity`: Optional, quantity curtailed from contract (kWh)
- `curtailmentReason`: Optional, reason code (GRID_OUTAGE, EMERGENCY, CONGESTION, MAINTENANCE, OTHER)
- `lastUpdated`: UTC timestamp of last update

**Meter Readings Structure** (IEC 61968/ESPI compliant):
```json
{
  "beckn:timeWindow": {
    "@type": "beckn:TimePeriod",
    "schema:startTime": "2024-10-04T06:00:00Z",
    "schema:endTime": "2024-10-04T09:00:00Z"
  },
  "deliveredEnergy": 0.0,     // Energy TO customer (imported from grid) - ESPI flowDirection=1
  "receivedEnergy": 7.5,      // Energy FROM customer (exported to grid) - ESPI flowDirection=19
  "allocatedEnergy": 7.5,     // Net energy allocated for this trade
  "unit": "kWh"
}
```

**Example** (within EnergyOrderItem.fulfillmentAttributes):
```json
{
  "beckn:orderItemAttributes": {
    "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
    "@type": "EnergyOrderItem",
    "customerAttributes": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
      "@type": "EnergyCustomer",
      "meterId": "der://meter/98765456",
      "utilityCustomerId": "UTIL-CUST-123456"
    },
    "fulfillmentAttributes": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
      "@type": "EnergyTradeDelivery",
      "deliveryStatus": "IN_PROGRESS",
      "deliveryMode": "GRID_INJECTION",
      "deliveredQuantity": 7.5,
      "meterReadings": [
        {
          "beckn:timeWindow": {
            "@type": "beckn:TimePeriod",
            "schema:startTime": "2024-10-04T06:00:00Z",
            "schema:endTime": "2024-10-04T09:00:00Z"
          },
          "deliveredEnergy": 0.0,
          "receivedEnergy": 7.5,
          "allocatedEnergy": 7.5,
          "unit": "kWh"
        }
      ],
      "lastUpdated": "2024-10-04T15:00:00Z"
    }
  }
}
```

**Note**: Top-level `beckn:fulfillment` is no longer used for energy delivery tracking. Each orderItem tracks its own fulfillment independently via `fulfillmentAttributes`.


# 10. API Reference & examples

## 10.1. Discover flow

**Purpose**: Search for available energy resources

**Endpoint**: `POST /discover`

**v1 to v2 Mapping**:
- v1 `message.intent.item.quantity.selected.measure` → v2 `message.filters.expression` (JSONPath filter on `availableQuantity`)
- v1 `message.intent.fulfillment.stops[].time.range.start` → v2 `message.filters.expression` (JSONPath filter on `productionWindow.start`)
- v1 `message.intent.fulfillment.stops[].time.range.end` → v2 `message.filters.expression` (JSONPath filter on `productionWindow.end`)
- **Note**: v2 does not support `intent` object. All search parameters are expressed via JSONPath filters.

<details>
<summary><a href="../../../../examples/p2p-trading/v2/discover-request.json">Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "timestamp": "2024-10-04T10:00:00Z",
    "message_id": "msg-discover-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0",
    "location": {
      "city": {
        "code": "BLR",
        "name": "Bangalore"
      },
      "country": {
        "code": "IND",
        "name": "India"
      }
    },
    "schema_context": [
      "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyResource/v0.2/context.jsonld"
    ]
  },
  "message": {
    "filters": {
      "type": "jsonpath",
      "expression": "$[?(@.beckn:itemAttributes.sourceType == 'SOLAR' && @.beckn:itemAttributes.deliveryMode == 'GRID_INJECTION' && @.beckn:itemAttributes.availableQuantity >= 10.0 )]",
      "expressionType": "jsonpath"
    }
  }
}

```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>


<details>
<summary><a href="../../../../examples/p2p-trading/v2/discover-response.json">Async Response Example: `on_discover`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_discover",
    "timestamp": "2024-10-04T10:00:05Z",
    "message_id": "msg-on-discover-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "catalogs": [
      {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Catalog",
        "beckn:id": "catalog-energy-001",
        "beckn:bppId": "bpp.energy-provider.com",
        "beckn:bppUri": "https://bpp.energy-provider.com",
        "beckn:descriptor": {
          "@type": "beckn:Descriptor",
          "schema:name": "Solar Energy Trading Catalog"
        },
        "beckn:items": [
          {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Item",
            "beckn:id": "energy-resource-solar-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Solar Energy - 30.5 kWh"
            },
            "beckn:provider": {
              "beckn:id": "provider-solar-farm-001",
              "beckn:descriptor": {
                "@type": "beckn:Descriptor",
                "schema:name": "Solar Farm 001"
              }
            },
            "beckn:itemAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyResource/v0.2/context.jsonld",
              "@type": "EnergyResource",
              "sourceType": "SOLAR",
              "deliveryMode": "GRID_INJECTION",
              "certificationStatus": "Carbon Offset Certified",
              "meterId": "der://meter/100200300",
              "availableQuantity": 30.5,
              "productionWindow": [
                {
                  "@type": "beckn:TimePeriod",
                  "schema:startTime": "2026-01-09T10:00:00Z",
                  "schema:endTime": "2026-01-09T18:00:00Z"
                }
              ],
              "sourceVerification": {
                "verified": true,
                "verificationDate": "2024-09-01T00:00:00Z",
                "certificates": [
                  "https://example.com/certs/solar-panel-cert.pdf"
                ]
              },
              "productionAsynchronous": true
            }
          }
        ],
        "beckn:offers": [
          {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:id": "offer-morning-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer - 6am-12pm"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "wheelingCharges": {
                "amount": 2.5,
                "currency": "USD",
                "description": "PG&E Grid Services wheeling charge"
              },
              "minimumQuantity": 1.0,
              "maximumQuantity": 100.0,
              "validityWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T00:00:00Z",
                "schema:endTime": "2026-01-09T23:59:59Z"
              },
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          },
          {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:id": "offer-afternoon-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer - 12pm-6pm"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "wheelingCharges": {
                "amount": 2.5,
                "currency": "USD",
                "description": "PG&E Grid Services wheeling charge"
              },
              "minimumQuantity": 1.0,
              "maximumQuantity": 100.0,
              "validityWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T00:00:00Z",
                "schema:endTime": "2026-01-09T23:59:59Z"
              },
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        ]
      }
    ]
  }
}

```
</details>

**Key Points**:
- **No Intent Object**: v2 does not support `intent` object in discover requests. All search parameters are expressed via JSONPath filters.
- **Quantity Filter**: Filter by `itemAttributes.availableQuantity >= 10.0` in JSONPath expression
- **Time Range Filter**: Filter by `productionWindow.start` and `productionWindow.end` to match desired trade time window
  - `productionWindow.start <= '2024-10-04T10:00:00Z'` - Energy available from start time or earlier
  - `productionWindow.end >= '2024-10-04T18:00:00Z'` - Energy available until end time or later
- **JSONPath Filters**: Use JSONPath filters to search by `itemAttributes.sourceType`, `itemAttributes.deliveryMode`, `itemAttributes.availableQuantity`, and `itemAttributes.productionWindow`
- **Response**: Includes full Item with EnergyResource attributes and Offer with EnergyTradeOffer attributes

## 10.2. Select Flow

**Purpose**: Select items and offers to build an order

**Endpoint**: `POST /select`

<details>
<summary><a href="../../../../examples/p2p-trading/v2/select-request.json">Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "select",
    "timestamp": "2024-10-04T10:15:00Z",
    "message_id": "msg-select-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-placeholder",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer"
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          }
        }
      ]
    }
  }
}

```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/select-response.json">Asynchronous Response Example: `on_select`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_select",
    "timestamp": "2024-10-04T10:15:05Z",
    "message_id": "msg-on-select-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-placeholder",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer"
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ]
    }
  }
}

```
</details>

**Key Points**:
- Select items by `beckn:id` and specify quantity
- Select offers by `beckn:id`
- Response includes priced quote with breakup

## 10.3. Init Flow

**Purpose**: Initialize order with fulfillment and payment details

**Endpoint**: `POST /init`

**v1 to v2 Mapping**:
- v1 `Order.fulfillments[].stops[].time.range` → v2 `Order.fulfillments[].stops[].time.range` (same structure)
- v1 `Order.fulfillments[].stops[].location.address` (der:// format) → v2 `Order.fulfillments[].stops[].location.address` (IEEE mRID format)
- v1 `Order.attributes.*` → v2 `Order.orderAttributes.*` (path change)

<details>
<summary><a href="../../../../examples/p2p-trading/v2/init-request.json">Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "init",
    "timestamp": "2024-10-04T10:20:00Z",
    "message_id": "msg-init-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "bap.energy-consumer.com",
        "bpp_id": "bpp.energy-provider.com",
        "total_quantity": 25.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/init-response.json">Asynchronous Response Example: `on_init`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_init",
    "timestamp": "2024-10-04T10:20:05Z",
    "message_id": "msg-on-init-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "bap.energy-consumer.com",
        "bpp_id": "bpp.energy-provider.com",
        "total_quantity": 25.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

**Key Points**:
- **Fulfillment Stops**: Must include START and END stops (same as v1)
- **Time Range**: Include `beckn:time.range` in stops to specify delivery time window (same as v1)
- **Meter IDs**: Use IEEE mRID format (`"100200300"`) instead of v1's `der://` format (`"der://pge.meter/100200300"`)
- **Response**: Includes EnergyTradeContract attributes with PENDING status

## 10.4. Confirm Flow

**Purpose**: Confirm and activate the order

**Endpoint**: `POST /confirm`

### 10.4.1. Cascaded Init Example (Utility Registration)

This flow demonstrates the cascaded `/init` call from the P2P Trading BPP to the Utility Company (Transmission BPP) to register the trade and calculate wheeling charges.

**Request Flow**: P2P Trading BPP sends a cascaded `init` request to the Utility BPP with the order details (items, offers, fulfillments, payments).

**Response Flow**: Utility BPP responds with `on_init` containing:
- **Wheeling charges**: Provided in `orderValue` with breakdown in `components` array (type: `FEE`)
- **Remaining trading limits**: Provided in `orderAttributes.remainingTradingLimit` including:
  - `remainingQuantity`: Remaining tradable quantity in kWh
  - `sanctionedLoad`: Breakdown of total, used, and remaining sanctioned load
  - `validUntil`: Validity timestamp for the limit information

<details>
<summary><a href="../../../../examples/p2p-trading/v2/cascaded-init-request.json">Cascaded Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "init",
    "timestamp": "2024-10-04T10:20:00Z",
    "message_id": "msg-cascaded-init-001",
    "transaction_id": "txn-cascaded-energy-001",
    "bap_id": "p2pTrading-bpp.com",
    "bap_uri": "https://api.p2pTrading-bpp.com/pilot/bap/energy/v2",
    "bpp_id": "example-transmission-bpp.com",
    "bpp_uri": "https://api.example-transmission-bpp.com/pilot/bpp/",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "p2pTrading-bpp.com",
        "bpp_id": "example-transmission-bpp.com",
        "total_quantity": 15.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/cascaded-on-init-response.json">Cascaded asynchronous Response Example: `on_init`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_init",
    "timestamp": "2024-10-04T10:20:05Z",
    "message_id": "msg-cascaded-on-init-001",
    "transaction_id": "txn-cascaded-energy-001",
    "bap_id": "p2pTrading-bpp.com",
    "bap_uri": "https://api.p2pTrading-bpp.com/pilot/bap/energy/v2",
    "bpp_id": "example-transmission-bpp.com",
    "bpp_uri": "https://api.example-transmission-bpp.com/pilot/bpp/",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "p2pTrading-bpp.com",
        "bpp_id": "example-transmission-bpp.com",
        "total_quantity": 15.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

## 10.5. Confirm Flow

**Purpose**: Confirm and activate the order

**Endpoint**: `POST /confirm`

<details>
<summary><a href="../../../../examples/p2p-trading/v2/confirm-request.json">Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "timestamp": "2024-10-04T10:25:00Z",
    "message_id": "msg-confirm-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "bap.energy-consumer.com",
        "bpp_id": "bpp.energy-provider.com",
        "total_quantity": 25.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/confirm-response.json">Asynchronous Response Example: `on_confirm`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_confirm",
    "timestamp": "2024-10-04T10:25:05Z",
    "message_id": "msg-on-confirm-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-energy-001",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "bap.energy-consumer.com",
        "bpp_id": "bpp.energy-provider.com",
        "total_quantity": 25.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

**Key Points**:
- Contract status changes from PENDING to ACTIVE
- Settlement cycle is initialized
- Order is now active and ready for fulfillment

### 10.5.1. Cascaded Confirm Example (Utility Trade Logging)

This flow demonstrates the cascaded `/confirm` call from the P2P Trading BPP to the Utility Company (Transmission BPP) to log the trade and deduct from trading limits.

**Request Flow**: P2P Trading BPP sends a cascaded `confirm` request to the Utility BPP with the order details to finalize the trade registration.

**Response Flow**: Utility BPP responds with `on_confirm` containing:
- **Contract activation**: Contract status set to `ACTIVE` in `orderAttributes.contractStatus`
- **Settlement cycle**: Initialized settlement cycle in `orderAttributes.settlementCycles`
- **Updated remaining trading limits**: Provided in `orderAttributes.remainingTradingLimit` with:
  - `remainingQuantity`: Updated remaining tradable quantity (reduced by the contracted quantity)
  - `sanctionedLoad`: Updated breakdown showing increased `used` and reduced `remaining` values after trade is logged
  - `validUntil`: Validity timestamp for the limit information

<details>
<summary><a href="../../../../examples/p2p-trading/v2/cascaded-confirm-request.json">Cascaded Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "timestamp": "2024-10-04T10:25:00Z",
    "message_id": "msg-cascaded-confirm-001",
    "transaction_id": "txn-cascaded-energy-001",
    "bap_id": "p2pTrading-bpp.com",
    "bap_uri": "https://api.p2pTrading-bpp.com/pilot/bap/energy/v2",
    "bpp_id": "example-transmission-bpp.com",
    "bpp_uri": "https://api.example-transmission-bpp.com/pilot/bpp/",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "p2pTrading-bpp.com",
        "bpp_id": "example-transmission-bpp.com",
        "total_quantity": 15.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/cascaded-on-confirm-response.json">Cascaded asynchronous Response Example: `on_confirm`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_confirm",
    "timestamp": "2024-10-04T10:25:05Z",
    "message_id": "msg-cascaded-on-confirm-001",
    "transaction_id": "txn-cascaded-energy-001",
    "bap_id": "p2pTrading-bpp.com",
    "bap_uri": "https://api.p2pTrading-bpp.com/pilot/bap/energy/v2",
    "bpp_id": "example-transmission-bpp.com",
    "bpp_uri": "https://api.example-transmission-bpp.com/pilot/bpp/",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-cascaded-utility-001",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
                "@type": "beckn:Buyer"
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOrder/v0.2/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "p2pTrading-bpp.com",
        "bpp_id": "example-transmission-bpp.com",
        "total_quantity": 15.0
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ],
      "beckn:fulfillment": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Fulfillment",
        "beckn:id": "fulfillment-energy-001",
        "beckn:mode": "DELIVERY"
      }
    }
  }
}

```
</details>

## 10.6. Status Flow

**Purpose**: Query order and delivery status

**Endpoint**: `POST /status`

<details>
<summary><a href="../../../../examples/p2p-trading/v2/status-request.json">Request Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "status",
    "timestamp": "2024-10-04T15:00:00Z",
    "message_id": "msg-status-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "beckn:id": "order-energy-001"
    }
  }
}
```
</details>

<details><summary>Immediate successful Response</summary>

```json
{
  "ack_status": "ACK",
  "timestamp": "2025-10-14T07:31:05Z"
}
```
</details>

<details>
<summary><a href="../../../../examples/p2p-trading/v2/status-response.json">Asynchronous Response Example: `on_status`</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "timestamp": "2024-10-04T15:00:05Z",
    "message_id": "msg-on-status-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-energy-001",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer"
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            },
            "fulfillmentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
              "@type": "EnergyTradeDelivery",
              "deliveryStatus": "IN_PROGRESS",
              "deliveryMode": "GRID_INJECTION",
              "deliveredQuantity": 7.5,
              "meterReadings": [
                {
                  "beckn:timeWindow": {
                    "@type": "beckn:TimePeriod",
                    "schema:startTime": "2024-10-04T06:00:00Z",
                    "schema:endTime": "2024-10-04T09:00:00Z"
                  },
                  "deliveredEnergy": 0.0,
                  "receivedEnergy": 7.5,
                  "allocatedEnergy": 7.5,
                  "unit": "kWh"
                }
              ],
              "lastUpdated": "2024-10-04T15:00:00Z"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            },
            "fulfillmentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
              "@type": "EnergyTradeDelivery",
              "deliveryStatus": "PENDING",
              "deliveryMode": "GRID_INJECTION",
              "deliveredQuantity": 0.0,
              "meterReadings": [],
              "lastUpdated": "2024-10-04T15:00:00Z"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ]
    }
  }
}

```
</details>

**Key Points**:
- Response includes EnergyTradeContract attributes (contract status)
- Response includes EnergyTradeDelivery attributes (delivery status, meter readings, telemetry)
- Meter readings show energy flow from source to target
- Telemetry provides real-time energy metrics

### 10.6.1. Curtailed Trade Status

When a trade has been curtailed (e.g., due to grid outage), the status response includes curtailment information for payment reconciliation:

<details>
<summary><a href="../../../../examples/p2p-trading/v2/status-response-curtailed.json">Curtailed Status Response Example</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "timestamp": "2024-10-04T16:00:00Z",
    "message_id": "msg-on-status-curtailed-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-energy-001",
      "beckn:orderStatus": "PARTIALLYFULFILLED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer"
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            },
            "fulfillmentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
              "@type": "EnergyTradeDelivery",
              "deliveryStatus": "COMPLETED",
              "deliveryMode": "GRID_INJECTION",
              "deliveredQuantity": 10.0,
              "curtailedQuantity": 5.0,
              "curtailmentReason": "GRID_OUTAGE",
              "meterReadings": [
                {
                  "beckn:timeWindow": {
                    "@type": "beckn:TimePeriod",
                    "schema:startTime": "2024-10-04T06:00:00Z",
                    "schema:endTime": "2024-10-04T14:30:00Z"
                  },
                  "deliveredEnergy": 0.0,
                  "receivedEnergy": 10.0,
                  "allocatedEnergy": 10.0,
                  "unit": "kWh"
                }
              ],
              "lastUpdated": "2024-10-04T14:30:00Z"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        },
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 10.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            },
            "fulfillmentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
              "@type": "EnergyTradeDelivery",
              "deliveryStatus": "FAILED",
              "deliveryMode": "GRID_INJECTION",
              "deliveredQuantity": 0.0,
              "curtailedQuantity": 10.0,
              "curtailmentReason": "GRID_OUTAGE",
              "meterReadings": [],
              "lastUpdated": "2024-10-04T14:30:00Z"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-afternoon-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Afternoon Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.18,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 15.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T12:00:00Z",
                "schema:endTime": "2026-01-09T18:00:00Z"
              }
            }
          }
        }
      ]
    }
  }
}

```
</details>

**Curtailment Fields for Payment Reconciliation**:
- `curtailedQuantity`: Revised trade limit (kWh) - the billable quantity
- `curtailmentReason`: Why curtailment occurred (`GRID_OUTAGE`, `EMERGENCY`, `CONGESTION`, `MAINTENANCE`, `OTHER`)
- `curtailmentTime`: When the curtailment was issued

**Payment Calculation**:
- Original contracted: `orderItems[].quantity`
- Actually delivered: `deliveredQuantity`
- Billable amount: `min(deliveredQuantity, curtailedQuantity) × price`

## 10.7. Update Flow (Provider-Initiated)

**Purpose**: Notify BAP of changes to an active order initiated by the provider (BPP) or utility

**Endpoint**: `POST /on_update` (unsolicited callback from BPP to BAP)

In Beckn protocol, `on_update` can be sent **without a preceding `update` request** from BAP. This is the standard "push notification" pattern for provider-initiated changes such as:
- Trade curtailment due to grid outages
- Delivery interruptions
- Settlement adjustments

### 10.7.1. Utility-Initiated Trade Curtailment

During active energy delivery, grid operators may need to curtail trades due to:
- **Grid outages**: Unexpected failures requiring immediate load reduction
- **Emergency conditions**: Frequency deviations, voltage issues
- **Congestion**: Transmission capacity limits
- **Scheduled maintenance**: Planned outages

When this happens, the Utility Company sends an unsolicited `on_update` to the BPP, which forwards it to the BAP. This enables both parties to reconcile payments based on the revised trade quantity.

```mermaid
sequenceDiagram
    participant Utility as Utility Grid Operator
    participant BPP as P2P Trading BPP
    participant BAP as P2P Trading BAP
    
    Note over Utility: Grid outage detected
    Utility->>BPP: on_update (curtailment notification)
    Note right of BPP: curtailedQuantity: 10kWh<br/>curtailmentReason: GRID_OUTAGE
    BPP->>BAP: on_update (forwarded)
    Note over BAP: Update UI, adjust payment
```

<details>
<summary><a href="../../../../examples/p2p-trading/v2/on-update-response-curtailment.json">Curtailment Notification Example (`on_update`)</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "timestamp": "2024-10-04T14:30:00Z",
    "message_id": "msg-on-update-curtailment-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "ttl": "PT30S",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-energy-001",
      "beckn:orderStatus": "INPROGRESS",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "beckn:id": "buyer-001",
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer"
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyOrderItem/v0.1/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyCustomer/v0.1/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/98765456",
              "utilityCustomerId": "UTIL-CUST-123456"
            },
            "fulfillmentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeDelivery/v0.2/context.jsonld",
              "@type": "EnergyTradeDelivery",
              "deliveryStatus": "IN_PROGRESS",
              "deliveryMode": "GRID_INJECTION",
              "deliveredQuantity": 8.5,
              "curtailedQuantity": 6.5,
              "curtailmentReason": "GRID_OUTAGE",
              "meterReadings": [
                {
                  "beckn:timeWindow": {
                    "@type": "beckn:TimePeriod",
                    "schema:startTime": "2024-10-04T06:00:00Z",
                    "schema:endTime": "2024-10-04T12:00:00Z"
                  },
                  "deliveredEnergy": 0.0,
                  "receivedEnergy": 8.5,
                  "allocatedEnergy": 8.5,
                  "unit": "kWh"
                }
              ],
              "lastUpdated": "2024-10-04T14:30:00Z"
            }
          },
          "beckn:acceptedOffer": {
            "beckn:id": "offer-morning-001",
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/main/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": [
              "energy-resource-solar-001"
            ],
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-new/refs/heads/p2p-trading/schema/EnergyTradeOffer/v0.2/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "settlementType": "DAILY",
              "sourceMeterId": "der://meter/100200300",
              "beckn:price": {
                "value": 0.15,
                "currency": "USD",
                "unitText": "kWh"
              },
              "beckn:maxQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh",
                "unitCode": "KWH"
              },
              "beckn:timeWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              }
            }
          }
        }
      ]
    }
  }
}

```
</details>

**Key Points**:
- `on_update` is **unsolicited** - no preceding `update` request needed
- Contains `curtailedQuantity` for payment reconciliation
- `curtailmentReason` provides audit trail for dispute resolution
- BAP should update UI and adjust pending payment based on revised quantity


# 11. Additional Resources

1. **Beckn 1.0 to 2.0 field mapping**: See `./v1_to_v2_field_mapping.md`
2. **Taxonomy Reference**: See `./taxonomy.md`
3. **Solar Energy Discovery**: Search for solar energy with grid injection delivery
4. **Daily Settlement**: Contract with daily settlement cycle
5. **Meter-Based Tracking**: Track energy flow using meter readings
6. **Telemetry Monitoring**: Monitor energy delivery with real-time telemetry

---

## 11.1. Inter energy retailer P2P trading 
This is a specific scenario of P2P trading where the participants come under differnet energy retailers and distribution utilities and engages in direct energy trade. Here, nuances of financial settlement, dispute resolution, energy accounting etc will have to be thought through without affecting ease of participation. More information can be found here [Inter-retailer P2P energy trading](/docs/implementation-guides/v2/P2P_Trading/Inter_energy_retailer_P2P_trading_draft.md)

# 12. Additional Resources

- **Field Mapping**: See `docs/v1_to_v2_field_mapping.md`
- **Taxonomy Reference**: See `docs/TAXONOMY.md`
- **Schema Definitions**: See `schema/Energy*/v0.2/attributes.yaml`
- **Context Files**: See `schema/Energy*/v0.2/context.jsonld`
- **Profile Configuration**: See `schema/EnergyResource/v0.2/profile.json`

### 12.0.1. **Integrating with your software**

This section gives a general walkthrough of how you would integrate your software with the Beckn network (say the sandbox environment). Refer to the starter kit for details on how to register with the sandbox and get credentials.

Beckn-ONIX is an initiative to promote easy installation and maintenance of a Beckn Network. Apart from the Registry and Gateway components that are required for a network facilitator, Beckn-ONIX provides a Beckn Adapter. A reference implementation of the Beckn-ONIX specification is available at [Beckn-ONIX repository](https://github.com/beckn/beckn-onix). The reference implementation of the Beckn Adapter is called the Protocol Server. Based on whether we are writing the seeker platform or the provider platform, we will be installing the BAP Protocol Server or the BPP Protocol Server respectively.

TODO

#### 12.0.1.1. **Integrating the BAP**

If you are writing the seeker platform software, the following are the steps you can follow to build and integrate your application.

1. **Discovery**: Use JSONPath filters to search by energy attributes (sourceType, deliveryMode, availableQuantity, productionWindow)
2. **Order Management**: Track order state through PENDING → ACTIVE → COMPLETED
3. **Status Polling**: Poll status endpoint every 15-30 minutes during active delivery
4. **Error Handling**: Handle cases where delivery fails or quantities don't match
5. **Settlement**: Monitor settlement cycle status for payment processing

TODO

#### 12.0.1.2. **Integrating the BPP**

If you are writing the provider platform software, the following are the steps you can follow to build and integrate your application.

6. **Catalog Management**: Keep catalog updated with available energy and accurate production windows
7. **Meter Readings**: Update meter readings regularly during delivery (every 15-30 minutes)
8. **Telemetry**: Provide real-time telemetry data for monitoring
9. **Settlement**: Calculate settlement amounts based on delivered quantity and pricing model
10. **State Management**: Properly transition contract and delivery statuses

TODO

## 12.1. FAQs

## 12.2. References

* [Postman collection for EV Charging](/testnet/ev-charging-devkit/postman/)  
* [Beckn 1.0 (legacy) Layer2 config for peer to peer trading](https://github.com/beckn/missions/blob/main/DEG2.0/layer2/P2P/trade_1.1.0.yaml)

