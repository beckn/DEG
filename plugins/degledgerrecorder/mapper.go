package degledgerrecorder

import (
	"encoding/json"
	"fmt"
	"strings"
)

// OnConfirmPayload represents the structure of an on_confirm beckn message.
type OnConfirmPayload struct {
	Context OnConfirmContext `json:"context"`
	Message OnConfirmMessage `json:"message"`
}

// OnConfirmContext represents the context portion of the on_confirm message.
type OnConfirmContext struct {
	Version       string `json:"version"`
	Action        string `json:"action"`
	Timestamp     string `json:"timestamp"`
	MessageID     string `json:"message_id"`
	TransactionID string `json:"transaction_id"`
	BapID         string `json:"bap_id"`
	BapURI        string `json:"bap_uri"`
	BppID         string `json:"bpp_id"`
	BppURI        string `json:"bpp_uri"`
	TTL           string `json:"ttl"`
	Domain        string `json:"domain"`
}

// OnConfirmMessage represents the message portion of the on_confirm message.
type OnConfirmMessage struct {
	Order Order `json:"order"`
}

// Order represents the order structure in the on_confirm message.
// Using map for flexible JSON-LD parsing.
type Order struct {
	ID              string                 `json:"beckn:id"`
	OrderStatus     string                 `json:"beckn:orderStatus"`
	Seller          string                 `json:"beckn:seller"`
	Buyer           map[string]interface{} `json:"beckn:buyer"`
	OrderAttributes map[string]interface{} `json:"beckn:orderAttributes"`
	OrderItems      []OrderItem            `json:"beckn:orderItems"`
	Fulfillment     map[string]interface{} `json:"beckn:fulfillment"`
}

// OrderItem represents an item in the order.
type OrderItem struct {
	OrderedItem         string                 `json:"beckn:orderedItem"`
	Quantity            Quantity               `json:"beckn:quantity"`
	OrderItemAttributes map[string]interface{} `json:"beckn:orderItemAttributes"`
	AcceptedOffer       AcceptedOffer          `json:"beckn:acceptedOffer"`
}

// Quantity represents quantity information.
type Quantity struct {
	UnitQuantity float64 `json:"unitQuantity"`
	UnitText     string  `json:"unitText"`
}

// AcceptedOffer represents the accepted offer in an order item.
type AcceptedOffer struct {
	ID              string                 `json:"beckn:id"`
	Descriptor      map[string]interface{} `json:"beckn:descriptor"`
	Provider        string                 `json:"beckn:provider"`
	Items           []string               `json:"beckn:items"`
	OfferAttributes map[string]interface{} `json:"beckn:offerAttributes"`
}

// LedgerPutRequest represents the request body for the ledger PUT API.
type LedgerPutRequest struct {
	Role              string        `json:"role"`
	TransactionID     string        `json:"transactionId"`
	OrderItemID       string        `json:"orderItemId"`
	PlatformIDBuyer   string        `json:"platformIdBuyer"`
	PlatformIDSeller  string        `json:"platformIdSeller"`
	DiscomIDBuyer     string        `json:"discomIdBuyer,omitempty"`
	DiscomIDSeller    string        `json:"discomIdSeller,omitempty"`
	BuyerID           string        `json:"buyerId,omitempty"`
	SellerID          string        `json:"sellerId,omitempty"`
	TradeTime         string        `json:"tradeTime,omitempty"`
	DeliveryStartTime string        `json:"deliveryStartTime,omitempty"`
	DeliveryEndTime   string        `json:"deliveryEndTime,omitempty"`
	TradeDetails      []TradeDetail `json:"tradeDetails,omitempty"`
	ClientReference   string        `json:"clientReference,omitempty"`
}

// TradeDetail represents a single trade detail entry.
type TradeDetail struct {
	TradeQty  float64 `json:"tradeQty"`
	TradeType string  `json:"tradeType"`
	TradeUnit string  `json:"tradeUnit"`
}

