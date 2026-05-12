package degledgerrecorder

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/beckn-one/beckn-onix/pkg/log"
	"github.com/beckn-one/beckn-onix/pkg/model"
)

// DEGLedgerRecorder is a Step plugin that records trade data to the DEG Ledger
// after on_confirm calls.
type DEGLedgerRecorder struct {
	config *Config
	client *LedgerClient

	// wg tracks in-flight async requests for graceful shutdown
	wg sync.WaitGroup
}

// New creates a new DEGLedgerRecorder instance.
func New(cfg map[string]string) (*DEGLedgerRecorder, error) {
	config, err := ParseConfig(cfg)
	if err != nil {
		return nil, err
	}

	// Create Beckn signer if signing is configured
	var signer *BecknSigner
	if config.SigningPrivateKey != "" && config.SubscriberID != "" && config.UniqueKeyID != "" {
		signer, err = NewBecknSigner(
			config.SubscriberID,
			config.UniqueKeyID,
			config.SigningPrivateKey,
			config.SignatureValiditySeconds,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create Beckn signer: %w", err)
		}

		// Log signing configuration source
		configSource := "explicit config"
		if config.SigningFromEnv {
			configSource = "environment variables (Vault/K8s secrets compatible)"
		}
		fmt.Printf("[DEGLedgerRecorder] Beckn signing enabled (subscriber_id=%s, key_id=%s, source=%s)\n",
			config.SubscriberID, config.UniqueKeyID, configSource)
	} else if config.APIKey != "" {
		fmt.Printf("[DEGLedgerRecorder] Simple API key authentication enabled\n")
	} else {
		fmt.Printf("[DEGLedgerRecorder] WARNING: No authentication configured for ledger API calls\n")
	}

	// Log enabled actions, role, and the three required mode flags so the
	// active behavior is visible at startup.
	fmt.Printf("[DEGLedgerRecorder] payloadShape=%s, ledgerUriSource=%s, ledgerApi=%s, role=%s, actions=[%s]\n",
		config.PayloadShape, config.LedgerUriSource, config.LedgerApi, config.Role,
		strings.Join(config.Actions, ", "))

	client := NewLedgerClient(
		config.LedgerHost,
		config.AsyncTimeout,
		config.RetryCount,
		config.APIKey,
		config.AuthHeader,
		config.DebugLogging,
		signer,
	)

	return &DEGLedgerRecorder{
		config: config,
		client: client,
	}, nil
}

// Run implements the Step interface. It processes the request and records
// events to the DEG Ledger based on configured actions.
func (r *DEGLedgerRecorder) Run(ctx *model.StepContext) error {
	// Skip if plugin is disabled
	if !r.config.Enabled {
		log.Debug(ctx, "DEGLedgerRecorder: plugin disabled, skipping")
		return nil
	}

	// Extract the action from the request
	action := ExtractAction(ctx.Request.URL.Path, ctx.Body)

	// Check if this action is enabled
	if !r.config.IsActionEnabled(action) {
		log.Debugf(ctx, "DEGLedgerRecorder: action '%s' not in configured actions %v, skipping", action, r.config.Actions)
		return nil
	}

	// Route to the appropriate handler based on action
	switch action {
	case ActionOnConfirm:
		return r.handleOnConfirm(ctx)
	case ActionOnStatus:
		return r.handleOnStatus(ctx)
	case ActionStatus:
		return r.handleStatus(ctx)
	default:
		log.Debugf(ctx, "DEGLedgerRecorder: no handler for action '%s', skipping", action)
		return nil
	}
}

