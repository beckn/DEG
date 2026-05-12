package degledgerrecorder

import (
	"fmt"
	"os"
	"strconv"
	"strings"
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

// Supported actions for ledger recording
const (
	ActionOnConfirm = "on_confirm"
	ActionOnStatus  = "on_status"
	ActionStatus    = "status"
)

// Supported payload shapes — selects which mapper parses the on_confirm body.
const (
	PayloadShapeWave1 = "wave1" // beckn:Order / beckn:orderItems (p2p-trading-ies-wave1)
	PayloadShapeWave2 = "wave2" // message.contract.commitments (p2p-trading-ies-wave2)
)

// Sources for the target ledger URI.
const (
	LedgerUriSourceConfig  = "config"  // use plugin config ledgerHost
	LedgerUriSourcePayload = "payload" // read participants[role=*Discom].participantAttributes.ledgerUri from payload
)

// Ledger API styles the plugin can speak to.
const (
	LedgerApiLegacyLedger = "legacy_ledger" // POST <uri>/ledger/put with custom JSON body
	LedgerApiBeckn        = "beckn"         // POST verbatim on_confirm to <uri>/on_confirm with rewritten context
)

// Config holds the configuration for the DEG Ledger Recorder plugin.
type Config struct {
	// PayloadShape selects which on_confirm body the mapper expects.
	// Required. One of: "wave1", "wave2".
	PayloadShape string

	// LedgerUriSource determines where the target ledger URI comes from.
	// Required. One of: "config" (uses LedgerHost), "payload" (reads
	// participants[role=*Discom].participantAttributes.ledgerUri).
	LedgerUriSource string

	// LedgerApi selects which API style the plugin speaks.
	// Required. One of: "legacy_ledger" (POST <uri>/ledger/put with custom
	// JSON), "beckn" (POST verbatim on_confirm to <uri>/on_confirm).
	LedgerApi string

	// LedgerHost is the base URL of the DEG Ledger service.
	// Required only when LedgerUriSource == "config".
	LedgerHost string

	// SenderHost is the base URL (scheme + host[:port]) the plugin advertises
	// when forwarding a beckn on_confirm to a ledger TSP. Used only when
	// LedgerApi == "beckn" to rewrite context.bppUri to "<SenderHost>/bpp/caller".
	// Optional — falls back to the host of context.bapUri (BUYER role) or
	// context.bppUri (SELLER role) extracted from the incoming payload.
	SenderHost string

	// Role is the ledger role for this platform (BUYER, SELLER, BUYER_DISCOM, SELLER_DISCOM)
	Role string

	// Actions is a list of beckn actions that trigger ledger recording.
	// Supported: "on_confirm" (trade records via /ledger/put), "on_status" (meter readings via /ledger/record)
	// Default: ["on_confirm"]
	Actions []string

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
// Note: PayloadShape, LedgerUriSource, and LedgerApi have no defaults — the
// caller must set them in YAML so the active behavior is always visible there
// instead of hidden in code.
func DefaultConfig() *Config {
	return &Config{
		PayloadShape:             "",
		LedgerUriSource:          "",
		LedgerApi:                "",
		LedgerHost:               "",
		SenderHost:               "",
		Role:                     "BUYER",
		Actions:                  []string{ActionOnConfirm}, // Default: only on_confirm
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

	// payloadShape — required, no default
	shape, ok := cfg["payloadShape"]
	if !ok || shape == "" {
		return nil, fmt.Errorf("payloadShape is required (one of: %s, %s)", PayloadShapeWave1, PayloadShapeWave2)
	}
	if !isValidPayloadShape(shape) {
		return nil, fmt.Errorf("invalid payloadShape: %s (must be %s or %s)", shape, PayloadShapeWave1, PayloadShapeWave2)
	}
	config.PayloadShape = shape

	// ledgerUriSource — required, no default
	source, ok := cfg["ledgerUriSource"]
	if !ok || source == "" {
		return nil, fmt.Errorf("ledgerUriSource is required (one of: %s, %s)", LedgerUriSourceConfig, LedgerUriSourcePayload)
	}
	if !isValidLedgerUriSource(source) {
		return nil, fmt.Errorf("invalid ledgerUriSource: %s (must be %s or %s)", source, LedgerUriSourceConfig, LedgerUriSourcePayload)
	}
	config.LedgerUriSource = source

	// ledgerApi — required, no default
	api, ok := cfg["ledgerApi"]
	if !ok || api == "" {
		return nil, fmt.Errorf("ledgerApi is required (one of: %s, %s)", LedgerApiLegacyLedger, LedgerApiBeckn)
	}
	if !isValidLedgerApi(api) {
		return nil, fmt.Errorf("invalid ledgerApi: %s (must be %s or %s)", api, LedgerApiLegacyLedger, LedgerApiBeckn)
	}
	config.LedgerApi = api

	// ledgerHost — required only when ledgerUriSource = config
	if host, ok := cfg["ledgerHost"]; ok && host != "" {
		config.LedgerHost = host
	}
	if config.LedgerUriSource == LedgerUriSourceConfig && config.LedgerHost == "" {
		return nil, fmt.Errorf("ledgerHost is required when ledgerUriSource=%s", LedgerUriSourceConfig)
	}

	// senderHost — optional; only consulted when ledgerApi=beckn
	if sh, ok := cfg["senderHost"]; ok && sh != "" {
		config.SenderHost = sh
	}

	if role, ok := cfg["role"]; ok && role != "" {
		if !isValidRole(role) {
			return nil, fmt.Errorf("invalid role: %s (must be BUYER, SELLER, BUYER_DISCOM, or SELLER_DISCOM)", role)
		}
		config.Role = role
	}

	// Parse actions (comma-separated list)
	if actions, ok := cfg["actions"]; ok && actions != "" {
		actionList := strings.Split(actions, ",")
		config.Actions = make([]string, 0, len(actionList))
		for _, action := range actionList {
			action = strings.TrimSpace(action)
			if action != "" {
				if !isValidAction(action) {
					return nil, fmt.Errorf("invalid action: %s (must be on_confirm or on_status)", action)
				}
				config.Actions = append(config.Actions, action)
			}
		}
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
	// Priority: explicit config > simplekeymanager-style config > environment variables
	//
	// Supported config key aliases (for compatibility with simplekeymanager):
	//   signingPrivateKey  (same in both)
	//   subscriberId       OR  networkParticipant
	//   uniqueKeyId        OR  keyId

	// Signing private key (same name in both styles)
	if signingKey, ok := cfg["signingPrivateKey"]; ok && signingKey != "" {
		config.SigningPrivateKey = signingKey
	}

	// Subscriber ID: check both "subscriberId" and "networkParticipant" (simplekeymanager style)
	if subscriberID, ok := cfg["subscriberId"]; ok && subscriberID != "" {
		config.SubscriberID = subscriberID
	} else if networkParticipant, ok := cfg["networkParticipant"]; ok && networkParticipant != "" {
		config.SubscriberID = networkParticipant
	}

	// Unique Key ID: check both "uniqueKeyId" and "keyId" (simplekeymanager style)
	if uniqueKeyID, ok := cfg["uniqueKeyId"]; ok && uniqueKeyID != "" {
		config.UniqueKeyID = uniqueKeyID
	} else if keyId, ok := cfg["keyId"]; ok && keyId != "" {
		config.UniqueKeyID = keyId
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
		"BUYER":         true,
		"SELLER":        true,
		"BUYER_DISCOM":  true,
		"SELLER_DISCOM": true,
	}
	return validRoles[role]
}

// isValidAction checks if the provided action is supported.
func isValidAction(action string) bool {
	validActions := map[string]bool{
		ActionOnConfirm: true,
		ActionOnStatus:  true,
		ActionStatus:    true,
	}
	return validActions[action]
}

// isValidPayloadShape checks if the provided payload shape is supported.
func isValidPayloadShape(shape string) bool {
	return shape == PayloadShapeWave1 || shape == PayloadShapeWave2
}

// isValidLedgerUriSource checks if the provided ledger URI source is supported.
func isValidLedgerUriSource(source string) bool {
	return source == LedgerUriSourceConfig || source == LedgerUriSourcePayload
}

// isValidLedgerApi checks if the provided ledger API style is supported.
func isValidLedgerApi(api string) bool {
	return api == LedgerApiLegacyLedger || api == LedgerApiBeckn
}

// IsActionEnabled checks if the given action is enabled in the config.
func (c *Config) IsActionEnabled(action string) bool {
	for _, a := range c.Actions {
		if a == action {
			return true
		}
	}
	return false
}

// IsDiscomRole returns true if the configured role is a discom role.
func (c *Config) IsDiscomRole() bool {
	return c.Role == "BUYER_DISCOM" || c.Role == "SELLER_DISCOM"
}

// IsBuyerSide returns true if the role is buyer or buyer discom.
func (c *Config) IsBuyerSide() bool {
	return c.Role == "BUYER" || c.Role == "BUYER_DISCOM"
}
