# V2 Discover/On_Discover Implementation

This directory contains the implementation of v2 discover and on_discover API examples for EV charging services, mapped from v1 search/on_search patterns.

## Files Generated

### 01_discover/
- **`time-based-ev-charging-slot-discover.json`** - Comprehensive discover request with text search, spatial filters, and JSONPath filtering

### 02_on_discover/
- **`time-based-ev-charging-slot-catalog.json`** - Comprehensive on_discover response with complete EV charging service catalog

### 03_select/
- **`time-based-ev-charging-slot-select.json`** - Comprehensive select request with full offer object and charging session details

### 04_on_select/
- **`time-based-ev-charging-slot-on-select.json`** - Comprehensive on_select response with order confirmation and pricing breakdown

## Implementation Details

### Discover Request Features

The discover request (`01_discover/time-based-ev-charging-slot-discover.json`) includes:

1. **Text Search**: `"EV charger fast charging"` - Broad search for charging stations
2. **Spatial Filter**: 5km radius search around Bengaluru coordinates (77.5946, 12.9716)
3. **JSONPath Filter**: Complex filtering for:
   - CCS2 connector type
   - Minimum 50kW power rating
   - Available station status
   - Percentage-based buyer finder fee

### On_Discover Response Features

The on_discover response (`02_on_discover/time-based-ev-charging-slot-catalog.json`) includes:

1. **Multiple Charging Stations**:
   - DC Fast Charger - CCS2 (60kW)
   - DC Fast Charger - CCS2 (120kW) 
   - AC Fast Charger - Type 2 (22kW)

2. **Complete ChargingService Attributes**:
   - Connector specifications (type, power, socket count)
   - Payment methods and reservation support
   - Location data with GeoJSON coordinates
   - Amenity features and operational status
   - OCPP and EVSE identifiers

3. **Pricing and Offers**:
   - Per-kWh tariff models
   - Different pricing tiers based on power rating
   - Buyer finder fee configurations
   - Idle fee policies

### Select Request Features

The select request (`03_select/time-based-ev-charging-slot-select.json`) includes:

1. **Item Selection**: References discovered charging station by ID
2. **Quantity Specification**: kWh amount for charging session (2.5 kWh)
3. **Full Offer Object**: Complete offer details with pricing and validity
4. **Fulfillment Mode**: RESERVATION for advance booking
5. **ChargingSession Attributes**: Session-specific technical details
6. **Buyer Finder Fee**: Commission structure declaration

### On_Select Response Features

The on_select response (`04_on_select/time-based-ev-charging-slot-on-select.json`) includes:

1. **Order Confirmation**: Order status and number assignment
2. **Pricing Breakdown**: Detailed cost components (unit, fees, surcharges)
3. **Fulfillment Details**: Charging session confirmation with tracking
4. **Reservation Management**: Reservation ID and grace period
5. **Authorization Instructions**: QR code scanning instructions

## Mapping from V1 to V2

### Search Criteria Mapping

| V1 Search Pattern | V2 Discover Pattern | Implementation |
|------------------|-------------------|----------------|
| `message.intent.descriptor.name` | `message.text_search` | "EV charger fast charging" |
| `message.intent.fulfillment.stops[].location.circle` | `message.spatial[].geometry` | GeoJSON Point with s_dwithin operator |
| `message.intent.fulfillment.tags.list` | `message.filters.expression` | JSONPath filtering for connector type |
| `message.intent.tags` | `message.filters.expression` | JSONPath filtering for buyer finder fee |

### Response Structure Mapping

| V1 Response Pattern | V2 On_Discover Pattern | Implementation |
|-------------------|----------------------|----------------|
| `message.catalog.providers[].items[]` | `message.catalogs[].beckn:items[]` | Beckn Item schema with ChargingService attributes |
| `providers[].locations[]` | `beckn:availableAt[]` | Location objects with GeoJSON |
| `items[].price` | `beckn:offers[].beckn:price` | PriceSpecification with proper units |
| Item tags | `beckn:itemAttributes` | ChargingService schema attributes |

