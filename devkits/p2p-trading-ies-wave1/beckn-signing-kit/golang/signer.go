// Package signer provides Beckn protocol payload signing for DEG (Digital Energy Grid).
//
// It signs JSON payloads using Ed25519 + BLAKE2-512 and produces an Authorization
// header compatible with the Beckn protocol specification.
//
// Usage:
//
//	s, err := signer.New(signer.Config{
//	    SubscriberID:      "p2p-trading-sandbox1.com",
//	    UniqueKeyID:       "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
//	    SigningPrivateKey:  "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
//	})
//
//	authHeader, err := s.SignPayload(payloadBytes)
package signer

import (
	"crypto/ed25519"
	"encoding/base64"
	"fmt"
	"time"

	"golang.org/x/crypto/blake2b"
)

// Config holds the signing configuration for a network participant.
// These values come from the simplekeymanager config in your beckn-onix YAML.
type Config struct {
	// SubscriberID is the network participant identifier (e.g. "p2p-trading-sandbox1.com").
	SubscriberID string

	// UniqueKeyID is the unique key identifier registered with the Beckn registry.
	UniqueKeyID string

	// SigningPrivateKey is the base64-encoded Ed25519 seed (32 bytes).
	SigningPrivateKey string

	// ExpiryDuration is how long the signature is valid. Defaults to 5 minutes.
	ExpiryDuration time.Duration
}

// Signer produces Beckn-compatible Authorization headers for JSON payloads.
type Signer struct {
	subscriberID string
	uniqueKeyID  string
	privateKey   ed25519.PrivateKey
	expiry       time.Duration
}

// SignedResult contains the signing output.
type SignedResult struct {
	// AuthorizationHeader is the full value for the HTTP Authorization header.
	AuthorizationHeader string

	// CreatedAt is the Unix timestamp when the signature was created.
	CreatedAt int64

	// ExpiresAt is the Unix timestamp when the signature expires.
	ExpiresAt int64

	// Signature is the raw base64-encoded Ed25519 signature.
	Signature string
}

// New creates a Signer from the provided config.
func New(cfg Config) (*Signer, error) {
	if cfg.SubscriberID == "" {
		return nil, fmt.Errorf("signer: SubscriberID is required")
	}
	if cfg.UniqueKeyID == "" {
		return nil, fmt.Errorf("signer: UniqueKeyID is required")
	}
	if cfg.SigningPrivateKey == "" {
		return nil, fmt.Errorf("signer: SigningPrivateKey is required")
	}

	seed, err := base64.StdEncoding.DecodeString(cfg.SigningPrivateKey)
	if err != nil {
		return nil, fmt.Errorf("signer: invalid base64 private key: %w", err)
	}
	if len(seed) != ed25519.SeedSize {
		return nil, fmt.Errorf("signer: private key seed must be %d bytes, got %d", ed25519.SeedSize, len(seed))
	}

	expiry := cfg.ExpiryDuration
	if expiry == 0 {
		expiry = 5 * time.Minute
	}

	return &Signer{
		subscriberID: cfg.SubscriberID,
		uniqueKeyID:  cfg.UniqueKeyID,
		privateKey:   ed25519.NewKeyFromSeed(seed),
		expiry:       expiry,
	}, nil
}

// SignPayload signs a JSON payload and returns the Authorization header value.
func (s *Signer) SignPayload(body []byte) (string, error) {
	result, err := s.SignPayloadDetailed(body)
	if err != nil {
		return "", err
	}
	return result.AuthorizationHeader, nil
}

// SignPayloadDetailed signs a JSON payload and returns full signing details.
func (s *Signer) SignPayloadDetailed(body []byte) (*SignedResult, error) {
	now := time.Now()
	return s.signPayloadAt(body, now)
}

// signPayloadAt signs at a specific time (used for deterministic testing).
func (s *Signer) signPayloadAt(body []byte, now time.Time) (*SignedResult, error) {
	createdAt := now.Unix()
	expiresAt := now.Add(s.expiry).Unix()

	signingString, err := buildSigningString(body, createdAt, expiresAt)
	if err != nil {
		return nil, fmt.Errorf("signer: failed to build signing string: %w", err)
	}

	sig := ed25519.Sign(s.privateKey, []byte(signingString))
	sigB64 := base64.StdEncoding.EncodeToString(sig)

	header := fmt.Sprintf(
		`Signature keyId="%s|%s|ed25519",algorithm="ed25519",created="%d",expires="%d",headers="(created) (expires) digest",signature="%s"`,
		s.subscriberID, s.uniqueKeyID, createdAt, expiresAt, sigB64,
	)

	return &SignedResult{
		AuthorizationHeader: header,
		CreatedAt:           createdAt,
		ExpiresAt:           expiresAt,
		Signature:           sigB64,
	}, nil
}

// buildSigningString creates the canonical string to sign:
//
//	(created): {timestamp}
//	(expires): {timestamp}
//	digest: BLAKE-512={base64_hash}
func buildSigningString(body []byte, createdAt, expiresAt int64) (string, error) {
	hasher, err := blake2b.New512(nil)
	if err != nil {
		return "", err
	}
	hasher.Write(body)
	digest := base64.StdEncoding.EncodeToString(hasher.Sum(nil))

	return fmt.Sprintf("(created): %d\n(expires): %d\ndigest: BLAKE-512=%s",
		createdAt, expiresAt, digest), nil
}