// handleOnConfirm processes on_confirm events and sends to /ledger/put.
// Branches on PayloadShape (wave1 vs wave2) and resolves the target ledger
// base URL per LedgerUriSource (config vs payload).
func (r *DEGLedgerRecorder) handleOnConfirm(ctx *model.StepContext) error {
	log.Infof(ctx, "DEGLedgerRecorder: processing on_confirm (payloadShape=%s, ledgerUriSource=%s, ledgerApi=%s)",
		r.config.PayloadShape, r.config.LedgerUriSource, r.config.LedgerApi)

	if len(ctx.Body) < 5000 {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body:\n%s", string(ctx.Body))
	} else {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body (truncated):\n%s...", string(ctx.Body[:5000]))
	}

	switch r.config.PayloadShape {
	case PayloadShapeWave1:
		return r.handleOnConfirmWave1(ctx)
	case PayloadShapeWave2:
		return r.handleOnConfirmWave2(ctx)
	default:
		log.Warnf(ctx, "DEGLedgerRecorder: unsupported payloadShape=%s", r.config.PayloadShape)
		return nil
	}
}

// handleOnConfirmWave1 — legacy wave1 path: parses beckn:Order/orderItems and
// emits one ledger record per order item.
func (r *DEGLedgerRecorder) handleOnConfirmWave1(ctx *model.StepContext) error {
	if r.config.LedgerApi != LedgerApiLegacyLedger {
		log.Warnf(ctx, "DEGLedgerRecorder: wave1 path only supports ledgerApi=legacy_ledger (got %s); skipping",
			r.config.LedgerApi)
		return nil
	}
	payload, err := ParseOnConfirm(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse wave1 on_confirm payload: %v", err)
		return nil
	}

	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: parsed wave1 context - transaction_id=%s, bap_id=%s, bpp_id=%s",
		payload.Context.TransactionID, payload.Context.BapID, payload.Context.BppID)

	records := MapToLedgerRecords(payload, r.config.Role)
	if len(records) == 0 {
		log.Warnf(ctx, "DEGLedgerRecorder: no order items found in on_confirm, skipping")
		return nil
	}

	// wave1 always has ledgerUriSource=config; falling back to LedgerHost.
	baseURL := r.config.LedgerHost
	if r.config.LedgerUriSource != LedgerUriSourceConfig || baseURL == "" {
		log.Warnf(ctx, "DEGLedgerRecorder: wave1 path requires ledgerUriSource=config and a non-empty ledgerHost (have source=%s, host=%q); skipping",
			r.config.LedgerUriSource, baseURL)
		return nil
	}

	log.Infof(ctx, "DEGLedgerRecorder: wave1 mapped %d records (transaction_id=%s) -> %s",
		len(records), payload.Context.TransactionID, baseURL)
	r.sendPutRecordsAsync(ctx, baseURL, records)
	return nil
}

// handleOnConfirmWave2 — wave2 (P2PTrade/v2.0) path: parses
// message.contract.commitments, resolves the target URL from either config or
// the payload's discom participantAttributes, then dispatches to either the
// legacy_ledger PUT shape or the beckn on_confirm forwarder per LedgerApi.
func (r *DEGLedgerRecorder) handleOnConfirmWave2(ctx *model.StepContext) error {
	payload, err := ParseOnConfirmWave2(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse wave2 on_confirm payload: %v", err)
		return nil
	}

	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: parsed wave2 context - transactionId=%s, bapId=%s, bppId=%s",
		payload.Context.TransactionID, payload.Context.BapID, payload.Context.BppID)

	baseURL, err := r.resolveWave2BaseURL(payload)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: wave2 base URL resolution failed (transaction_id=%s): %v",
			payload.Context.TransactionID, err)
		return nil
	}

	switch r.config.LedgerApi {
	case LedgerApiLegacyLedger:
		records, err := MapWave2ToLedgerRecords(payload, r.config.Role)
		if err != nil {
			log.Warnf(ctx, "DEGLedgerRecorder: wave2 mapping failed: %v", err)
			return nil
		}
		log.Infof(ctx, "DEGLedgerRecorder: wave2 (legacy_ledger) mapped %d record(s) (transaction_id=%s) -> %s",
			len(records), payload.Context.TransactionID, baseURL)
		r.sendPutRecordsAsync(ctx, baseURL, records)

	case LedgerApiBeckn:
		senderHost := r.config.SenderHost
		if senderHost == "" {
			senderHost = DeriveSenderHostFromWave2(payload, r.config.Role)
		}
		if senderHost == "" {
			log.Warnf(ctx, "DEGLedgerRecorder: beckn mode requires a sender host (config.senderHost or context.bapUri/bppUri); skipping (transaction_id=%s)",
				payload.Context.TransactionID)
			return nil
		}
		rewritten, err := RewriteContextForBeckn(ctx.Body, senderHost, baseURL)
		if err != nil {
			log.Warnf(ctx, "DEGLedgerRecorder: beckn context rewrite failed: %v", err)
			return nil
		}
		log.Infof(ctx, "DEGLedgerRecorder: wave2 (beckn) forwarding on_confirm (transaction_id=%s) -> %s/on_confirm (sender=%s)",
			payload.Context.TransactionID, baseURL, senderHost)
		r.sendBecknOnConfirmAsync(ctx, baseURL, rewritten, payload.Context.TransactionID)

	default:
		log.Warnf(ctx, "DEGLedgerRecorder: unsupported ledgerApi=%s", r.config.LedgerApi)
	}
	return nil
}

