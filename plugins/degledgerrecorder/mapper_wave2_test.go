package degledgerrecorder

import (
	"testing"
)

// Trimmed wave2 on_confirm body covering all the fields the mapper reads:
// context (transactionId, bapId, bppId, timestamp), participants
// (buyer/seller with utilityId+meterId, buyerDiscom/sellerDiscom with
// ledgerUri), and a single commitment with a seller-side delivery window.
const sampleWave2OnConfirm = `{
  "context": {
    "networkId": "nfh.global/testnet-deg",
    "version": "2.0.0",
    "action": "on_confirm",
    "bapId": "bap.example.com",
    "bapUri": "https://bap.example.com/beckn",
    "bppId": "bpp.example.com",
    "bppUri": "https://bpp.example.com/beckn",
    "transactionId": "txn-p2p-001",
    "messageId": "msg-on-confirm-001",
    "timestamp": "2026-04-25T10:10:05Z"
  },
  "message": {
    "contract": {
      "id": "contract-p2p-001",
      "commitments": [
        {
          "id": "commitment-p2p-001",
          "resources": [
            {
              "id": "energy-resource-solar-001",
              "quantity": {
                "@type": "Quantity",
                "unitCode": "KWH",
                "unitQuantity": 35.0
              }
            }
          ],
          "offer": {
            "id": "offer-p2p-001",
            "offerAttributes": {
              "@type": "EnergyTradeOffer",
              "inputs": [
                {
                  "role": "seller",
                  "participantId": "TPDDL-DL-seller-001",
                  "inputs": {
                    "offers": [
                      {
                        "pricePerKwh": 12,
                        "deliveryWindow": {
                          "@type": "beckn:TimePeriod",
                          "schema:startTime": "2026-04-26T04:30:00Z",
                          "schema:endTime": "2026-04-26T05:30:00Z"
                        }
                      }
                    ]
                  }
                },
                {
                  "role": "buyer",
                  "participantId": "BRPL-DL-buyer-001",
                  "inputs": {}
                }
              ]
            }
          }
        }
      ],
      "participants": [
        {
          "role": "seller",
          "participantId": "TPDDL-DL-seller-001",
          "participantAttributes": {
            "@type": "EnergyCustomer",
            "meterId": "der://meter/seller-001",
            "utilityId": "TPDDL-DL",
            "utilityCustomerId": "TPDDL-CUST-S-001"
          }
        },
        {
          "role": "buyer",
          "participantId": "BRPL-DL-buyer-001",
          "participantAttributes": {
            "@type": "EnergyCustomer",
            "meterId": "der://meter/buyer-001",
            "utilityId": "BRPL-DL",
            "utilityCustomerId": "BRPL-CUST-B-001"
          }
        },
        {
          "role": "buyerDiscom",
          "participantId": "buyer-discom-ledger",
          "participantAttributes": {
            "@type": "DiscomLedgerProvider",
            "utilityId": "BRPL-DL",
            "ledgerUri": "https://ies-p2p-energy-ledger.beckn.io"
          }
        },
        {
          "role": "sellerDiscom",
          "participantId": "seller-discom-ledger",
          "participantAttributes": {
            "@type": "DiscomLedgerProvider",
            "utilityId": "TPDDL-DL",
            "ledgerUri": "https://ies-p2p-energy-ledger.beckn.io"
          }
        }
      ]
    }
  }
}`

func TestParseOnConfirmWave2_ContextFields(t *testing.T) {
	p, err := ParseOnConfirmWave2([]byte(sampleWave2OnConfirm))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if p.Context.TransactionID != "txn-p2p-001" {
		t.Errorf("transactionId: got %q", p.Context.TransactionID)
	}
	if p.Context.BapID != "bap.example.com" || p.Context.BppID != "bpp.example.com" {
		t.Errorf("bapId/bppId: got %q/%q", p.Context.BapID, p.Context.BppID)
	}
	if len(p.Message.Contract.Commitments) != 1 {
		t.Errorf("commitments: got %d", len(p.Message.Contract.Commitments))
	}
}

func TestMapWave2ToLedgerRecord_AllFields(t *testing.T) {
	p, err := ParseOnConfirmWave2([]byte(sampleWave2OnConfirm))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	rec, err := MapWave2ToLedgerRecord(p, "BUYER")
	if err != nil {
		t.Fatalf("map: %v", err)
	}

	checks := []struct{ name, got, want string }{
		{"role", rec.Role, "BUYER"},
		{"transactionId", rec.TransactionID, "txn-p2p-001"},
		{"orderItemId", rec.OrderItemID, "txn-p2p-001"}, // wave2: orderItemId == transactionId
		{"platformIdBuyer", rec.PlatformIDBuyer, "bap.example.com"},
		{"platformIdSeller", rec.PlatformIDSeller, "bpp.example.com"},
		{"discomIdBuyer", rec.DiscomIDBuyer, "BRPL-DL"},
		{"discomIdSeller", rec.DiscomIDSeller, "TPDDL-DL"},
		{"buyerId", rec.BuyerID, "der://meter/buyer-001"},
		{"sellerId", rec.SellerID, "der://meter/seller-001"},
		{"tradeTime", rec.TradeTime, "2026-04-25T10:10:05Z"},
		{"deliveryStartTime", rec.DeliveryStartTime, "2026-04-26T04:30:00Z"},
		{"deliveryEndTime", rec.DeliveryEndTime, "2026-04-26T05:30:00Z"},
	}
	for _, c := range checks {
		if c.got != c.want {
			t.Errorf("%s: got %q, want %q", c.name, c.got, c.want)
		}
	}

	if len(rec.TradeDetails) != 1 {
		t.Fatalf("tradeDetails: got %d", len(rec.TradeDetails))
	}
	td := rec.TradeDetails[0]
	if td.TradeQty != 35.0 || td.TradeUnit != "KWH" || td.TradeType != "ENERGY" {
		t.Errorf("tradeDetail: got qty=%v, unit=%q, type=%q", td.TradeQty, td.TradeUnit, td.TradeType)
	}
}

func TestExtractWave2DiscomLedgerUri(t *testing.T) {
	p, err := ParseOnConfirmWave2([]byte(sampleWave2OnConfirm))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if got := ExtractWave2DiscomLedgerUri(p, SideBuyer); got != "https://ies-p2p-energy-ledger.beckn.io" {
		t.Errorf("buyerDiscom ledgerUri: got %q", got)
	}
	if got := ExtractWave2DiscomLedgerUri(p, SideSeller); got != "https://ies-p2p-energy-ledger.beckn.io" {
		t.Errorf("sellerDiscom ledgerUri: got %q", got)
	}
}

func TestExtractWave2DiscomLedgerUri_MissingReturnsEmpty(t *testing.T) {
	const noLedgerUri = `{"context":{"transactionId":"x"},"message":{"contract":{"participants":[{"role":"buyerDiscom","participantId":"x"}]}}}`
	p, err := ParseOnConfirmWave2([]byte(noLedgerUri))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if got := ExtractWave2DiscomLedgerUri(p, SideBuyer); got != "" {
		t.Errorf("expected empty, got %q", got)
	}
	if got := ExtractWave2DiscomLedgerUri(p, SideSeller); got != "" {
		t.Errorf("expected empty for missing side, got %q", got)
	}
}

func TestMapWave2_NoCommitmentsErrors(t *testing.T) {
	p := &Wave2OnConfirmPayload{}
	if _, err := MapWave2ToLedgerRecord(p, "BUYER"); err == nil {
		t.Errorf("expected error for empty commitments, got nil")
	}
}
