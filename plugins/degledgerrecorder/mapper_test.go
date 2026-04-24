package degledgerrecorder

import (
	"encoding/json"
	"testing"
)

// Sample on_confirm payload for testing
const sampleOnConfirmPayload = `{
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
    "domain": "beckn.one:deg:p2p-trading-interdiscom:2.0.0"
  },
  "message": {
    "order": {
      "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/core/v2/context.jsonld",
      "@type": "beckn:Order",
      "beckn:id": "order-energy-001",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001",
      "beckn:buyer": {
        "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/core/v2/context.jsonld",
        "@type": "beckn:Buyer",
        "beckn:id": "buyer-001",
        "beckn:buyerAttributes": {
          "@context": "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.1/specification/schema/EnergyTrade/v0.3/context.jsonld",
          "@type": "EnergyCustomer",
          "meterId": "der://meter/98765456",
          "utilityCustomerId": "BESCOM-CUST-001",
          "utilityId": "BESCOM-KA"
        }
      },
      "beckn:orderAttributes": {
        "@context": "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.1/specification/schema/EnergyTrade/v0.3/context.jsonld",
        "@type": "EnergyTradeOrder",
        "bap_id": "bap.energy-consumer.com",
        "bpp_id": "bpp.energy-provider.com",
        "total_quantity": {
          "unitQuantity": 25.0,
          "unitText": "kWh"
        }
      },
      "beckn:orderItems": [
        {
          "beckn:orderedItem": "energy-resource-solar-001",
          "beckn:quantity": {
            "unitQuantity": 15.0,
            "unitText": "kWh"
          },
          "beckn:orderItemAttributes": {
            "@context": "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.1/specification/schema/EnergyTrade/v0.3/context.jsonld",
            "@type": "EnergyOrderItem",
            "providerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.1/specification/schema/EnergyTrade/v0.3/context.jsonld",
              "@type": "EnergyCustomer",
              "meterId": "der://meter/100200300",
              "utilityCustomerId": "TPDDL-CUST-001",
              "utilityId": "TPDDL-DL"
            }
          },
          "beckn:acceptedOffer": {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/core/v2/context.jsonld",
            "@type": "beckn:Offer",
            "beckn:id": "offer-morning-001",
            "beckn:descriptor": {
              "@type": "beckn:Descriptor",
              "schema:name": "Morning Solar Energy Offer"
            },
            "beckn:provider": "provider-solar-farm-001",
            "beckn:items": ["energy-resource-solar-001"],
            "beckn:price": {
              "@type": "schema:PriceSpecification",
              "schema:price": 0.15,
              "schema:priceCurrency": "USD",
              "unitText": "kWh",
              "applicableQuantity": {
                "unitQuantity": 20.0,
                "unitText": "kWh"
              }
            },
            "beckn:offerAttributes": {
              "@context": "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.1/specification/schema/EnergyTrade/v0.3/context.jsonld",
              "@type": "EnergyTradeOffer",
              "pricingModel": "PER_KWH",
              "deliveryWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T06:00:00Z",
                "schema:endTime": "2026-01-09T12:00:00Z"
              },
              "validityWindow": {
                "@type": "beckn:TimePeriod",
                "schema:startTime": "2026-01-09T00:00:00Z",
                "schema:endTime": "2026-01-09T05:00:00Z"
              }
            }
          }
        }
      ]
    }
  }
}`