// sendBecknOnConfirmAsync forwards a beckn on_confirm body in the background.
// Mirrors sendPutRecordsAsync but for the beckn API path.
func (r *DEGLedgerRecorder) sendBecknOnConfirmAsync(parentCtx *model.StepContext, baseURL string, body []byte, transactionID string) {
	r.wg.Add(1)
	go func() {
		defer r.wg.Done()
		ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
		defer cancel()
		resp, err := r.client.PostBecknOnConfirm(ctx, baseURL, body)
		if err != nil {
			log.Errorf(parentCtx, err,
				"DEGLedgerRecorder: failed to forward beckn on_confirm (transaction_id=%s, base_url=%s): %v",
				transactionID, baseURL, err)
			return
		}
		log.Infof(parentCtx,
			"DEGLedgerRecorder: successfully forwarded beckn on_confirm (transaction_id=%s, record_id=%s, base_url=%s)",
			transactionID, resp.RecordID, baseURL)
	}()
}

// resolveWave2BaseURL picks the target ledger URL according to LedgerUriSource.
// For payload mode, the side is determined by the configured role:
// BUYER → buyerDiscom.ledgerUri, SELLER → sellerDiscom.ledgerUri.
func (r *DEGLedgerRecorder) resolveWave2BaseURL(payload *Wave2OnConfirmPayload) (string, error) {
	switch r.config.LedgerUriSource {
	case LedgerUriSourceConfig:
		if r.config.LedgerHost == "" {
			return "", fmt.Errorf("ledgerHost is empty")
		}
		return r.config.LedgerHost, nil
	case LedgerUriSourcePayload:
		var side Side
		switch r.config.Role {
		case "BUYER":
			side = SideBuyer
		case "SELLER":
			side = SideSeller
		default:
			return "", fmt.Errorf("payload-sourced ledger URI requires role BUYER or SELLER, got %s", r.config.Role)
		}
		uri := ExtractWave2DiscomLedgerUri(payload, side)
		if uri == "" {
			return "", fmt.Errorf("no ledgerUri found in participants[role=%s].participantAttributes", side)
		}
		return uri, nil
	default:
		return "", fmt.Errorf("unsupported ledgerUriSource: %s", r.config.LedgerUriSource)
	}
}