// -------------------------
// on_status → /ledger/record mapping
// -------------------------

// LedgerRecordRequest represents the request body for the ledger RECORD API (discom actuals).
type LedgerRecordRequest struct {
	Role                              string             `json:"role"`
	TransactionID                     string             `json:"transactionId"`
	OrderItemID                       string             `json:"orderItemId"`
	BuyerFulfillmentValidationMetrics []ValidationMetric `json:"buyerFulfillmentValidationMetrics,omitempty"`
	SellerFulfillmentValidationMetrics []ValidationMetric `json:"sellerFulfillmentValidationMetrics,omitempty"`
	// StatusBuyerDiscom  string `json:"statusBuyerDiscom,omitempty"`  // Future: leave empty for now
	// StatusSellerDiscom string `json:"statusSellerDiscom,omitempty"` // Future: leave empty for now
	ClientReference string `json:"clientReference,omitempty"`
}

// ValidationMetric represents a fulfillment validation metric.
type ValidationMetric struct {
	ValidationMetricType  string  `json:"validationMetricType"`
	ValidationMetricValue float64 `json:"validationMetricValue"`
}

// OnStatusPayload represents the structure of an on_status beckn message.
// Uses the same context structure as on_confirm.
type OnStatusPayload struct {
	Context OnConfirmContext `json:"context"` // Reuse context structure
	Message OnStatusMessage  `json:"message"`
}

// OnStatusMessage represents the message portion of the on_status message.
type OnStatusMessage struct {
	Order OnStatusOrder `json:"order"`
}

// OnStatusOrder represents the order in on_status with fulfillment attributes.
type OnStatusOrder struct {
	ID              string                 `json:"beckn:id"`
	OrderStatus     string                 `json:"beckn:orderStatus"`
	Seller          string                 `json:"beckn:seller"`
	Buyer           map[string]interface{} `json:"beckn:buyer"`
	OrderAttributes map[string]interface{} `json:"beckn:orderAttributes"`
	OrderItems      []OnStatusOrderItem    `json:"beckn:orderItems"`
}

// OnStatusOrderItem represents an order item in on_status with fulfillment data.
type OnStatusOrderItem struct {
	OrderedItem         string                 `json:"beckn:orderedItem"`
	Quantity            Quantity               `json:"beckn:quantity"`
	OrderItemAttributes map[string]interface{} `json:"beckn:orderItemAttributes"`
	AcceptedOffer       AcceptedOffer          `json:"beckn:acceptedOffer"`
}

// MeterReading represents a meter reading from fulfillmentAttributes.
type MeterReading struct {
	TimeWindow      map[string]interface{} `json:"beckn:timeWindow"`
	ConsumedEnergy  float64                `json:"consumedEnergy"`
	ProducedEnergy  float64                `json:"producedEnergy"`
	AllocatedEnergy float64                `json:"allocatedEnergy"`
	Unit            string                 `json:"unit"`
}

// ParseOnConfirm parses the raw JSON body into an OnConfirmPayload.
func ParseOnConfirm(body []byte) (*OnConfirmPayload, error) {
	var payload OnConfirmPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("failed to parse on_confirm payload: %w", err)
	}
	return &payload, nil
}

