package degledgerrecorder

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
)

// LedgerClient handles communication with the DEG Ledger API.
type LedgerClient struct {
	baseURL      string
	httpClient   *http.Client
	retryCount   int
	apiKey       string
	authHeader   string
	debugLogging bool
	signer       *BecknSigner // Optional: for Beckn-style signature authentication
}

// LedgerPutResponse represents the response from the ledger PUT API.
type LedgerPutResponse struct {
	Success      bool   `json:"success"`
	RecordID     string `json:"recordId"`
	CreationTime string `json:"creationTime"`
	RowDigest    string `json:"rowDigest"`
	Message      string `json:"message"`
}

// LedgerErrorResponse represents an error response from the ledger API.
type LedgerErrorResponse struct {
	Code    string                 `json:"code"`
	Message string                 `json:"message"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// BecknAckEnvelope is the response shape the ledger TSP returns when called
// over beckn `on_confirm`. The legacy ledger record metadata is wrapped inside
// `message.ledger` so callers can unwrap it back into a `LedgerPutResponse`.
type BecknAckEnvelope struct {
	Message struct {
		Ack struct {
			Status string `json:"status"`
		} `json:"ack"`
		Ledger LedgerPutResponse `json:"ledger"`
	} `json:"message"`
}

// RequestLog captures details of an HTTP request for logging.
type RequestLog struct {
	RequestID   string            `json:"request_id"`
	Method      string            `json:"method"`
	URL         string            `json:"url"`
	Headers     map[string]string `json:"headers"`
	Body        interface{}       `json:"body"`
	Timestamp   string            `json:"timestamp"`
}

// ResponseLog captures details of an HTTP response for logging.
type ResponseLog struct {
	RequestID  string            `json:"request_id"`
	StatusCode int               `json:"status_code"`
	Headers    map[string]string `json:"headers"`
	Body       string            `json:"body"`
	Duration   string            `json:"duration"`
	Timestamp  string            `json:"timestamp"`
}

// NewLedgerClient creates a new LedgerClient instance.
func NewLedgerClient(baseURL string, timeout time.Duration, retryCount int, apiKey, authHeader string, debugLogging bool, signer *BecknSigner) *LedgerClient {
	return &LedgerClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
		},
		retryCount:   retryCount,
		apiKey:       apiKey,
		authHeader:   authHeader,
		debugLogging: debugLogging,
		signer:       signer,
	}
}

// PutRecord sends a record to the ledger PUT API at the given baseURL. The
// baseURL is supplied per-call (rather than taken from the client) so the same
// client can target different discom ledger TSPs based on payload-extracted
// URIs.
func (c *LedgerClient) PutRecord(ctx context.Context, baseURL string, record LedgerPutRequest) (*LedgerPutResponse, error) {
	if baseURL == "" {
		return nil, fmt.Errorf("baseURL is required for PutRecord")
	}
	var lastErr error

	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for order_item_id=%s\n",
				attempt, c.retryCount, record.OrderItemID)
		}

		resp, err := c.doPutRequest(ctx, baseURL, record, attempt)
		if err == nil {
			return resp, nil
		}

		lastErr = err

		// Don't retry on context cancellation
		if ctx.Err() != nil {
			return nil, fmt.Errorf("context cancelled: %w", ctx.Err())
		}

		// Simple backoff for retries
		if attempt < c.retryCount {
			backoff := time.Duration(attempt+1) * 100 * time.Millisecond
			fmt.Printf("[DEGLedgerRecorder] Backing off for %v before retry\n", backoff)
			time.Sleep(backoff)
		}
	}

	return nil, lastErr
}

// PostBecknOnConfirm forwards a beckn on_confirm body verbatim to a ledger TSP
// at <baseURL>/on_confirm. The caller must have already rewritten context.bapUri
// and context.bppUri appropriately. The TSP is expected to return a
// BecknAckEnvelope; the inner `message.ledger` block is returned as a
// LedgerPutResponse so call sites can be uniform with the legacy_ledger path.
func (c *LedgerClient) PostBecknOnConfirm(ctx context.Context, baseURL string, body []byte) (*LedgerPutResponse, error) {
	if baseURL == "" {
		return nil, fmt.Errorf("baseURL is required for PostBecknOnConfirm")
	}
	var lastErr error
	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for beckn on_confirm\n",
				attempt, c.retryCount)
		}
		resp, err := c.doBecknOnConfirmRequest(ctx, baseURL, body, attempt)
		if err == nil {
			return resp, nil
		}
		lastErr = err
		if ctx.Err() != nil {
			return nil, fmt.Errorf("context cancelled: %w", ctx.Err())
		}
		if attempt < c.retryCount {
			backoff := time.Duration(attempt+1) * 100 * time.Millisecond
			time.Sleep(backoff)
		}
	}
	return nil, lastErr
}

// PostBecknStatus forwards a beckn status body to <baseURL>/status. The ledger
// TSP is expected to respond with ACK and later call back with on_status.
func (c *LedgerClient) PostBecknStatus(ctx context.Context, baseURL string, body []byte) error {
	if baseURL == "" {
		return fmt.Errorf("baseURL is required for PostBecknStatus")
	}
	var lastErr error
	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for beckn status\n", attempt, c.retryCount)
		}
		if err := c.doBecknStatusRequest(ctx, baseURL, body, attempt); err == nil {
			return nil
		} else {
			lastErr = err
		}
		if ctx.Err() != nil {
			return fmt.Errorf("context cancelled: %w", ctx.Err())
		}
		if attempt < c.retryCount {
			time.Sleep(time.Duration(attempt+1) * 100 * time.Millisecond)
		}
	}
	return lastErr
}

// PostBecknOnStatus forwards a beckn on_status body to <baseURL>/on_status.
// Used by the buyer-side plugin to relay performance data to the buyer ledger.
func (c *LedgerClient) PostBecknOnStatus(ctx context.Context, baseURL string, body []byte) (*LedgerPutResponse, error) {
	if baseURL == "" {
		return nil, fmt.Errorf("baseURL is required for PostBecknOnStatus")
	}
	var lastErr error
	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for beckn on_status\n", attempt, c.retryCount)
		}
		resp, err := c.doBecknOnStatusRequest(ctx, baseURL, body, attempt)
		if err == nil {
			return resp, nil
		}
		lastErr = err
		if ctx.Err() != nil {
			return nil, fmt.Errorf("context cancelled: %w", ctx.Err())
		}
		if attempt < c.retryCount {
			time.Sleep(time.Duration(attempt+1) * 100 * time.Millisecond)
		}
	}
	return nil, lastErr
}

// doBecknStatusRequest performs a single beckn status POST and expects ACK.
func (c *LedgerClient) doBecknStatusRequest(ctx context.Context, baseURL string, body []byte, attempt int) error {
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	targetURL := fmt.Sprintf("%s/status", strings.TrimRight(baseURL, "/"))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, targetURL, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Request-ID", requestID)
	c.setAuthHeader(req, body)
	c.logSimpleRequest(requestID, req, body, "BECKN status", attempt)

	resp, err := c.httpClient.Do(req)
	duration := time.Since(startTime)
	if err != nil {
		c.logError(requestID, "HTTP request failed", err, duration)
		return fmt.Errorf("ledger beckn status request failed: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	c.logResponse(requestID, resp, respBody, duration)

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(respBody))
	}
	return nil
}

// doBecknOnStatusRequest performs a single beckn on_status POST.
func (c *LedgerClient) doBecknOnStatusRequest(ctx context.Context, baseURL string, body []byte, attempt int) (*LedgerPutResponse, error) {
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	targetURL := fmt.Sprintf("%s/on_status", strings.TrimRight(baseURL, "/"))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, targetURL, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Request-ID", requestID)
	c.setAuthHeader(req, body)
	c.logSimpleRequest(requestID, req, body, "BECKN on_status", attempt)

	resp, err := c.httpClient.Do(req)
	duration := time.Since(startTime)
	if err != nil {
		c.logError(requestID, "HTTP request failed", err, duration)
		return nil, fmt.Errorf("ledger beckn on_status request failed: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	c.logResponse(requestID, resp, respBody, duration)

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(respBody))
	}
	var envelope BecknAckEnvelope
	if err := json.Unmarshal(respBody, &envelope); err != nil {
		// Non-fatal: ledger ACK'd but response shape unknown; return empty record.
		return &LedgerPutResponse{}, nil
	}
	ledger := envelope.Message.Ledger
	return &ledger, nil
}

// setAuthHeader applies signing or API-key auth to req, factored out so all
// beckn request helpers share the same logic.
func (c *LedgerClient) setAuthHeader(req *http.Request, body []byte) {
	if c.signer != nil && c.signer.IsConfigured() {
		if authHeader, err := c.signer.GenerateAuthHeader(body); err == nil {
			req.Header.Set("Authorization", authHeader)
		}
	} else if c.apiKey != "" {
		req.Header.Set(c.authHeader, c.apiKey)
	}
}

// logSimpleRequest logs an outgoing beckn request with action label, used by
// the status/on_status paths that don't have a structured request body type.
func (c *LedgerClient) logSimpleRequest(requestID string, req *http.Request, body []byte, label string, attempt int) {
	fmt.Println("")
	fmt.Printf("╔═══════════════════════════════════════════════════════════════════╗\n")
	fmt.Printf("║  DEGLedgerRecorder - OUTGOING REQUEST (%s)\n", label)
	fmt.Printf("╠═══════════════════════════════════════════════════════════════════╣\n")
	fmt.Printf("║ Request ID: %s  Attempt: %d/%d\n", requestID, attempt+1, c.retryCount+1)
	fmt.Printf("║ %s %s\n", req.Method, req.URL.String())
	fmt.Printf("╠═══════════════════════════════════════════════════════════════════╣\n")
	fmt.Printf("║   %s\n", string(body))
	fmt.Printf("╚═══════════════════════════════════════════════════════════════════╝\n")
}

// doBecknOnConfirmRequest performs a single beckn on_confirm POST.
func (c *LedgerClient) doBecknOnConfirmRequest(ctx context.Context, baseURL string, body []byte, attempt int) (*LedgerPutResponse, error) {
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	url := fmt.Sprintf("%s/on_confirm", strings.TrimRight(baseURL, "/"))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Request-ID", requestID)

	if c.signer != nil && c.signer.IsConfigured() {
		authHeader, err := c.signer.GenerateAuthHeader(body)
		if err != nil {
			return nil, fmt.Errorf("failed to generate Authorization header: %w", err)
		}
		req.Header.Set("Authorization", authHeader)
	} else if c.apiKey != "" {
		req.Header.Set(c.authHeader, c.apiKey)
	}

	c.logBecknRequest(requestID, req, body, attempt)

	resp, err := c.httpClient.Do(req)
	duration := time.Since(startTime)
	if err != nil {
		c.logError(requestID, "HTTP request failed", err, duration)
		return nil, fmt.Errorf("ledger beckn on_confirm request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.logError(requestID, "Failed to read response body", err, duration)
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	c.logResponse(requestID, resp, respBody, duration)

	switch resp.StatusCode {
	case http.StatusOK:
		var envelope BecknAckEnvelope
		if err := json.Unmarshal(respBody, &envelope); err != nil {
			return nil, fmt.Errorf("failed to parse beckn ack envelope: %w", err)
		}
		// Surface the inner ledger response so call sites are uniform.
		ledger := envelope.Message.Ledger
		return &ledger, nil
	case http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusConflict:
		var errResp LedgerErrorResponse
		if err := json.Unmarshal(respBody, &errResp); err != nil {
			return nil, fmt.Errorf("ledger TSP error (status %d): %s", resp.StatusCode, string(respBody))
		}
		return nil, fmt.Errorf("ledger TSP error (status %d, code %s): %s", resp.StatusCode, errResp.Code, errResp.Message)
	default:
		return nil, fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(respBody))
	}
}

// logBecknRequest renders the outgoing beckn on_confirm body in the same
// boxed-banner style as the legacy ledger logger.
func (c *LedgerClient) logBecknRequest(requestID string, req *http.Request, body []byte, attempt int) {
	headers := make(map[string]string)
	for key, values := range req.Header {
		value := strings.Join(values, ", ")
		if strings.Contains(strings.ToLower(key), "auth") ||
			strings.Contains(strings.ToLower(key), "api-key") ||
			strings.Contains(strings.ToLower(key), "x-api-key") ||
			key == c.authHeader {
			if len(value) > 8 {
				headers[key] = value[:4] + "****" + value[len(value)-4:]
			} else {
				headers[key] = "****"
			}
		} else {
			headers[key] = value
		}
	}

	fmt.Println("")
	fmt.Println("╔════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║       DEGLedgerRecorder - OUTGOING REQUEST (BECKN on_confirm)      ║")
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ Request ID:     %s\n", requestID)
	fmt.Printf("║ Timestamp:      %s\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("║ Attempt:        %d/%d\n", attempt+1, c.retryCount+1)
	fmt.Printf("║ Method:         %s\n", req.Method)
	fmt.Printf("║ URL:            %s\n", req.URL.String())
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ HEADERS:")
	for k, v := range headers {
		fmt.Printf("║   %s: %s\n", k, v)
	}
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ REQUEST BODY (JSON):")
	fmt.Printf("║   %s\n", string(body))
	fmt.Println("╚════════════════════════════════════════════════════════════════════╝")
}

// RecordActuals sends meter readings/validation metrics to the ledger RECORD API.
// This is for discom roles (BUYER_DISCOM, SELLER_DISCOM).
func (c *LedgerClient) RecordActuals(ctx context.Context, record LedgerRecordRequest) (*LedgerPutResponse, error) {
	var lastErr error

	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for order_item_id=%s (record actuals)\n",
				attempt, c.retryCount, record.OrderItemID)
		}

		resp, err := c.doRecordRequest(ctx, record, attempt)
		if err == nil {
			return resp, nil
		}

		lastErr = err

		// Don't retry on context cancellation
		if ctx.Err() != nil {
			return nil, fmt.Errorf("context cancelled: %w", ctx.Err())
		}

		// Don't retry on 404 (record not found)
		if strings.Contains(err.Error(), "404") {
			return nil, err
		}

		// Simple backoff for retries
		if attempt < c.retryCount {
			backoff := time.Duration(attempt+1) * 100 * time.Millisecond
			fmt.Printf("[DEGLedgerRecorder] Backing off for %v before retry\n", backoff)
			time.Sleep(backoff)
		}
	}

	return nil, lastErr
}

// doRecordRequest performs a single request to the ledger RECORD API.
func (c *LedgerClient) doRecordRequest(ctx context.Context, record LedgerRecordRequest, attempt int) (*LedgerPutResponse, error) {
	// Generate unique request ID for correlation
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	// Serialize the request body
	body, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ledger record request: %w", err)
	}

	// Create the HTTP request
	url := fmt.Sprintf("%s/ledger/record", c.baseURL)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Request-ID", requestID)

	// Add authentication header
	if c.signer != nil && c.signer.IsConfigured() {
		authHeader, err := c.signer.GenerateAuthHeader(body)
		if err != nil {
			return nil, fmt.Errorf("failed to generate Authorization header: %w", err)
		}
		req.Header.Set("Authorization", authHeader)
	} else if c.apiKey != "" {
		req.Header.Set(c.authHeader, c.apiKey)
	}

	// Log request details
	c.logRecordRequest(requestID, req, record, attempt)

	// Execute the request
	resp, err := c.httpClient.Do(req)
	duration := time.Since(startTime)

	if err != nil {
		c.logError(requestID, "HTTP request failed", err, duration)
		return nil, fmt.Errorf("ledger record request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read the response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.logError(requestID, "Failed to read response body", err, duration)
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	// Log response details
	c.logResponse(requestID, resp, respBody, duration)

	// Handle different status codes
	switch resp.StatusCode {
	case http.StatusOK:
		var ledgerResp LedgerPutResponse
		if err := json.Unmarshal(respBody, &ledgerResp); err != nil {
			return nil, fmt.Errorf("failed to parse success response: %w", err)
		}
		return &ledgerResp, nil

	case http.StatusNotFound:
		return nil, fmt.Errorf("ledger record not found (404): %s", string(respBody))

	case http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusConflict:
		var errResp LedgerErrorResponse
		if err := json.Unmarshal(respBody, &errResp); err != nil {
			return nil, fmt.Errorf("ledger API error (status %d): %s", resp.StatusCode, string(respBody))
		}
		return nil, fmt.Errorf("ledger API error (status %d, code %s): %s", resp.StatusCode, errResp.Code, errResp.Message)

	default:
		return nil, fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(respBody))
	}
}

// doPutRequest performs a single PUT request to the ledger API.
func (c *LedgerClient) doPutRequest(ctx context.Context, baseURL string, record LedgerPutRequest, attempt int) (*LedgerPutResponse, error) {
	// Generate unique request ID for correlation
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	// Serialize the request body
	body, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ledger request: %w", err)
	}

	// Create the HTTP request
	url := fmt.Sprintf("%s/ledger/put", baseURL)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Request-ID", requestID)

	// Add authentication header
	// Priority: Beckn signature > API Key
	if c.signer != nil && c.signer.IsConfigured() {
		// Generate Beckn-style Authorization header with signature
		authHeader, err := c.signer.GenerateAuthHeader(body)
		if err != nil {
			return nil, fmt.Errorf("failed to generate Authorization header: %w", err)
		}
		req.Header.Set("Authorization", authHeader)
	} else if c.apiKey != "" {
		// Fall back to simple API key authentication
		req.Header.Set(c.authHeader, c.apiKey)
	}

	// Log request details
	c.logRequest(requestID, req, record, attempt)

	// Execute the request
	resp, err := c.httpClient.Do(req)
	duration := time.Since(startTime)

	if err != nil {
		c.logError(requestID, "HTTP request failed", err, duration)
		return nil, fmt.Errorf("ledger request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read the response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.logError(requestID, "Failed to read response body", err, duration)
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	// Log response details
	c.logResponse(requestID, resp, respBody, duration)

	// Handle different status codes
	switch resp.StatusCode {
	case http.StatusOK:
		var ledgerResp LedgerPutResponse
		if err := json.Unmarshal(respBody, &ledgerResp); err != nil {
			return nil, fmt.Errorf("failed to parse success response: %w", err)
		}
		return &ledgerResp, nil

	case http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusConflict:
		var errResp LedgerErrorResponse
		if err := json.Unmarshal(respBody, &errResp); err != nil {
			return nil, fmt.Errorf("ledger API error (status %d): %s", resp.StatusCode, string(respBody))
		}
		return nil, fmt.Errorf("ledger API error (status %d, code %s): %s", resp.StatusCode, errResp.Code, errResp.Message)

	default:
		return nil, fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(respBody))
	}
}

// logRequest logs the full HTTP request details.
func (c *LedgerClient) logRequest(requestID string, req *http.Request, record LedgerPutRequest, attempt int) {
	// Build headers map (masking sensitive values)
	headers := make(map[string]string)
	for key, values := range req.Header {
		value := strings.Join(values, ", ")
		// Mask auth-related headers
		if strings.Contains(strings.ToLower(key), "auth") ||
			strings.Contains(strings.ToLower(key), "api-key") ||
			strings.Contains(strings.ToLower(key), "x-api-key") ||
			key == c.authHeader {
			if len(value) > 8 {
				headers[key] = value[:4] + "****" + value[len(value)-4:]
			} else {
				headers[key] = "****"
			}
		} else {
			headers[key] = value
		}
	}

	fmt.Println("")
	fmt.Println("╔════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║              DEGLedgerRecorder - OUTGOING REQUEST                  ║")
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ Request ID:     %s\n", requestID)
	fmt.Printf("║ Timestamp:      %s\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("║ Attempt:        %d/%d\n", attempt+1, c.retryCount+1)
	fmt.Printf("║ Method:         %s\n", req.Method)
	fmt.Printf("║ URL:            %s\n", req.URL.String())
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ HEADERS:")
	for k, v := range headers {
		fmt.Printf("║   %s: %s\n", k, v)
	}
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ REQUEST BODY (JSON):")

	compactBody, err := json.Marshal(record)
	if err != nil {
		fmt.Printf("║   (error formatting body: %v)\n", err)
	} else {
		fmt.Printf("║   %s\n", string(compactBody))
	}
	fmt.Println("╚════════════════════════════════════════════════════════════════════╝")
}

// logRecordRequest logs the full HTTP request details for /ledger/record.
func (c *LedgerClient) logRecordRequest(requestID string, req *http.Request, record LedgerRecordRequest, attempt int) {
	// Build headers map (masking sensitive values)
	headers := make(map[string]string)
	for key, values := range req.Header {
		value := strings.Join(values, ", ")
		// Mask auth-related headers
		if strings.Contains(strings.ToLower(key), "auth") ||
			strings.Contains(strings.ToLower(key), "api-key") ||
			strings.Contains(strings.ToLower(key), "x-api-key") ||
			key == c.authHeader {
			if len(value) > 8 {
				headers[key] = value[:4] + "****" + value[len(value)-4:]
			} else {
				headers[key] = "****"
			}
		} else {
			headers[key] = value
		}
	}

	fmt.Println("")
	fmt.Println("╔════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║         DEGLedgerRecorder - OUTGOING REQUEST (RECORD)              ║")
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ Request ID:     %s\n", requestID)
	fmt.Printf("║ Timestamp:      %s\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("║ Attempt:        %d/%d\n", attempt+1, c.retryCount+1)
	fmt.Printf("║ Method:         %s\n", req.Method)
	fmt.Printf("║ URL:            %s\n", req.URL.String())
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ HEADERS:")
	for k, v := range headers {
		fmt.Printf("║   %s: %s\n", k, v)
	}
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ REQUEST BODY (JSON):")

	compactBody, err := json.Marshal(record)
	if err != nil {
		fmt.Printf("║   (error formatting body: %v)\n", err)
	} else {
		fmt.Printf("║   %s\n", string(compactBody))
	}
	fmt.Println("╚════════════════════════════════════════════════════════════════════╝")
}

// logResponse logs the full HTTP response details.
func (c *LedgerClient) logResponse(requestID string, resp *http.Response, body []byte, duration time.Duration) {
	// Build headers map
	headers := make(map[string]string)
	for key, values := range resp.Header {
		headers[key] = strings.Join(values, ", ")
	}

	// Determine status emoji
	statusEmoji := "✓"
	if resp.StatusCode >= 400 {
		statusEmoji = "✗"
	}

	fmt.Println("")
	fmt.Println("╔════════════════════════════════════════════════════════════════════╗")
	fmt.Printf("║              DEGLedgerRecorder - RESPONSE %s                        ║\n", statusEmoji)
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ Request ID:     %s\n", requestID)
	fmt.Printf("║ Timestamp:      %s\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("║ Duration:       %v\n", duration)
	fmt.Printf("║ Status:         %d %s\n", resp.StatusCode, http.StatusText(resp.StatusCode))
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ RESPONSE HEADERS:")
	for k, v := range headers {
		fmt.Printf("║   %s: %s\n", k, v)
	}
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Println("║ RESPONSE BODY:")

	bodyStr := string(body)
	if len(bodyStr) > 2000 {
		bodyStr = bodyStr[:2000] + "... (truncated)"
	}
	fmt.Printf("║   %s\n", bodyStr)
	fmt.Println("╚════════════════════════════════════════════════════════════════════╝")
}

// logError logs an error that occurred during the request.
func (c *LedgerClient) logError(requestID string, message string, err error, duration time.Duration) {
	fmt.Println("")
	fmt.Println("╔════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║              DEGLedgerRecorder - ERROR ✗                           ║")
	fmt.Println("╠════════════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ Request ID:     %s\n", requestID)
	fmt.Printf("║ Timestamp:      %s\n", time.Now().UTC().Format(time.RFC3339))
	fmt.Printf("║ Duration:       %v\n", duration)
	fmt.Printf("║ Error:          %s\n", message)
	fmt.Printf("║ Details:        %v\n", err)
	fmt.Println("╚════════════════════════════════════════════════════════════════════╝")
}

// Close releases resources held by the client.
func (c *LedgerClient) Close() error {
	c.httpClient.CloseIdleConnections()
	return nil
}