## Schema Compliance

### Core V2 Schema Compliance
- ✅ Uses proper `beckn:Item` structure
- ✅ Implements `beckn:availableAt` for locations
- ✅ Follows `beckn:descriptor` pattern
- ✅ Uses `beckn:category` for classification
- ✅ Implements `beckn:rating` system
- ✅ Proper JSON-LD context references

### ChargingService Schema Compliance
- ✅ All required fields: `connectorType`, `maxPowerKW`, `socketCount`
- ✅ Optional fields: `minPowerKW`, `reservationSupported`, `paymentAccepted`
- ✅ Location mapping: `serviceLocation` with GeoJSON
- ✅ Technical details: `powerType`, `connectorFormat`, `chargingSpeed`
- ✅ Operational status: `stationStatus`, `amenityFeature`

## Key Features Demonstrated

### Discover Request
1. **Multi-modal Search**: Combines text search with spatial and attribute filtering
2. **Geographic Search**: 5km radius search using CQL2 spatial operators
3. **Technical Filtering**: JSONPath expressions for EV-specific attributes
4. **Business Logic**: Buyer finder fee filtering for commission-based discovery

### On_Discover Response
1. **Diverse Charging Options**: Different connector types and power ratings
2. **Realistic Data**: Actual Bengaluru locations with proper addresses
3. **Complete Attributes**: All ChargingService schema fields populated
4. **Pricing Models**: Different tariff structures based on charging speed
5. **Provider Information**: Multiple CPOs with contact details

## Usage Examples

### Basic Discovery
```bash
curl -X POST https://bpp.example.com/beckn/discover \
  -H "Content-Type: application/json" \
  -d @time-based-ev-charging-slot-discover.json
```

### Expected Response
The BPP should respond with the catalog data from `time-based-ev-charging-slot-catalog.json` containing available charging stations matching the search criteria.

## Validation

Both JSON files have been validated for:
- ✅ JSON syntax correctness
- ✅ Schema compliance with discover.yaml API specification
- ✅ Proper JSON-LD context references
- ✅ Complete ChargingService attribute population
- ✅ Realistic EV charging service data

## 05_init and 06_on_init Examples

### Files
- `05_init/time-based-ev-charging-slot-init.json` - V2 init request
- `06_on_init/time-based-ev-charging-slot-on-init.json` - V2 on_init response

### Key Features
- **Order Schema**: Complete v2 Order structure with JSON-LD context
- **Buyer Schema**: Proper v2 Party schema with billing details (not in orderAttributes)
- **ChargingSession Integration**: EV charging specific attributes in fulfillment
- **Fee Breakdown**: Detailed price components (UNIT, FEE, SURCHARGE, DISCOUNT)
- **Enhanced Payment Schema**: Structured payment methods with schema.org compliance
- **Status Flow**: PENDING status throughout init/on_init (confirmation in on_confirm)

### Payment Schema Enhancements
- **Structured Payment Methods**: Object-based method with `type` and `details` fields
- **Schema.org Compliance**: Uses proper payment method types (schema:BankTransfer, schema:UPI, etc.)
- **Payment URL**: Core field for payment processing/redirection
- **Accepted Methods**: Array of supported payment method types
- **Method Details**: Key-value pairs for payment-specific information

### Charging Session Details
- **Session Management**: Start/end times, customer details, vehicle info
- **Location Data**: GPS coordinates and station address
- **Authorization**: OTP-based session authorization
- **Connector Specifications**: CCS2 connector with 50kW power rating
- **Session Preferences**: Notification preferences and timing

### V1 to V2 Mapping Improvements
- **Billing Mapping**: v1 `billing` → v2 `beckn:buyer` (Buyer schema)
- **Payment Methods**: v1 `payments[].tags` → v2 `beckn:method.details` array
- **Payment URL**: v1 `payments[].url` → v2 `beckn:paymentURL`
- **Order Status**: Correct PENDING status (not CONFIRMED in init phase)

