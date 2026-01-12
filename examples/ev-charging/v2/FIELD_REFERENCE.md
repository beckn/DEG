# Beckn V2 EV Charging API - Field Reference Guide

This document provides a comprehensive reference for all fields used in the Beckn V2 EV Charging API examples.

There is a [google sheet version](https://docs.google.com/spreadsheets/d/1ilIob4B7aPoSrixPbEi0__4sL6GURDj8jux9GOnDy3c/edit?gid=0#gid=0) of this document for users who are comfortable with google sheets.

## Table of Contents
- [Context Fields](#context-fields)
- [Discovery & Search](#discovery--search)
- [Catalog & Items](#catalog--items)
- [ChargingService Attributes](#chargingservice-attributes)
- [Offers & Pricing](#offers--pricing)
- [Order Management](#order-management)
- [Buyer Information](#buyer-information)
- [Order Items](#order-items)
- [Fulfillment](#fulfillment)
- [ChargingSession Attributes](#chargingsession-attributes)
- [Tracking](#tracking)
- [Payment](#payment)
- [Rating & Feedback](#rating--feedback)
- [Support](#support)
- [Cancellation](#cancellation)

---

## Context Fields

Fields that appear in the `context` object of every API call.

| Field Path | Field Name | Type | Required | Description | Example | Used In |
|------------|-----------|------|----------|-------------|---------|---------|
| `context.version` | Version | String | ✅ | Beckn protocol version | `2.0.0` | All APIs |
| `context.action` | Action | String | ✅ | The API action being performed | `discover`, `on_discover`, `select`, etc. | All APIs |
| `context.domain` | Domain | String | ✅ | Domain/use case identifier | `beckn.one:deg:ev-charging:*` | All APIs |
| `context.location.country.code` | Country Code | String | ✅ | ISO 3166-1 alpha-3 country code | `IND` | All APIs |
| `context.location.city.code` | City Code | String | ✅ | City code with standard prefix | `std:080` | All APIs |
| `context.timestamp` | Timestamp | DateTime | ✅ | Request/response timestamp | `2024-01-15T10:30:00Z` | All APIs |
| `context.transaction_id` | Transaction ID | UUID | ✅ | Unique identifier for the transaction | `2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002` | All APIs |
| `context.message_id` | Message ID | UUID | ✅ | Unique identifier for each message | `a1eabf26-29f5-4a01-9d4e-4c5c9d1a3d02` | All APIs |
| `context.bap_id` | BAP ID | String | ✅ | Buyer Application Platform identifier | `bap.example.com` | All APIs |
| `context.bap_uri` | BAP URI | URL | ✅ | BAP callback endpoint | `https://bap.example.com` | All APIs |
| `context.bpp_id` | BPP ID | String | ❌ | Beckn Provider Platform identifier | `bpp.example.com` | Response APIs |
| `context.bpp_uri` | BPP URI | URL | ❌ | BPP endpoint | `https://bpp.example.com` | Response APIs |
| `context.ttl` | Time To Live | Duration | ✅ | Maximum time to wait for response | `PT30S` | All APIs |
| `context.schema_context` | Schema Context | Array[URL] | ✅ | JSON-LD context references | `["https://...context.jsonld"]` | All APIs |

**Notes:**
- `transaction_id` remains the same across request-response pairs
- `message_id` is unique for each request/response
- `ttl` uses ISO 8601 duration format
- `bpp_id` and `bpp_uri` only present in response APIs

---

## Discovery & Search

Fields used in `discover` request for searching charging stations.

| Field Path | Field Name | Type | Required | Description | Example | Notes |
|------------|-----------|------|----------|-------------|---------|-------|
| `message.text_search` | Text Search | String | ❌ | Free-text search query | `EV charger fast charging` | Natural language search |
| `message.spatial` | Spatial Filters | Array[Object] | ❌ | Geographic search filters | `[{op: "s_dwithin", ...}]` | CQL2 spatial operators |
| `message.spatial[].op` | Spatial Operator | String | ✅ | Spatial operation type | `s_dwithin`, `s_contains`, `s_intersects` | CQL2 standard |
| `message.spatial[].targets` | Targets JSONPath | String | ✅ | JSONPath to target fields | `$['beckn:availableAt'][*]['geo']` | Which fields to filter |
| `message.spatial[].geometry.type` | Geometry Type | String | ✅ | GeoJSON geometry type | `Point`, `Polygon`, `LineString` | GeoJSON standard |
| `message.spatial[].geometry.coordinates` | Coordinates | Array | ✅ | Geographic coordinates | `[77.5900, 12.9400]` | [longitude, latitude] |
| `message.spatial[].distanceMeters` | Distance (m) | Number | ❌ | Radius for distance queries | `10000` | For s_dwithin operator |
| `message.filters.expression` | Filter Expression | String | ❌ | JSONPath filtering logic | `$[?(@.itemAttributes.connectorType=='CCS2')]` | Complex filtering |

**Notes:**
- Spatial filters use CQL2 (Common Query Language 2) operators
- Coordinates are always [longitude, latitude] order (GeoJSON standard)
- Multiple spatial filters can be combined (AND logic)
- JSONPath expressions allow complex attribute filtering

---

## Catalog & Items

Fields in `on_discover` response containing available charging stations.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.catalogs` | Catalogs | Array[Object] | ✅ | Array of catalog objects | `[{@type: "beckn:Catalog", ...}]` |
| `message.catalogs[].@context` | Context | URL | ✅ | JSON-LD context | `https://becknprotocol.io/.../Catalog/schema-context.jsonld` |
| `message.catalogs[].@type` | Type | String | ✅ | JSON-LD type | `beckn:Catalog` |
| `message.catalogs[].beckn:descriptor` | Descriptor | Object | ✅ | Catalog description | `{schema:name: "EV Charging Services"}` |
| `message.catalogs[].beckn:descriptor.schema:name` | Name | String | ✅ | Display name | `EV Charging Services Network` |
| `message.catalogs[].beckn:descriptor.beckn:shortDesc` | Short Description | String | ❌ | Brief description | `Comprehensive network of fast charging stations` |
| `message.catalogs[].beckn:validity` | Validity Period | Object | ❌ | Time period for catalog | `{schema:startDate, schema:endDate}` |
| `message.catalogs[].beckn:validity.schema:startDate` | Start Date | DateTime | ✅ | Validity start | `2024-10-01T00:00:00Z` |
| `message.catalogs[].beckn:validity.schema:endDate` | End Date | DateTime | ✅ | Validity end | `2025-01-15T23:59:59Z` |
| `message.catalogs[].beckn:items` | Items | Array[Object] | ✅ | Available items/services | `[{@type: "beckn:Item", ...}]` |

### Item Fields

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:items[].@context` | Context | URL | ✅ | JSON-LD context | `https://becknprotocol.io/.../Item/schema-context.jsonld` |
| `beckn:items[].@type` | Type | String | ✅ | JSON-LD type | `beckn:Item` |
| `beckn:items[].beckn:id` | Item ID | String | ✅ | Unique item identifier | `ev-charger-ccs2-001` |
| `beckn:items[].beckn:descriptor` | Descriptor | Object | ✅ | Item description | `{schema:name, beckn:shortDesc, beckn:longDesc}` |
| `beckn:items[].beckn:descriptor.schema:name` | Name | String | ✅ | Display name | `DC Fast Charger - CCS2 (60kW)` |
| `beckn:items[].beckn:descriptor.beckn:shortDesc` | Short Description | String | ❌ | Brief description | `High-speed DC charging station` |
| `beckn:items[].beckn:descriptor.beckn:longDesc` | Long Description | String | ❌ | Detailed description | `Ultra-fast DC charging station supporting...` |
| `beckn:items[].beckn:category` | Category | Object | ✅ | Item classification | `{schema:codeValue: "ev-charging"}` |
| `beckn:items[].beckn:category.schema:codeValue` | Code Value | String | ✅ | Category code | `ev-charging` |
| `beckn:items[].beckn:category.schema:name` | Category Name | String | ✅ | Category name | `EV Charging` |

### Location Fields

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:items[].beckn:availableAt` | Available At | Array[Object] | ✅ | Geographic locations | `[{geo, address}]` |
| `beckn:items[].beckn:availableAt[].geo` | Geo Location | Object | ✅ | GeoJSON location | `{type: "Point", coordinates: [77.5946, 12.9716]}` |
| `beckn:items[].beckn:availableAt[].geo.type` | Geometry Type | String | ✅ | GeoJSON type | `Point` |
| `beckn:items[].beckn:availableAt[].geo.coordinates` | Coordinates | Array[Number] | ✅ | [Longitude, Latitude] | `[77.5946, 12.9716]` |
| `beckn:items[].beckn:availableAt[].address` | Address | Object | ✅ | Postal address | `{streetAddress, addressLocality, ...}` |
| `beckn:items[].beckn:availableAt[].address.streetAddress` | Street Address | String | ✅ | Street and building | `EcoPower BTM Hub, 100 Ft Rd` |
| `beckn:items[].beckn:availableAt[].address.addressLocality` | City/Locality | String | ✅ | City name | `Bengaluru` |
| `beckn:items[].beckn:availableAt[].address.addressRegion` | State/Region | String | ✅ | State or province | `Karnataka` |
| `beckn:items[].beckn:availableAt[].address.postalCode` | Postal Code | String | ✅ | ZIP/postal code | `560076` |
| `beckn:items[].beckn:availableAt[].address.addressCountry` | Country | String | ✅ | Country code | `IN` |

### Item Metadata

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:items[].beckn:availabilityWindow` | Availability Window | Object | ❌ | Operating hours | `{schema:startTime: "06:00:00", schema:endTime: "22:00:00"}` |
| `beckn:items[].beckn:availabilityWindow.schema:startTime` | Start Time | Time | ✅ | Opening time | `06:00:00` |
| `beckn:items[].beckn:availabilityWindow.schema:endTime` | End Time | Time | ✅ | Closing time | `22:00:00` |
| `beckn:items[].beckn:rateable` | Rateable | Boolean | ✅ | Can be rated | `true` |
| `beckn:items[].beckn:rating` | Rating | Object | ❌ | Rating info | `{beckn:ratingValue: 4.5, beckn:ratingCount: 128}` |
| `beckn:items[].beckn:rating.beckn:ratingValue` | Rating Value | Number | ✅ | Average rating | `4.5` |
| `beckn:items[].beckn:rating.beckn:ratingCount` | Rating Count | Integer | ✅ | Number of ratings | `128` |
| `beckn:items[].beckn:isActive` | Is Active | Boolean | ✅ | Currently active | `true` |

### Provider Fields

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:items[].beckn:provider` | Provider | Object | ✅ | Provider info | `{beckn:id, beckn:descriptor}` |
| `beckn:items[].beckn:provider.beckn:id` | Provider ID | String | ✅ | Provider identifier | `ecopower-charging` |
| `beckn:items[].beckn:provider.beckn:descriptor` | Descriptor | Object | ✅ | Provider details | `{schema:name: "EcoPower Charging Pvt Ltd"}` |

---

## ChargingService Attributes

EV-specific attributes in `beckn:itemAttributes` (ChargingService schema).

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:itemAttributes.@context` | Context | URL | ✅ | ChargingService context | `https://raw.githubusercontent.com/.../EvChargingService/v1/context.jsonld` |
| `beckn:itemAttributes.@type` | Type | String | ✅ | Type identifier | `ChargingService` |
| `beckn:itemAttributes.connectorType` | Connector Type | String | ✅ | Charging connector | `CCS2`, `CHAdeMO`, `Type2`, `GBT` |
| `beckn:itemAttributes.maxPowerKW` | Max Power (kW) | Number | ✅ | Maximum power | `60` |
| `beckn:itemAttributes.minPowerKW` | Min Power (kW) | Number | ❌ | Minimum power | `5` |
| `beckn:itemAttributes.socketCount` | Socket Count | Integer | ✅ | Available sockets | `2` |
| `beckn:itemAttributes.reservationSupported` | Reservation | Boolean | ✅ | Advance booking | `true` |
| `beckn:itemAttributes.acceptedPaymentMethod` | Payment Methods | Array[String] | ✅ | Accepted payments | `["schema:UPI", "schema:CreditCard", "schema:Wallet"]` |
| `beckn:itemAttributes.serviceLocation` | Service Location | Object | ✅ | Location details | `{geo, address}` |
| `beckn:itemAttributes.amenityFeature` | Amenities | Array[String] | ❌ | Available facilities | `["RESTAURANT", "RESTROOM", "WI-FI"]` |
| `beckn:itemAttributes.ocppId` | OCPP ID | String | ❌ | OCPP station ID | `IN-ECO-BTM-01` |
| `beckn:itemAttributes.evseId` | EVSE ID | String | ❌ | EVSE identifier | `IN*ECO*BTM*01*CCS2*A` |
| `beckn:itemAttributes.roamingNetwork` | Roaming Network | String | ❌ | Network name | `GreenRoam` |
| `beckn:itemAttributes.parkingType` | Parking Type | String | ❌ | Parking category | `Mall`, `Street`, `Highway` |
| `beckn:itemAttributes.connectorId` | Connector ID | String | ❌ | Physical connector | `CCS2-A` |
| `beckn:itemAttributes.powerType` | Power Type | String | ✅ | AC or DC | `AC`, `DC` |
| `beckn:itemAttributes.connectorFormat` | Connector Format | String | ✅ | Socket or cable | `SOCKET`, `CABLE` |
| `beckn:itemAttributes.chargingSpeed` | Charging Speed | String | ✅ | Speed category | `SLOW`, `FAST`, `ULTRA_FAST` |
| `beckn:itemAttributes.stationStatus` | Station Status | String | ✅ | Availability status | `Available`, `Charging`, `Offline` |

**Notes:**
- `connectorType` follows ISO 15118 standards
- `evseId` format: Country*Operator*Location*EVSE*Connector
- `acceptedPaymentMethod` uses schema.org types
- Status updates in real-time

---

## Offers & Pricing

Fields in `beckn:offers` array for pricing plans.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:offers[].@context` | Context | URL | ✅ | Offer context | `https://becknprotocol.io/.../Offer/schema-context.jsonld` |
| `beckn:offers[].@type` | Type | String | ✅ | Type identifier | `beckn:Offer` |
| `beckn:offers[].beckn:id` | Offer ID | String | ✅ | Unique offer ID | `eco-charge-offer-ccs2-60kw-kwh` |
| `beckn:offers[].beckn:descriptor` | Descriptor | Object | ✅ | Offer description | `{schema:name: "Per-kWh Tariff - CCS2 60kW"}` |
| `beckn:offers[].beckn:items` | Items | Array[Object] | ✅ | Applicable items | `[{beckn:id: "ev-charger-ccs2-001"}]` |
| `beckn:offers[].beckn:price` | Price | Object | ✅ | Pricing details | `{@type: "schema:PriceSpecification", ...}` |

### Price Specification

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:price.@type` | Type | String | ✅ | Price type | `schema:PriceSpecification` |
| `beckn:price.schema:priceCurrency` | Currency | String | ✅ | Currency code | `INR` |
| `beckn:price.schema:price` | Unit Price | Number | ✅ | Price per unit | `18.00` |
| `beckn:price.schema:unitCode` | Unit Code | String | ✅ | Measurement unit | `KWH` |
| `beckn:price.schema:valueAddedTaxIncluded` | VAT Included | Boolean | ✅ | Tax inclusion | `false` |

**Notes:**
- Currency codes follow ISO 4217
- Unit codes follow UN/CEFACT standards
- Multiple offers can exist per item (different pricing tiers)

---

## Order Management

Fields in `message.order` object for order handling.

| Field Path | Field Name | Type | Required | Description | Example | Used In |
|------------|-----------|------|----------|-------------|---------|---------|
| `message.order.@context` | Context | URL | ✅ | Order context | `https://becknprotocol.io/.../Order/schema-context.jsonld` | select, on_select, init, on_init, confirm, on_confirm |
| `message.order.@type` | Type | String | ✅ | Type identifier | `beckn:Order` | select, on_select, init, on_init, confirm, on_confirm |
| `message.order.beckn:id` | Order ID | String | ✅ | Unique order ID | `order-12345` | All order APIs |
| `message.order.beckn:status` | Order Status | String | ✅ | Current status | `PENDING`, `CONFIRMED`, `ACTIVE`, `COMPLETED`, `CANCELLED` | on_select onwards |
| `message.order.beckn:orderNumber` | Order Number | String | ❌ | Display number | `ORD-2024-001` | on_confirm onwards |

**Order Status Values:**
- `PENDING` - Order created, awaiting confirmation
- `CONFIRMED` - Order confirmed by provider
- `ACTIVE` - Service is active (charging in progress)
- `COMPLETED` - Service completed successfully
- `CANCELLED` - Order cancelled

---

## Buyer Information

Fields in `message.order.beckn:buyer` (Party schema).

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:buyer.@context` | Context | URL | ✅ | Party context | `https://becknprotocol.io/.../Party/schema-context.jsonld` |
| `beckn:buyer.@type` | Type | String | ✅ | Type identifier | `beckn:Party` |
| `beckn:buyer.schema:name` | Name | String | ✅ | Buyer name | `Rajesh Kumar` |
| `beckn:buyer.schema:email` | Email | String | ✅ | Email address | `rajesh.kumar@example.com` |
| `beckn:buyer.schema:telephone` | Phone | String | ✅ | Phone number | `+91-9876543210` |
| `beckn:buyer.schema:address` | Address | Object | ✅ | Billing address | `{streetAddress, addressLocality, ...}` |
| `beckn:buyer.beckn:taxId` | Tax ID | String | ❌ | Tax number | `GSTIN29ABCDE1234F1Z5` |

---

## Order Items

Fields in `message.order.beckn:orderItems` array.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:orderItems[].beckn:id` | Item ID | String | ✅ | Catalog item reference | `ev-charger-ccs2-001` |
| `beckn:orderItems[].beckn:quantity` | Quantity | Object | ✅ | Quantity details | `{beckn:count: 2.5, beckn:unitCode: "KWH"}` |
| `beckn:orderItems[].beckn:quantity.beckn:count` | Count | Number | ✅ | Quantity amount | `2.5` |
| `beckn:orderItems[].beckn:quantity.beckn:unitCode` | Unit Code | String | ✅ | Unit of measure | `KWH` |
| `beckn:orderItems[].beckn:offer` | Offer | Object | ✅ | Selected offer | `{beckn:id: "eco-charge-offer..."}` |

---

## Fulfillment

Fields in `message.order.beckn:fulfillments` array.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:fulfillments[].beckn:id` | Fulfillment ID | String | ✅ | Unique fulfillment ID | `fulfillment-001` |
| `beckn:fulfillments[].beckn:status` | Status | String | ✅ | Current status | `PENDING`, `ACTIVE`, `COMPLETED`, `CANCELLED` |
| `beckn:fulfillments[].beckn:deliveryMethod` | Delivery Method | String | ✅ | Fulfillment type | `RESERVATION` |
| `beckn:fulfillments[].beckn:start` | Start | Object | ✅ | Start details | `{beckn:time, beckn:location}` |
| `beckn:fulfillments[].beckn:start.beckn:time` | Start Time | Object | ✅ | Time details | `{beckn:timestamp, beckn:range}` |
| `beckn:fulfillments[].beckn:start.beckn:location` | Start Location | Object | ✅ | Location details | `{beckn:id, geo, address}` |
| `beckn:fulfillments[].beckn:end` | End | Object | ❌ | End details | `{beckn:time}` |

**Fulfillment Status Values:**
- `PENDING` - Not yet started
- `ACTIVE` - Currently in progress (charging)
- `COMPLETED` - Finished successfully
- `CANCELLED` - Cancelled

---

## ChargingSession Attributes

EV-specific fulfillment data in `beckn:fulfillmentAttributes` (ChargingSession schema).

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:fulfillmentAttributes.@context` | Context | URL | ✅ | ChargingSession context | `https://raw.githubusercontent.com/.../ChargingSession/v1/context.jsonld` |
| `beckn:fulfillmentAttributes.@type` | Type | String | ✅ | Type identifier | `ChargingSession` |
| `beckn:fulfillmentAttributes.sessionId` | Session ID | String | ❌ | Session identifier | `SESSION-123` |
| `beckn:fulfillmentAttributes.sessionStatus` | Session Status | String | ✅ | Charging status | `PENDING`, `ACTIVE`, `COMPLETED`, `INTERRUPTED` |
| `beckn:fulfillmentAttributes.authorizationMode` | Authorization Mode | String | ✅ | Auth method | `OTP`, `RFID`, `APP` |
| `beckn:fulfillmentAttributes.authorizationToken` | Authorization Token | String | ❌ | Auth credential | `123456` |
| `beckn:fulfillmentAttributes.vehicleRegistration` | Vehicle Registration | String | ❌ | License plate | `KA01AB1234` |
| `beckn:fulfillmentAttributes.vehicleModel` | Vehicle Model | String | ❌ | Make and model | `Tesla Model 3` |
| `beckn:fulfillmentAttributes.batteryCapacityKWh` | Battery Capacity | Number | ❌ | Battery size (kWh) | `75` |
| `beckn:fulfillmentAttributes.currentBatteryLevelPercent` | Current Battery % | Number | ❌ | Starting battery | `25` |
| `beckn:fulfillmentAttributes.targetBatteryLevelPercent` | Target Battery % | Number | ❌ | Desired battery | `80` |
| `beckn:fulfillmentAttributes.connectorId` | Connector ID | String | ✅ | Which connector | `CCS2-A` |
| `beckn:fulfillmentAttributes.chargingPowerKW` | Charging Power | Number | ❌ | Current power (kW) | `45.5` |
| `beckn:fulfillmentAttributes.energyDeliveredKWh` | Energy Delivered | Number | ❌ | Total energy (kWh) | `2.3` |
| `beckn:fulfillmentAttributes.chargingProgressPercent` | Charging Progress | Number | ❌ | Completion % | `65` |
| `beckn:fulfillmentAttributes.estimatedCompletionTime` | Estimated Completion | DateTime | ❌ | Expected end time | `2024-01-15T12:45:00Z` |

**Session Status Values:**
- `PENDING` - Session created, not started
- `ACTIVE` - Charging in progress
- `COMPLETED` - Charging finished
- `INTERRUPTED` - Charging stopped unexpectedly

---

## Tracking

Fields for real-time tracking in `beckn:fulfillments[].beckn:trackingAction`.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:trackingAction.@type` | Type | String | ✅ | Action type | `schema:TrackAction` |
| `beckn:trackingAction.schema:target` | Target | Object | ✅ | Tracking target | `{@type: "schema:EntryPoint", ...}` |
| `beckn:trackingAction.schema:target.schema:urlTemplate` | URL Template | String | ✅ | Tracking URL | `https://track.example.com/session/SESSION-123` |
| `beckn:trackingAction.schema:object` | Object | Object | ✅ | Tracked entity | `{schema:identifier: "RESERVATION-12345"}` |

---

## Payment

Fields in `message.order.beckn:payment` for payment handling.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:payment.@context` | Context | URL | ✅ | Payment context | `https://becknprotocol.io/.../Payment/schema-context.jsonld` |
| `beckn:payment.@type` | Type | String | ✅ | Payment type | `schema:PayAction` |
| `beckn:payment.schema:name` | Payment Name | String | ❌ | Description | `Charging Session Payment` |
| `beckn:payment.beckn:status` | Payment Status | String | ✅ | Current status | `PENDING`, `PAID`, `FAILED`, `REFUNDED` |
| `beckn:payment.beckn:paymentURL` | Payment URL | URL | ❌ | Payment link | `https://pay.example.com?order=12345` |
| `beckn:payment.beckn:method` | Payment Method | Object | ❌ | Selected method | `{beckn:type, beckn:details}` |
| `beckn:payment.beckn:method.beckn:type` | Payment Type | String | ✅ | Method type | `schema:UPI`, `schema:CreditCard`, `schema:Wallet` |
| `beckn:payment.beckn:method.beckn:details` | Payment Details | Array[Object] | ❌ | Method specifics | `[{beckn:key: "vpa", beckn:value: "user@upi"}]` |
| `beckn:payment.beckn:acceptedPaymentMethod` | Accepted Methods | Array[String] | ❌ | Available methods | `["schema:UPI", "schema:CreditCard"]` |
| `beckn:payment.schema:paymentDueDate` | Payment Due Date | DateTime | ❌ | Due date | `2024-01-15T12:00:00Z` |

**Payment Status Values:**
- `PENDING` - Payment not yet completed
- `PAID` - Payment successful
- `FAILED` - Payment failed
- `REFUNDED` - Payment refunded

---

## Order Value

Fields in `message.order.beckn:orderValue` for pricing breakdown.

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `beckn:orderValue.@type` | Type | String | ✅ | Price type | `schema:PriceSpecification` |
| `beckn:orderValue.schema:priceCurrency` | Currency | String | ✅ | Currency code | `INR` |
| `beckn:orderValue.schema:price` | Total Price | Number | ✅ | Total amount | `55.00` |
| `beckn:orderValue.beckn:components` | Price Components | Array[Object] | ❌ | Price breakdown | `[{beckn:item, beckn:title, schema:price}]` |
| `beckn:components[].beckn:item` | Component Type | String | ✅ | Cost category | `UNIT`, `FEE`, `SURCHARGE`, `DISCOUNT` |
| `beckn:components[].beckn:title` | Title | String | ✅ | Description | `Energy Charges (2.5 kWh)` |
| `beckn:components[].schema:price` | Price | Number | ✅ | Component amount | `45.00` |

**Component Types:**
- `UNIT` - Base unit cost (energy charges)
- `FEE` - Service/platform fees
- `SURCHARGE` - Additional charges (idle fees, peak hour charges)
- `DISCOUNT` - Price reductions

---

## Rating & Feedback

Fields for rating submission and response.

### Rating Input (rating request)

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.rating.@context` | Context | URL | ✅ | Rating context | `https://becknprotocol.io/.../Rating/schema-context.jsonld` |
| `message.rating.@type` | Type | String | ✅ | Rating type | `beckn:RatingInput` |
| `message.rating.beckn:id` | Reference ID | String | ✅ | What to rate | `fulfillment-001` |
| `message.rating.beckn:category` | Category | String | ✅ | Rating category | `FULFILLMENT`, `PROVIDER`, `ITEM` |
| `message.rating.beckn:value` | Rating Value | Number | ✅ | Rating score | `5` |
| `message.rating.beckn:feedback` | Feedback | String | ❌ | User comments | `Great charging experience!` |
| `message.rating.beckn:feedbackTags` | Feedback Tags | Array[String] | ❌ | Quick feedback | `["Fast", "Clean", "Well-maintained"]` |

**Rating Categories:**
- `FULFILLMENT` - Rate the charging session experience
- `PROVIDER` - Rate the charging station operator
- `ITEM` - Rate the specific charging equipment

### Rating Output (on_rating response)

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.ratingOutput.beckn:ratingValue` | Average Rating | Number | ✅ | Mean rating | `4.5` |
| `message.ratingOutput.beckn:ratingCount` | Rating Count | Integer | ✅ | Total ratings | `129` |
| `message.ratingOutput.beckn:bestRating` | Best Rating | Number | ✅ | Maximum possible | `5` |
| `message.ratingOutput.beckn:worstRating` | Worst Rating | Number | ✅ | Minimum possible | `1` |
| `message.ratingOutput.beckn:feedbackForm` | Feedback Form | Object | ❌ | Extended feedback | `{beckn:url, beckn:mimeType}` |

---

## Support

Fields for support requests and responses.

### Support Request

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.support.beckn:ref_id` | Reference ID | String | ✅ | Entity needing support | `order-12345` |
| `message.support.beckn:ref_type` | Reference Type | String | ✅ | Type of entity | `ORDER`, `FULFILLMENT`, `ITEM`, `PROVIDER` |
| `message.support.beckn:issue` | Issue | String | ❌ | Problem description | `Payment not processing` |

**Reference Types:**
- `ORDER` - Support for order-level issues
- `FULFILLMENT` - Support for charging session problems
- `ITEM` - Support for specific charging station issues
- `PROVIDER` - General support from operator

### Support Information (on_support response)

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.supportInfo.beckn:phone` | Support Phone | String | ❌ | Phone number | `1800-123-4567` |
| `message.supportInfo.beckn:email` | Support Email | String | ❌ | Email address | `support@example.com` |
| `message.supportInfo.beckn:url` | Support URL | URL | ❌ | Help center | `https://help.example.com` |
| `message.supportInfo.beckn:supportTicketURL` | Ticket URL | URL | ❌ | Create ticket | `https://support.example.com/create` |

---

## Cancellation

Fields for order cancellation.

### Cancellation Request (cancel)

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.cancellationRequest.beckn:reason` | Reason | String | ❌ | Reason text | `User changed plans` |
| `message.cancellationRequest.beckn:reasonCode` | Reason Code | String | ✅ | Standardized code | `USER_CANCELLED`, `NO_SHOW`, `TECHNICAL_ISSUE` |
| `message.cancellationRequest.beckn:requestedBy` | Requested By | String | ✅ | Who cancelled | `BUYER`, `PROVIDER` |

**Reason Codes:**
- `USER_CANCELLED` - Buyer cancelled voluntarily
- `NO_SHOW` - Buyer didn't show up for reservation
- `TECHNICAL_ISSUE` - Technical problem with station
- `PROVIDER_CANCELLED` - Provider cancelled the service

### Cancellation Terms (on_cancel response)

| Field Path | Field Name | Type | Required | Description | Example |
|------------|-----------|------|----------|-------------|---------|
| `message.cancellationTerms.beckn:refundAmount` | Refund Amount | Number | ❌ | Amount refunded | `45.00` |
| `message.cancellationTerms.beckn:cancellationFee` | Cancellation Fee | Number | ❌ | Fee charged | `10.00` |
| `message.cancellationTerms.beckn:refundPolicy` | Refund Policy | String | ❌ | Policy details | `Full refund if cancelled 1hr before` |

---

## Data Type Reference

### Common Data Types

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| String | Text | `"example"` | UTF-8 encoded text |
| Number | Numeric | `45.5` | Integer or decimal |
| Integer | Whole number | `128` | No decimal places |
| Boolean | true/false | `true` | Logical value |
| DateTime | ISO 8601 | `2024-01-15T10:30:00Z` | UTC timezone recommended |
| Date | ISO 8601 | `2024-01-15` | Date only |
| Time | HH:MM:SS | `10:30:00` | 24-hour format |
| Duration | ISO 8601 | `PT30S` | Period notation |
| URL | Web address | `https://example.com` | Full URL with protocol |
| UUID | UUID v4 | `2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002` | Unique identifier |
| Array | List | `[1, 2, 3]` | Ordered collection |
| Object | JSON object | `{"key": "value"}` | Key-value pairs |

### GeoJSON Coordinate Order

⚠️ **Important**: GeoJSON always uses `[longitude, latitude]` order, which is opposite to common usage:
- ✅ Correct: `[77.5946, 12.9716]` (longitude first)
- ❌ Wrong: `[12.9716, 77.5946]` (latitude first)

### Unit Codes (UN/CEFACT)

Common unit codes used in EV charging:
- `KWH` - Kilowatt-hour (energy)
- `KW` - Kilowatt (power)
- `HUR` - Hour (time)
- `MIN` - Minute (time)
- `MTR` - Meter (distance)

### Currency Codes (ISO 4217)

- `INR` - Indian Rupee
- `USD` - US Dollar
- `EUR` - Euro
- `GBP` - British Pound

---

## API Flow Examples

### Discovery Flow
1. **discover** → Search for charging stations
2. **on_discover** ← Receive catalog of stations

### Booking Flow
3. **select** → Select station and charging amount
4. **on_select** ← Receive order confirmation with pricing
5. **init** → Initialize order with buyer details
6. **on_init** ← Receive order with payment details
7. **confirm** → Confirm order with payment method
8. **on_confirm** ← Receive confirmed order with BPP order ID

### Charging Flow
9. **update** → Start charging session (with OTP)
10. **on_update** ← Receive active session details
11. **track** → Track charging progress
12. **on_track** ← Receive real-time charging data
13. **on_status** ← Receive status updates (interruptions, completion)
14. **on_update** ← Receive final billing

### Post-Service Flow
15. **rating** → Submit rating and feedback
16. **on_rating** ← Receive aggregate ratings
17. **support** → Request support
18. **on_support** ← Receive support contact info

### Cancellation Flow
19. **cancel** → Cancel order/reservation
20. **on_cancel** ← Receive cancellation terms and refund details

---

## Additional Resources

- [Beckn Protocol Specification](https://github.com/beckn/protocol-specifications)
- [Schema.org Documentation](https://schema.org/)
- [GeoJSON Specification](https://geojson.org/)
- [CQL2 Specification](https://docs.ogc.org/is/21-065r2/21-065r2.html)
- [UN/CEFACT Unit Codes](https://unece.org/trade/uncefact/cl-recommendations)
- [ISO 4217 Currency Codes](https://www.iso.org/iso-4217-currency-codes.html)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-10-30 | Initial comprehensive field reference |

---

## Contributing

If you find any errors or have suggestions for improvement, please submit an issue or pull request to the repository.

---

**Generated for**: Beckn V2 EV Charging API Examples  
**Location**: `/Users/rajaneesh/beckn/specs/DEG/examples/v2/`  
**Last Updated**: October 30, 2024