func TestExtractBuyerID(t *testing.T) {
	tests := []struct {
		name     string
		buyer    map[string]interface{}
		expected string
	}{
		{
			name:     "nil buyer",
			buyer:    nil,
			expected: "",
		},
		{
			name:     "empty buyer",
			buyer:    map[string]interface{}{},
			expected: "",
		},
		{
			name: "buyer without buyerAttributes",
			buyer: map[string]interface{}{
				"beckn:id": "buyer-001",
			},
			expected: "",
		},
		{
			name: "buyer with buyerAttributes containing meterId",
			buyer: map[string]interface{}{
				"beckn:id": "buyer-001",
				"beckn:buyerAttributes": map[string]interface{}{
					"meterId":   "der://meter/98765456",
					"utilityId": "BESCOM-KA",
				},
			},
			expected: "der://meter/98765456",
		},
		{
			name: "buyer with buyerAttributes but no meterId",
			buyer: map[string]interface{}{
				"beckn:id": "buyer-001",
				"beckn:buyerAttributes": map[string]interface{}{
					"utilityId": "BESCOM-KA",
				},
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractBuyerID(tt.buyer)
			if result != tt.expected {
				t.Errorf("extractBuyerID() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestExtractSellerID(t *testing.T) {
	tests := []struct {
		name           string
		orderItemAttrs map[string]interface{}
		expected       string
	}{
		{
			name:           "nil orderItemAttrs",
			orderItemAttrs: nil,
			expected:       "",
		},
		{
			name:           "empty orderItemAttrs",
			orderItemAttrs: map[string]interface{}{},
			expected:       "",
		},
		{
			name: "orderItemAttrs without providerAttributes",
			orderItemAttrs: map[string]interface{}{
				"@type": "EnergyOrderItem",
			},
			expected: "",
		},
		{
			name: "orderItemAttrs with providerAttributes containing meterId",
			orderItemAttrs: map[string]interface{}{
				"@type": "EnergyOrderItem",
				"providerAttributes": map[string]interface{}{
					"meterId":   "der://meter/100200300",
					"utilityId": "TPDDL-DL",
				},
			},
			expected: "der://meter/100200300",
		},
		{
			name: "orderItemAttrs with providerAttributes but no meterId",
			orderItemAttrs: map[string]interface{}{
				"@type": "EnergyOrderItem",
				"providerAttributes": map[string]interface{}{
					"utilityId": "TPDDL-DL",
				},
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractSellerID(tt.orderItemAttrs)
			if result != tt.expected {
				t.Errorf("extractSellerID() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestExtractBuyerUtilityID(t *testing.T) {
	tests := []struct {
		name     string
		buyer    map[string]interface{}
		expected string
	}{
		{
			name:     "nil buyer",
			buyer:    nil,
			expected: "",
		},
		{
			name: "buyer with buyerAttributes containing utilityId",
			buyer: map[string]interface{}{
				"beckn:id": "buyer-001",
				"beckn:buyerAttributes": map[string]interface{}{
					"meterId":   "der://meter/98765456",
					"utilityId": "BESCOM-KA",
				},
			},
			expected: "BESCOM-KA",
		},
		{
			name: "buyer with buyerAttributes but no utilityId",
			buyer: map[string]interface{}{
				"beckn:id": "buyer-001",
				"beckn:buyerAttributes": map[string]interface{}{
					"meterId": "der://meter/98765456",
				},
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractBuyerUtilityID(tt.buyer)
			if result != tt.expected {
				t.Errorf("extractBuyerUtilityID() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestExtractSellerUtilityID(t *testing.T) {
	tests := []struct {
		name           string
		orderItemAttrs map[string]interface{}
		expected       string
	}{
		{
			name:           "nil orderItemAttrs",
			orderItemAttrs: nil,
			expected:       "",
		},
		{
			name: "orderItemAttrs with providerAttributes containing utilityId",
			orderItemAttrs: map[string]interface{}{
				"@type": "EnergyOrderItem",
				"providerAttributes": map[string]interface{}{
					"meterId":   "der://meter/100200300",
					"utilityId": "TPDDL-DL",
				},
			},
			expected: "TPDDL-DL",
		},
		{
			name: "orderItemAttrs with providerAttributes but no utilityId",
			orderItemAttrs: map[string]interface{}{
				"@type": "EnergyOrderItem",
				"providerAttributes": map[string]interface{}{
					"meterId": "der://meter/100200300",
				},
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractSellerUtilityID(tt.orderItemAttrs)
			if result != tt.expected {
				t.Errorf("extractSellerUtilityID() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestMapToLedgerRecords(t *testing.T) {
	// Parse the sample payload
	payload, err := ParseOnConfirm([]byte(sampleOnConfirmPayload))
	if err != nil {
		t.Fatalf("Failed to parse sample payload: %v", err)
	}

	// Map to ledger records
	records := MapToLedgerRecords(payload, "BUYER")

	// Verify we got one record (one order item in the sample)
	if len(records) != 1 {
		t.Fatalf("Expected 1 record, got %d", len(records))
	}

	record := records[0]

	// Test all extracted fields
	tests := []struct {
		field    string
		got      string
		expected string
	}{
		{"Role", record.Role, "BUYER"},
		{"TransactionID", record.TransactionID, "txn-energy-001"},
		{"OrderItemID", record.OrderItemID, "offer-morning-001"},
		{"PlatformIDBuyer", record.PlatformIDBuyer, "bap.energy-consumer.com"},
		{"PlatformIDSeller", record.PlatformIDSeller, "bpp.energy-provider.com"},
		{"BuyerID", record.BuyerID, "der://meter/98765456"},
		{"SellerID", record.SellerID, "der://meter/100200300"},
		{"DiscomIDBuyer", record.DiscomIDBuyer, "BESCOM-KA"},
		{"DiscomIDSeller", record.DiscomIDSeller, "TPDDL-DL"},
		{"TradeTime", record.TradeTime, "2024-10-04T10:25:05Z"},
		{"DeliveryStartTime", record.DeliveryStartTime, "2026-01-09T06:00:00Z"},
		{"DeliveryEndTime", record.DeliveryEndTime, "2026-01-09T12:00:00Z"},
	}

	for _, tt := range tests {
		t.Run(tt.field, func(t *testing.T) {
			if tt.got != tt.expected {
				t.Errorf("%s = %q, want %q", tt.field, tt.got, tt.expected)
			}
		})
	}

	// Verify trade details
	if len(record.TradeDetails) != 1 {
		t.Fatalf("Expected 1 trade detail, got %d", len(record.TradeDetails))
	}

	tradeDetail := record.TradeDetails[0]
	if tradeDetail.TradeQty != 15.0 {
		t.Errorf("TradeQty = %f, want %f", tradeDetail.TradeQty, 15.0)
	}
	if tradeDetail.TradeType != "ENERGY" {
		t.Errorf("TradeType = %q, want %q", tradeDetail.TradeType, "ENERGY")
	}
	if tradeDetail.TradeUnit != "KWH" {
		t.Errorf("TradeUnit = %q, want %q", tradeDetail.TradeUnit, "KWH")
	}

	// Verify client reference format
	expectedClientRef := "onix-txn-energy-001-offer-morning-001"
	if record.ClientReference != expectedClientRef {
		t.Errorf("ClientReference = %q, want %q", record.ClientReference, expectedClientRef)
	}
}

func TestMapToLedgerRecords_MultipleOrderItems(t *testing.T) {
	// Create a payload with multiple order items
	payloadWithMultipleItems := `{
		"context": {
			"version": "2.0.0",
			"action": "on_confirm",
			"timestamp": "2024-10-04T10:25:05Z",
			"message_id": "msg-001",
			"transaction_id": "txn-multi-001",
			"bap_id": "bap.test.com",
			"bap_uri": "https://bap.test.com",
			"bpp_id": "bpp.test.com",
			"bpp_uri": "https://bpp.test.com",
			"ttl": "PT30S",
			"domain": "deg:p2p-trading"
		},
		"message": {
			"order": {
				"beckn:id": "order-001",
				"beckn:orderStatus": "CREATED",
				"beckn:seller": "seller-001",
				"beckn:buyer": {
					"beckn:id": "buyer-001",
					"beckn:buyerAttributes": {
						"meterId": "der://meter/buyer-meter",
						"utilityId": "BUYER-DISCOM"
					}
				},
				"beckn:orderAttributes": {},
				"beckn:orderItems": [
					{
						"beckn:orderedItem": "item-001",
						"beckn:quantity": {"unitQuantity": 10.0, "unitText": "kWh"},
						"beckn:orderItemAttributes": {
							"providerAttributes": {
								"meterId": "der://meter/seller-meter-1",
								"utilityId": "SELLER-DISCOM-1"
							}
						},
						"beckn:acceptedOffer": {
							"beckn:id": "offer-001",
							"beckn:offerAttributes": {}
						}
					},
					{
						"beckn:orderedItem": "item-002",
						"beckn:quantity": {"unitQuantity": 20.0, "unitText": "kWh"},
						"beckn:orderItemAttributes": {
							"providerAttributes": {
								"meterId": "der://meter/seller-meter-2",
								"utilityId": "SELLER-DISCOM-2"
							}
						},
						"beckn:acceptedOffer": {
							"beckn:id": "offer-002",
							"beckn:offerAttributes": {}
						}
					}
				]
			}
		}
	}`

	payload, err := ParseOnConfirm([]byte(payloadWithMultipleItems))
	if err != nil {
		t.Fatalf("Failed to parse payload: %v", err)
	}

	records := MapToLedgerRecords(payload, "SELLER")

	if len(records) != 2 {
		t.Fatalf("Expected 2 records, got %d", len(records))
	}

	// First order item
	if records[0].SellerID != "der://meter/seller-meter-1" {
		t.Errorf("Record[0].SellerID = %q, want %q", records[0].SellerID, "der://meter/seller-meter-1")
	}
	if records[0].DiscomIDSeller != "SELLER-DISCOM-1" {
		t.Errorf("Record[0].DiscomIDSeller = %q, want %q", records[0].DiscomIDSeller, "SELLER-DISCOM-1")
	}
	if records[0].TradeDetails[0].TradeQty != 10.0 {
		t.Errorf("Record[0].TradeQty = %f, want %f", records[0].TradeDetails[0].TradeQty, 10.0)
	}

	// Second order item
	if records[1].SellerID != "der://meter/seller-meter-2" {
		t.Errorf("Record[1].SellerID = %q, want %q", records[1].SellerID, "der://meter/seller-meter-2")
	}
	if records[1].DiscomIDSeller != "SELLER-DISCOM-2" {
		t.Errorf("Record[1].DiscomIDSeller = %q, want %q", records[1].DiscomIDSeller, "SELLER-DISCOM-2")
	}
	if records[1].TradeDetails[0].TradeQty != 20.0 {
		t.Errorf("Record[1].TradeQty = %f, want %f", records[1].TradeDetails[0].TradeQty, 20.0)
	}

	// Both should have the same buyer info
	for i, rec := range records {
		if rec.BuyerID != "der://meter/buyer-meter" {
			t.Errorf("Record[%d].BuyerID = %q, want %q", i, rec.BuyerID, "der://meter/buyer-meter")
		}
		if rec.DiscomIDBuyer != "BUYER-DISCOM" {
			t.Errorf("Record[%d].DiscomIDBuyer = %q, want %q", i, rec.DiscomIDBuyer, "BUYER-DISCOM")
		}
	}
}

func TestExtractTimeWindowField(t *testing.T) {
	tests := []struct {
		name       string
		offerAttrs map[string]interface{}
		field      string
		expected   string
	}{
		{
			name:       "nil offerAttrs",
			offerAttrs: nil,
			field:      "schema:startTime",
			expected:   "",
		},
		{
			name:       "empty offerAttrs",
			offerAttrs: map[string]interface{}{},
			field:      "schema:startTime",
			expected:   "",
		},
		{
			name: "offerAttrs without deliveryWindow",
			offerAttrs: map[string]interface{}{
				"pricingModel": "PER_KWH",
			},
			field:    "schema:startTime",
			expected: "",
		},
		{
			name: "offerAttrs with deliveryWindow containing startTime",
			offerAttrs: map[string]interface{}{
				"pricingModel": "PER_KWH",
				"deliveryWindow": map[string]interface{}{
					"@type":            "beckn:TimePeriod",
					"schema:startTime": "2026-01-09T06:00:00Z",
					"schema:endTime":   "2026-01-09T12:00:00Z",
				},
			},
			field:    "schema:startTime",
			expected: "2026-01-09T06:00:00Z",
		},
		{
			name: "offerAttrs with deliveryWindow containing endTime",
			offerAttrs: map[string]interface{}{
				"deliveryWindow": map[string]interface{}{
					"schema:startTime": "2026-01-09T06:00:00Z",
					"schema:endTime":   "2026-01-09T12:00:00Z",
				},
			},
			field:    "schema:endTime",
			expected: "2026-01-09T12:00:00Z",
		},
		{
			name: "offerAttrs with deliveryWindow but missing requested field",
			offerAttrs: map[string]interface{}{
				"deliveryWindow": map[string]interface{}{
					"schema:startTime": "2026-01-09T06:00:00Z",
				},
			},
			field:    "schema:endTime",
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractTimeWindowField(tt.offerAttrs, tt.field)
			if result != tt.expected {
				t.Errorf("extractTimeWindowField() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestParseOnConfirm(t *testing.T) {
	payload, err := ParseOnConfirm([]byte(sampleOnConfirmPayload))
	if err != nil {
		t.Fatalf("ParseOnConfirm failed: %v", err)
	}

	// Verify context parsing
	if payload.Context.Action != "on_confirm" {
		t.Errorf("Context.Action = %q, want %q", payload.Context.Action, "on_confirm")
	}
	if payload.Context.TransactionID != "txn-energy-001" {
		t.Errorf("Context.TransactionID = %q, want %q", payload.Context.TransactionID, "txn-energy-001")
	}

	// Verify order parsing
	if payload.Message.Order.ID != "order-energy-001" {
		t.Errorf("Order.ID = %q, want %q", payload.Message.Order.ID, "order-energy-001")
	}
	if len(payload.Message.Order.OrderItems) != 1 {
		t.Errorf("len(OrderItems) = %d, want %d", len(payload.Message.Order.OrderItems), 1)
	}
}

func TestParseOnConfirm_InvalidJSON(t *testing.T) {
	_, err := ParseOnConfirm([]byte("invalid json"))
	if err == nil {
		t.Error("Expected error for invalid JSON, got nil")
	}
}

// Helper to pretty print JSON for debugging
func prettyJSON(v interface{}) string {
	b, _ := json.MarshalIndent(v, "", "  ")
	return string(b)
}
