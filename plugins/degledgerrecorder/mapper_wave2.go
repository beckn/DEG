package degledgerrecorder

import (
	"encoding/json"
	"fmt"
	"log"
	"net/url"
	"strings"
)

// Side identifies which discom's ledgerUri to read from the payload.
type Side string

const (
	SideBuyer  Side = "buyerDiscom"
	SideSeller Side = "sellerDiscom"
)

// Wave2OnConfirmPayload is the wave2 (P2PTrade/v2.0) on_confirm body.
// Wave2 uses camelCase context keys and a `message.contract.commitments` shape.
type Wave2OnConfirmPayload struct {
	Context Wave2Context `json:"context"`
	Message struct {
		Contract Wave2Contract `json:"contract"`
	} `json:"message"`
}

// Wave2Context — wave2 uses camelCase (bapId, bppId, transactionId), not snake_case.
type Wave2Context struct {
	NetworkID     string `json:"networkId"`
	Version       string `json:"version"`
	Action        string `json:"action"`
	BapID         string `json:"bapId"`
	BapURI        string `json:"bapUri"`
	BppID         string `json:"bppId"`
	BppURI        string `json:"bppUri"`
	TransactionID string `json:"transactionId"`
	MessageID     string `json:"messageId"`
	Timestamp     string `json:"timestamp"`
}

// Wave2Contract is `message.contract`.
type Wave2Contract struct {
	ID                 string                 `json:"id"`
	Commitments        []Wave2Commitment      `json:"commitments"`
	Performance        []Wave2Performance     `json:"performance"`
	Participants       []Wave2Participant     `json:"participants"`
	ContractAttributes map[string]interface{} `json:"contractAttributes"`
}

// Wave2Performance is `message.contract.performance[*]`.
type Wave2Performance struct {
	ID                    string                 `json:"id"`
	CommitmentIDs         []string               `json:"commitmentIds"`
	PerformanceAttributes map[string]interface{} `json:"performanceAttributes"`
}

// Wave2Commitment is `message.contract.commitments[*]`.
type Wave2Commitment struct {
	ID        string          `json:"id"`
	Resources []Wave2Resource `json:"resources"`
	Offer     Wave2Offer      `json:"offer"`
}

// Wave2Resource is `commitments[*].resources[*]`.
type Wave2Resource struct {
	ID       string        `json:"id"`
	Quantity Wave2Quantity `json:"quantity"`
}

// Wave2Quantity captures unitCode + unitQuantity (kWh, kW, etc.).
type Wave2Quantity struct {
	UnitCode     string  `json:"unitCode"`
	UnitQuantity float64 `json:"unitQuantity"`
}

// Wave2Offer is `commitments[*].offer`.
type Wave2Offer struct {
	ID              string                 `json:"id"`
	ResourceIDs     []string               `json:"resourceIds"`
	OfferAttributes map[string]interface{} `json:"offerAttributes"`
}

// Wave2Participant is `contract.participants[*]`. participantAttributes is
// loose-typed because its shape varies by role: EnergyCustomer for buyer/seller,
// DiscomLedgerProvider for buyerDiscom/sellerDiscom.
type Wave2Participant struct {
	Role                  string                 `json:"role"`
	ParticipantID         string                 `json:"participantId"`
	ParticipantAttributes map[string]interface{} `json:"participantAttributes"`
}

// ParseOnConfirmWave2 unmarshals a wave2 on_confirm body.
func ParseOnConfirmWave2(body []byte) (*Wave2OnConfirmPayload, error) {
	var payload Wave2OnConfirmPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("failed to parse wave2 on_confirm payload: %w", err)
	}
	return &payload, nil
}