## 07_confirm and 08_on_confirm Examples

### Files
- `07_confirm/time-based-ev-charging-slot-confirm.json` - V2 confirm request
- `08_on_confirm/time-based-ev-charging-slot-on-confirm.json` - V2 on_confirm response

### Key Features
- **Order Confirmation**: Complete order confirmation flow with payment details
- **Payment Status Updates**: PENDING → PAID payment status progression
- **BPP Order ID**: Provider-assigned order identifier in on_confirm
- **Virtual Payment Address**: Payment method details with VPA
- **Confirmation Details**: Order and session confirmation timestamps
- **Status Flow**: PENDING → CONFIRMED order status progression

### Payment Confirmation Details
- **Payment Method Selection**: Structured payment method with VPA details
- **Payment Status**: PENDING in confirm, PAID in on_confirm
- **Transaction References**: Payment transaction and confirmation codes
- **Beneficiary Information**: Clear payment recipient identification

### Charging Session Confirmation
- **Session Confirmation**: Confirmed charging session details
- **Authorization**: OTP-based session authorization
- **Confirmation Timestamps**: Order and session confirmation times
- **Provider Details**: BPP confirmation and tracking information

### V1 to V2 Mapping Enhancements
- **Payment Confirmation**: v1 payment status changes → v2 Payment schema updates
- **Virtual Payment Address**: v1 VPA → v2 `beckn:method.details`
- **Order ID Assignment**: BPP-assigned order ID in on_confirm response
- **Confirmation Tracking**: Enhanced confirmation details and timestamps

## 09_update and 10_on_update Examples

### Files
- `09_update/time-based-ev-charging-slot-update.json` - V2 update request
- `10_on_update/time-based-ev-charging-slot-on-update.json` - V2 on_update response

### Key Features
- **Charging Session Start**: Initiates active charging session with OTP authorization
- **Order Status Update**: PENDING → ACTIVE order status progression
- **Fulfillment Status**: PENDING → ACTIVE fulfillment status for charging
- **Session Management**: Real-time charging session details and progress tracking
- **Authorization Flow**: OTP-based session authorization and validation

### Physical Charging Process Integration
- **Pre-Update Steps**: Drive to station, plug vehicle, provide OTP
- **API Call**: Update API initiates charging session (like pressing "Start" button)
- **Session Activation**: Real-time charging session with power and energy tracking
- **Progress Monitoring**: Current power, energy delivered, and completion estimates

### Charging Session State Updates
- **Session Status**: PENDING → ACTIVE (charging started)
- **Station Status**: Available → Charging
- **Session Details**: Real-time power delivery and energy consumption
- **Progress Tracking**: Charging progress percentage and time estimates

### Authorization and Security
- **OTP Validation**: Authorization token validation for session start
- **Session Security**: Unique session ID and authorization mode
- **Station Validation**: OTP must match station and time slot
- **Safety Instructions**: Charging safety guidelines and emergency procedures

### V1 to V2 Mapping Enhancements
- **Update Target**: v1 `update_target` → v2 fulfillment status update
- **State Change**: v1 `state.descriptor.code` → v2 `beckn:status`
- **Authorization**: v1 `authorization.token` → v2 `authorizationToken`
- **Session Status**: Map to ChargingSession `sessionStatus`
- **Order Status**: Use "ACTIVE" for charging session start

## 11_track, 12_on_track, 13_on_status, and 14_on_update Examples

### Files
- `11_track/time-based-ev-charging-slot-track.json` - V2 track request
- `12_on_track/time-based-ev-charging-slot-on-track.json` - V2 on_track response
- `13_on_status/time-based-ev-charging-slot-on-status.json` - V2 on_status response
- `14_on_update/time-based-ev-charging-slot-on-update.json` - V2 on_update response

### Key Features
- **Session Tracking**: Real-time tracking with trackingAction object
- **Status Monitoring**: Session interruption and completion notifications
- **Billing Reconciliation**: Dynamic billing based on actual energy consumption
- **Session Management**: Complete charging session lifecycle tracking

