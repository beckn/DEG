package degledgerrecorder

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// LedgerClient handles communication with the DEG Ledger API.
type LedgerClient struct {
	baseURL    string
	httpClient *http.Client
	retryCount int
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

// NewLedgerClient creates a new LedgerClient instance.
func NewLedgerClient(baseURL string, timeout time.Duration, retryCount int) *LedgerClient {
	return &LedgerClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
		},
		retryCount: retryCount,
	}
}

// PutRecord sends a record to the ledger PUT API.
func (c *LedgerClient) PutRecord(ctx context.Context, record LedgerPutRequest) (*LedgerPutResponse, error) {
	var lastErr error

	for attempt := 0; attempt <= c.retryCount; attempt++ {
		resp, err := c.doPutRequest(ctx, record)
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
			time.Sleep(time.Duration(attempt+1) * 100 * time.Millisecond)
		}
	}

	return nil, lastErr
}

// doPutRequest performs a single PUT request to the ledger API.
func (c *LedgerClient) doPutRequest(ctx context.Context, record LedgerPutRequest) (*LedgerPutResponse, error) {
	// Serialize the request body (pretty for debug)
	prettyBody, _ := json.MarshalIndent(record, "", "  ")
	body, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ledger request: %w", err)
	}

	// Create the HTTP request
	url := fmt.Sprintf("%s/ledger/put", c.baseURL)

	// DEBUG: Log the full request details
	fmt.Println("")
	fmt.Println("============ DEGLedgerRecorder DEBUG ============")
	fmt.Println("Ledger API URL:", url)
	fmt.Println("Request payload (pretty):")
	fmt.Println(string(prettyBody))
	fmt.Println("==================================================")

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	// Execute the request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		fmt.Printf("[DEGLedgerRecorder DEBUG] HTTP request failed: %v\n", err)
		return nil, fmt.Errorf("ledger request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read the response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	// DEBUG: Log the response
	fmt.Printf("[DEGLedgerRecorder DEBUG] Response status: %d\n", resp.StatusCode)
	fmt.Printf("[DEGLedgerRecorder DEBUG] Response body:\n%s\n", string(respBody))

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

// Close releases resources held by the client.
func (c *LedgerClient) Close() error {
	c.httpClient.CloseIdleConnections()
	return nil
}