// MapWave2ToLedgerRecords builds one LedgerPutRequest per interval found in the
// first commitment's seller offerTimeseries. record_id format:
// {transactionId}_{contractId}_{intervalId}.
func MapWave2ToLedgerRecords(payload *Wave2OnConfirmPayload, role string) ([]LedgerPutRequest, error) {
	if len(payload.Message.Contract.Commitments) == 0 {
		return nil, fmt.Errorf("wave2 payload has no commitments")
	}
	commitment := payload.Message.Contract.Commitments[0]
	if len(payload.Message.Contract.Commitments) > 1 {
		log.Printf("WARNING: wave2 payload has %d commitments; using only the first (txn: %s)",
			len(payload.Message.Contract.Commitments), payload.Context.TransactionID)
	}

	buyerPart := findWave2Participant(payload.Message.Contract.Participants, "buyer")
	sellerPart := findWave2Participant(payload.Message.Contract.Participants, "seller")

	deliveryStart, deliveryEnd := extractWave2DeliveryWindow(commitment.Offer.OfferAttributes)
	if deliveryStart == "" {
		log.Printf("WARNING: wave2 deliveryStartTime not found (txn: %s, commitment: %s)",
			payload.Context.TransactionID, commitment.ID)
	}
	if deliveryEnd == "" {
		log.Printf("WARNING: wave2 deliveryEndTime not found (txn: %s, commitment: %s)",
			payload.Context.TransactionID, commitment.ID)
	}

	tradeQty, tradeUnit := extractWave2QuantityAndUnit(commitment.Resources)
	contractID := payload.Message.Contract.ID
	intervalIDs := extractWave2IntervalIDs(commitment.Offer.OfferAttributes)

	// Always emit at least one record even if interval list is empty (id=0).
	if len(intervalIDs) == 0 {
		intervalIDs = []int{0}
	}

	records := make([]LedgerPutRequest, 0, len(intervalIDs))
	for _, intervalID := range intervalIDs {
		orderItemID := fmt.Sprintf("%s_%s_%d", payload.Context.TransactionID, contractID, intervalID)
		records = append(records, LedgerPutRequest{
			Role:              role,
			TransactionID:     payload.Context.TransactionID,
			OrderItemID:       orderItemID,
			PlatformIDBuyer:   payload.Context.BapID,
			PlatformIDSeller:  payload.Context.BppID,
			DiscomIDBuyer:     wave2StringAttr(buyerPart, "utilityId"),
			DiscomIDSeller:    wave2StringAttr(sellerPart, "utilityId"),
			BuyerID:           wave2StringAttr(buyerPart, "meterId"),
			SellerID:          wave2StringAttr(sellerPart, "meterId"),
			TradeTime:         payload.Context.Timestamp,
			DeliveryStartTime: deliveryStart,
			DeliveryEndTime:   deliveryEnd,
			TradeDetails: []TradeDetail{
				{
					TradeQty:  tradeQty,
					TradeType: "ENERGY",
					TradeUnit: normalizeTradeUnit(tradeUnit),
				},
			},
			ClientReference: generateClientReference(payload.Context.TransactionID, orderItemID),
		})
	}
	return records, nil
}

// ExtractWave2DiscomLedgerUri returns the ledgerUri for the requested side from
// `participants[role=buyerDiscom|sellerDiscom].participantAttributes.ledgerUri`.
// Returns "" if the side is missing or has no ledgerUri.
func ExtractWave2DiscomLedgerUri(payload *Wave2OnConfirmPayload, side Side) string {
	part := findWave2Participant(payload.Message.Contract.Participants, string(side))
	return wave2StringAttr(part, "ledgerUri")
}

// findWave2Participant returns the first participant entry matching the role.
func findWave2Participant(participants []Wave2Participant, role string) *Wave2Participant {
	for i := range participants {
		if participants[i].Role == role {
			return &participants[i]
		}
	}
	return nil
}

