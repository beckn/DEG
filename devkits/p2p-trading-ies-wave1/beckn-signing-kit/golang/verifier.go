package signer

import (
	"crypto/ed25519"
	"encoding/base64"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// Verify checks that an Authorization header is a valid signature for the given body,
// using the sender's base64-encoded public key. Returns nil if valid.
func Verify(body []byte, authHeader string, publicKeyBase64 string) error {
	return VerifyAt(body, authHeader, publicKeyBase64, time.Now())
}

// VerifyAt checks validity at a specific time (useful for testing).
func VerifyAt(body []byte, authHeader string, publicKeyBase64 string, now time.Time) error {
	created, expires, sig, err := parseAuthHeader(authHeader)
	if err != nil {
		return fmt.Errorf("verifier: %w", err)
	}

	currentTime := now.Unix()
	if created > currentTime {
		return fmt.Errorf("verifier: signature not yet valid (created %d > now %d)", created, currentTime)
	}
	if currentTime > expires {
		return fmt.Errorf("verifier: signature expired (expires %d < now %d)", expires, currentTime)
	}

	sigBytes, err := base64.StdEncoding.DecodeString(sig)
	if err != nil {
		return fmt.Errorf("verifier: invalid signature base64: %w", err)
	}

	signingString, err := buildSigningString(body, created, expires)
	if err != nil {
		return fmt.Errorf("verifier: %w", err)
	}

	pubKeyBytes, err := base64.StdEncoding.DecodeString(publicKeyBase64)
	if err != nil {
		return fmt.Errorf("verifier: invalid public key base64: %w", err)
	}

	if !ed25519.Verify(ed25519.PublicKey(pubKeyBytes), []byte(signingString), sigBytes) {
		return fmt.Errorf("verifier: signature verification failed")
	}

	return nil
}

// ParseKeyID extracts subscriberID, uniqueKeyID, and algorithm from a keyId field.
// Format: "subscriber_id|unique_key_id|algorithm"
func ParseKeyID(keyID string) (subscriberID, uniqueKeyID, algorithm string, err error) {
	parts := strings.Split(keyID, "|")
	if len(parts) != 3 {
		return "", "", "", fmt.Errorf("invalid keyId format, expected 'subscriber|keyId|algorithm', got %q", keyID)
	}
	return parts[0], parts[1], parts[2], nil
}

func parseAuthHeader(header string) (created, expires int64, signature string, err error) {
	header = strings.TrimPrefix(header, "Signature ")

	params := make(map[string]string)
	for _, part := range strings.Split(header, ",") {
		kv := strings.SplitN(strings.TrimSpace(part), "=", 2)
		if len(kv) == 2 {
			params[strings.TrimSpace(kv[0])] = strings.Trim(kv[1], `"`)
		}
	}

	createdStr, ok := params["created"]
	if !ok {
		return 0, 0, "", fmt.Errorf("missing 'created' in auth header")
	}
	created, err = strconv.ParseInt(createdStr, 10, 64)
	if err != nil {
		return 0, 0, "", fmt.Errorf("invalid 'created' timestamp: %w", err)
	}

	expiresStr, ok := params["expires"]
	if !ok {
		return 0, 0, "", fmt.Errorf("missing 'expires' in auth header")
	}
	expires, err = strconv.ParseInt(expiresStr, 10, 64)
	if err != nil {
		return 0, 0, "", fmt.Errorf("invalid 'expires' timestamp: %w", err)
	}

	signature, ok = params["signature"]
	if !ok {
		return 0, 0, "", fmt.Errorf("missing 'signature' in auth header")
	}

	return created, expires, signature, nil
}