// handleOnStatus processes on_status events.
// For BUYER/SELLER roles with ledgerApi=beckn: forwards to the appropriate
// discom ledger when performance data is present (wave2 path).
// For BUYER_DISCOM/SELLER_DISCOM roles: writes meter readings to /ledger/record (wave1 path).
func (r *DEGLedgerRecorder) handleOnStatus(ctx *model.StepContext) error {
	log.Infof(ctx, "DEGLedgerRecorder: processing on_status (role=%s, ledgerApi=%s, payloadShape=%s)",
		r.config.Role, r.config.LedgerApi, r.config.PayloadShape)

	// Wave2 beckn forwarding path: BUYER or SELLER role forwards on_status with performance data.
	if r.config.PayloadShape == PayloadShapeWave2 && r.config.LedgerApi == LedgerApiBeckn &&
		(r.config.Role == "BUYER" || r.config.Role == "SELLER") {
		return r.handleOnStatusWave2(ctx)
	}

	// Wave1 / DISCOM path: write meter readings to /ledger/record.
	if !r.config.IsDiscomRole() {
		log.Warnf(ctx, "DEGLedgerRecorder: on_status requires BUYER_DISCOM or SELLER_DISCOM role for legacy path, got %s", r.config.Role)
		return nil
	}

	// DEBUG: Log the raw body received
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body length=%d", len(ctx.Body))
	if len(ctx.Body) < 5000 {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body:\n%s", string(ctx.Body))
	} else {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body (truncated):\n%s...", string(ctx.Body[:5000]))
	}

	// Parse the on_status payload
	payload, err := ParseOnStatus(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse on_status payload: %v", err)
		return nil
	}

	// DEBUG: Log parsed payload details
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: parsed context - transaction_id=%s, action=%s",
		payload.Context.TransactionID, payload.Context.Action)
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: order items count=%d", len(payload.Message.Order.OrderItems))

	// Map to ledger record requests (one per order item with meter readings)
	records := MapToLedgerRecordRequests(payload, r.config.Role)

	// DEBUG: Log mapped records
	for i, rec := range records {
		metricCount := len(rec.BuyerFulfillmentValidationMetrics) + len(rec.SellerFulfillmentValidationMetrics)
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: record[%d] - transactionId=%s, orderItemId=%s, metrics=%d",
			i, rec.TransactionID, rec.OrderItemID, metricCount)
	}

	if len(records) == 0 {
		log.Warnf(ctx, "DEGLedgerRecorder: no meter readings found in on_status, skipping ledger recording")
		return nil
	}

	log.Infof(ctx, "DEGLedgerRecorder: mapped %d ledger record requests from on_status (transaction_id=%s)",
		len(records), payload.Context.TransactionID)

	// Send records to ledger asynchronously (fire-and-forget)
	r.sendRecordActualsAsync(ctx, records, payload.Context.TransactionID)

	return nil
}

// handleStatus forwards an incoming wave2 beckn `status` request to the
// appropriate discom ledger as a beckn `status` call. The ledger will
// asynchronously call back with `on_status`.
// SELLER role → sellerDiscom.ledgerUri; BUYER role → buyerDiscom.ledgerUri.
func (r *DEGLedgerRecorder) handleStatus(ctx *model.StepContext) error {
	log.Infof(ctx, "DEGLedgerRecorder: processing status (role=%s, ledgerApi=%s)", r.config.Role, r.config.LedgerApi)

	if r.config.LedgerApi != LedgerApiBeckn {
		log.Warnf(ctx, "DEGLedgerRecorder: status forwarding only supported with ledgerApi=beckn (got %s); skipping", r.config.LedgerApi)
		return nil
	}

	payload, err := ParseStatusWave2(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse wave2 status payload: %v", err)
		return nil
	}

	var side Side
	switch r.config.Role {
	case "SELLER":
		side = SideSeller
	case "BUYER":
		side = SideBuyer
	default:
		log.Warnf(ctx, "DEGLedgerRecorder: status forwarding requires BUYER or SELLER role, got %s", r.config.Role)
		return nil
	}

	baseURL := r.config.LedgerHost
	if r.config.LedgerUriSource == LedgerUriSourcePayload {
		baseURL = ExtractWave2StatusDiscomLedgerUri(payload, side)
	}
	if baseURL == "" {
		log.Warnf(ctx, "DEGLedgerRecorder: no ledger URI resolved for status forwarding (role=%s, side=%s)", r.config.Role, side)
		return nil
	}

	senderHost := r.config.SenderHost
	if senderHost == "" {
		senderHost = DeriveSenderHostFromWave2Status(payload, r.config.Role)
	}
	if senderHost == "" {
		log.Warnf(ctx, "DEGLedgerRecorder: beckn status forwarding requires a sender host; skipping (transaction_id=%s)", payload.Context.TransactionID)
		return nil
	}

	rewritten, err := RewriteContextForBeckn(ctx.Body, senderHost, baseURL)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: beckn status context rewrite failed: %v", err)
		return nil
	}

	log.Infof(ctx, "DEGLedgerRecorder: forwarding status (transaction_id=%s, contract_id=%s) -> %s/status (sender=%s)",
		payload.Context.TransactionID, payload.Message.Contract.ID, baseURL, senderHost)
	r.sendBecknStatusAsync(ctx, baseURL, rewritten, payload.Context.TransactionID)
	return nil
}

