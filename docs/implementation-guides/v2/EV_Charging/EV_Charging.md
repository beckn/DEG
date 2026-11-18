Implementation Guide \- EV Charging \- Version 0.8 (DRAFT) <!-- omit from toc -->
==========================================================

> **Status:** The examples in this guide use the Beckn 2.0 LTS core specification (`core-v2.0.0-lts`): the order is a `contract` (`commitments`, `consideration`, `settlements`, `performance`, `participants`) and the EV charging data is carried in attribute packs. The [EV charging examples README](../../../../examples/ev-charging/v2/README.md) has the conventions, the pack used in each slot and the field map from the earlier shape. Examples in the earlier `core-2.0.0-rc-eos-release` shape (`message.order`) are kept in [examples/ev-charging/v2-rc](../../../../examples/ev-charging/v2-rc).

## Table of Contents <!-- omit from toc -->

- [1. Request for Comments](#1-request-for-comments)
- [2. Copyright Notice](#2-copyright-notice)
- [3. Status of This Memo](#3-status-of-this-memo)
- [4. Abstract](#4-abstract)
- [5. Introduction](#5-introduction)
- [6. Scope](#6-scope)
- [7. Intended Audience](#7-intended-audience)
- [8. Conventions and Terminology](#8-conventions-and-terminology)
- [9. Terminology](#9-terminology)
- [10. Reference Architecture](#10-reference-architecture)
  - [10.1. Architecture Diagram](#101-architecture-diagram)
  - [10.2. Actors](#102-actors)
- [11. Creating an Open Network for EV Charging](#11-creating-an-open-network-for-ev-charging)
  - [11.1. Setting up a Registry](#111-setting-up-a-registry)
    - [11.1.1. For a Network Participant](#1111-for-a-network-participant)
      - [11.1.1.1. Step 1 :  Claiming a Namespace](#11111-step-1---claiming-a-namespace)
      - [11.1.1.2. Step 2 :  Setting up a Registry](#11112-step-2---setting-up-a-registry)
      - [11.1.1.3. Step 3 :  Publishing subscriber details](#11113-step-3---publishing-subscriber-details)
    - [11.1.2. Step 4 :  Share details of the registry created with the Beckn One team](#1112-step-4---share-details-of-the-registry-created-with-the-beckn-one-team)
    - [11.1.3. For a Network facilitator organization](#1113-for-a-network-facilitator-organization)
      - [11.1.3.1. Step 1 :  Claiming a Namespace](#11131-step-1---claiming-a-namespace)
      - [11.1.3.2. Step 2 :  Setting up a Registry](#11132-step-2---setting-up-a-registry)
      - [11.1.3.3. Step 3 :  Publishing subscriber details](#11133-step-3---publishing-subscriber-details)
      - [11.1.3.4. Step 4 :  Share details of the registry created with the Beckn One team](#11134-step-4---share-details-of-the-registry-created-with-the-beckn-one-team)
  - [11.2. Setting up the Protocol Endpoints](#112-setting-up-the-protocol-endpoints)
    - [11.2.1. Installing Beckn ONIX](#1121-installing-beckn-onix)
    - [11.2.2. Configuring Beckn ONIX for EV Charging Transactions](#1122-configuring-beckn-onix-for-ev-charging-transactions)
    - [11.2.3. 10.2.3 Performing a test EV charging transaction](#1123-1023-performing-a-test-ev-charging-transaction)
- [12. Implementing EV Charging Semantics on Beckn Protocol](#12-implementing-ev-charging-semantics-on-beckn-protocol)
  - [12.1. Key Assumptions](#121-key-assumptions)
  - [12.2. Semantic Model](#122-semantic-model)
  - [12.3. Example Category Codes](#123-example-category-codes)
- [13. Example Workflows (EV User’s Perspective)](#13-example-workflows-ev-users-perspective)
  - [13.1. Example 1 - Walk-In to a charging station without reservation.](#131-example-1---walk-in-to-a-charging-station-without-reservation)
    - [13.1.1. Consumer User Journey](#1311-consumer-user-journey)
    - [13.1.2. **API Calls and Schema**](#1312-api-calls-and-schema)
      - [13.1.2.1. `action: discover`](#13121-action-discover)
      - [13.1.2.2. `action: on_discover`](#13122-action-on_discover)
      - [13.1.2.3. `action: select`](#13123-action-select)
      - [13.1.2.4. `action: on_select`](#13124-action-on_select)
      - [13.1.2.5. `action: init`](#13125-action-init)
      - [13.1.2.6. `action: on_init`](#13126-action-on_init)
      - [13.1.2.7. 13.1.2.6.1 `action: on_status`](#13127-131261-action-on_status)
      - [13.1.2.8. `action: confirm`](#13128-action-confirm)
      - [13.1.2.9. `action: on_confirm`](#13129-action-on_confirm)
      - [13.1.2.10. `action: status`](#131210-action-status)
      - [13.1.2.11. `action: on_status`](#131211-action-on_status)
      - [13.1.2.12. `action: update` (start charging)](#131212-action-update-start-charging)
      - [13.1.2.13. `action: on_update` (start charging)](#131213-action-on_update-start-charging)
      - [13.1.2.14. `action: status` (charging-session progress)](#131214-action-status-charging-session-progress)
      - [13.1.2.15. `action: on_status`](#131215-action-on_status)
      - [13.1.2.16. async `action: on_status`](#131216-async-action-on_status)
      - [13.1.2.17. `action: on_update` (stop-charging)](#131217-action-on_update-stop-charging)
      - [13.1.2.18. async `action: on_update` (stop-charging)](#131218-async-action-on_update-stop-charging)
      - [13.1.2.19. `action: rating`](#131219-action-rating)
      - [13.1.2.20. `action: on_rating`](#131220-action-on_rating)
      - [13.1.2.21. `action: support`](#131221-action-support)
      - [13.1.2.22. `action: on_support`](#131222-action-on_support)
  - [13.2. Use case 2- Reservation of an EV charging time slot.](#132-use-case-2--reservation-of-an-ev-charging-time-slot)
      - [13.2.0.1. Context:](#13201-context)
      - [13.2.0.2. Discovery](#13202-discovery)
        - [13.2.0.2.1. Adam discovers nearby charging services](#132021-adam-discovers-nearby-charging-services)
      - [13.2.0.3. Order (Reservation)](#13203-order-reservation)
      - [13.2.0.4. Fulfilment (Session Start \& Tracking)](#13204-fulfilment-session-start--tracking)
      - [13.2.0.5. Post-Fulfilment](#13205-post-fulfilment)
    - [13.2.1. **API Calls and Schema**](#1321-api-calls-and-schema)
      - [13.2.1.1. `action: discover`](#13211-action-discover)
        - [13.2.1.1.1. Discovery of EV charging services within a circular boundary](#132111-discovery-of-ev-charging-services-within-a-circular-boundary)
        - [13.2.1.1.2. Discovery within circle + connector specs as filters](#132112-discovery-within-circle--connector-specs-as-filters)
        - [13.2.1.1.3. Discovery within circle + vehicle specifications as filters](#132113-discovery-within-circle--vehicle-specifications-as-filters)
        - [13.2.1.1.4. Discovery of services offered by a specific CPO](#132114-discovery-of-services-offered-by-a-specific-cpo)
        - [13.2.1.1.5. Viewing details of a single charging station (by its Item Identifier)](#132115-viewing-details-of-a-single-charging-station-by-its-item-identifier)
        - [13.2.1.1.6. Fetching details of a specific charger (EVSE) on-site (by its EVSE identifier)](#132116-fetching-details-of-a-specific-charger-evse-on-site-by-its-evse-identifier)
        - [13.2.1.1.7. Discovering chargers in a specific circular area, a specific connector type and availability time range](#132117-discovering-chargers-in-a-specific-circular-area-a-specific-connector-type-and-availability-time-range)
      - [13.2.1.2. `action: on_discover`](#13212-action-on_discover)
        - [13.2.1.2.1. Offers as part of the Catalog](#132121-offers-as-part-of-the-catalog)
      - [13.2.1.3. `action: select`](#13213-action-select)
      - [13.2.1.4. `action: on_select`](#13214-action-on_select)
        - [13.2.1.4.1. Surge Pricing](#132141-surge-pricing)
      - [13.2.1.5. `action: init`](#13215-action-init)
      - [13.2.1.6. `action: on_init`](#13216-action-on_init)
      - [13.2.1.7. `action: on_status` (payment)](#13217-action-on_status-payment)
      - [13.2.1.8. `action: confirm`](#13218-action-confirm)
      - [13.2.1.9. `action: on_confirm`](#13219-action-on_confirm)
      - [13.2.1.10. `action: update` (start charging)](#132110-action-update-start-charging)
      - [13.2.1.11. `action: on_update` (start charging)](#132111-action-on_update-start-charging)
      - [13.2.1.12. `action: status`](#132112-action-status)
      - [13.2.1.13. `action: on_status`](#132113-action-on_status)
      - [13.2.1.14. asynchronous `action: on_status` (temporary connection interruption)](#132114-asynchronous-action-on_status-temporary-connection-interruption)
          - [13.2.1.14.0.1. **A)Undercharge (Power Cut Mid-Session)**](#13211401-aundercharge-power-cut-mid-session)
          - [13.2.1.14.0.2. **B) Overcharge (Charger Offline to CMS; Keeps Dispensing)**](#13211402-b-overcharge-charger-offline-to-cms-keeps-dispensing)
      - [13.2.1.15. Asynchronous `action: on_update` (stop charging)](#132115-asynchronous-action-on_update-stop-charging)
      - [13.2.1.16. Synchronous/Asynchronous on\_update (stop charging)](#132116-synchronousasynchronous-on_update-stop-charging)
      - [13.2.1.17. `action: cancel`](#132117-action-cancel)
      - [13.2.1.18. `action: on_cancel`](#132118-action-on_cancel)
      - [13.2.1.19. `action: rating`](#132119-action-rating)
      - [13.2.1.20. `action: on_rating`](#132120-action-on_rating)
      - [13.2.1.21. `action: support`](#132121-action-support)
      - [13.2.1.22. `action: on_support`](#132122-action-on_support)
    - [13.2.2. **Integrating with your software**](#1322-integrating-with-your-software)
      - [13.2.2.1. **Integrating the BAP**](#13221-integrating-the-bap)
      - [13.2.2.2. **Integrating the BPP**](#13222-integrating-the-bpp)
  - [13.3. FAQs](#133-faqs)
  - [13.4. References](#134-references)

Table of contents and section auto-numbering was done using [Markdown-All-In-One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) vscode extension. Specifically `Markdown All in One: Create Table of Contents` and `Markdown All in One: Add/Update section numbers` commands accessible via vs code command pallete.

Example jsons were imported directly from source of truth elsewhere in this repo inline by inserting the pattern below within all json expand blocks, and running this [script](/scripts/embed_example_json.py), e.g. `python3 scripts/embed_example_json.py docs/implementation-guides/v2/EV_Charging/EV_Charging.md`.

```
<details><summary><a href="/path_to_file_from_root">txt_with_json_keyword</a></summary>

</details>
``` 


# 1. Request for Comments

# 2. Copyright Notice

**License: [CC-BY-NC-SA 4.0](https://becknprotocol.io/license/) becknprotocol.io**

# 3. Status of This Memo

**This is a draft RFC for implementing EV charging use cases using the Beckn Protocol. It provides implementation guidance for anyone to build interoperable EV charging applications that integrate with each other on a decentralized network while maintaining compatibility with OCPI standards for CPO communication.**

# 4. Abstract

This document proposes a practical way to make EV charging services easier to find and use by applying the Beckn Protocol’s distributed commerce model. Instead of juggling multiple apps and accounts for different charging networks, EV users on any Beckn protocol-enabled consumer platform (a.k.a BAPs) – can discover and book charging services from Beckn protocol-enabled provider platforms (a.k.a BPPs) that have onboarded one or more Charge Point Operators (CPOs).

EV users can discover, compare options, view transparent pricing, and reserve a slot at any eligible charging station owned or operated by CPOs. By standardizing discovery, pricing, and booking, the approach tackles three persistent barriers to EV adoption: charging anxiety, network fragmentation, and payment complexity.

Built on Beckn’s commerce capabilities and aligned with OCPI for technical interoperability, the implementation lets e-Mobility Service Providers (eMSPs) aggregate services from multiple CPOs while delivering a consistent, app-agnostic experience to consumers. 

# 5. Introduction

This document provides an implementation guidance for deploying EV charging services using the Beckn Protocol ecosystem. It specifically addresses how consumer applications can provide unified access to charging infrastructure across multiple Charge Point Operators while maintaining technical compatibility with existing OCPI-based systems.

# 6. Scope

This document covers:

* Architecture patterns for EV charging marketplace implementation using Beckn Protocol  
* Discovery and charging mechanisms for charging EVs across multiple CPOs  
* Some recommendations for BAPs, BPPs and NFOs on how to map protocol API calls to internal systems (or vice-versa).  
* Real-time availability and pricing integration with OCPI-based systems  
* Session management and billing coordination between Beckn and OCPI protocols

This document does NOT cover:

* Detailed OCPI protocol specifications (refer to OCPI 2.2.1 documentation)  
* Physical charging infrastructure requirements and standards  
* Regulatory compliance beyond technical implementation (varies by jurisdiction)  
* Smart grid integration and load management systems

# 7. Intended Audience

* Consumer Application Developers (BAPs): Building EV driver-facing charging applications with unified cross-network access  
* e-Mobility Service Providers (eMSPs/BPPs): Implementing charging service aggregation platforms across multiple CPO networks  
* Charge Point Operators (CPOs): Understanding integration requirements for Beckn-enabled marketplace participation  
* Technology Integrators: Building bridges between existing OCPI infrastructure and new Beckn-based marketplaces  
* System Architects: Designing scalable, interoperable EV charging ecosystems  
* Business Stakeholders: Understanding technical capabilities and implementation requirements for EV charging marketplace strategies  
* Standards Organizations: Evaluating interoperability approaches for future EV charging standards development

# 8. Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described [here](https://github.com/beckn/protocol-specifications/blob/draft/docs/BECKN-010-Keyword-Definitions-for-Technical-Specifications.md).

# 9. Terminology

| Acronym | Full Form/Description             | Description                                                                                                           |
| ------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| BAP     | Beckn Application Platform        | Consumer-facing application that initiates transactions. Mapped to EV users and eMSPs.                                |
| BPP     | Beckn Provider Platform           | Service provider platform that responds to BAP requests. Mapped to CPOs.                                              |
| NFO     | Network Facilitator Organization  | Organization responsible for the adoption and growth of the network. Usually the custodian of the network’s registry. |
| CDS     | Catalog Discovery Service         | Enables discovery of charging services from BPPs in the network.                                                      |
| eMSP    | e-Mobility Service Provider       | Service provider that aggregates multiple CPOs. Generally onboarded by BAPs.                                          |
| CPO     | Charge Point Operator             | Entity that owns and operates charging infrastructure. Generally onboarded by BPPs.                                   |
| EVSE    | Electric Vehicle Supply Equipment | Individual charging station unit. Owned and operated by CPOs                                                          |
| OCPI    | Open Charge Point Interface       | Protocol for communication between eMSPs and CPOs.                                                                    |

> Note:
> This document does not detail the mapping between Beckn Protocol and OCPI. Please refer to [this](../../../../docs/implementation-guides/v1-EOS/DEG00x_Mapping-OCPI-and-Beckn-Protocol-for-EV-Charging-Interoperability.md) document for the same.
> BPPs are NOT aggregators. Any CPO that has implemented a Beckn Protocol endpoint is a BPP. 
> For all sense and purposes, CPOs are essentially BPPs and eMSPs are essentially BAPs.

# 10. Reference Architecture

The section defines the reference ecosystem architecture that is used for building this implementation guide. 

## 10.1. Architecture Diagram

![](../assets/beckn-one-deg-arch.png)

## 10.2. Actors

1. Beckn One Global Root Registry  
2. Beckn One Catalog Discovery Service  
3. Beckn Application Platforms  
4. Beckn Provider Platforms  
5. EV Charging Registry

# 11. Creating an Open Network for EV Charging

To create an open network for EV charging requires all the EV charging BAPs, BPPs, to be able to discover each other and become part of a common club. This club is manifested in the form of a Registry maintained by an NFO. 

## 11.1. Setting up a Registry

The NP Registry serves as the root of addressability and trust for all network participants. It maintains comprehensive details such as the participant’s globally unique identifier (ID), network address (Beckn API URL), public key, operational domains, and assigned role (e.g., BAP, BPP, CDS). In addition to managing participant registration, authentication, authorization, and permission control, the Registry oversees participant verification, activation, and overall lifecycle management, ensuring that only validated and authorized entities can operate within the network.

![](../assets/registry-arch.png)

You can publish your registries at [DeDi.global](https://publish.dedi.global/).

### 11.1.1. For a Network Participant

#### 11.1.1.1. Step 1 :  Claiming a Namespace

To get started, any platform that has implemented Beckn Protocol MUST create a globally unique namespace for themselves.   
All NPs (BAPs, BPPs, CDS’es) **MUST** register as a user on dedi.global and claim a unique namespace against their FQDN to become globally addressable. As part of the claiming process, the user must prove ownership of the namespace by verifying the ownership of their domain. Namespace would be at an organisation level. You can put your organisation name as the name of the namespace.

#### 11.1.1.2. Step 2 :  Setting up a Registry

Once the namespace is claimed, each NP **MUST** create a Beckn NP registry in the namespace to list their subscriber details. While creating the registry, the user **MUST** configure it with the [subscriber schema](https://gist.githubusercontent.com/nirmalnr/a6e5b17522169ecea4f3ccdd831af7e4/raw/7744f2542034db9675901b61b41c8228ea239074/beckn-subscriber-no-refs.schema.json). Example of a registry name can be `subscription-details`.

#### 11.1.1.3. Step 3 :  Publishing subscriber details

In the registry that is created, NPs **MUST** publish their subscription details including their ID, network endpoints, public keys, operational domains and assigned roles (BAP, BPP) as records.

*Detailed steps to create namespaces and registries in dedi.global can be found [here](https://github.com/dedi-global/docs/blob/0976607aabc6641d330a3d41a3bd89ab8790ea09/user-guides/namespace%20and%20registry%20creation.md).*

### 11.1.2. Step 4 :  Share details of the registry created with the Beckn One team

Once the registry is created and details are published, the namespace and the registry name of the newly created registry should be shared with the beckn one team.

### 11.1.3. For a Network facilitator organization

#### 11.1.3.1. Step 1 :  Claiming a Namespace

An NFO **MAY** register as a user on dedi.global and claim a unique namespace against their FQDN. As part of the claiming process, the user must prove ownership of that namespace by verifying the ownership of that domain. The NFO name can be set as the name of the namespace. 
*Note: A calibrated roll out of this infrastructure is planned and hence before it is open to the general public NFOs are advised to share their own domain and the domains of their NPs to the Beckn One team so that they can be whitelisted which will allow the NPs to verify the same using TXT records in their DNS.*

#### 11.1.3.2. Step 2 :  Setting up a Registry

Network facilitators **MAY** create registries under their own namespace using the [subscriber reference schema](https://gist.githubusercontent.com/nirmalnr/a6e5b17522169ecea4f3ccdd831af7e4/raw/b7cf8a47e6531ef22744b43e6305b8d8cc106e7b/beckn-subscriber-reference.schema.json) to point to either whole registries or records created by the NPs in their own namespaces.  Example of a registry name can be `subscription-details`.

#### 11.1.3.3. Step 3 :  Publishing subscriber details

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

#### 11.1.3.4. Step 4 :  Share details of the registry created with the Beckn One team

Once the registry is created and details are published, the namespace and the registry name of the newly created registry should be shared with the beckn one team.

## 11.2. Setting up the Protocol Endpoints

This section contains instructions to set up and test the protocol stack for EV charging transactions. 

### 11.2.1. Installing Beckn ONIX

All NPs SHOULD install the Beckn ONIX adapter to quickly get set up and become Beckn Protocol compliant. Click [here](https://github.com/Beckn-One/beckn-onix?tab=readme-ov-file#automated-setup-recommended)) to learn how to set up Beckn ONIX.

### 11.2.2. Configuring Beckn ONIX for EV Charging Transactions

A detailed Configuration Guide is available [here](https://github.com/Beckn-One/beckn-onix/blob/main/CONFIG.md). A quick read of key concepts from the link is recommended.

Specifically, for EV Charging, please use the following configuration:
1. Configure dediregistry plugin instead of registry plugin. Read more [here](https://github.com/Beckn-One/beckn-onix/tree/main/pkg/plugin/implementation/dediregistry).
2. Start with using Simplekeymanager plugin during development, read more [here](https://github.com/Beckn-One/beckn-onix/tree/main/pkg/plugin/implementation/simplekeymanager). For production deployment, you may setup vault.
3. For routing calls to Catalog Discovery Service, refer to routing configuration [here](https://github.com/Beckn-One/beckn-onix/blob/main/config/local-simple-routing-BAPCaller.yaml).
4. ONIX validates messages against the Beckn 2.0 LTS core specification (`core-v2.0.0-lts`) by default from v1.7.1 onwards. The examples in this guide are validated through ONIX 1.9.4, against the LTS core schema and the attribute packs.
5. Set `context.networkId` to `nfh.global/testnet-evcharging` for the EV charging test network, on which the devkit's example participants are registered.
6. The [EV charging devkit](../../../../devkits/ev-charging/README.md) has ready ONIX configurations for a BAP and a BPP (`config/`), a Docker Compose setup and reference apps that run every use case in this guide. The conventions the examples follow are in the [examples README](../../../../examples/ev-charging/v2/README.md).

### 11.2.3. 10.2.3 Performing a test EV charging transaction

Step 1 : Download the postman collection, from [here](/devkits/ev-charging/uc1-ev-charging/postman/).

Step 2 : Run API calls

If you are a BAP

1. Configure the collection/environment variables to the newly installed Beckn ONIX adapter URL and other variables in the collection.
2. Select the discover example and hit send
3. You should see the EV charging service catalog response

If you are a BPP

1. Configure the collection/environment variables to the newly installed Beckn ONIX adapter URL and other variables in the collection.
2. Select the on_status example and hit send
3. You should see the response in your console

# 12. Implementing EV Charging Semantics on Beckn Protocol

This section contains recommendations and guidelines on how to implement EV Charging Services on Beckn Protocol enabled networks. To ensure global interoperability between actors of the EV charging network, the semantics of the EV charging industry need to be mapped to the core schema of Beckn Protocol. The below table summarizes key semantic mappings between the EV Charging Domain and Beckn Protocol domain.

## 12.1. Key Assumptions

- **Assumption 1 :** EV charging is treated as a service, not as a physical object.  
- **Assumption 2:** All CPOs have implemented OCPI interfaces 

Each entity in the charging lifecycle — the service, the commercial terms, and the usage instance — maps to a well-defined semantic concept, enabling platforms to exchange information in a standardized, machine-readable way.

## 12.2. Semantic Model

| EV Charging Domain Entity | Charging Example                                                                       |                                                    Semantically maps to                                                     |
| ------------------------- | -------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------: |
| Charging Service Listing  | “DC Fast-Charging (60 kW CCS2)”                                                        | Resource (`catalogs[].resources[]`) with [ChargingService](../../../../specification/schema/EvChargingService/v2.0/attributes.yaml) attributes in `resourceAttributes` |
| Charging tariff           | “₹18 per kWh”, “₹150 per hour”, “₹999 monthly pass”, “Off-peak discount 2 AM–5 AM”     | Offer (`catalogs[].offers[]`) with [ChargingOffer](../../../../specification/schema/EvChargingOffer/v2.0/attributes.yaml) attributes in `offerAttributes`; the price is in `offers[].considerations[]` (`PriceSpecification`) |
| Charging Session          | A specific booking or usage instance created when the user plugs in or reserves a slot | Contract (`message.contract`); the session is its `performance[]`, with [ChargingSession](../../../../specification/schema/EvChargingSession/v2.0/attributes.yaml) attributes in `performanceAttributes` |

## 12.3. Example Category Codes

The following section contains example category codes that can be 

Charger types

| Code      | What it means                                                                              |
| --------- | ------------------------------------------------------------------------------------------ |
| AC\_SLOW  | AC charge points in the “slow” band (≈ 3–7 kW).                                            |
| AC\_FAST  | AC “fast” public charging (≈ 7–22 kW; UK fast band 8–49 kW covers AC up to \~22 kW).       |
| DC\_FAST  | DC “rapid/fast” typically \~50–149 kW.                                                     |
| DC\_ULTRA | DC “ultra-rapid/ultra-fast”, ≥ 150 kW (also aligns with AFIR focus on ≥ 150 kW corridors). |

Connector types

| Code    | What it means                                                                           |
| ------- | --------------------------------------------------------------------------------------- |
| TYPE1   | Type 1 (SAE J1772) AC connector (North America/JP usage).                               |
| TYPE2   | Type 2 (IEC 62196-2) AC connector; EU standard.                                         |
| CCS2    | Combined Charging System “Combo 2” (IEC 62196 based) enabling high-power DC on Type 2\. |
| CHADEMO | CHAdeMO DC fast-charging standard.                                                      |
| GB\_T   | China’s GB/T charging standard (AC & DC).                                               |

Service types

| Code                     | What it means                                                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| GREEN\_ENERGY\_CERTIFIED | Flag that the site/session is supplied by verified green energy per catalog metadata (e.g., OCPI EnergyMix.is\_green\_energy). |
| GO\_EU                   | Energy backed by EU Guarantees of Origin (GOs).                                                                                |
| REGO\_UK                 | Energy backed by the UK Renewable Energy Guarantees of Origin (REGO) scheme.                                                   |
| I\_REC                   | Energy backed by I-REC certificates (international EACs).                                                                      |
| V2G\_ENABLED             | Charger/site supports bidirectional power transfer (V2G), e.g., per ISO 15118-20 implementations.                              |
| REMOTE\_START\_STOP      | Remote start/stop of sessions exposed via roaming interface (OCPI Commands module).                                            |


# 13. Example Workflows (EV User’s Perspective)

## 13.1. Example 1 \- Walk-In to a charging station without reservation.

This section covers a walk-in case where users discover the charger using third-party apps, word of mouth, or Beckn API, and then drive to the location, plug in their EV and charge their vehicle. 

### 13.1.1. Consumer User Journey

A 34-year-old sales manager who drives an EV to client meetings. He’s time-bound, cost-conscious, and prefers simple, scan-and-go experiences. Raghav arrives at a large dine-in restaurant for a one-hour client meeting. He notices a charging bay in the parking lot and decides to top up while he’s inside.

**Discovery**: Raghav opens his EV app, taps sScan & Charge, and scans the QR on the charger. The app pulls the charger’s details (connector, power rating, live status, tariff, any active time-bound offer).

**Order**: Raghav selects a 60-minute top-up, reviews session terms (rate, idle fee window, cancellation rules), and confirms. He chooses UPI and authorizes payment (or an authorization hold, as supported). The app returns a booking/transaction ID.

**Fulfilment**: He plugs in and starts the session from the app. Live progress (kWh, ₹ consumed, ETA) is shown while he’s in the meeting. If the bay has a lunch-hour promo, the discounted rate is applied automatically.

**Post-Fulfilment**: At \~60 minutes, the session stops (or notifies him to unplug). He receives a digital invoice and session summary in-app. If anything went wrong (e.g., session interrupted, SOC reaches 100%, etc.), the app reconciles to bill only for energy delivered and issues any adjustment or refund automatically.

Important points of consideration:

1. From a technical standpoint, the walk-in scenario is comparable to booking an instant slot *after* reaching the location. While it may appear different from a user experience perspective, the underlying API calls and system processes remain largely the same as the advance reservation use case, with key differences in timing and availability checks.  
2. The order flow happens while the user is physically present at the charging station. This creates a more compressed transaction timeline where all booking steps occur on-site, making it essential for the system to handle real-time availability updates and quick response times to ensure a smooth user experience.  
3. Real-time availability: The system checks for immediate slot availability instead of future time slots  
4. Instant booking: The entire discovery → select → init → confirm flow happens within minutes at the physical location  
5. Same API endpoints: Uses identical Beckn protocol calls but with compressed timeframes  
6. Immediate fulfillment: The charging session can start immediately after confirmation, rather than waiting for a scheduled time

### 13.1.2. **API Calls and Schema**

Note: The API calls and schema for walk-in charging are identical to the [advance reservation use case](#132-use-case-2--reservation-of-an-ev-charging-time-slot) with minor differences in timing and availability. Where sections reference Use Case 2, the same API structure, field definitions, and examples apply unless specifically noted otherwise.

#### 13.1.2.1. `action: discover`

- Method: POST
- Use Cases: Raghav scans QR code on Charging Point Connector using his BAP user app
- Request: Fetching details of a specific Charging Point Connector (EVSE) after reaching site (using its identifier): [Example](../../../../examples/ev-charging/v2/01_discover/discovery-by-EVSE.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-by-EVSE.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "8267211d-5b74-5509-a2f1-a2d616f7c782",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].resources[?(@.resourceAttributes.evseId == 'IN*ECO*BTM*01*CCS2*A')]"
      }
    }
  }
}

```
</details>

- Successful Response: 
<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

Note: Users can discover the charging station through off-network channels (such as physical signage, word-of-mouth, or third-party apps not integrated with Beckn) and arrive directly at the location to initiate charging. In this scenario:

* The discovery phase is skipped entirely  
* Users proceed directly to the Select API call by scanning QR codes or using location-based identification  
* The charging station must be able to handle direct selection requests without prior search/discovery  
* This represents a more streamlined flow for walk-in customers who have already identified their preferred charging location

#### 13.1.2.2. `action: on_discover`

- Method: POST
- Use Cases: The app receives the charger’s details (connector, power rating, live status, tariff, any active time-bound offer).
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/02_on_discover/ev-charging-specific-evse-catalog.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "bppId": "example-cds.com",
    "bppUri": "https://example-cds.com/pilot/cds/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "8267211d-5b74-5509-a2f1-a2d616f7c782",
    "timestamp": "2025-10-14T07:31:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "catalogs": [
      {
        "id": "catalog-ev-charging-001-ecopower-charging",
        "descriptor": {
          "name": "EV Charging Services Network",
          "shortDesc": "Comprehensive network of fast charging stations across Bengaluru"
        },
        "bppId": "bpp.ev-network.example.com",
        "bppUri": "https://bpp.ev-network.example.com/bpp",
        "provider": {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          },
          "availableAt": [
            {
              "geo": {
                "type": "Point",
                "coordinates": [
                  77.5946,
                  12.9716
                ]
              },
              "address": {
                "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
                "addressLocality": "Bengaluru",
                "addressRegion": "Karnataka",
                "postalCode": "560076",
                "addressCountry": "IN"
              }
            }
          ]
        },
        "resources": [
          {
            "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
            "descriptor": {
              "name": "DC Fast Charger - CCS2 (60kW)",
              "shortDesc": "High-speed DC charging station with CCS2 connector",
              "longDesc": "Ultra-fast DC charging station supporting CCS2 connector type with 60kW maximum power output. Features advanced thermal management and smart charging capabilities."
            },
            "resourceAttributes": {
              "@context": "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
              "@type": "ChargingService",
              "connectorType": "CCS2",
              "maxPowerKW": 60,
              "minPowerKW": 5,
              "reservationSupported": true,
              "chargingStation": {
                "id": "IN-ECO-BTM-STATION-01",
                "serviceLocation": {
                  "geo": {
                    "type": "Point",
                    "coordinates": [
                      77.5946,
                      12.9716
                    ]
                  },
                  "address": {
                    "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
                    "addressLocality": "Bengaluru",
                    "addressRegion": "Karnataka",
                    "postalCode": "560076",
                    "addressCountry": "IN"
                  }
                }
              },
              "amenityFeature": [
                "RESTAURANT",
                "RESTROOM",
                "WI-FI"
              ],
              "evseId": "IN*ECO*BTM*01*CCS2*A",
              "parkingType": "Mall",
              "powerType": "DC",
              "connectorFormat": "CABLE",
              "chargingSpeed": "FAST",
              "vehicleType": "4-WHEELER"
            }
          }
        ],
        "offers": [
          {
            "id": "eco-charge-offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-eco-charge-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ],
            "validity": {
              "startDate": "2025-10-10T00:00:00Z",
              "endDate": "2026-04-10T23:59:59Z",
              "startTime": "06:00:00",
              "endTime": "22:00:00"
            },
            "offerAttributes": {
              "@context": "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld",
              "@type": "ChargingOffer",
              "tariffModel": "PER_KWH",
              "idleFeePolicy": {
                "currency": "INR",
                "value": 2,
                "applicableQuantity": {
                  "unitCode": "MIN",
                  "unitText": "minutes",
                  "unitQuantity": 10
                }
              },
              "acceptedPaymentMethods": [
                "UPI",
                "CREDIT_CARD",
                "WALLET"
              ]
            }
          }
        ]
      }
    ]
  }
}

```
</details>

CPO returns details of a specific charger: [Example](../../../../examples/ev-charging/v2/02_on_discover/ev-charging-specific-evse-catalog.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.3. `action: select`

- Method: POST
- Use Cases: Raghav selects a service offering from the options he gets. He chooses a 2.5 KWH top-up and requests for a preferred time slot.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/03_select/ev-charging-select.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "select",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b16f4529-c67a-5b55-b4af-a95a8898b9c1",
    "timestamp": "2024-01-15T10:30:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "contractAttributes": {
        "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
        "@type": "ChargingSession",
        "buyerFinderFee": {
          "feeType": "PERCENTAGE",
          "feeValue": 2.5
        },
        "preferences": {
          "startTime": "2025-12-20T10:00:00Z",
          "endTime": "2025-12-20T11:30:00Z"
        }
      }
    }
  }
}

```
</details>

EV user requests charge worth in KWH: [Example](../../../../examples/ev-charging/v2/03_select/ev-charging-select.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.4. `action: on_select`

- Method: POST
- Use Cases: Raghav receives estimated quotations for the selected service.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_select",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b16f4529-c67a-5b55-b4af-a95a8898b9c1",
    "timestamp": "2024-01-15T10:30:05Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "contractAttributes": {
        "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
        "@type": "ChargingSession",
        "buyerFinderFee": {
          "feeType": "PERCENTAGE",
          "feeValue": 2.5
        },
        "preferences": {
          "startTime": "2025-12-20T10:00:00Z",
          "endTime": "2025-12-20T11:30:00Z"
        }
      }
    }
  }
}

```
</details>

CPO responds with dynamically calculated quote: [Example](../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.5. `action: init`

- Method: POST
- Use Cases: Raghav reviews charger tariff, idle fee window, cancellation rules etc. BAP initiates the payment on Raghav’s behalf, with the BPP acting as the payment collector. BAP sends payment settlement account information for future reconciliation.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/05_init/ev-charging-bpp-payment-init.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "init",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "bd411d71-0140-531c-bfdb-659bf5317e7e",
    "timestamp": "2025-01-27T10:00:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "DRAFT",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:paymentStatus": "INITIATED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:beneficiary": "BPP",
            "beckn:paymentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
              "@type": "PaymentSettlement",
              "settlementAccounts": [
                {
                  "beneficiaryId": "example-bap.com",
                  "accountHolderName": "Example BAP Solutions Pvt Ltd",
                  "accountNumber": "9876543210123",
                  "ifscCode": "HDFC0009876",
                  "bankName": "HDFC Bank",
                  "vpa": "example-bap@paytm"
                }
              ]
            }
          }
        }
      ]
    }
  }
}

```
</details>

EV user requests for payment information: [Example](../../../../examples/ev-charging/v2/05_init/ev-charging-bpp-payment-init.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.6. `action: on_init`

- Method: POST
- Use Cases: Raghav receives the charging session order ID and payment link, reviews the terms, selects UPI, and authorizes the payment (or an authorization hold, if supported).
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/06_on_init/ev-charging-bpp-payment-on-init.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_init",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "bd411d71-0140-531c-bfdb-659bf5317e7e",
    "timestamp": "2025-01-27T10:00:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "DRAFT",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "INITIATED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:acceptedPaymentMethod": [
              "BANK_TRANSFER",
              "UPI",
              "WALLET"
            ],
            "beckn:beneficiary": "BPP",
            "beckn:paymentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
              "@type": "PaymentSettlement",
              "settlementAccounts": [
                {
                  "beneficiaryId": "example-bap.com",
                  "accountHolderName": "Example BAP Solutions Pvt Ltd",
                  "accountNumber": "9876543210123",
                  "ifscCode": "HDFC0009876",
                  "bankName": "HDFC Bank",
                  "vpa": "example-bap@paytm"
                },
                {
                  "beneficiaryId": "example-bpp.com",
                  "accountHolderName": "EcoPower Charging Solutions Pvt Ltd",
                  "accountNumber": "1234567890123",
                  "ifscCode": "HDFC0001234",
                  "bankName": "HDFC Bank",
                  "vpa": "ecopower@paytm"
                }
              ]
            }
          }
        }
      ]
    }
  }
}

```
</details>

CPO responds with the payment link for the user to authorize payment: [Example](../../../../examples/ev-charging/v2/06_on_init/ev-charging-bpp-payment-on-init.json)

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.7. 13.1.2.6.1 `action: on_status`

- Method: POST
- Use Cases: Raghav receives a notification on the status of the payment initiated for the charging session.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/06_on_status_1/ev-charging-bpp-payment-check-on-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0ae4d99e-80ea-5f68-959a-84992fd40d6a",
    "timestamp": "2025-01-27T10:05:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

CPO sends the status of the payment: [Example](../../../../examples/ev-charging/v2/06_on_status_1/ev-charging-bpp-payment-check-on-status.json)

#### 13.1.2.8. `action: confirm`

- Method: POST
- Use Cases: Raghav confirms the order.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/07_confirm/ev-charging-confirm.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0e6f056f-ea93-5c29-bc8f-6f32e90d644c",
    "timestamp": "2025-01-27T10:05:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

EV user confirms reservation of a slot at a particular charging station at a particular time: [Example](../../../../examples/ev-charging/v2/07_confirm/ev-charging-confirm.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.9. `action: on_confirm`

- Method: POST
- Use Cases: The CPO confirms the order along with the charging session details (`performance`).
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/08_00_on_confirm/ev-charging-on-confirm.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_confirm",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0e6f056f-ea93-5c29-bc8f-6f32e90d644c",
    "timestamp": "2025-01-27T10:05:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

CPO responds with confirmed slot: [Example](../../../../examples/ev-charging/v2/08_00_on_confirm/ev-charging-on-confirm.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.10. `action: status`

- Method: POST
- Use Cases: Raghav connects the charging gun and checks the status of the charging connector.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/08_01_status/ev-charging-connector-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ec5b2d58-4c80-5982-bc61-6af6b5c1642c",
    "timestamp": "2025-01-27T10:05:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

The user checks the status of charging connector: [Example](../../../../examples/ev-charging/v2/08_01_status/ev-charging-connector-status.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.11. `action: on_status`

- Method: POST
- Use Cases: The CPO responds with the connector status PREPARING, indicating readiness to supply power.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/08_02_on_status/ev-charging-connector-on-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ec5b2d58-4c80-5982-bc61-6af6b5c1642c",
    "timestamp": "2025-01-27T10:05:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING",
            "connectorStatus": "PREPARING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

The CPO response with the status of the charging connector: [Example](../../../../examples/ev-charging/v2/08_02_on_status/ev-charging-connector-on-status.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.12. `action: update` (start charging)

- Method: POST
- Use Cases: Raghav starts the session from the app.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/09_update/ev-charging-01-session-start-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b9c96f71-7fc1-5f21-b0ad-1d81df131ef5",
    "timestamp": "2025-01-27T10:15:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

EV user starts a charging session: [Example](../../../../examples/ev-charging/v2/09_update/ev-charging-01-session-start-update.json)

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.13. `action: on_update` (start charging)

- Method: POST
- Use Cases: Response for the charging session initiation. The sessionStatus changes to ACTIVE from PENDING.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/10_on_update/ev-charging-session-on-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b9c96f71-7fc1-5f21-b0ad-1d81df131ef5",
    "timestamp": "2025-01-27T10:15:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "ACTIVE"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "ACTIVE",
            "connectorType": "CCS2",
            "maxPowerKW": 50
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

CPO responds with confirmed start of charging session: [Example](../../../../examples/ev-charging/v2/10_on_update/ev-charging-session-on-update.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.14. `action: status` (charging-session progress)

- Method: POST
- Use Cases: Raghav requests to track the live status of the charging session. state of charge(how much charging has been done).
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/11_status/ev-charging-session-track.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "98d6a0a2-5219-57fd-8737-e0c09307973c",
    "timestamp": "2025-01-27T17:00:40.065Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ]
    }
  }
}

```
</details>

EV User tracks a live charging session in real-time: [Example](../../../../examples/ev-charging/v2/11_status/ev-charging-session-track.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.15. `action: on_status`

- Method: POST
- Use Cases: Raghav receives the state of charge(how much charging has been done) of the vehicle.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/12_on_status/ev-charging-session-on-track.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "98d6a0a2-5219-57fd-8737-e0c09307973c",
    "timestamp": "2025-01-27T17:00:42Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "ACTIVE"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "ACTIVE",
            "chargingTelemetry": [
              {
                "eventTime": "2025-01-27T17:00:00Z",
                "metrics": [
                  {
                    "name": "STATE_OF_CHARGE",
                    "value": 62.5,
                    "unitCode": "PERCENTAGE"
                  },
                  {
                    "name": "POWER",
                    "value": 18.4,
                    "unitCode": "KW"
                  },
                  {
                    "name": "ENERGY",
                    "value": 10.2,
                    "unitCode": "KWH"
                  },
                  {
                    "name": "VOLTAGE",
                    "value": 392,
                    "unitCode": "VLT"
                  },
                  {
                    "name": "CURRENT",
                    "value": 47.0,
                    "unitCode": "AMP"
                  }
                ]
              },
              {
                "eventTime": "2025-01-27T17:05:00Z",
                "metrics": [
                  {
                    "name": "STATE_OF_CHARGE",
                    "value": 65.0,
                    "unitCode": "PERCENTAGE"
                  },
                  {
                    "name": "POWER",
                    "value": 17.1,
                    "unitCode": "KW"
                  },
                  {
                    "name": "ENERGY",
                    "value": 11.1,
                    "unitCode": "KWH"
                  },
                  {
                    "name": "VOLTAGE",
                    "value": 388,
                    "unitCode": "VLT"
                  },
                  {
                    "name": "CURRENT",
                    "value": 44.2,
                    "unitCode": "AMP"
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  }
}

```
</details>

EV User receives a live charging session in real-time: [Example](../../../../examples/ev-charging/v2/12_on_status/ev-charging-session-on-track.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.16. async `action: on_status`

- Method: POST
- Use Cases: Raghav receives a notification if there is any error/interruption during the charging session.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/13_on_status/ev-charging-session-interrupt-on-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6a60f5cf-609d-538d-8952-0926b68fe57f",
    "timestamp": "2025-01-27T13:07:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "INTERRUPTED"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "INTERRUPTED"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

EV user reveives a notification in case of any error occuring during charging session: [Example](../../../../examples/ev-charging/v2/13_on_status/ev-charging-session-interrupt-on-status.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.17. `action: on_update` (stop-charging)

- Method: POST
- Use Cases: Raghav initiates a stop chargig request when his requirement is met. Note: In practice it is not necessary that an EV user initiates a charging session stop. Based on actual scenario, a charging session can be stopped by the CPO as well.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/14_01_update/ev-charging-session-end-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "722a01ac-5cb9-5013-8d0b-c659573f840a",
    "timestamp": "2025-01-27T10:15:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "STOP"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "STOP"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

EV user stops the charging session: [Example](../../../../examples/ev-charging/v2/14_01_update/ev-charging-session-end-update.json)

#### 13.1.2.18. async `action: on_update` (stop-charging)

- Method: POST 
- Use Case: At \~60 minutes(or upon the EV user request), the session stops (or notifies the EV user to unplug). He receives a digital invoice and session summary in-app. If anything went wrong (e.g., session interrupted, SOC reaches 100%, etc.), the app reconciles to bill only for energy delivered and issues any adjustment or refund automatically.
- Request:

<details>
<summary><a href="../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "722a01ac-5cb9-5013-8d0b-c659573f840a",
    "timestamp": "2025-01-27T11:45:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "COMPLETE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "CLOSED"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "FINAL"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 130.93,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "COMPLETED"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "COMPLETED",
            "meteredEnergyKWh": 2.5,
            "totalCost": {
              "inclVat": 130.93
            }
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        },
        {
          "id": "settlement-002",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "refund-001",
            "beckn:paymentStatus": "REFUNDED",
            "beckn:amount": {
              "currency": "INR",
              "value": 13.5
            },
            "beckn:beneficiary": "BUYER"
          }
        }
      ]
    }
  }
}

```
</details>

EV user receives the session details upon chargign session end: [Example](../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json)

When the invoice is ready, the CPO sends a further unsolicited on\_update with the invoice link in `contract.descriptor.docs[]`: [Example](../../../../examples/ev-charging/v2/14_03_on_update/ev-charging-invoice-ready-on-update.json)

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.19. `action: rating`

- Method: POST
- Use Cases: Raghav provides rating for the charging session.
- In Beckn 2.0 LTS the endpoint is `rate` (callback `on_rate`). The request carries `ratingInputs[]`: the `target` rated (here the charging session, `fulfillment-001`), a `range` (`ratingValue` between `worstRating` and `bestRating`) and optional `feedbackFormSubmission`.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/15_rating/ev-charging-session-rating.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "rate",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ed611c7a-ad96-5a7e-9730-2013292385c4",
    "timestamp": "2025-01-27T12:00:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "ratingInputs": [
      {
        "target": {
          "id": "fulfillment-001",
          "descriptor": {
            "code": "FULFILLMENT"
          }
        },
        "range": {
          "bestRating": 5,
          "worstRating": 1,
          "ratingValue": 4
        },
        "feedbackFormSubmission": {
          "data": {
            "comments": "Excellent charging experience! The station was clean, easy to find, and the charging was fast and reliable. The staff was helpful and the payment process was smooth.",
            "tags": "fast-charging,easy-to-use,clean-station,helpful-staff,smooth-payment"
          }
        }
      }
    ]
  }
}

```
</details>

EV user rates charging service experience: [Example](../../../../examples/ev-charging/v2/15_rating/ev-charging-session-rating.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.20. `action: on_rating`

- Method: POST
- Use Cases: Raghav receives an acknowledgement after rating the charging session.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/16_on_rating/ev-charging-session-on-rating.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_rate",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ed611c7a-ad96-5a7e-9730-2013292385c4",
    "timestamp": "2025-01-27T12:00:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "ratings": [
      {
        "target": {
          "id": "fulfillment-001",
          "descriptor": {
            "code": "FULFILLMENT"
          }
        },
        "range": {
          "bestRating": 5,
          "worstRating": 1,
          "ratingValue": 4
        },
        "feedbackFormSubmission": {
          "data": {
            "comments": "Excellent charging experience! The station was clean, easy to find, and the charging was fast and reliable. The staff was helpful and the payment process was smooth.",
            "tags": "fast-charging,easy-to-use,clean-station,helpful-staff,smooth-payment"
          },
          "id": "https://example-bpp.com/feedback/portal"
        }
      }
    ]
  }
}

```
</details>

CPO accepts rating: [Example](../../../../examples/ev-charging/v2/16_on_rating/ev-charging-session-on-rating.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.21. `action: support`

- Method: POST
- Use Cases: Raghav reaches out for support.
- Request: 

EV user contacts support: [Example](../../../../examples/ev-charging/v2/17_support/ev-charging-session-support.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/17_support/ev-charging-session-support.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "support",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "5bfb2396-247e-57b5-9a5b-2f19181ec67e",
    "timestamp": "2025-01-27T12:15:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "support": {
      "orderId": "order-ev-charging-001",
      "descriptor": {
        "name": "Help with charging session",
        "code": "ORDER"
      },
      "channels": [
        {
          "@context": "https://schema.nfh.global/SupportInfo/v2.1/context.jsonld",
          "@type": "SupportInfo",
          "name": "Ravi Kumar",
          "telephone": "+91-9876543210",
          "email": "ravi.kumar@example.com",
          "hoursAvailable": "Mon–Sun: 6:00 PM - 10:00 PM IST",
          "channels": [
            "PHONE",
            "WHATSAPP"
          ]
        }
      ]
    }
  }
}

```
</details>
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.1.2.22. `action: on_support`

- Method: POST
- Use Cases: Raghav receives a response to his support request.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/18_on_support/ev-charging-session-on-support.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_support",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "5bfb2396-247e-57b5-9a5b-2f19181ec67e",
    "timestamp": "2025-01-27T12:15:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "support": {
      "orderId": "order-ev-charging-001",
      "descriptor": {
        "name": "Support ticket SUP-20250730-001",
        "code": "OPEN"
      },
      "channels": [
        {
          "@context": "https://schema.nfh.global/SupportInfo/v2.1/context.jsonld",
          "@type": "SupportInfo",
          "name": "BlueCharge Support Team",
          "telephone": "18001080",
          "email": "support@bluechargenet-aggregator.io",
          "url": "https://support.bluechargenet-aggregator.io/ticket/SUP-20250730-001",
          "hoursAvailable": "Mon–Sun 24/7 IST",
          "channels": [
            "PHONE",
            "EMAIL",
            "WEB",
            "CHAT"
          ]
        }
      ]
    }
  }
}

```
</details>

CPO returns support information: [Example](../../../../examples/ev-charging/v2/18_on_support/ev-charging-session-on-support.json)
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

## 13.2. Use case 2- Reservation of an EV charging time slot.

This section covers advance reservation of a charging slot where users discover and book a charger before driving to the location.

#### 13.2.0.1. Context:

Adam is driving his electric vehicle along the highway when he notices that his battery level is getting low. Using an EV Charging BAP, Adam discovers nearby charging stations that are compatible with his vehicle. The BAP retrieves available slots and charger specifications from the available provider’s BPPs. Adam selects a preferred charger and books a slot through beckn APIs to avoid waiting on arrival.

![][image1]

#### 13.2.0.2. Discovery

##### 13.2.0.2.1. Adam discovers nearby charging services

About **30 minutes before lunch**, Adam opens his EV Charging BAP (powered by a Beckn-enabled discovery network).

He filters for:

1. **DC Fast chargers** within 5 km of her location,  
2. **Connector Type:** CCS2,  
3. **Amenities:** restaurants or cafes,  
4. **Tariff Model:** per kWh.

The app queries multiple charging providers and returns options showing:

1. **ETA** from current location,  
2. **Real-time availability**,  
3. **Tariff per kWh**,  
4. **Active offers** (e.g., lunch-hour discounts).

She compares them and selects **“EcoPower Highway Hub – Mandya Food Court”**.

#### 13.2.0.3. Order (Reservation)

Adam taps **Reserve Slot → 12:45–13:15 PM**.

The app displays the **session terms**:

| Term               | Example                  |
| ------------------ | ------------------------ |
| Tariff             | ₹18 / kWh                |
| Grace period       | 10 min post-session      |
| Idle fee policy    | ₹2/min after grace       |
| Cancellation rules | Free up to 15 min before |
| Payment options    | Hold, Pre-pay, Post-pay  |

They confirm.

The provider returns a **reservation ID and QR code**, plus a **navigation link** to the site.

#### 13.2.0.4. Fulfilment (Session Start & Tracking)

On arrival, Adam scans the charger’s **QR code**.

The backend matches it to her **reservation ID**, verifies her **OTP authorization**, and starts charging.

In-app, he view live telemetry:

1. Energy dispensed (kWh)  
2. Elapsed time (min)  
3. Running cost (₹)  
4. Estimated completion time

He enjoys lunch while the system manages the session.

If she arrives a few minutes late, the charger holds the slot until the **grace period** expires.

#### 13.2.0.5. Post-Fulfilment

Charging auto-stops at her **target energy level (80 %)** or when she manually ends the session.

The system issues a **digital invoice**, updates her **wallet balance**, and prompts for quick feedback:

1. Amenity rating (1–5)  
2. Overall experience (1–5)  
3. Optional text comments.

Satisfied, Adam resumes his trip—arriving in Mysuru with time to spare.

### 13.2.1. **API Calls and Schema**

#### 13.2.1.1. `action: discover`

Consumers can search for EV charging stations with specific criteria including location, connector type, time window, finder fee etc.

- Method: POST
- Use Cases: Adam opens his EV Charging BAP (powered by a Beckn-enabled discovery network). He filters for chargers within 5 km of his location.
- Request: 

##### 13.2.1.1.1. Discovery of EV charging services within a circular boundary

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-within-a-circular-boundary.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "2806a7fc-19c0-58bd-8bfc-f83e3635e086",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "spatial": [
        {
          "op": "S_DWITHIN",
          "targets": "$.catalogs[*].provider.availableAt[*].geo",
          "geometry": {
            "type": "Point",
            "coordinates": [
              77.59,
              12.94
            ]
          },
          "distanceMeters": 10000
        }
      ]
    }
  }
}

```
</details>

Discovery of EV charging services within a circular boundary: [Example](../../../../examples/ev-charging/v2/01_discover/discovery-within-a-circular-boundary.json)

##### 13.2.1.1.2. Discovery within circle \+ connector specs as filters

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-within-boundary-with-connection-spec.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "3aa0fe16-fdda-5e5d-bfbf-387d7fa41dfb",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].resources[?(@.resourceAttributes.connectorType == 'CCS2' && @.resourceAttributes.maxPowerKW >= 50)]"
      },
      "spatial": [
        {
          "op": "S_DWITHIN",
          "targets": "$.catalogs[*].provider.availableAt[*].geo",
          "geometry": {
            "type": "Point",
            "coordinates": [
              77.59,
              12.94
            ]
          },
          "distanceMeters": 10000
        }
      ]
    }
  }
}

```
</details>

Discovery of EV Charging stations within a circular boundary using connector specs as filters: [Example](../../../../examples/ev-charging/v2/01_discover/discovery-within-boundary-with-connection-spec.json)

##### 13.2.1.1.3. Discovery within circle \+ vehicle specifications as filters

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-within-boundary-with-vehicle-spec.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "8e1380f2-c077-5387-895a-d11ce38dff03",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].resources[?(@.resourceAttributes.vehicleType == '4-WHEELER' && @.resourceAttributes.connectorType == 'CCS2')]"
      },
      "spatial": [
        {
          "op": "S_DWITHIN",
          "targets": "$.catalogs[*].provider.availableAt[*].geo",
          "geometry": {
            "type": "Point",
            "coordinates": [
              77.6,
              12.95
            ]
          },
          "distanceMeters": 8000
        }
      ]
    }
  }
}

```
</details>

Discovery of EV Charging stations within circular boundary using vehicle specifications as filters: [Example](../../../../examples/ev-charging/v2/01_discover/discovery-within-boundary-with-vehicle-spec.json)

The catalog describes chargers, not vehicles, so the vehicle is expressed as what the charger must serve: `resourceAttributes.vehicleType == '4-WHEELER'` and `resourceAttributes.connectorType == 'CCS2'`.

##### 13.2.1.1.4. Discovery of services offered by a specific CPO

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-services-by-a-cpo.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "d6a077b6-fa87-5389-82e2-df5878c73c42",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[?(@.provider.id == 'ecopower-charging')]"
      }
    }
  }
}

```
</details>

Discovery of EV charging services offered by a specific CPO: [Example](../../../../examples/ev-charging/v2/01_discover/discovery-services-by-a-cpo.json)

##### 13.2.1.1.5. Viewing details of a single charging station (by its Item Identifier)

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-services-by-a-station.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "d034f124-83b5-5630-8336-18aba3a18e1a",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].resources[?(@.resourceAttributes.chargingStation.id == 'IN-ECO-BTM-STATION-01')]"
      }
    }
  }
}

```
</details>

Viewing details of a single charging station (using its Identifier): [Example](../../../../examples/ev-charging/v2/01_discover/discovery-services-by-a-station.json)

##### 13.2.1.1.6. Fetching details of a specific charger (EVSE) on-site (by its EVSE identifier)

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-by-EVSE.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "8267211d-5b74-5509-a2f1-a2d616f7c782",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].resources[?(@.resourceAttributes.evseId == 'IN*ECO*BTM*01*CCS2*A')]"
      }
    }
  }
}

```
</details>

Fetching details of a specific charger (EVSE) after reaching site (using its identifier): [Example](../../../../examples/ev-charging/v2/01_discover/discovery-by-EVSE.json)

##### 13.2.1.1.7. Discovering chargers in a specific circular area, a specific connector type and availability time range

<details>
<summary><a href="../../../../examples/ev-charging/v2/01_discover/discovery-within-a-timerange.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0ce79d1e-ea01-5def-9905-b2ab6711830a",
    "timestamp": "2025-10-14T07:31:00Z",
    "ttl": "PT30S",
    "schemaContext": [
      "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
      "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld"
    ]
  },
  "message": {
    "intent": {
      "filters": {
        "type": "jsonpath",
        "expression": "$.catalogs[*].offers[?(@.validity.startTime <= '11:30:00' && @.validity.endTime >= '14:30:00')]"
      }
    }
  }
}

```
</details>

Discovering chargers in a specific circular area, a specific connector type and availability time range: [Example](../../../../examples/ev-charging/v2/01_discover/discovery-within-a-timerange.json)

1. **filters**  
   1. **expression** (`type: jsonpath`): A boolean predicate to enforce strict constraints. It is an absolute JSONPath from the catalog root, so it names what it filters: chargers (`$.catalogs[*].resources[?(...)]`), offers (`$.catalogs[*].offers[?(...)]`) or whole catalogs (`$.catalogs[?(@.provider.id == 'ecopower-charging')]`).  
   2. Charger properties are under `resourceAttributes` (e.g., `@.resourceAttributes.connectorType == 'CCS2'`); an availability window is matched on the offer's `validity.startTime` / `validity.endTime`, as in this example.  
   3. Supports comparisons (==, \>=, etc.) and logical operations (&&, ||).  
   4. Location is not a filter: "within N metres" goes in `spatial` as `S_DWITHIN` with `distanceMeters`, on `$.catalogs[*].provider.availableAt[*].geo` (see 13.2.1.1.1). `S_WITHIN` is containment, ignores `distanceMeters` and never matches a point.  
   5. Entries missing a referenced field don't match.  
   6. This example expresses only the availability window; the connector-type filter and the circle are shown in 13.2.1.1.2.
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.2. `action: on_discover`

- Method: POST
- Use Cases: Adam receives a comprehensive catalog of available charging stations from multiple CPOs with detailed specifications, pricing, and location information.

1. Multiple providers (CPOs) with their charging networks, one catalog per CPO  
2. Detailed location information with GPS coordinates  
3. Individual charging station specifications and pricing  
4. Connector types, power ratings, and availability status
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/02_on_discover/ev-charging-discovery-catalog.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_discover",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "app.example.com",
    "bapUri": "https://app.example.com/bap",
    "bppId": "example-cds.com",
    "bppUri": "https://example-cds.com/pilot/cds/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "2806a7fc-19c0-58bd-8bfc-f83e3635e086",
    "timestamp": "2025-10-14T07:31:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "catalogs": [
      {
        "id": "catalog-ev-charging-001-ecopower-charging",
        "descriptor": {
          "name": "EV Charging Services Network",
          "shortDesc": "Comprehensive network of fast charging stations across Bengaluru"
        },
        "bppId": "bpp.ev-network.example.com",
        "bppUri": "https://bpp.ev-network.example.com/bpp",
        "provider": {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          },
          "availableAt": [
            {
              "geo": {
                "type": "Point",
                "coordinates": [
                  77.5946,
                  12.9716
                ]
              },
              "address": {
                "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
                "addressLocality": "Bengaluru",
                "addressRegion": "Karnataka",
                "postalCode": "560076",
                "addressCountry": "IN"
              }
            }
          ]
        },
        "resources": [
          {
            "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
            "descriptor": {
              "name": "DC Fast Charger - CCS2 (60kW)",
              "shortDesc": "High-speed DC charging station with CCS2 connector",
              "longDesc": "Ultra-fast DC charging station supporting CCS2 connector type with 60kW maximum power output. Features advanced thermal management and smart charging capabilities."
            },
            "resourceAttributes": {
              "@context": "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
              "@type": "ChargingService",
              "connectorType": "CCS2",
              "maxPowerKW": 60,
              "minPowerKW": 5,
              "reservationSupported": true,
              "chargingStation": {
                "id": "IN-ECO-BTM-STATION-01",
                "serviceLocation": {
                  "geo": {
                    "type": "Point",
                    "coordinates": [
                      77.5946,
                      12.9716
                    ]
                  },
                  "address": {
                    "streetAddress": "EcoPower BTM Hub, 100 Ft Rd",
                    "addressLocality": "Bengaluru",
                    "addressRegion": "Karnataka",
                    "postalCode": "560076",
                    "addressCountry": "IN"
                  }
                }
              },
              "amenityFeature": [
                "RESTAURANT",
                "RESTROOM",
                "WI-FI"
              ],
              "evseId": "IN*ECO*BTM*01*CCS2*A",
              "parkingType": "Mall",
              "powerType": "DC",
              "connectorFormat": "CABLE",
              "chargingSpeed": "FAST",
              "vehicleType": "4-WHEELER"
            }
          }
        ],
        "offers": [
          {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ],
            "validity": {
              "startDate": "2025-10-01T00:00:00Z",
              "endDate": "2026-03-31T23:59:59Z",
              "startTime": "06:00:00",
              "endTime": "22:00:00"
            },
            "offerAttributes": {
              "@context": "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld",
              "@type": "ChargingOffer",
              "tariffModel": "PER_KWH",
              "idleFeePolicy": {
                "currency": "INR",
                "value": 2,
                "applicableQuantity": {
                  "unitCode": "MIN",
                  "unitText": "minutes",
                  "unitQuantity": 10
                }
              },
              "acceptedPaymentMethods": [
                "UPI",
                "CREDIT_CARD",
                "WALLET"
              ]
            }
          }
        ]
      },
      {
        "id": "catalog-ev-charging-001-greencharge-koramangala",
        "descriptor": {
          "name": "EV Charging Services Network",
          "shortDesc": "Comprehensive network of fast charging stations across Bengaluru"
        },
        "bppId": "bpp.ev-network.example.com",
        "bppUri": "https://bpp.ev-network.example.com/bpp",
        "provider": {
          "id": "greencharge-koramangala",
          "descriptor": {
            "name": "GreenCharge Energy Solutions"
          },
          "availableAt": [
            {
              "geo": {
                "type": "Point",
                "coordinates": [
                  77.6104,
                  12.9153
                ]
              },
              "address": {
                "streetAddress": "GreenCharge Koramangala, 80 Ft Rd",
                "addressLocality": "Bengaluru",
                "addressRegion": "Karnataka",
                "postalCode": "560034",
                "addressCountry": "IN"
              }
            }
          ]
        },
        "resources": [
          {
            "id": "IND*greencharge-koramangala*cs-02*IN*GC*KOR*01*CCS2*A*CCS2-B",
            "descriptor": {
              "name": "DC Fast Charger - CCS2 (120kW)",
              "shortDesc": "Ultra-fast DC charging station with CCS2 connector",
              "longDesc": "Ultra-fast DC charging station supporting CCS2 connector type with 120kW maximum power output. Features liquid cooling and advanced power management."
            },
            "resourceAttributes": {
              "@context": "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
              "@type": "ChargingService",
              "connectorType": "CCS2",
              "maxPowerKW": 120,
              "minPowerKW": 10,
              "reservationSupported": true,
              "chargingStation": {
                "id": "cs-02",
                "serviceLocation": {
                  "geo": {
                    "type": "Point",
                    "coordinates": [
                      77.6104,
                      12.9153
                    ]
                  },
                  "address": {
                    "streetAddress": "GreenCharge Koramangala, 80 Ft Rd",
                    "addressLocality": "Bengaluru",
                    "addressRegion": "Karnataka",
                    "postalCode": "560034",
                    "addressCountry": "IN"
                  }
                }
              },
              "amenityFeature": [
                "RESTAURANT",
                "RESTROOM",
                "WI-FI",
                "PARKING"
              ],
              "evseId": "IN*GC*KOR*01*CCS2*A",
              "parkingType": "OffStreet",
              "powerType": "DC",
              "connectorFormat": "CABLE",
              "chargingSpeed": "ULTRAFAST",
              "vehicleType": "3-WHEELER"
            }
          }
        ],
        "offers": [
          {
            "id": "offer-ccs2-120kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 120kW"
            },
            "provider": {
              "id": "greencharge-koramangala",
              "descriptor": {
                "name": "GreenCharge Energy Solutions"
              }
            },
            "resourceIds": [
              "IND*greencharge-koramangala*cs-02*IN*GC*KOR*01*CCS2*A*CCS2-B"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-120kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 22.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ],
            "validity": {
              "startDate": "2025-10-15T00:00:00Z",
              "endDate": "2026-04-15T23:59:59Z",
              "startTime": "00:00:00",
              "endTime": "23:59:59"
            },
            "offerAttributes": {
              "@context": "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld",
              "@type": "ChargingOffer",
              "tariffModel": "PER_KWH",
              "idleFeePolicy": {
                "currency": "INR",
                "value": 3,
                "applicableQuantity": {
                  "unitCode": "MIN",
                  "unitText": "minutes",
                  "unitQuantity": 15
                }
              },
              "acceptedPaymentMethods": [
                "UPI",
                "CREDIT_CARD",
                "WALLET",
                "BANK_TRANSFER"
              ]
            }
          }
        ]
      },
      {
        "id": "catalog-ev-charging-001-powergrid-indiranagar",
        "descriptor": {
          "name": "EV Charging Services Network",
          "shortDesc": "Comprehensive network of fast charging stations across Bengaluru"
        },
        "bppId": "bpp.ev-network.example.com",
        "bppUri": "https://bpp.ev-network.example.com/bpp",
        "provider": {
          "id": "powergrid-indiranagar",
          "descriptor": {
            "name": "PowerGrid Charging Solutions"
          },
          "availableAt": [
            {
              "geo": {
                "type": "Point",
                "coordinates": [
                  77.6254,
                  12.9716
                ]
              },
              "address": {
                "streetAddress": "PowerGrid Indiranagar, 100 Ft Rd",
                "addressLocality": "Bengaluru",
                "addressRegion": "Karnataka",
                "postalCode": "560008",
                "addressCountry": "IN"
              }
            }
          ]
        },
        "resources": [
          {
            "id": "IND*powergrid-indiranagar*cs-03*IN*PG*IND*01*TYPE2*A*TYPE2-A",
            "descriptor": {
              "name": "AC Fast Charger - Type 2 (22kW)",
              "shortDesc": "AC fast charging station with Type 2 connector",
              "longDesc": "AC fast charging station supporting Type 2 connector type with 22kW maximum power output. Ideal for overnight charging and workplace charging."
            },
            "resourceAttributes": {
              "@context": "https://schema.nfh.global/EvChargingService/v2.0/context.jsonld",
              "@type": "ChargingService",
              "connectorType": "Type2",
              "maxPowerKW": 22,
              "minPowerKW": 3,
              "reservationSupported": true,
              "chargingStation": {
                "id": "cs-03",
                "serviceLocation": {
                  "geo": {
                    "type": "Point",
                    "coordinates": [
                      77.6254,
                      12.9716
                    ]
                  },
                  "address": {
                    "streetAddress": "PowerGrid Indiranagar, 100 Ft Rd",
                    "addressLocality": "Bengaluru",
                    "addressRegion": "Karnataka",
                    "postalCode": "560008",
                    "addressCountry": "IN"
                  }
                }
              },
              "amenityFeature": [
                "RESTROOM",
                "WI-FI",
                "PARKING"
              ],
              "evseId": "IN*PG*IND*01*TYPE2*A",
              "parkingType": "Office",
              "powerType": "AC_3_PHASE",
              "connectorFormat": "SOCKET",
              "chargingSpeed": "NORMAL",
              "vehicleType": "4-WHEELER"
            }
          }
        ],
        "offers": [
          {
            "id": "offer-type2-22kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - Type 2 22kW"
            },
            "provider": {
              "id": "powergrid-indiranagar",
              "descriptor": {
                "name": "PowerGrid Charging Solutions"
              }
            },
            "resourceIds": [
              "IND*powergrid-indiranagar*cs-03*IN*PG*IND*01*TYPE2*A*TYPE2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-type2-22kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 15.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ],
            "validity": {
              "startDate": "2025-10-20T00:00:00Z",
              "endDate": "2026-04-20T23:59:59Z",
              "startTime": "08:00:00",
              "endTime": "20:00:00"
            },
            "offerAttributes": {
              "@context": "https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld",
              "@type": "ChargingOffer",
              "tariffModel": "PER_KWH",
              "idleFeePolicy": {
                "currency": "INR",
                "value": 1,
                "applicableQuantity": {
                  "unitCode": "MIN",
                  "unitText": "minutes",
                  "unitQuantity": 30
                }
              },
              "acceptedPaymentMethods": [
                "UPI",
                "CREDIT_CARD",
                "WALLET",
                "BANK_TRANSFER"
              ]
            }
          }
        ]
      }
    ]
  }
}

```
</details>

CPO returns EV Charging Service Catalog Listing: [Example](../../../../examples/ev-charging/v2/02_on_discover/ev-charging-discovery-catalog.json)

The `@context` and `@type` on each attribute object (`resourceAttributes`, `offerAttributes`, `considerationAttributes`) bring **true semantic meaning** to the payload, allowing any system to interpret the data consistently based on shared schema definitions.

CPOs place their catalogs on the discovery service with `catalog/publish` and receive a result per catalog in `catalog/on_publish`: [publish](../../../../examples/ev-charging/v2/23_catalog_publish/ev-charging-catalog-publish.json) → [on_publish](../../../../examples/ev-charging/v2/24_catalog_on_publish/ev-charging-catalog-on-publish.json).

Note: This is just an example catalog. CPOs are encouraged to innovate on various catalog offerings that involve charging services \+ add\_ons, green charging, etc. More such examples will be added to this document in future releases.

This section outlines the `catalogs` array returned in on\_discover. A Beckn 2.0 LTS catalog has a single `provider`, so a search that matches several CPOs returns one catalog per CPO. Each catalog includes:

1. **id**: Catalog identifier.  
2. **descriptor**: Human-readable description (`name`, `shortDesc`).  
3. **bppId / bppUri**: The BPP serving this catalog.  
4. **provider**: The CPO (`id`, `descriptor.name`) and `availableAt[]`, its station locations (`geo` as a GeoJSON point, `address`). Spatial discovery matches on `provider.availableAt[*].geo`.  
5. **resources**: The chargers, each with:  
   * **id**: Charger identifier.  
   * **descriptor**: Display data (`name`, `shortDesc`, `longDesc`).  
   * **resourceAttributes**: EV-charging specifics from the `ChargingService` pack (`@context` / `@type` point at `EvChargingService/v2.0`):  
     * **connectorType** (e.g., CCS2) and **connectorFormat** (e.g., CABLE).  
     * **powerType** (e.g., DC, AC\_3\_PHASE), **maxPowerKW** / **minPowerKW** and **chargingSpeed**.  
     * **evseId**, **vehicleType** (e.g., 4-WHEELER) and **reservationSupported**.  
     * **chargingStation**: Station `id` and `serviceLocation` (`geo`, `address`).  
     * **amenityFeature** (e.g., RESTAURANT, WI-FI) and **parkingType**.  
6. **offers**: The tariffs for these chargers; see [Offers as part of the Catalog](#132121-offers-as-part-of-the-catalog).

The item `category`, `rateable` flag and aggregate `rating` of the earlier shape have no Beckn 2.0 LTS equivalent and are not carried.
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

##### 13.2.1.2.1. Offers as part of the Catalog

While browsing the charging app for a session, Srilekha notices a banner:  
“Limited Time Offer: ₹20 off when you charge above 5 kWh – Valid till Sunday\!”  
User Journey:  
Discovery  
Srilekha searches for a charger.  
The app shows eligible stations with a badge or label indicating the reward:

* “Offer: ₹20 off above 5 kWh”  
* Visible next to charger name or on charger details screen  
* Optional “Know More” link to view:  
  * Offer conditions  
  * Validity window  
  * Eligible locations

Charging session initiation  
Srilekha selects a charger that displays the reward.  
Before starting, she sees a preview:

* Estimated cost based on kWh  
* Reward condition reminder: “Charge ≥5 kWh to get ₹20 off”  
* Final price estimate with and without reward

Charging  
While charging:

* The app shows real-time updates (optional):  
  * Energy delivered  
  * How close he is to hitting the reward threshold  
  * “You will unlock ₹20 off\!” once 5 kWh is crossed

If the session ends before meeting the threshold, app shows:

* “You used 3.2 kWh \- reward not applied”

**Post-charging**  
Aarav receives a receipt or invoice with a clear breakdown:

* Base charge (e.g., ₹60)  
* Reward discount (e.g., – ₹20)  
* Final amount paid (e.g., ₹40)  
* Message: “Thanks for charging with us. You saved ₹20 with this week’s offer\!”

The example catalog carries plain per-kWh tariffs; a conditional reward like the one above is not covered by the examples.

**offers**: Commercial offers (tariffs) in the CPO's catalog, each with:

1. **id**: Offer identifier.  
2. **descriptor.name**: Offer title.  
3. **provider**: The CPO making the offer (`id`, `descriptor.name`).  
4. **resourceIds**: The chargers (`resources[].id`) the offer covers.  
5. **considerations**: The unit price, as a `PriceSpecification` in `considerationAttributes` (`currency`, `value`, `applicableQuantity`; e.g., 45 INR per 1 KWH).  
6. **validity**: The dates (`startDate`, `endDate`) and daily hours (`startTime`, `endTime`) in which the offer applies; availability-window searches match on these.  
7. **offerAttributes**: `ChargingOffer` terms: `tariffModel` (e.g., PER\_KWH), `idleFeePolicy` and `acceptedPaymentMethods`.

Offer schema in the catalog:

1. The offer's own fields (`id`, `descriptor`, `provider`, `resourceIds`, `considerations`, `validity`) are defined by the Beckn 2.0 LTS core schema and carry no namespace prefix.  
2. Domain data sits in attribute objects that use **JSON-LD**: `offerAttributes` and each `considerationAttributes` carry an `@context` (the pack's context on schema.nfh.global) and an `@type` (`ChargingOffer`, `PriceSpecification`), giving each term a globally unique interpretation.  
3. ONIX validates each attribute object against its pack, enabling consistent validation across systems.

#### 13.2.1.3. `action: select`

- Method: POST
- Use Cases: Adam selects a charging session slot. 
- Request: EV user requests charge worth specific KWH: [Example](../../../../examples/ev-charging/v2/03_select/ev-charging-select.json)

1. **commitments:**  
   1. Defines what the buyer has chosen to purchase or book — in this case, the EV charging service. The contract is still a quote (`status.code` DRAFT).  
   2. `resources[]` names the specific charger (`id`) and the energy requested as `quantity` (2.5 KWH), representing the intended energy consumption for that session.  
   3. `offer` is the tariff chosen from the catalog (`id`, `resourceIds`, and `considerations` with the unit price).  
2. **participants:** The CPO (`ecopower-charging`) and the driver, whose contact details are in the `Consumer` pack (`participantAttributes.person`).  
3. **contractAttributes** (`ChargingSession` pack):  
   1. `preferences.startTime` / `preferences.endTime`: Proposed charging window chosen by the user or system.  
   2. `buyerFinderFee`: The BAP's finder fee (`feeType`, `feeValue`).  
4. The select carries no vehicle details. Compatibility is matched at discovery against the charger's `resourceAttributes` (`connectorType`, `vehicleType`); see 13.2.1.1.3.

<details>
<summary><a href="../../../../examples/ev-charging/v2/03_select/ev-charging-select.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "select",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b16f4529-c67a-5b55-b4af-a95a8898b9c1",
    "timestamp": "2024-01-15T10:30:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "contractAttributes": {
        "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
        "@type": "ChargingSession",
        "buyerFinderFee": {
          "feeType": "PERCENTAGE",
          "feeValue": 2.5
        },
        "preferences": {
          "startTime": "2025-12-20T10:00:00Z",
          "endTime": "2025-12-20T11:30:00Z"
        }
      }
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.4. `action: on_select` 

- Method: POST
- Use Cases: Adam receives an estimated quotation for the selected slot. 
- Request: CPO responds with dynamically calculated quote: [Example](../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select.json)

1. **commitments:**  
   1. Returned by the BPP to confirm what is being quoted: the charger (`resources[].id`), the energy (`quantity`, 2.5 KWH) and the accepted `offer` with its tariff (45 INR per KWH in `offer.considerations`).  
   2. The charger's technical details (connector type, power) are not repeated; they are in its catalog `resourceAttributes`.  
   3. This ensures that the buyer and provider are aligned before moving to booking.  
2. **consideration:**  
   1. Contains the computed **estimated price** based on the selection: one entry with `status.code` QUOTED.  
   2. Its `considerationAttributes` (`PriceSpecification`) give the total `value` (144.43 INR) and a `components[]` **breakup** that adds up to it: UNIT (session cost), SURCHARGE (surge), DISCOUNT (offer), and FEE (service fee, overcharge estimation, buyer finder fee).  
   3. This is a **pre-confirmation cost estimate**, enabling the buyer to review pricing before proceeding to init.

Recommendations for BPP:

1. on\_select payload MUST have a quotation (`consideration`) with detailed breakup (`components`) for the selected time slot based on the parameters provided by the user in the select request.

Variants: a slot that is already booked returns the contract with an `error` beside `message` (`BIZ_FULFILLMENT_UNAVAILABLE`, pointing at `contractAttributes.preferences`): [Example](../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select-slot-unavailable.json). A balance still owed from an earlier session is added to the next quote as a FEE component: [Example](../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select-outstanding-dues.json).

<details>
<summary><a href="../../../../examples/ev-charging/v2/04_on_select/ev-charging-on-select.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_select",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b16f4529-c67a-5b55-b4af-a95a8898b9c1",
    "timestamp": "2024-01-15T10:30:05Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "contractAttributes": {
        "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
        "@type": "ChargingSession",
        "buyerFinderFee": {
          "feeType": "PERCENTAGE",
          "feeValue": 2.5
        },
        "preferences": {
          "startTime": "2025-12-20T10:00:00Z",
          "endTime": "2025-12-20T11:30:00Z"
        }
      }
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

##### 13.2.1.4.1. Surge Pricing

Surge pricing is an uplift applied on top of the base charging tariff during peak conditions (for example, certain hours or high-demand locations).  
User Journey:  
Discovery  
While searching for a charger around 6:15 PM, Srilekha sees a warning icon and note:  
“Peak-hour surge: +20% between 6 PM – 9 PM.”  
The app highlights this surcharge in:

* The station list view (via badge or icon)  
* The charger details page  
* A “Know More” section that explains:  
  * Why the surge is applied  
  * When and where it applies  
  * How the uplift is calculated against the base fare

Session preview  
Before starting, the app shows the full estimated cost with the same components used in the canonical example:

* Base session cost (45 INR/kWh × 2.5 kWh): ₹112.50  
* Surge pricing uplift (20% of energy cost): ₹22.50  
* Service fee: ₹10.00  
* Overcharge estimate (0.3 kWh, refunded if unused): ₹13.50  
* Promotional discount (15% of energy cost): −₹16.88  
* Buyer finder fee (2.5% of energy cost): ₹2.81  
* Estimated total: ₹144.43

Mid-session  
While charging (e.g., after 3.4 kWh delivered), the UI keeps a running tally so the user can see how surge pricing is influencing the bill:

* Base energy accrued: ₹67.50 (3.4 kWh of the 45 INR/kWh)  
* Surge uplift (20% of accrued base): ₹13.50  
* Running subtotal so far: ₹81.00 (service fee, buffer, discount, and buyer finder fee are applied at session close)

Post-charging  
When the session completes, Srilekha receives an itemized receipt that matches the quotation components:

* Energy Delivered: 5.0 kWh (bundle)  
* Base session cost: ₹112.50 (45 INR/kWh × 2.5 kWh)  
* Surge pricing uplift (20% of energy cost): ₹22.50  
* Service fee: ₹10.00  
* Overcharge estimate (refunded if unused): ₹13.50  
* Offer discount (15% of energy cost): −₹16.88  
* Buyer finder fee (2.5% of energy cost): ₹2.81  
* Total Payable: ₹144.43 (the final bill for the full 2.5 kWh is ₹130.93; the unused ₹13.50 estimate is refunded)

Quote Information:

* message.contract.consideration[0].considerationAttributes.value: Total estimated price for the service (e.g., 144.43 INR after applying offer discount and fees)  
* message.contract.consideration[0].considerationAttributes.currency: Currency of the total estimated price (e.g., "INR")  
* message.contract.consideration[0].considerationAttributes.components: Itemized breakdown of the total estimated price reflecting the components below (mirrors the on\_select example above):  
  * type: Kind of charge (UNIT, SURCHARGE, DISCOUNT, FEE)  
  * description: Description of the charge (e.g., "Base charging session cost (45 INR/kWh × 2.5 kWh)", "Surge price (20%)", "Service fee", "Overcharge estimation", "Offer discount (15%)", "Buyer finder fee (2.5%)")  
  * value: Value of the individual charge in the breakup (positive for charges, negative for discounts)  
  * currency: Currency of the individual charge in the breakup  
  * Breakup typically includes: base charge = 112.50 INR (45 INR/kWh × 2.5 kWh), surge (20%) = 22.50 INR, offer discount (15%) = −16.88 INR, service fee = 10.00 INR, overcharge estimate = 13.50 INR, and buyer finder fee (2.5%) = 2.81 INR

#### 13.2.1.5. `action: init`

Loyalty Program and Authorization Process:

The system handles two different scenarios for loyalty programs and authorization:

Example Individual Customer Approach:

* User provides their mobile number in the billing details  
* The BPP may check the user's registered mobile number to identify any active loyalty programs attached to it  
* If loyalty programs are found, the BPP can automatically adjust discounts in the quote based on the customer's loyalty status  
* This approach provides seamless discount application without requiring additional user input

Example B2B Fleet Approach:

* B2B deals typically happen offline, where fleet operators and CPOs (Charge Point Operators) establish commercial agreements outside of the Beckn protocol  
* Fleet drivers may choose an option indicating they have a B2B loyalty program  
* The fleet driver could provide an OTP received from the BPP on their registered mobile number  
* The BPP validates the OTP and adjusts the final quote based on the B2B loyalty program benefits  
* This approach ensures fleet-specific pricing and discounts are applied correctly

Note: These are example implementation approaches. Different networks may choose alternative methods for loyalty program integration, such as QR code scanning, app-based authentication, RFID cards, or other identification mechanisms depending on their technical infrastructure and business requirements.

- Method: POST
- Use Cases: The BAP agrees to collect the payment and sends the payload along with its settlement account details for reconciliation.
- Request: The BAP app requests the final quote and payment terms by submitting billing details along with approval from the BPP to collect the payment: [Example](../../../../examples/ev-charging/v2/05_init/ev-charging-bap-payment-init.json)

1. **contract.id:**
   When the BAP collects the payment, it generates the contract (order) id (`order-ev-charging-001`) and includes it in the init payload sent to the BPP.
2. **commitments:**  
   Echo the charger, the energy (`resources[].quantity`) and the accepted `offer` from on\_select, ensuring both BAP and BPP have an agreed reference for the tariff and the charger at the time of selection.  
3. **consideration:**  
   The price quoted by the BPP in on\_select (`status.code` QUOTED), consolidating all applicable charges.  
   1. The `components` array of its `PriceSpecification` itemizes each cost component (e.g., session cost, service fee) to enable transparency in pricing and later reconciliation.
4. **settlements:**  
   The payment terms, in `settlementAttributes` (`Payment` pack): `beckn:beneficiary` BAP (the consumer app collects), `beckn:amount`, `beckn:paymentStatus` INITIATED, and the BAP's settlement account in `beckn:paymentAttributes.settlementAccounts`.

Recommendations for BAP:

1. init payload MUST contain the payment terms (`settlements`) in addition to the details which were part of the select request; the user's contact details are in the driver's `participants` entry (`Consumer` pack).

<details>
<summary><a href="../../../../examples/ev-charging/v2/05_init/ev-charging-bap-payment-init.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "init",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6c48217c-aa0c-5bd7-bb7c-1a73c77c9ed4",
    "timestamp": "2025-01-27T10:00:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "DRAFT",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "INITIATED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:beneficiary": "BAP",
            "beckn:paymentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
              "@type": "PaymentSettlement",
              "settlementAccounts": [
                {
                  "beneficiaryId": "example-bap.com",
                  "accountHolderName": "Example BAP Solutions Pvt Ltd",
                  "accountNumber": "9876543210123",
                  "ifscCode": "HDFC0009876",
                  "bankName": "HDFC Bank",
                  "vpa": "example-bap@paytm"
                }
              ]
            }
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.6. `action: on_init`

- Method: POST
- Use Cases: The BAP receives approval for payment collection on the behalf of BPP.
- Request: The CPO confirms acceptance of BAP-led payment collection and shares the BPP’s settlement account details: [Example](../../../../examples/ev-charging/v2/06_on_init/ev-charging-bap-payment-on-init.json)

  1. **settlements:**  
      Represents the payment terms returned by the BPP after the init stage — this confirms how the user can complete payment before confirmation. The `Payment` pack in `settlementAttributes` keeps `beckn:beneficiary` BAP and `beckn:amount`, and `beckn:paymentAttributes.settlementAccounts` now lists both the BAP's and the BPP's accounts for reconciliation.  
  2. **beckn:paymentStatus / settlements[].status:**  
      Indicate the current payment state. In this stage, INITIATED (with the settlement in DRAFT) means payment is yet to be completed by the buyer.  
  3. **contract.id:**  
      The contract (order) id the BAP generated in init, echoed back.  
  4. When the BPP collects instead (walk-in, 13.1.2.6), the settlement has `beckn:beneficiary` BPP and adds the buyer-facing `beckn:paymentURL`, a `beckn:txnRef` and the `beckn:acceptedPaymentMethod` list. No invoice link is sent at this stage; it follows after the session (see 13.1.2.18).

  Recommendations for BPP:

  1. on\_init payload MUST have the settlement account details of the BPP (`beckn:paymentAttributes.settlementAccounts`) in addition to the details which were part of the on\_select payload.

<details>
<summary><a href="../../../../examples/ev-charging/v2/06_on_init/ev-charging-bap-payment-on-init.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_init",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6c48217c-aa0c-5bd7-bb7c-1a73c77c9ed4",
    "timestamp": "2025-01-27T10:00:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "DRAFT",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "INITIATED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:beneficiary": "BAP",
            "beckn:paymentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
              "@type": "PaymentSettlement",
              "settlementAccounts": [
                {
                  "beneficiaryId": "example-bap.com",
                  "accountHolderName": "Example BAP Solutions Pvt Ltd",
                  "accountNumber": "9876543210123",
                  "ifscCode": "HDFC0009876",
                  "bankName": "HDFC Bank",
                  "vpa": "example-bap@paytm"
                },
                {
                  "beneficiaryId": "example-bpp.com",
                  "accountHolderName": "EcoPower Charging Solutions Pvt Ltd",
                  "accountNumber": "1234567890123",
                  "ifscCode": "HDFC0001234",
                  "bankName": "HDFC Bank",
                  "vpa": "ecopower@paytm"
                }
              ]
            }
          }
        }
      ]
    }
  }
}

```
</details>



- Successful Response: In cases where BPP is collecting payment directly using a payment link and the payment terms dictate that the payment needs to be completed PRE-ORDER, once the payment completion event happens at the BPP’s payment gateway, the BPP may send an unsolicited on\_status call to the BAP with the settlement's `beckn:paymentStatus` changed to COMPLETED (`settlements[].status` COMPLETE). Once the BAP receives the same they can trigger the confirm API with that COMPLETED settlement.

However, when the BAP collects the payment, an unsolicited on\_status call is not required.

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.7. `action: on_status` (payment)

- Method: POST
- Use Cases: Adam receives a payment confirmation from BPP.
- Request: In case the BAP is not receiving on\_status from the BPP, it may also allow the user to declare they have completed payment and confirm the order using a user input at the BAP.
- CPO sends the status of the payment: [Example](../../../../examples/ev-charging/v2/06_on_status_1/ev-charging-bpp-payment-check-on-status.json). The settlement shows `beckn:paymentStatus` COMPLETED with `beckn:paidAt` and `beckn:txnRef`.

<details>
<summary><a href="../../../../examples/ev-charging/v2/06_on_status_1/ev-charging-bpp-payment-check-on-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0ae4d99e-80ea-5f68-959a-84992fd40d6a",
    "timestamp": "2025-01-27T10:05:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.8. `action: confirm`

- Method: POST
- Use Cases: Adam accepts the terms of the order and confirms the order.
- Request: EV user confirms reservation of a slot at a particular charging station at a particular time: [Example](../../../../examples/ev-charging/v2/07_confirm/ev-charging-bap-payment-confirm.json)
  1. **settlements:**  
      Captures the *final* payment record at confirmation — this confirms the completion of the payment flow.  
  2. **beckn:paymentStatus:**  
      Set to COMPLETED (with `settlements[].status` COMPLETE), indicating the payment has been successfully received (i.e., no longer pending or provisional).  
  3. **beckn:amount:**  
      The amount received (144.43 INR), matching the quoted `consideration`.  
  4. **beckn:txnRef / beckn:paidAt:**  
      The gateway-side transaction reference and the time of payment, for traceability in settlements.  
  5. **beckn:beneficiary:**  
      Who collected the payment. The example shows BPP (the CPO's payment link, as in the walk-in flow); when the consumer app collects, the settlement keeps `beckn:beneficiary` BAP and the BAP sends COMPLETED in this confirm.  
  6. The example carries no gateway name, payment method used, receipt number or invoice link; the invoice link follows after the session (see 13.1.2.18).

  Recommendations for BAP:

  1. confirm payload MUST have a proof of payment in the settlement (`beckn:paymentStatus` COMPLETED with `beckn:txnRef`) if the payment is collected by BPP, in addition to the details which were part of the init request.


<details>
<summary><a href="../../../../examples/ev-charging/v2/07_confirm/ev-charging-bap-payment-confirm.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "44a92229-47dd-50ce-ad4b-220b7dc46ade",
    "timestamp": "2025-01-27T10:04:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "DRAFT"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "DRAFT"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "QUOTED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:beneficiary": "BAP",
            "beckn:paymentAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
              "@type": "PaymentSettlement",
              "settlementAccounts": [
                {
                  "beneficiaryId": "example-bap.com",
                  "accountHolderName": "Example BAP Solutions Pvt Ltd",
                  "accountNumber": "9876543210123",
                  "ifscCode": "HDFC0009876",
                  "bankName": "HDFC Bank",
                  "vpa": "example-bap@paytm"
                },
                {
                  "beneficiaryId": "example-bpp.com",
                  "accountHolderName": "EcoPower Charging Solutions Pvt Ltd",
                  "accountNumber": "1234567890123",
                  "ifscCode": "HDFC0001234",
                  "bankName": "HDFC Bank",
                  "vpa": "ecopower@paytm"
                }
              ]
            },
            "beckn:txnRef": "BAP-UPI-7781234567",
            "beckn:paidAt": "2025-01-27T10:03:40Z"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.9. `action: on_confirm`

- Method: POST
- Use Cases: Adam receives an order ID and QR code, plus a navigation link to the charging site.
- Request: 
  CPO responds with confirmed slot: [Example](../../../../examples/ev-charging/v2/08_00_on_confirm/ev-charging-on-confirm.json)

  **performance:**  
  Represents the charging session the booking creates: one entry linked to the commitment (`commitmentIds`), with `status.code` PENDING.

  * **performanceAttributes** (`ChargingSession` pack): `sessionStatus` PENDING (booked, not yet charging) and the connector booked (`connectorType`, `maxPowerKW`); BAPs/BPPs use `sessionStatus` for workflow automation.  
  * **status:** `contract.status.code` and `commitments[].status.descriptor.code` move to ACTIVE, and `consideration[].status.code` to AGREED.

  Recommendations for BPP:

  1. on\_confirm payload MUST have the contract id assigned to this order. Payload MUST also have the current session state (`performance`) of the contract.  
  2. These details are in addition to the details which were part of the on\_init payload.

<details>
<summary><a href="../../../../examples/ev-charging/v2/08_00_on_confirm/ev-charging-on-confirm.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_confirm",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "0e6f056f-ea93-5c29-bc8f-6f32e90d644c",
    "timestamp": "2025-01-27T10:05:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.10. `action: update` (start charging)

Physical Charging Process:

Before initiating the charging session through the API, the EV driver must complete the following physical steps at the charging station:

1. Drive to the charging point: The user arrives at the reserved charging location at the scheduled time  
2. Plug the vehicle: Connect the charging cable from the EVSE (Electric Vehicle Supply Equipment) to their vehicle's charging port  
3. Authenticate, if the CPO requires it (for example with an OTP or by scanning the charger's QR code). The examples carry no OTP or other authorization data, so this check is outside the messages shown in this guide.

Once these physical steps are completed, the charging session can be initiated through the update API call.

- Method: POST
- Use Cases: On arrival, Adam scans the charger’s **QR code**. The backend matches it to her **reservation ID** and starts charging.
- Request: EV user starts a charging session: [Example](../../../../examples/ev-charging/v2/09_update/ev-charging-01-session-start-update.json)
  **performance:** Carries the booked charging session the user asks to start, identified by the contract `id` and the `performance[].id`.

  * `performanceAttributes.sessionStatus` (and `performance[].status.code`) is still PENDING in the request; the BPP starts the session and answers in on\_update with ACTIVE, which indicates that energy delivery is in progress.  
  * This state evolves as updates continue from the BPP. The values used across the examples are PENDING, ACTIVE, INTERRUPTED, STOP (the user's stop request, 13.2.1.16) and COMPLETED.

  The rest of the contract (`commitments`, `consideration`, `settlements`) is echoed from on\_confirm. The request carries no OTP or authorization data; authenticating the driver at the charger is not covered by the examples.

<details>
<summary><a href="../../../../examples/ev-charging/v2/09_update/ev-charging-01-session-start-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b9c96f71-7fc1-5f21-b0ad-1d81df131ef5",
    "timestamp": "2025-01-27T10:15:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "PENDING"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "connectorType": "CCS2",
            "maxPowerKW": 50,
            "sessionStatus": "PENDING"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.11. `action: on_update` (start charging)

- Method: POST
- Use Cases: Adam receives an acknowledgement on charging initialisation.
- Request: CPO starts a charging session: [Example](../../../../examples/ev-charging/v2/10_on_update/ev-charging-session-on-update.json)

  **performance:** Communicates the *real-time charging session state* as sent back by the BPP.

  1. **status.code:** ACTIVE — confirms that the EV charging session has officially started at the station.  
  2. **performanceAttributes.sessionStatus:** ACTIVE (from PENDING) — a standardized machine-readable code that BAPs can use to update the user interface, start timers, or calculate live charging duration.

  If the charger cannot start (EVSE inoperative), the on\_update carries an `error` beside `message` (`BIZ_FULFILLMENT_UNAVAILABLE`, with the OCPI cause in `details.cause`) and the session stays PENDING: [Example](../../../../examples/ev-charging/v2/10_on_update/ev-charging-session-start-rejected-on-update.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/10_on_update/ev-charging-session-on-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "b9c96f71-7fc1-5f21-b0ad-1d81df131ef5",
    "timestamp": "2025-01-27T10:15:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "ACTIVE"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "ACTIVE",
            "connectorType": "CCS2",
            "maxPowerKW": 50
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.12. `action: status`

- Method: POST
- Use Cases: Adam initiates a request to track the charging progress of the active charging session.
- Request: EV User tracks a live charging session in real-time: [Example](../../../../examples/ev-charging/v2/11_status/ev-charging-session-track.json)

  The request names the contract (`id`, `status`, `participants`, `commitments`); the BPP answers with the current session in on\_status.

  There is no callback URL or tracking flag in the request. For a live tracking link, the BAP calls `track` and receives the URL in `on_track` (`tracking.url`, with the session state in `trackingAttributes`): [track](../../../../examples/ev-charging/v2/21_track/ev-charging-session-track.json) → [on\_track](../../../../examples/ev-charging/v2/22_on_track/ev-charging-session-on-track.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/11_status/ev-charging-session-track.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "98d6a0a2-5219-57fd-8737-e0c09307973c",
    "timestamp": "2025-01-27T17:00:40.065Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.13. `action: on_status`

- Method: POST
- Use Cases: Adam receives the current charging progress.
- Request: EV User receives live charging session details in real-time: [Example](../../../../examples/ev-charging/v2/12_on_status/ev-charging-session-on-track.json)

  **performance[].performanceAttributes** (`ChargingSession` pack):  
  `sessionStatus` ACTIVE and **chargingTelemetry**, the real-time measurements captured during the session as a list of readings.

  1. Each reading has **eventTime** and **metrics[]** (`name`, `value`, `unitCode`) with multiple *live telemetry readings*, including:  
    1. **STATE\_OF\_CHARGE:** Vehicle’s current battery level (62.5% → 65%, PERCENTAGE).  
    2. **POWER:** Current charging power rate (18.4 → 17.1 KW).  
    3. **ENERGY:** Energy delivered (10.2 → 11.1 KWH).  
    4. **VOLTAGE:** Supply voltage level (392 → 388 VLT).  
    5. **CURRENT:** Electrical current being drawn (47.0 → 44.2 AMP).

  **eventTime** shows when each reading was recorded — helps synchronize live dashboards or notifications on the BAP side.

  The running cost is not part of this example; the session's `totalCost` appears with the metered energy (`meteredEnergyKWh`) in the final bill after stop and in the power-cut on\_status (13.2.1.14).

<details>
<summary><a href="../../../../examples/ev-charging/v2/12_on_status/ev-charging-session-on-track.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "98d6a0a2-5219-57fd-8737-e0c09307973c",
    "timestamp": "2025-01-27T17:00:42Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "ACTIVE"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "ACTIVE",
            "chargingTelemetry": [
              {
                "eventTime": "2025-01-27T17:00:00Z",
                "metrics": [
                  {
                    "name": "STATE_OF_CHARGE",
                    "value": 62.5,
                    "unitCode": "PERCENTAGE"
                  },
                  {
                    "name": "POWER",
                    "value": 18.4,
                    "unitCode": "KW"
                  },
                  {
                    "name": "ENERGY",
                    "value": 10.2,
                    "unitCode": "KWH"
                  },
                  {
                    "name": "VOLTAGE",
                    "value": 392,
                    "unitCode": "VLT"
                  },
                  {
                    "name": "CURRENT",
                    "value": 47.0,
                    "unitCode": "AMP"
                  }
                ]
              },
              {
                "eventTime": "2025-01-27T17:05:00Z",
                "metrics": [
                  {
                    "name": "STATE_OF_CHARGE",
                    "value": 65.0,
                    "unitCode": "PERCENTAGE"
                  },
                  {
                    "name": "POWER",
                    "value": 17.1,
                    "unitCode": "KW"
                  },
                  {
                    "name": "ENERGY",
                    "value": 11.1,
                    "unitCode": "KWH"
                  },
                  {
                    "name": "VOLTAGE",
                    "value": 388,
                    "unitCode": "VLT"
                  },
                  {
                    "name": "CURRENT",
                    "value": 44.2,
                    "unitCode": "AMP"
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  }
}

```
</details>

EV User receives live charging session details in real-time: [Example](../../../../examples/ev-charging/v2/12_on_status/ev-charging-session-on-track.json)

**performance[].performanceAttributes** (`ChargingSession` pack):  
`sessionStatus` ACTIVE and **chargingTelemetry**, the real-time measurements captured during the session as a list of readings.

1. Each reading has **eventTime** and **metrics[]** (`name`, `value`, `unitCode`) with multiple *live telemetry readings*, including:  
   1. **STATE\_OF\_CHARGE:** Vehicle’s current battery level (62.5% → 65%, PERCENTAGE).  
   2. **POWER:** Current charging power rate (18.4 → 17.1 KW).  
   3. **ENERGY:** Energy delivered (10.2 → 11.1 KWH).  
   4. **VOLTAGE:** Supply voltage level (392 → 388 VLT).  
   5. **CURRENT:** Electrical current being drawn (47.0 → 44.2 AMP).

**eventTime** shows when each reading was recorded — helps synchronize live dashboards or notifications on the BAP side.

The running cost is not part of this example; the session's `totalCost` appears with the metered energy (`meteredEnergyKWh`) in the final bill after stop and in the power-cut on\_status (13.2.1.14).

- Successful Response:

<details>
<summary>Example json :rocket:</summary>
```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.14. asynchronous `action: on_status` (temporary connection interruption)

1. This is used in case of a connection interruption during a charging session.  
2. Applicable only in case of temporary connection interruptions, BPPs expect to recover from these connection interruptions in the short term.  
3. BPP notifies the BAP about this interruption using an unsolicited on\_status callback.  
4. NOTE: if the issue remains unresolved and BPP expects it to be a long term issue, BPP must send an unsolicited on\_update to the BAP with relevant details.

###### 13.2.1.14.0.1. **A)Undercharge (Power Cut Mid-Session)**

Scenario: The user reserves a 12:45–13:30 slot and prepays ₹500 in the app to the BPP platform. Charging starts on time; the app shows ETA and live ₹/kWh. At 13:05 a power cut stops the charger. The charger loses connectivity and can’t push meter data. The app immediately shows: “Session interrupted—only actual energy will be billed. You may unplug or wait for power to resume.”

Handling & experience:

* User side: Clear banner \+ push notification; live session switches to “Paused (site offline)”. If the user leaves, the session is treated as completed-so-far.  
* CPO/BPP side: When power/comms return, the CMS syncs the actual kWh delivered and stop timestamp.  
* Settlement logic:  
  * If prepaid: compute final ₹ from synced kWh; auto-refund the unused balance to the original instrument; issue invoice.  
  * If auth-hold/UPI mandate (preferred): capture only the final ₹; release remainder instantly.

Contract/UI terms to bake in: “Power/interruption protection: you are charged only for energy delivered; any excess prepayment is automatically refunded on sync.” Show an estimated refund immediately, and a final confirmation after sync.

In the messages: once the meter data has synced, an unsolicited on\_status closes the contract (`status.code` COMPLETE, commitment CLOSED) with the session INTERRUPTED and its metered values (`meteredEnergyKWh`, `meteredDurationMinutes`, `totalCost`), a FINAL `consideration` for the 1.2 kWh delivered (68.05 INR), and a second settlement with `beckn:paymentStatus` REFUNDED and `beckn:beneficiary` BUYER for the rest of the prepayment (75.90 INR): [Example](../../../../examples/ev-charging/v2/13_on_status/ev-charging-session-undercharge-refund-on-status.json)

###### 13.2.1.14.0.2. **B) Overcharge (Charger Offline to CMS; Keeps Dispensing)**

Scenario: The user reserves a slot with ₹500 budget. Charging begins; mid-session the charger loses connectivity to its CMS (e.g., basement, patchy network). Hardware keeps dispensing; when connectivity returns, the log shows ₹520 worth of energy delivered.

Handling & experience:

* User side: The app shows “Connectivity issue at site—session continues locally. The final bill will be reconciled in sync.” On sync, the app shows: “Final: ₹520 for X kWh; ₹30 auto-settled.”  
* CPO/BPP side: Charger syncs start/stop/kWh; CMS reconciles vs. contract.

Settlement logic (three safe patterns):

* Buffer in quote (prepaid with overage provision):  
  * Quote line items include: “Energy (₹500) \+ Overage Provision (₹50) — unused portion auto-refunded.”  
  * BPP collects ₹550; captures actual ₹520; refunds ₹30 immediately on sync.  
* Authorization hold / UPI one-time mandate (preferred):  
  * Place a hold/mandate for ₹550; capture ₹520, release ₹30. No debit-then-refund friction.  
* Top-up debit fallback:  
  * If only ₹500 was captured and no mandate exists, the app auto-initiates a ₹20 top-up request (same instrument), with clear messaging and a single-tap confirmation.

Contract/UI terms to bake in: “Offline continuity & overage: sessions may continue locally during short connectivity loss; final billing reflects meter data. We place a buffer hold to avoid delays; unused amounts are released automatically.”

In the messages: the final on\_update bills the metered 2.8 kWh, with a FEE component for the 0.3 kWh delivered while the charger was offline (FINAL `consideration` of 144.43 INR, equal to the 144.43 INR paid, because the 0.3 kWh overcharge used up the overcharge estimate exactly), so nothing is refunded or owed. An overcharge beyond the estimate leaves a `DRAFT` settlement with `beckn:paymentStatus` PENDING and `beckn:beneficiary` BPP for the amount still owed: [Example](../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-overcharge-on-update.json)

API Implementation: The above under and overcharge scenarios are supported through Beckn protocol callbacks:

* Interruption notification: BPP informs BAP about any session interruption using unsolicited on\_status callback (`sessionStatus` INTERRUPTED)  
* Final billing adjustment: The adjusted bill reflecting overcharge or undercharge reconciliation is conveyed as a FINAL `consideration` for the metered energy, in on\_update (or in on\_status after a power cut), with any refund as a further `REFUNDED` settlement to the buyer, or any amount still owed as a `DRAFT` / `PENDING` settlement  
* Real-time status updates: Continuous session monitoring and status communication ensure transparent billing for actual energy delivered

- Method: POST
- Use Cases: Adam receives notification when there is any error during an ongoing charging session.
- Request: EV user reveives details in case of any error during a charging session: [Example](../../../../examples/ev-charging/v2/13_on_status/ev-charging-session-interrupt-on-status.json). The example sets `performance[].status.code` and `performanceAttributes.sessionStatus` to INTERRUPTED; the contract stays ACTIVE.

<details>
<summary><a href="../../../../examples/ev-charging/v2/13_on_status/ev-charging-session-interrupt-on-status.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_status",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6a60f5cf-609d-538d-8952-0926b68fe57f",
    "timestamp": "2025-01-27T13:07:02Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "AGREED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "INTERRUPTED"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "INTERRUPTED"
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        }
      ]
    }
  }
}

```
</details>
- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.15. Asynchronous `action: on_update` (stop charging)

- Method: POST
- Use Cases: Use Cases: Adam receives an update when the charging session ends. This might reflect payment adjustment as per use.
- Request: EV user receives final order details after the charging session ends: [Example](../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json)

  1. **performance:**  
    `sessionStatus` COMPLETED (and `performance[].status.code` COMPLETED) indicates that the charging session has ended successfully and all energy delivery is complete; `contract.status.code` is COMPLETE and the commitment CLOSED.  
  2. **consideration:**  
    Contains the **final bill** (`status.code` FINAL) returned after charging completion — its `PriceSpecification` has the total `value` and the complete cost breakdown for the session in `components` (e.g., energy cost and service fee).  
  3. **settlements:**  
    Confirms that the corresponding payment has been successfully captured (`beckn:paymentStatus` COMPLETED).  
    Includes the transaction reference (`beckn:txnRef`), payment time (`beckn:paidAt`) and `beckn:beneficiary` for settlement and customer records. A refund appears as a further settlement with `beckn:paymentStatus` REFUNDED and `beckn:beneficiary` BUYER.

  Variants: battery full early, where the bill covers the 2 kWh delivered (106.75 INR) and 37.68 INR is refunded: [Example](../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-undercharge-on-update.json). Charger offline and overcharging: see B above.

<details>
<summary><a href="../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "722a01ac-5cb9-5013-8d0b-c659573f840a",
    "timestamp": "2025-01-27T11:45:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "COMPLETE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "CLOSED"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "FINAL"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 130.93,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "COMPLETED"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "COMPLETED",
            "meteredEnergyKWh": 2.5,
            "totalCost": {
              "inclVat": 130.93
            }
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        },
        {
          "id": "settlement-002",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "refund-001",
            "beckn:paymentStatus": "REFUNDED",
            "beckn:amount": {
              "currency": "INR",
              "value": 13.5
            },
            "beckn:beneficiary": "BUYER"
          }
        }
      ]
    }
  }
}

```
</details>


#### 13.2.1.16. Synchronous/Asynchronous on\_update (stop charging)

- Method: POST 
- Use Case: Adam receives an update when the charging session ends. This might reflect payment adjustment as per use.
- EV user ends the charging session (`update` with `performanceAttributes.sessionStatus` STOP): [Example](../../../../examples/ev-charging/v2/14_01_update/ev-charging-session-end-update.json)
- Receives on_update response with completed status. [Example](/examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json)
- Request:

<details>
<summary><a href="../../../../examples/ev-charging/v2/14_02_on_update/ev-charging-session-complete-on-update.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_update",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "722a01ac-5cb9-5013-8d0b-c659573f840a",
    "timestamp": "2025-01-27T11:45:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "COMPLETE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar",
              "telephone": "+91-9876543210",
              "email": "ravi.kumar@example.com"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "CLOSED"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "FINAL"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 130.93,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "performance": [
        {
          "id": "fulfillment-001",
          "status": {
            "code": "COMPLETED"
          },
          "commitmentIds": [
            "commitment-001"
          ],
          "performanceAttributes": {
            "@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession",
            "sessionStatus": "COMPLETED",
            "meteredEnergyKWh": 2.5,
            "totalCost": {
              "inclVat": 130.93
            }
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-123e4567-e89b-12d3-a456-426614174000",
            "beckn:paymentStatus": "COMPLETED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-123456789",
            "beckn:paidAt": "2025-12-19T10:05:00Z",
            "beckn:beneficiary": "BPP"
          }
        },
        {
          "id": "settlement-002",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "refund-001",
            "beckn:paymentStatus": "REFUNDED",
            "beckn:amount": {
              "currency": "INR",
              "value": 13.5
            },
            "beckn:beneficiary": "BUYER"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response:

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.17. `action: cancel`

It’s like when a client calls to cancel an appointment — maybe something came up, or their plans have changed. When they request to cancel, it’s about freeing up that slot and keeping things organized.

**Note:** Users can cancel a reserved charging slot only in accordance with the network or CPO’s cancellation policy. For example, cancellations may only be allowed **at least 3 hours before the scheduled start time**, **only for pre-booked sessions**, or **subject to a small cancellation fee** depending on the operator’s terms.

This API is **NOT** to be used to cancel an ongoing session. To cancel an ongoing session, use the update API.

- Method: POST
- Use Cases: Adam cancels a scheduled charging session.
- Request: EV user cancels a charging slot reservation: [Example](../../../../examples/ev-charging/v2/19_cancel/ev-charging-cancel-reserved-slot.json). The request names the contract (`id`) and its commitments.
- To see the cancellation terms and the refund first without cancelling, send the same call with `context.try: true`: [cancel](../../../../examples/ev-charging/v2/19_cancel/ev-charging-cancel-preview.json) → [on\_cancel](../../../../examples/ev-charging/v2/20_on_cancel/ev-charging-cancel-preview-on-cancel.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/19_cancel/ev-charging-cancel-reserved-slot.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "cancel",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6c4b843d-d746-5bc0-aaf1-b59ec0e54ffc",
    "timestamp": "2025-01-27T12:15:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "ACTIVE"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "user-123"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "person": {
              "id": "user-123"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "ACTIVE"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response:

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.18. `action: on_cancel`

- Method: POST
- Use Cases: Adam receives order cancellation confirmation.  The advance payment will be adjusted as per network/CPO rule.
- Request: CPO cancels a charging session reservation: [Example](../../../../examples/ev-charging/v2/20_on_cancel/ev-charging-bpp-reservation-on-cancel.json). `contract.status.code` is CANCELLED, the commitment CLOSED, and the refund is a settlement with `beckn:paymentStatus` REFUNDED and `beckn:beneficiary` BUYER.
- A CPO can also cancel on its own (for example, a charger fault) with an unsolicited on\_cancel that gives the reason in `contract.descriptor` and refunds in full: [Example](../../../../examples/ev-charging/v2/20_on_cancel/ev-charging-cpo-initiated-on-cancel.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/20_on_cancel/ev-charging-bpp-reservation-on-cancel.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_cancel",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "6c4b843d-d746-5bc0-aaf1-b59ec0e54ffc",
    "timestamp": "2025-01-27T12:15:32Z",
    "ttl": "PT30S"
  },
  "message": {
    "contract": {
      "id": "order-ev-charging-001",
      "status": {
        "code": "CANCELLED"
      },
      "participants": [
        {
          "id": "ecopower-charging",
          "descriptor": {
            "name": "EcoPower Charging Pvt Ltd"
          }
        },
        {
          "id": "user-123",
          "descriptor": {
            "name": "Ravi Kumar"
          },
          "participantAttributes": {
            "@context": "https://schema.nfh.global/Consumer/v2.0/context.jsonld",
            "@type": "Consumer",
            "role": "BUYER",
            "person": {
              "id": "user-123",
              "name": "Ravi Kumar"
            }
          }
        }
      ],
      "commitments": [
        {
          "id": "commitment-001",
          "status": {
            "descriptor": {
              "code": "CLOSED"
            }
          },
          "resources": [
            {
              "id": "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A",
              "quantity": {
                "unitText": "Kilowatt Hour",
                "unitCode": "KWH",
                "unitQuantity": 2.5
              }
            }
          ],
          "offer": {
            "id": "offer-ccs2-60kw-kwh",
            "descriptor": {
              "name": "Per-kWh Tariff - CCS2 60kW"
            },
            "provider": {
              "id": "ecopower-charging",
              "descriptor": {
                "name": "EcoPower Charging Pvt Ltd"
              }
            },
            "resourceIds": [
              "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
            ],
            "considerations": [
              {
                "id": "price-offer-ccs2-60kw-kwh",
                "considerationAttributes": {
                  "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
                  "@type": "PriceSpecification",
                  "currency": "INR",
                  "value": 45.0,
                  "applicableQuantity": {
                    "unitText": "Kilowatt Hour",
                    "unitCode": "KWH",
                    "unitQuantity": 1
                  }
                }
              }
            ]
          }
        }
      ],
      "consideration": [
        {
          "id": "consideration-001",
          "status": {
            "code": "REFUNDED"
          },
          "considerationAttributes": {
            "@context": "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld",
            "@type": "PriceSpecification",
            "currency": "INR",
            "value": 144.43,
            "components": [
              {
                "type": "UNIT",
                "value": 112.5,
                "currency": "INR",
                "description": "Charging energy (45 INR/kWh x 2.5 kWh)"
              },
              {
                "type": "SURCHARGE",
                "value": 22.5,
                "currency": "INR",
                "description": "Surge price (20% of energy cost)"
              },
              {
                "type": "DISCOUNT",
                "value": -16.88,
                "currency": "INR",
                "description": "Offer discount (15% of energy cost)"
              },
              {
                "type": "FEE",
                "value": 10.0,
                "currency": "INR",
                "description": "Service fee"
              },
              {
                "type": "FEE",
                "value": 13.5,
                "currency": "INR",
                "description": "Overcharge estimate (0.3 kWh, refunded if unused)"
              },
              {
                "type": "FEE",
                "value": 2.81,
                "currency": "INR",
                "description": "Buyer finder fee (2.5% of energy cost)"
              }
            ]
          }
        }
      ],
      "settlements": [
        {
          "id": "settlement-001",
          "considerationId": "consideration-001",
          "status": "COMPLETE",
          "settlementAttributes": {
            "@context": "https://schema.nfh.global/Payment/v2.0/context.jsonld",
            "@type": "Payment",
            "beckn:id": "payment-987e6543-e21b-34c5-b567-537725285111",
            "beckn:paymentStatus": "REFUNDED",
            "beckn:amount": {
              "currency": "INR",
              "value": 144.43
            },
            "beckn:paymentURL": "https://payments.bluechargenet-aggregator.io/pay?transaction_id=$transaction_id&amount=$amount",
            "beckn:txnRef": "TXN-987654321",
            "beckn:paidAt": "2025-12-19T17:35:00Z",
            "beckn:beneficiary": "BUYER"
          }
        }
      ]
    }
  }
}

```
</details>

- Successful Response:

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.19. `action: rating`

- Method: POST
- Use Cases: Adam rates the order.
- In Beckn 2.0 LTS the endpoint is `rate` (callback `on_rate`); see [13.1.2.19](#131219-action-rating) for the fields.
- Request: 

<details>
<summary><a href="../../../../examples/ev-charging/v2/15_rating/ev-charging-session-rating.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "rate",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ed611c7a-ad96-5a7e-9730-2013292385c4",
    "timestamp": "2025-01-27T12:00:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "ratingInputs": [
      {
        "target": {
          "id": "fulfillment-001",
          "descriptor": {
            "code": "FULFILLMENT"
          }
        },
        "range": {
          "bestRating": 5,
          "worstRating": 1,
          "ratingValue": 4
        },
        "feedbackFormSubmission": {
          "data": {
            "comments": "Excellent charging experience! The station was clean, easy to find, and the charging was fast and reliable. The staff was helpful and the payment process was smooth.",
            "tags": "fast-charging,easy-to-use,clean-station,helpful-staff,smooth-payment"
          }
        }
      }
    ]
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.20. `action: on_rating`

- Method: POST
- Use Cases: Adam receives an acknowledgement.
- Request: CPO accepts rating: [Example](../../../../examples/ev-charging/v2/16_on_rating/ev-charging-session-on-rating.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/16_on_rating/ev-charging-session-on-rating.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_rate",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "ed611c7a-ad96-5a7e-9730-2013292385c4",
    "timestamp": "2025-01-27T12:00:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "ratings": [
      {
        "target": {
          "id": "fulfillment-001",
          "descriptor": {
            "code": "FULFILLMENT"
          }
        },
        "range": {
          "bestRating": 5,
          "worstRating": 1,
          "ratingValue": 4
        },
        "feedbackFormSubmission": {
          "data": {
            "comments": "Excellent charging experience! The station was clean, easy to find, and the charging was fast and reliable. The staff was helpful and the payment process was smooth.",
            "tags": "fast-charging,easy-to-use,clean-station,helpful-staff,smooth-payment"
          },
          "id": "https://example-bpp.com/feedback/portal"
        }
      }
    ]
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.21. `action: support`

- Method: POST
- Use Cases: Adma reaches out for support.
- Request: EV user contacts support: [Example](../../../../examples/ev-charging/v2/17_support/ev-charging-session-support.json)

<details>
<summary><a href="../../../../examples/ev-charging/v2/17_support/ev-charging-session-support.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "support",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://api.example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bap/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "5bfb2396-247e-57b5-9a5b-2f19181ec67e",
    "timestamp": "2025-01-27T12:15:00Z",
    "ttl": "PT30S"
  },
  "message": {
    "support": {
      "orderId": "order-ev-charging-001",
      "descriptor": {
        "name": "Help with charging session",
        "code": "ORDER"
      },
      "channels": [
        {
          "@context": "https://schema.nfh.global/SupportInfo/v2.1/context.jsonld",
          "@type": "SupportInfo",
          "name": "Ravi Kumar",
          "telephone": "+91-9876543210",
          "email": "ravi.kumar@example.com",
          "hoursAvailable": "Mon–Sun: 6:00 PM - 10:00 PM IST",
          "channels": [
            "PHONE",
            "WHATSAPP"
          ]
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

#### 13.2.1.22. `action: on_support`

- Method: POST
- Use Cases: Raghav receives a response to his support request.
- Request: CPO returns support information: [Example](../../../../examples/ev-charging/v2/18_on_support/ev-charging-session-on-support.json)
- For a ticket raised about a charger fault and later resolved by the CPO, see [support](../../../../examples/ev-charging/v2/17_support/ev-charging-connector-fault-support.json) → [on\_support](../../../../examples/ev-charging/v2/18_on_support/ev-charging-support-resolved-on-support.json).

<details>
<summary><a href="../../../../examples/ev-charging/v2/18_on_support/ev-charging-session-on-support.json">Example json :rocket:</a></summary>

```json
{
  "context": {
    "version": "2.0.0",
    "action": "on_support",
    "networkId": "nfh.global/testnet-evcharging",
    "bapId": "example-bap.com",
    "bapUri": "https://example-bap.com/pilot/bap/energy/v2",
    "bppId": "example-bpp.com",
    "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2",
    "transactionId": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002",
    "messageId": "5bfb2396-247e-57b5-9a5b-2f19181ec67e",
    "timestamp": "2025-01-27T12:15:30Z",
    "ttl": "PT30S"
  },
  "message": {
    "support": {
      "orderId": "order-ev-charging-001",
      "descriptor": {
        "name": "Support ticket SUP-20250730-001",
        "code": "OPEN"
      },
      "channels": [
        {
          "@context": "https://schema.nfh.global/SupportInfo/v2.1/context.jsonld",
          "@type": "SupportInfo",
          "name": "BlueCharge Support Team",
          "telephone": "18001080",
          "email": "support@bluechargenet-aggregator.io",
          "url": "https://support.bluechargenet-aggregator.io/ticket/SUP-20250730-001",
          "hoursAvailable": "Mon–Sun 24/7 IST",
          "channels": [
            "PHONE",
            "EMAIL",
            "WEB",
            "CHAT"
          ]
        }
      ]
    }
  }
}

```
</details>

- Successful Response: 

<details>
<summary>Example json :rocket:</summary>

```json
{
  "message": {
    "status": "ACK",
    "messageId": "6f1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
  }
}
```
</details>

### 13.2.2. **Integrating with your software**

This section gives a general walkthrough of how you would integrate your software with the Beckn network (say the sandbox environment). Refer to the starter kit for details on how to register with the sandbox and get credentials.

Beckn-ONIX is an initiative to promote easy installation and maintenance of a Beckn Network. Apart from the Registry and Gateway components that are required for a network facilitator, Beckn-ONIX provides a Beckn Adapter. A reference implementation of the Beckn-ONIX specification is available at [Beckn-ONIX repository](https://github.com/beckn/beckn-onix). The reference implementation of the Beckn Adapter is called the Protocol Server. Based on whether we are writing the seeker platform or the provider platform, we will be installing the BAP Protocol Server or the BPP Protocol Server respectively.

#### 13.2.2.1. **Integrating the BAP**

If you are writing the seeker platform software, the following are the steps you can follow to build and integrate your application.

1. Identify the use cases from the above section that are close to the functionality you plan for your application.  
2. Design and develop the UI that implements the flow you need. Typically you will have an API server that this UI talks to and it is called the Seeker Platform in the diagram below.  
3. The API server should construct the required JSON message packets required for the different endpoints shown in the API section above.  
4. Install the BAP Protocol Server using the reference implementation of Beckn-ONIX. During the installation, you will need the address of the registry of the environment, a URL where the Beckn responses will arrive (called Subscriber URL) and a subscriber\_id (typically the same as subscriber URL without the "https://" prefix)  
5. Install the layer 2 file for the domain (Link is in the last section of this document)  
6. Check with your network tech support to enable your BAP Protocol Server in the registry.  
7. Once enabled, you can transact on the Beckn Network. Typically the sandbox environment will have the rest of the components you need to test your software. In the diagram below,  
   * you write the Seeker Platform(dark blue)  
   * install the BAP Protocol Server (light blue)  
   * the remaining components are provided by the sandbox environment  
8. Once the application is working on the Sandbox, refer to the Starter kit for instructions to take it to pre-production and production.

#### 13.2.2.2. **Integrating the BPP**

If you are writing the provider platform software, the following are the steps you can follow to build and integrate your application.

1. Identify the use cases from the above section that are close to the functionality you plan for your application.  
2. Design and develop the component that accepts the Beckn requests and interacts with your software to do transactions. It has to be an endpoint(it is called as webhook\_url in the description below) which receives all the Beckn requests (search, select etc). This endpoint can either exist outside of your marketplace/shop software or within it. That is a design decision that will have to be taken by you based on the design of your existing marketplace/shop software. This component is also responsible for sending back the responses to the Beckn Adaptor.  
3. Install the BPP Protocol Server using the reference implementation of Beckn-ONIX. During the installation, you will need the address of the registry of the environment, a URL where the Beckn responses will arrive (called Subscriber URL), a subscriber\_id (typically the same as subscriber URL without the "https://" prefix) and the webhook\_url that you configured in the step above. Also the address of the BPP Protocol Server Client will have to be configured in your component above. This address hosts all the response endpoints (on\_search,on\_select etc)  
4. Install the layer 2 file for the domain (Link is in the last section of this document)  
5. Check with your network tech support to enable your BPP Protocol Server in the registry.  
6. Once enabled, you can transact on the Beckn Network. Typically the sandbox environment will have the rest of the components you need to test your software. In the diagram below,  
   * you write the Provider Platform(dark blue) \- Here the component you wrote above in point 2 as well as your marketplace/shop software is together shown as Provider Platform  
   * install the BPP Protocol Server (light blue)  
   * the remaining components are provided by the sandbox environment  
   * Use the postman collection to test your Provider Platform  
7. Once the application is working on the Sandbox, refer to the Starter kit for instructions to take it to pre-production and production.

## 13.3. FAQs

## 13.4. References

* [Postman collection for UEI EV Charging](https://github.com/beckn/missions/blob/main/UEI/postman/ev-charging_uei_postman_collection.json)  
* [Layer2 config for UEI EV Charging](https://github.com/beckn/missions/blob/main/UEI/layer2/EV-charging/3.1/energy_EV_1.1.0_openapi_3.1.yaml)  
* When installing layer2 using Beckn-ONIX use this web address ([https://raw.githubusercontent.com/beckn/missions/refs/heads/main/UEI/layer2/EV-charging/3.1/energy\_EV\_1.1.0\_openapi\_3.1.yaml](https://raw.githubusercontent.com/beckn/missions/refs/heads/main/UEI/layer2/EV-charging/3.1/energy_EV_1.1.0_openapi_3.1.yaml))  