// MapToLedgerRecords converts an on_confirm payload to ledger PUT requests.
// Returns one LedgerPutRequest per order item.
func MapToLedgerRecords(payload *OnConfirmPayload, role string) []LedgerPutRequest {
	records := make([]LedgerPutRequest, 0, len(payload.Message.Order.OrderItems))

	for _, item := range payload.Message.Order.OrderItems {
		record := LedgerPutRequest{
			Role:             role,
			TransactionID:    payload.Context.TransactionID,
			OrderItemID:      item.AcceptedOffer.ID,
			PlatformIDBuyer:  payload.Context.BapID,
			PlatformIDSeller: payload.Context.BppID,
			DiscomIDBuyer:    extractStringField(payload.Message.Order.OrderAttributes, "utilityIdBuyer"),
			DiscomIDSeller:   extractStringField(payload.Message.Order.OrderAttributes, "utilityIdSeller"),
			BuyerID:          extractBuyerID(payload.Message.Order.Buyer),
			SellerID:         payload.Message.Order.Seller,
			TradeTime:        payload.Context.Timestamp,
			DeliveryStartTime: extractTimeWindowField(item.AcceptedOffer.OfferAttributes, "schema:startTime"),
			DeliveryEndTime:   extractTimeWindowField(item.AcceptedOffer.OfferAttributes, "schema:endTime"),
			TradeDetails:      mapTradeDetails(item),
			ClientReference:   generateClientReference(payload.Context.TransactionID, item.AcceptedOffer.ID),
		}
		records = append(records, record)
	}

	return records
}

