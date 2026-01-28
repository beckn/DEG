package degledgerrecorder

import (
	"fmt"
	"strconv"
	"time"
)

// Config holds the configuration for the DEG Ledger Recorder plugin.
type Config struct {
	// LedgerHost is the base URL of the DEG Ledger service (e.g., "https://ledger.example.org")
	LedgerHost string

	// Role is the ledger role for this platform (BUYER, SELLER, BUYER_DISCOM, SELLER_DISCOM)
	Role string

	// Enabled controls whether the plugin is active
	Enabled bool

	// AsyncTimeout is the timeout for async ledger API calls in milliseconds
	AsyncTimeout time.Duration

	// RetryCount is the number of retries for failed ledger calls (0 = no retry)
	RetryCount int
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		LedgerHost:   "",
		Role:         "BUYER",
		Enabled:      true,
		AsyncTimeout: 5 * time.Second,
		RetryCount:   0,
	}
}

// ParseConfig parses the plugin configuration map into a Config struct.
func ParseConfig(cfg map[string]string) (*Config, error) {
	config := DefaultConfig()

	if host, ok := cfg["ledgerHost"]; ok && host != "" {
		config.LedgerHost = host
	}
	if config.LedgerHost == "" {
		return nil, fmt.Errorf("ledgerHost is required")
	}

	if role, ok := cfg["role"]; ok && role != "" {
		if !isValidRole(role) {
			return nil, fmt.Errorf("invalid role: %s (must be BUYER, SELLER, BUYER_DISCOM, or SELLER_DISCOM)", role)
		}
		config.Role = role
	}

	if enabled, ok := cfg["enabled"]; ok {
		config.Enabled = enabled == "true" || enabled == "1"
	}

	if timeout, ok := cfg["asyncTimeout"]; ok && timeout != "" {
		ms, err := strconv.Atoi(timeout)
		if err != nil {
			return nil, fmt.Errorf("invalid asyncTimeout: %s", timeout)
		}
		config.AsyncTimeout = time.Duration(ms) * time.Millisecond
	}

	if retry, ok := cfg["retryCount"]; ok && retry != "" {
		count, err := strconv.Atoi(retry)
		if err != nil {
			return nil, fmt.Errorf("invalid retryCount: %s", retry)
		}
		config.RetryCount = count
	}

	return config, nil
}

// isValidRole checks if the provided role is valid for the ledger API.
func isValidRole(role string) bool {
	validRoles := map[string]bool{
		"BUYER":        true,
		"SELLER":       true,
		"BUYER_DISCOM": true,
		"SELLER_DISCOM": true,
	}
	return validRoles[role]
}
