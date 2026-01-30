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

	// Log enabled actions and role
	fmt.Printf("[DEGLedgerRecorder] Enabled actions: [%s], role: %s\n",
		strings.Join(config.Actions, ", "), config.Role)

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
	default:
		log.Debugf(ctx, "DEGLedgerRecorder: no handler for action '%s', skipping", action)
		return nil
	}
}

// handleOnConfirm processes on_confirm events and sends to /ledger/put.
func (r *DEGLedgerRecorder) handleOnConfirm(ctx *model.StepContext) error {
	log.Infof(ctx, "DEGLedgerRecorder: processing on_confirm")

	// DEBUG: Log the raw body received
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body length=%d", len(ctx.Body))
	if len(ctx.Body) < 5000 {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body:\n%s", string(ctx.Body))
	} else {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: raw body (truncated):\n%s...", string(ctx.Body[:5000]))
	}

	// Parse the on_confirm payload
	payload, err := ParseOnConfirm(ctx.Body)
	if err != nil {
		log.Warnf(ctx, "DEGLedgerRecorder: failed to parse on_confirm payload: %v", err)
		return nil
	}

	// DEBUG: Log parsed payload details
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: parsed context - transaction_id=%s, action=%s, bap_id=%s, bpp_id=%s",
		payload.Context.TransactionID, payload.Context.Action, payload.Context.BapID, payload.Context.BppID)
	log.Debugf(ctx, "DEGLedgerRecorder DEBUG: order items count=%d", len(payload.Message.Order.OrderItems))

	// Map to ledger records (one per order item)
	records := MapToLedgerRecords(payload, r.config.Role)

	// DEBUG: Log mapped records
	for i, rec := range records {
		log.Debugf(ctx, "DEGLedgerRecorder DEBUG: record[%d] - transactionId=%s, orderItemId=%s, platformIdBuyer=%s, platformIdSeller=%s",
			i, rec.TransactionID, rec.OrderItemID, rec.PlatformIDBuyer, rec.PlatformIDSeller)
	}

	if len(records) == 0 {
		log.Warnf(ctx, "DEGLedgerRecorder: no order items found in on_confirm, skipping ledger recording")
		return nil
	}

	log.Infof(ctx, "DEGLedgerRecorder: mapped %d ledger records from on_confirm (transaction_id=%s)",
		len(records), payload.Context.TransactionID)

	// Send records to ledger asynchronously (fire-and-forget)
	r.sendPutRecordsAsync(ctx, records, payload.Context.TransactionID)

	return nil
}

// handleOnStatus processes on_status events and sends meter readings to /ledger/record.
func (r *DEGLedgerRecorder) handleOnStatus(ctx *model.StepContext) error {
	log.Infof(ctx, "DEGLedgerRecorder: processing on_status")

	// Validate role - only discom roles can use /ledger/record
	if !r.config.IsDiscomRole() {
		log.Warnf(ctx, "DEGLedgerRecorder: on_status requires BUYER_DISCOM or SELLER_DISCOM role, got %s", r.config.Role)
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

// sendPutRecordsAsync sends ledger PUT records in the background without blocking the main flow.
// Used for on_confirm → /ledger/put
func (r *DEGLedgerRecorder) sendPutRecordsAsync(parentCtx *model.StepContext, records []LedgerPutRequest, transactionID string) {
	for _, record := range records {
		r.wg.Add(1)
		go func(rec LedgerPutRequest) {
			defer r.wg.Done()

			// Create a new context with timeout for the async operation
			ctx, cancel := context.WithTimeout(context.Background(), r.config.AsyncTimeout)
			defer cancel()

			resp, err := r.client.PutRecord(ctx, rec)
			if err != nil {
				log.Errorf(parentCtx, err,
					"DEGLedgerRecorder: failed to PUT record to ledger (transaction_id=%s, order_item_id=%s): %v",
					rec.TransactionID, rec.OrderItemID, err)
				return
			}

			log.Infof(parentCtx,
				"DEGLedgerRecorder: successfully PUT record to ledger (transaction_id=%s, order_item_id=%s, record_id=%s)",
				rec.TransactionID, rec.OrderItemID, resp.RecordID)
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
