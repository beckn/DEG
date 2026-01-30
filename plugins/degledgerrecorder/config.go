package degledgerrecorder

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Environment variable names for signing configuration.
// These are the same env vars typically used by beckn-onix simplekeymanager,
// allowing single-source-of-truth configuration.
// Also compatible with Vault Agent, K8s secrets, etc.
const (
	EnvSigningPrivateKey = "SIGNING_PRIVATE_KEY"
	EnvSubscriberID      = "SUBSCRIBER_ID"
	EnvUniqueKeyID       = "UNIQUE_KEY_ID"
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

	// APIKey is an optional API key for ledger service authentication (simple auth)
	APIKey string

	// AuthHeader is the header name for the API key (default: X-API-Key)
	AuthHeader string

	// DebugLogging enables verbose request/response logging
	DebugLogging bool

	// --- Beckn-style Signature Authentication ---
	// When configured, generates Authorization header using the same signing mechanism
	// as beckn-onix (ed25519 + BLAKE2b-512)

	// SigningPrivateKey is the base64-encoded ed25519 private key seed for signing
	// This should be the same key used by beckn-onix for signing outgoing messages
	SigningPrivateKey string

	// SubscriberID is the subscriber ID used in the Authorization header keyId
	// Format in header: keyId="<subscriberId>|<uniqueKeyId>|ed25519"
	SubscriberID string

	// UniqueKeyID is the unique key identifier used in the Authorization header keyId
	UniqueKeyID string

	// SignatureValiditySeconds is how long the signature is valid (default: 30 seconds)
	SignatureValiditySeconds int

	// SigningFromEnv indicates if signing config was loaded from environment variables
	// (used for logging purposes)
	SigningFromEnv bool
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		LedgerHost:               "",
		Role:                     "BUYER",
		Enabled:                  true,
		AsyncTimeout:             5 * time.Second,
		RetryCount:               0,
		APIKey:                   "",
		AuthHeader:               "X-API-Key",
		DebugLogging:             false,
		SigningPrivateKey:        "",
		SubscriberID:             "",
		UniqueKeyID:              "",
		SignatureValiditySeconds: 30,
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

	if apiKey, ok := cfg["apiKey"]; ok {
		config.APIKey = apiKey
	}

	if authHeader, ok := cfg["authHeader"]; ok && authHeader != "" {
		config.AuthHeader = authHeader
	}

	if debug, ok := cfg["debugLogging"]; ok {
		config.DebugLogging = debug == "true" || debug == "1"
	}

	// Beckn-style signature authentication
	// Priority: explicit config > environment variables
	if signingKey, ok := cfg["signingPrivateKey"]; ok && signingKey != "" {
		config.SigningPrivateKey = signingKey
	}

	if subscriberID, ok := cfg["subscriberId"]; ok && subscriberID != "" {
		config.SubscriberID = subscriberID
	}

	if uniqueKeyID, ok := cfg["uniqueKeyId"]; ok && uniqueKeyID != "" {
		config.UniqueKeyID = uniqueKeyID
	}

	if validity, ok := cfg["signatureValiditySeconds"]; ok && validity != "" {
		seconds, err := strconv.Atoi(validity)
		if err != nil {
			return nil, fmt.Errorf("invalid signatureValiditySeconds: %s", validity)
		}
		config.SignatureValiditySeconds = seconds
	}

	// Fallback to environment variables if not explicitly configured
	// This allows reusing the same env vars as beckn-onix simplekeymanager
	// and is compatible with Vault Agent, K8s secrets, etc.
	signingFromEnv := false
	if config.SigningPrivateKey == "" {
		if envVal := os.Getenv(EnvSigningPrivateKey); envVal != "" {
			config.SigningPrivateKey = envVal
			signingFromEnv = true
		}
	}
	if config.SubscriberID == "" {
		if envVal := os.Getenv(EnvSubscriberID); envVal != "" {
			config.SubscriberID = envVal
			signingFromEnv = true
		}
	}
	if config.UniqueKeyID == "" {
		if envVal := os.Getenv(EnvUniqueKeyID); envVal != "" {
			config.UniqueKeyID = envVal
			signingFromEnv = true
		}
	}

	// Store whether config came from env for logging purposes
	config.SigningFromEnv = signingFromEnv

	// Validate signing config: if any signing field is set, all must be set
	signingConfigured := config.SigningPrivateKey != "" || config.SubscriberID != "" || config.UniqueKeyID != ""
	if signingConfigured {
		if config.SigningPrivateKey == "" {
			return nil, fmt.Errorf("signingPrivateKey is required when Beckn signing is configured (set via config or %s env var)", EnvSigningPrivateKey)
		}
		if config.SubscriberID == "" {
			return nil, fmt.Errorf("subscriberId is required when Beckn signing is configured (set via config or %s env var)", EnvSubscriberID)
		}
		if config.UniqueKeyID == "" {
			return nil, fmt.Errorf("uniqueKeyId is required when Beckn signing is configured (set via config or %s env var)", EnvUniqueKeyID)
		}
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