// extractStringField extracts a string field from a map.
func extractStringField(m map[string]interface{}, key string) string {
	if m == nil {
		return ""
	}
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// extractBuyerID extracts the buyer ID from the buyer object.
func extractBuyerID(buyer map[string]interface{}) string {
	if buyer == nil {
		return ""
	}
	if id, ok := buyer["beckn:id"]; ok {
		if s, ok := id.(string); ok {
			return s
		}
	}
	return ""
}

// extractTimeWindowField extracts a time field from the offer attributes' timeWindow.
func extractTimeWindowField(offerAttrs map[string]interface{}, field string) string {
	if offerAttrs == nil {
		return ""
	}

	// Navigate to beckn:timeWindow
	timeWindow, ok := offerAttrs["beckn:timeWindow"]
	if !ok {
		return ""
	}

	twMap, ok := timeWindow.(map[string]interface{})
	if !ok {
		return ""
	}

	if v, ok := twMap[field]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// mapTradeDetails creates trade details from an order item.
func mapTradeDetails(item OrderItem) []TradeDetail {
	tradeUnit := normalizeTradeUnit(item.Quantity.UnitText)

	return []TradeDetail{
		{
			TradeQty:  item.Quantity.UnitQuantity,
			TradeType: "ENERGY", // Default to ENERGY for P2P trading
			TradeUnit: tradeUnit,
		},
	}
}

// normalizeTradeUnit converts unit text to ledger API enum format.
func normalizeTradeUnit(unitText string) string {
	normalized := strings.ToUpper(strings.TrimSpace(unitText))
	switch normalized {
	case "KWH", "KW":
		return normalized
	case "KW/H", "KILOWATT-HOUR", "KILOWATT HOUR":
		return "KWH"
	case "KILOWATT":
		return "KW"
	default:
		// Default to KWH for energy trading
		return "KWH"
	}
}

// generateClientReference creates an idempotency key from transaction and order item IDs.
func generateClientReference(transactionID, orderItemID string) string {
	return fmt.Sprintf("onix-%s-%s", transactionID, orderItemID)
}

// ExtractAction extracts the action from the request URL path or body.
func ExtractAction(urlPath string, body []byte) string {
	// First, try to extract from URL path
	// Expected format: /bap/receiver/{action} or /bpp/caller/{action}
	parts := strings.Split(strings.Trim(urlPath, "/"), "/")
	if len(parts) >= 3 {
		return parts[len(parts)-1]
	}

	// Fallback: extract from body context
	var payload struct {
		Context struct {
			Action string `json:"action"`
		} `json:"context"`
	}
	if err := json.Unmarshal(body, &payload); err == nil && payload.Context.Action != "" {
		return payload.Context.Action
	}

	return ""
}

// -------------------------
// on_status parsing and mapping
// -------------------------

// ParseOnStatus parses the raw JSON body into an OnStatusPayload.
func ParseOnStatus(body []byte) (*OnStatusPayload, error) {
	var payload OnStatusPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("failed to parse on_status payload: %w", err)
	}
	return &payload, nil
}

// MapToLedgerRecordRequests converts an on_status payload to ledger RECORD requests.
// Returns one LedgerRecordRequest per order item with aggregated meter readings.
// role should be BUYER_DISCOM or SELLER_DISCOM.
func MapToLedgerRecordRequests(payload *OnStatusPayload, role string) []LedgerRecordRequest {
	records := make([]LedgerRecordRequest, 0, len(payload.Message.Order.OrderItems))

	isBuyerDiscom := role == "BUYER_DISCOM"

	for _, item := range payload.Message.Order.OrderItems {
		// Extract meter readings from fulfillmentAttributes
		meterReadings := extractMeterReadings(item.OrderItemAttributes)
		if len(meterReadings) == 0 {
			continue // Skip items without meter readings
		}

		// Aggregate allocatedEnergy from all meter readings
		totalAllocatedEnergy := 0.0
		for _, reading := range meterReadings {
			totalAllocatedEnergy += reading.AllocatedEnergy
		}

		// Create validation metric based on role
		// BUYER_DISCOM → ACTUAL_PULLED
		// SELLER_DISCOM → ACTUAL_PUSHED
		var metricType string
		if isBuyerDiscom {
			metricType = "ACTUAL_PULLED"
		} else {
			metricType = "ACTUAL_PUSHED"
		}

		metric := ValidationMetric{
			ValidationMetricType:  metricType,
			ValidationMetricValue: totalAllocatedEnergy,
		}

		record := LedgerRecordRequest{
			Role:            role,
			TransactionID:   payload.Context.TransactionID,
			OrderItemID:     item.AcceptedOffer.ID,
			ClientReference: generateClientReference(payload.Context.TransactionID, item.AcceptedOffer.ID),
		}

		// Assign metrics based on role
		if isBuyerDiscom {
			record.BuyerFulfillmentValidationMetrics = []ValidationMetric{metric}
		} else {
			record.SellerFulfillmentValidationMetrics = []ValidationMetric{metric}
		}

		records = append(records, record)
	}

	return records
}

// extractMeterReadings extracts meter readings from orderItemAttributes.fulfillmentAttributes.meterReadings
func extractMeterReadings(orderItemAttrs map[string]interface{}) []MeterReading {
	if orderItemAttrs == nil {
		return nil
	}

	// Navigate: orderItemAttributes → fulfillmentAttributes → meterReadings
	fulfillmentAttrs, ok := orderItemAttrs["fulfillmentAttributes"]
	if !ok {
		return nil
	}

	fulfillmentMap, ok := fulfillmentAttrs.(map[string]interface{})
	if !ok {
		return nil
	}

	meterReadingsRaw, ok := fulfillmentMap["meterReadings"]
	if !ok {
		return nil
	}

	meterReadingsSlice, ok := meterReadingsRaw.([]interface{})
	if !ok {
		return nil
	}

	readings := make([]MeterReading, 0, len(meterReadingsSlice))
	for _, readingRaw := range meterReadingsSlice {
		readingMap, ok := readingRaw.(map[string]interface{})
		if !ok {
			continue
		}

		reading := MeterReading{
			ConsumedEnergy:  extractFloat(readingMap, "consumedEnergy"),
			ProducedEnergy:  extractFloat(readingMap, "producedEnergy"),
			AllocatedEnergy: extractFloat(readingMap, "allocatedEnergy"),
			Unit:            extractStringField(readingMap, "unit"),
		}

		if tw, ok := readingMap["beckn:timeWindow"]; ok {
			if twMap, ok := tw.(map[string]interface{}); ok {
				reading.TimeWindow = twMap
			}
		}

		readings = append(readings, reading)
	}

	return readings
}

// extractFloat extracts a float64 from a map, handling both float64 and int types.
func extractFloat(m map[string]interface{}, key string) float64 {
	if m == nil {
		return 0
	}
	if v, ok := m[key]; ok {
		switch val := v.(type) {
		case float64:
			return val
		case int:
			return float64(val)
		case int64:
			return float64(val)
		}
	}
	return 0
}