// wave2StringAttr reads a string attribute from a participant's participantAttributes.
func wave2StringAttr(p *Wave2Participant, key string) string {
	if p == nil || p.ParticipantAttributes == nil {
		return ""
	}
	if v, ok := p.ParticipantAttributes[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}

// extractWave2DeliveryWindow walks
// offerAttributes.inputs[role=seller].inputs.offers[0].deliveryWindow.{schema:startTime, schema:endTime}.
// Returns ("", "") if any hop is missing.
func extractWave2DeliveryWindow(offerAttrs map[string]interface{}) (string, string) {
	if offerAttrs == nil {
		return "", ""
	}
	inputs, ok := offerAttrs["inputs"].([]interface{})
	if !ok {
		return "", ""
	}
	for _, raw := range inputs {
		entry, ok := raw.(map[string]interface{})
		if !ok {
			continue
		}
		if entry["role"] != "seller" {
			continue
		}
		inner, ok := entry["inputs"].(map[string]interface{})
		if !ok {
			continue
		}
		offers, ok := inner["offers"].([]interface{})
		if !ok || len(offers) == 0 {
			continue
		}
		first, ok := offers[0].(map[string]interface{})
		if !ok {
			continue
		}
		dw, ok := first["deliveryWindow"].(map[string]interface{})
		if !ok {
			continue
		}
		start, _ := dw["schema:startTime"].(string)
		end, _ := dw["schema:endTime"].(string)
		return start, end
	}
	return "", ""
}

// extractWave2QuantityAndUnit reads the first resource's quantity. wave2 keeps
// trade qty/unit on commitment.resources[0].quantity; returns 0 / "" if missing.
func extractWave2QuantityAndUnit(resources []Wave2Resource) (float64, string) {
	if len(resources) == 0 {
		return 0, ""
	}
	q := resources[0].Quantity
	return q.UnitQuantity, q.UnitCode
}

// RewriteContextForBeckn rewrites context.bppUri and context.bapUri on the
// raw on_confirm body so that, from the ledger TSP's POV:
//   - bppUri = "<senderHost>/bpp/caller"   — the platform sending this call
//   - bapUri = "<ledgerURI>/bap/receiver"  — the TSP itself, as the receiving BAP
//
// Everything else (other context fields, message body) is preserved verbatim.
// Handles both wave2 (camelCase: bapUri/bppUri) and wave1 (snake_case:
// bap_uri/bpp_uri) shapes by detecting which key style the original uses.
func RewriteContextForBeckn(body []byte, senderHost, ledgerURI string) ([]byte, error) {
	var raw map[string]interface{}
	if err := json.Unmarshal(body, &raw); err != nil {
		return nil, fmt.Errorf("rewriteContext: parse body: %w", err)
	}
	ctxRaw, ok := raw["context"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("rewriteContext: missing or invalid context")
	}

	bppKey, bapKey := "bppUri", "bapUri"
	if _, hasCamel := ctxRaw[bppKey]; !hasCamel {
		if _, hasSnake := ctxRaw["bpp_uri"]; hasSnake {
			bppKey, bapKey = "bpp_uri", "bap_uri"
		}
	}

	ctxRaw[bppKey] = strings.TrimRight(senderHost, "/") + "/bpp/caller"
	ctxRaw[bapKey] = strings.TrimRight(ledgerURI, "/") + "/bap/receiver"
	raw["context"] = ctxRaw

	return json.Marshal(raw)
}

// DeriveSenderHostFromWave2 returns "<scheme>://<host[:port]>" extracted from
// the original payload's bapUri (BUYER role) or bppUri (SELLER role). Used as
// a fallback when SenderHost is not configured explicitly. Returns "" if the
// chosen URI is missing or unparseable.
func DeriveSenderHostFromWave2(payload *Wave2OnConfirmPayload, role string) string {
	var rawURI string
	switch role {
	case "BUYER":
		rawURI = payload.Context.BapURI
	case "SELLER":
		rawURI = payload.Context.BppURI
	default:
		return ""
	}
	return hostBase(rawURI)
}

// hostBase parses a URI and returns "<scheme>://<host[:port]>", or "" if the
// URI is missing or unparseable.
func hostBase(rawURI string) string {
	if rawURI == "" {
		return ""
	}
	u, err := url.Parse(rawURI)
	if err != nil || u.Host == "" {
		return ""
	}
	return u.Scheme + "://" + u.Host
}

// extractWave2IntervalIDs walks offerAttributes.inputs[role=seller].inputs.offerTimeseries.intervals
// and returns each interval's numeric id. Returns nil if the path is missing.
func extractWave2IntervalIDs(offerAttrs map[string]interface{}) []int {
	if offerAttrs == nil {
		return nil
	}
	inputs, ok := offerAttrs["inputs"].([]interface{})
	if !ok {
		return nil
	}
	for _, raw := range inputs {
		entry, ok := raw.(map[string]interface{})
		if !ok || entry["role"] != "seller" {
			continue
		}
		inner, ok := entry["inputs"].(map[string]interface{})
		if !ok {
			continue
		}
		ts, ok := inner["offerTimeseries"].(map[string]interface{})
		if !ok {
			continue
		}
		intervals, ok := ts["intervals"].([]interface{})
		if !ok {
			continue
		}
		ids := make([]int, 0, len(intervals))
		for _, iv := range intervals {
			m, ok := iv.(map[string]interface{})
			if !ok {
				continue
			}
			switch v := m["id"].(type) {
			case float64:
				ids = append(ids, int(v))
			case int:
				ids = append(ids, v)
			}
		}
		return ids
	}
	return nil
}

// -------------------------
// wave2 status types and parsers
// -------------------------

// Wave2StatusPayload is the wave2 `status` request body. The contract carries
// minimum id + participants (with ledgerUri) so the plugin can route to the
// right ledger without a cache lookup.
type Wave2StatusPayload struct {
	Context  Wave2Context      `json:"context"`
	Message  Wave2StatusMessage `json:"message"`
}

type Wave2StatusMessage struct {
	Contract Wave2StatusContract `json:"contract"`
}

// Wave2StatusContract carries only what is needed for ledger routing.
type Wave2StatusContract struct {
	ID           string             `json:"id"`
	Participants []Wave2Participant `json:"participants"`
}

// ParseStatusWave2 unmarshals a wave2 status body.
func ParseStatusWave2(body []byte) (*Wave2StatusPayload, error) {
	var payload Wave2StatusPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("failed to parse wave2 status payload: %w", err)
	}
	return &payload, nil
}

