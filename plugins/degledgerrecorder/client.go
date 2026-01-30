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

// PutRecord sends a record to the ledger PUT API.
func (c *LedgerClient) PutRecord(ctx context.Context, record LedgerPutRequest) (*LedgerPutResponse, error) {
	var lastErr error

	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			fmt.Printf("[DEGLedgerRecorder] Retry attempt %d/%d for order_item_id=%s\n",
				attempt, c.retryCount, record.OrderItemID)
		}

		resp, err := c.doPutRequest(ctx, record, attempt)
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

// doPutRequest performs a single PUT request to the ledger API.
func (c *LedgerClient) doPutRequest(ctx context.Context, record LedgerPutRequest, attempt int) (*LedgerPutResponse, error) {
	// Generate unique request ID for correlation
	requestID := uuid.New().String()[:8]
	startTime := time.Now()

	// Serialize the request body
	body, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ledger request: %w", err)
	}

	// Create the HTTP request
	url := fmt.Sprintf("%s/ledger/put", c.baseURL)
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

	// Pretty print the request body
	prettyBody, err := json.MarshalIndent(record, "║   ", "  ")
	if err != nil {
		fmt.Printf("║   (error formatting body: %v)\n", err)
	} else {
		lines := strings.Split(string(prettyBody), "\n")
		for _, line := range lines {
			fmt.Printf("║   %s\n", line)
		}
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

	// Try to pretty print JSON, fall back to raw if not valid JSON
	var prettyBody bytes.Buffer
	if err := json.Indent(&prettyBody, body, "║   ", "  "); err == nil {
		lines := strings.Split(prettyBody.String(), "\n")
		for _, line := range lines {
			fmt.Printf("║   %s\n", line)
		}
	} else {
		// Not JSON or invalid JSON, print raw (truncated if too long)
		bodyStr := string(body)
		if len(bodyStr) > 2000 {
			bodyStr = bodyStr[:2000] + "... (truncated)"
		}
		fmt.Printf("║   %s\n", bodyStr)
	}
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