### Tracking and Monitoring
- **TrackAction Schema**: Proper use of `trackingAction` in fulfillment
- **Tracking URL**: Clickable tracking dashboard links
- **Reservation ID**: Unique session tracking identifiers
- **Delivery Method**: "RESERVATION" for charging sessions

### Session State Progression
- **Track**: Request tracking for active session
- **On_Track**: Provide tracking details with live session data
- **On_Status**: Notify about session interruptions
- **On_Update**: Report session completion with final billing

### Session Interruption Handling
- **Connection Loss**: Automatic retry attempts with user notification
- **Billing Adjustment**: Real-time billing based on actual energy delivered
- **Status Updates**: Continuous monitoring and status communication
- **Recovery Process**: Automatic retry with manual intervention options

### Session Completion Details
- **Final Billing**: Complete energy consumption and cost reconciliation
- **Session Summary**: Energy delivered, duration, efficiency metrics
- **Performance Data**: Average power, peak power, charging efficiency
- **Completion Tracking**: Full session timeline and final status

### V1 to V2 Mapping Enhancements
- **Tracking**: v1 `tracking` → v2 `beckn:fulfillment.trackingAction`
- **State Changes**: v1 `state.descriptor.code` → v2 `beckn:status`
- **Billing**: v1 `billing` → v2 `beckn:buyer` (Buyer schema)
- **Quote Breakdown**: v1 `quote.breakup` → v2 `beckn:orderValue.components`
- **Session Details**: Map to ChargingSession `sessionStatus` and attributes

## 15_rating, 16_on_rating, 17_support, and 18_on_support Examples

### Files
- `15_rating/time-based-ev-charging-slot-rating.json` - V2 rating request
- `16_on_rating/time-based-ev-charging-slot-on-rating.json` - V2 on_rating response
- `17_support/time-based-ev-charging-slot-support.json` - V2 support request
- `18_on_support/time-based-ev-charging-slot-on-support.json` - V2 on_support response

### Key Features
- **Rating System**: Comprehensive rating with feedback and tags
- **Feedback Collection**: Additional feedback forms for detailed input
- **Support System**: Multi-channel support with contact information
- **Aggregate Statistics**: Rating counts and average scores

### Rating and Feedback
- **RatingInput Schema**: Proper v2 schema with id, value, category, feedback
- **Multi-category Rating**: Fulfillment, provider, and item ratings
- **Feedback System**: Comments and tags for detailed feedback
- **Aggregate Statistics**: Rating count, average value, best/worst scores

### Support and Customer Service
- **Reference Types**: Order, fulfillment, item, provider support
- **Contact Information**: Phone, email, web, chat channels
- **Support Tickets**: URL-based ticket creation and tracking
- **Escalation Procedures**: Different support channels for different issues

### Rating Categories for EV Charging
- **Fulfillment Rating**: Charging session experience (speed, reliability, ease of use)
- **Provider Rating**: Charging station operator service quality
- **Item Rating**: Specific charging station equipment and location

### Support Scenarios
- **Order Support**: Billing questions, payment problems, order modifications
- **Fulfillment Support**: Charging session problems, technical issues
- **Item Support**: Station-specific problems, equipment issues
- **Provider Support**: General service questions, complaints

### V1 to V2 Mapping Enhancements
- **Rating**: v1 `ratings[]` → v2 `RatingInput` schema
- **Support Reference**: v1 `support.ref_id` → v2 `ref_id` and `ref_type`
- **Feedback Form**: v1 `feedback_form` → v2 `feedbackForm` using Form object
- **Support Contact**: v1 `support.phone/email` → v2 SupportInfo schema

## Next Steps

These examples can be used as:
1. **API Testing**: Reference implementations for all v2 endpoints
2. **Integration Guides**: Examples for BAP/BPP integration
3. **Schema Validation**: Test cases for schema compliance
4. **Documentation**: Reference for EV charging service patterns