// ExtractWave2StatusDiscomLedgerUri returns the ledgerUri for the given side
// from a wave2 status payload's participants array.
func ExtractWave2StatusDiscomLedgerUri(payload *Wave2StatusPayload, side Side) string {
	for i := range payload.Message.Contract.Participants {
		if payload.Message.Contract.Participants[i].Role == string(side) {
			return wave2StringAttr(&payload.Message.Contract.Participants[i], "ledgerUri")
		}
	}
	return ""
}

// DeriveSenderHostFromWave2Status returns the sender host from the status payload context.
func DeriveSenderHostFromWave2Status(payload *Wave2StatusPayload, role string) string {
	switch role {
	case "BUYER":
		return hostBase(payload.Context.BapURI)
	case "SELLER":
		return hostBase(payload.Context.BppURI)
	default:
		return ""
	}
}

// -------------------------
// wave2 on_status types, parsers, and performance guard
// -------------------------

// performancePayloadTypes are the columns emitted by the ledger in on_status.
var performancePayloadTypes = map[string]bool{
	"BUYER_DISCOM_ALLOC":   true,
	"SELLER_DISCOM_ALLOC":  true,
	"BUYER_DISCOM_STATUS":  true,
	"SELLER_DISCOM_STATUS": true,
	"FINAL_ALLOC":          true,
}

// Wave2OnStatusPayload is the wave2 `on_status` body.
type Wave2OnStatusPayload struct {
	Context Wave2Context      `json:"context"`
	Message Wave2OnStatusMessage `json:"message"`
}

type Wave2OnStatusMessage struct {
	Contract Wave2OnStatusContract `json:"contract"`
}

type Wave2OnStatusContract struct {
	ID           string             `json:"id"`
	Status       map[string]interface{} `json:"status"`
	Performance  []Wave2Performance `json:"performance"`
	Participants []Wave2Participant `json:"participants"`
}

// ParseOnStatusWave2 unmarshals a wave2 on_status body.
func ParseOnStatusWave2(body []byte) (*Wave2OnStatusPayload, error) {
	var payload Wave2OnStatusPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("failed to parse wave2 on_status payload: %w", err)
	}
	return &payload, nil
}

// Wave2OnStatusHasPerformanceData returns true if any performance entry contains
// at least one non-empty value for a recognised performance payload type.
func Wave2OnStatusHasPerformanceData(payload *Wave2OnStatusPayload) bool {
	for _, perf := range payload.Message.Contract.Performance {
		ts := extractPerformanceTimeseries(perf.PerformanceAttributes)
		if ts == nil {
			continue
		}
		intervals, _ := ts["intervals"].([]interface{})
		for _, iv := range intervals {
			m, ok := iv.(map[string]interface{})
			if !ok {
				continue
			}
			payloads, _ := m["payloads"].([]interface{})
			for _, p := range payloads {
				pm, ok := p.(map[string]interface{})
				if !ok {
					continue
				}
				typ, _ := pm["type"].(string)
				if !performancePayloadTypes[typ] {
					continue
				}
				vals, _ := pm["values"].([]interface{})
				if len(vals) > 0 {
					return true
				}
			}
		}
	}
	return false
}

// ExtractWave2OnStatusDiscomLedgerUri returns ledgerUri for the given side.
func ExtractWave2OnStatusDiscomLedgerUri(payload *Wave2OnStatusPayload, side Side) string {
	for i := range payload.Message.Contract.Participants {
		if payload.Message.Contract.Participants[i].Role == string(side) {
			return wave2StringAttr(&payload.Message.Contract.Participants[i], "ledgerUri")
		}
	}
	return ""
}

// DeriveSenderHostFromWave2OnStatus returns the sender host from the on_status context.
func DeriveSenderHostFromWave2OnStatus(payload *Wave2OnStatusPayload, role string) string {
	switch role {
	case "BUYER":
		return hostBase(payload.Context.BapURI)
	case "SELLER":
		return hostBase(payload.Context.BppURI)
	default:
		return ""
	}
}

// extractPerformanceTimeseries walks performanceAttributes to find performanceTimeseries.
func extractPerformanceTimeseries(attrs map[string]interface{}) map[string]interface{} {
	if attrs == nil {
		return nil
	}
	ts, ok := attrs["performanceTimeseries"].(map[string]interface{})
	if !ok {
		return nil
	}
	return ts
}
