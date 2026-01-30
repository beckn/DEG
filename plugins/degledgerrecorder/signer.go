package degledgerrecorder

import (
	"crypto/ed25519"
	"encoding/base64"
	"errors"
	"fmt"
	"time"

	"golang.org/x/crypto/blake2b"
)

// BecknSigner generates Beckn-compliant Authorization headers using ed25519 signing.
type BecknSigner struct {
	subscriberID     string
	uniqueKeyID      string
	signingPrivateKey []byte
	signatureValidity time.Duration
}

// NewBecknSigner creates a new BecknSigner instance.
// signingPrivateKeyBase64 should be the base64-encoded ed25519 seed (32 bytes).
func NewBecknSigner(subscriberID, uniqueKeyID, signingPrivateKeyBase64 string, validitySeconds int) (*BecknSigner, error) {
	if subscriberID == "" {
		return nil, errors.New("subscriberID is required for signing")
	}
	if uniqueKeyID == "" {
		return nil, errors.New("uniqueKeyID is required for signing")
	}
	if signingPrivateKeyBase64 == "" {
		return nil, errors.New("signingPrivateKey is required for signing")
	}

	privateKeyBytes, err := base64.StdEncoding.DecodeString(signingPrivateKeyBase64)
	if err != nil {
		return nil, fmt.Errorf("failed to decode signing private key: %w", err)
	}

	if len(privateKeyBytes) != ed25519.SeedSize {
		return nil, fmt.Errorf("invalid signing private key length: expected %d bytes, got %d", ed25519.SeedSize, len(privateKeyBytes))
	}

	validity := time.Duration(validitySeconds) * time.Second
	if validity <= 0 {
		validity = 30 * time.Second // Default 30 seconds validity
	}

	return &BecknSigner{
		subscriberID:      subscriberID,
		uniqueKeyID:       uniqueKeyID,
		signingPrivateKey: privateKeyBytes,
		signatureValidity: validity,
	}, nil
}

// GenerateAuthHeader generates a Beckn-compliant Authorization header for the given payload.
// Returns the header value in the format:
// Signature keyId="<subscriber_id>|<key_id>|ed25519",algorithm="ed25519",created="<ts>",expires="<ts>",headers="(created) (expires) digest",signature="<base64_sig>"
func (s *BecknSigner) GenerateAuthHeader(payload []byte) (string, error) {
	now := time.Now()
	createdAt := now.Unix()
	expiresAt := now.Add(s.signatureValidity).Unix()

	// Generate the signing string using BLAKE2b-512
	signingString, err := s.createSigningString(payload, createdAt, expiresAt)
	if err != nil {
		return "", fmt.Errorf("failed to create signing string: %w", err)
	}

	// Sign the signing string with ed25519
	signature, err := s.sign([]byte(signingString))
	if err != nil {
		return "", fmt.Errorf("failed to sign: %w", err)
	}

	signatureB64 := base64.StdEncoding.EncodeToString(signature)

	// Build the Authorization header in Beckn format
	// Format: Signature keyId="...",algorithm="ed25519",created="...",expires="...",headers="(created) (expires) digest",signature="..."
	authHeader := fmt.Sprintf(
		`Signature keyId="%s|%s|ed25519",algorithm="ed25519",created="%d",expires="%d",headers="(created) (expires) digest",signature="%s"`,
		s.subscriberID,
		s.uniqueKeyID,
		createdAt,
		expiresAt,
		signatureB64,
	)

	return authHeader, nil
}

// createSigningString creates the string to be signed using BLAKE2b-512 hash.
// Format: (created): <ts>\n(expires): <ts>\ndigest: BLAKE-512=<base64_hash>
func (s *BecknSigner) createSigningString(payload []byte, createdAt, expiresAt int64) (string, error) {
	hasher, err := blake2b.New512(nil)
	if err != nil {
		return "", fmt.Errorf("failed to create BLAKE2b hasher: %w", err)
	}

	_, err = hasher.Write(payload)
	if err != nil {
		return "", fmt.Errorf("failed to hash payload: %w", err)
	}

	hashSum := hasher.Sum(nil)
	digestB64 := base64.StdEncoding.EncodeToString(hashSum)

	return fmt.Sprintf("(created): %d\n(expires): %d\ndigest: BLAKE-512=%s", createdAt, expiresAt, digestB64), nil
}

// sign signs the given data using ed25519.
func (s *BecknSigner) sign(data []byte) ([]byte, error) {
	privateKey := ed25519.NewKeyFromSeed(s.signingPrivateKey)
	return ed25519.Sign(privateKey, data), nil
}

// IsConfigured returns true if the signer has valid configuration.
func (s *BecknSigner) IsConfigured() bool {
	return s != nil && len(s.signingPrivateKey) > 0
}