// handleOnStatusWave2 checks whether the on_status body carries actual
// performance data and, if so, forwards it as a beckn on_status to the
// appropriate discom ledger.
// BUYER role → buyerDiscom.ledgerUri; SELLER role → sellerDiscom.ledgerUri.
func (r *DEGLedgerRecorder) handleOnStatusWave2(ctx *model.StepContext) error {
	payload, err := ParseOnStatusWave2(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse wave2 on_status payload: %v", err)
		return nil
	}

	if !Wave2OnStatusHasPerformanceData(payload) {
		log.Debugf(ctx, "DEGLedgerRecorder: on_status has no performance payload columns; skipping ledger forward (transaction_id=%s)", payload.Context.TransactionID)
		return nil
	}

	var side Side
	switch r.config.Role {
	case "BUYER":
		side = SideBuyer
	case "SELLER":
		side = SideSeller
	default:
		log.Warnf(ctx, "DEGLedgerRecorder: on_status wave2 forwarding requires BUYER or SELLER role, got %s", r.config.Role)
		return nil
	}

	baseURL := r.config.LedgerHost
	if r.config.LedgerUriSource == LedgerUriSourcePayload {
		baseURL = ExtractWave2OnStatusDiscomLedgerUri(payload, side)
	}
	if baseURL == "" {
		log.Warnf(ctx, "DEGLedgerRecorder: no ledger URI resolved for on_status forwarding (role=%s, side=%s)", r.config.Role, side)
		return nil
	}

	senderHost := r.config.SenderHost
	if senderHost == "" {
		senderHost = DeriveSenderHostFromWave2OnStatus(payload, r.config.Role)
	}
	if senderHost == "" {
		log.Warnf(ctx, "DEGLedgerRecorder: beckn on_status forwarding requires a sender host; skipping (transaction_id=%s)", payload.Context.TransactionID)
		return nil
	}

	rewritten, err := RewriteContextForBeckn(ctx.Body, senderHost, baseURL)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: beckn on_status context rewrite failed: %v", err)
		return nil
	}

	log.Infof(ctx, "DEGLedgerRecorder: forwarding on_status with performance data (transaction_id=%s) -> %s/on_status (sender=%s)",
		payload.Context.TransactionID, baseURL, senderHost)
	r.sendBecknOnStatusAsync(ctx, baseURL, rewritten, payload.Context.TransactionID)
	return nil
}

// sendBecknStatusAsync forwards a beckn status body in the background.
func (r *DEGLedgerRecorder) sendBecknStatusAsync(parentCtx *model.StepContext, baseURL string, body []byte, transactionID string) {
	r.wg.Add(1)
	go func() {
		defer r.wg.Done()
		ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
		defer cancel()
		if err := r.client.PostBecknStatus(ctx, baseURL, body); err != nil {
			log.Errorf(parentCtx, err,
				"DEGLedgerRecorder: failed to forward beckn status (transaction_id=%s, base_url=%s): %v",
				transactionID, baseURL, err)
			return
		}
		log.Infof(parentCtx,
			"DEGLedgerRecorder: successfully forwarded beckn status (transaction_id=%s, base_url=%s)",
			transactionID, baseURL)
	}()
}

// sendBecknOnStatusAsync forwards a beckn on_status body in the background.
func (r *DEGLedgerRecorder) sendBecknOnStatusAsync(parentCtx *model.StepContext, baseURL string, body []byte, transactionID string) {
	r.wg.Add(1)
	go func() {
		defer r.wg.Done()
		ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
		defer cancel()
		resp, err := r.client.PostBecknOnStatus(ctx, baseURL, body)
		if err != nil {
			log.Errorf(parentCtx, err,
				"DEGLedgerRecorder: failed to forward beckn on_status (transaction_id=%s, base_url=%s): %v",
				transactionID, baseURL, err)
			return
		}
		log.Infof(parentCtx,
			"DEGLedgerRecorder: successfully forwarded beckn on_status (transaction_id=%s, record_id=%s, base_url=%s)",
			transactionID, resp.RecordID, baseURL)
	}()
}

// sendPutRecordsAsync sends ledger PUT records in the background without blocking the main flow.
// Used for on_confirm → /ledger/put. baseURL is supplied per-call so the same
// recorder can target different discom ledger TSPs based on payload-sourced URIs.
func (r *DEGLedgerRecorder) sendPutRecordsAsync(parentCtx *model.StepContext, baseURL string, records []LedgerPutRequest) {
	for _, record := range records {
		r.wg.Add(1)
		go func(rec LedgerPutRequest) {
			defer r.wg.Done()

			// Create a new context with timeout for the async operation
			ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
			defer cancel()

			resp, err := r.client.PutRecord(ctx, baseURL, rec)
			if err != nil {
				log.Errorf(parentCtx, err,
					"DEGLedgerRecorder: failed to PUT record to ledger (transaction_id=%s, order_item_id=%s, base_url=%s): %v",
					rec.TransactionID, rec.OrderItemID, baseURL, err)
				return
			}

			log.Infof(parentCtx,
				"DEGLedgerRecorder: successfully PUT record to ledger (transaction_id=%s, order_item_id=%s, record_id=%s, base_url=%s)",
				rec.TransactionID, rec.OrderItemID, resp.RecordID, baseURL)
		}(record)
	}
}

// sendRecordActualsAsync sends meter readings/validation metrics in the background.
// Used for on_status → /ledger/record
func (r *DEGLedgerRecorder) sendRecordActualsAsync(parentCtx *model.StepContext, records []LedgerRecordRequest, transactionID string) {
	for _, record := range records {
		r.wg.Add(1)
		go func(rec LedgerRecordRequest) {
			defer r.wg.Done()

			// Create a new context with timeout for the async operation
			ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
			defer cancel()

			resp, err := r.client.RecordActuals(ctx, rec)
			if err != nil {
				log.Errorf(parentCtx, err,
					"DEGLedgerRecorder: failed to RECORD actuals to ledger (transaction_id=%s, order_item_id=%s): %v",
					rec.TransactionID, rec.OrderItemID, err)
				return
			}

			log.Infof(parentCtx,
				"DEGLedgerRecorder: successfully RECORDED actuals to ledger (transaction_id=%s, order_item_id=%s, record_id=%s)",
				rec.TransactionID, rec.OrderItemID, resp.RecordID)
		}(record)
	}
}

// Close gracefully shuts down the recorder, waiting for in-flight requests.
func (r *DEGLedgerRecorder) Close() {
	// Wait for all in-flight requests to complete
	r.wg.Wait()

	// Close the HTTP client
	if r.client != nil {
		r.client.Close()
	}
}
