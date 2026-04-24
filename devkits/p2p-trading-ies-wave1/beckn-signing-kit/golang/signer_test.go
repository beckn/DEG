package signer

import (
	"crypto/ed25519"
	"encoding/base64"
	"strings"
	"testing"
	"time"
)

// Test keys matching the config in local-p2p-bap.yaml (sandbox1).
const (
	testSubscriberID = "p2p-trading-sandbox1.com"
	testKeyID        = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ"
	testPrivateKey   = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw="
	testPublicKey    = "KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE="
)

// Sample beckn payload (trimmed confirm request).
var samplePayload = []byte(`{
  "context": {
    "version": "2.0.0",
    "action": "confirm",
    "timestamp": "2024-10-04T10:25:00Z",
    "message_id": "msg-confirm-001",
    "transaction_id": "txn-energy-001",
    "bap_id": "bap.energy-consumer.com",
    "bap_uri": "https://bap.energy-consumer.com",
    "bpp_id": "bpp.energy-provider.com",
    "bpp_uri": "https://bpp.energy-provider.com",
    "domain": "beckn.one:deg:p2p-trading:2.0.0"
  },
  "message": {
    "order": {
      "@type": "beckn:Order",
      "beckn:orderStatus": "CREATED",
      "beckn:seller": "provider-solar-farm-001"
    }
  }
}`)

func TestSignAndVerifyRoundTrip(t *testing.T) {
	// --- Sign ---
	s, err := New(Config{
		SubscriberID:     testSubscriberID,
		UniqueKeyID:      testKeyID,
		SigningPrivateKey: testPrivateKey,
	})
	if err != nil {
		t.Fatalf("New() error: %v", err)
	}

	authHeader, err := s.SignPayload(samplePayload)
	if err != nil {
		t.Fatalf("SignPayload() error: %v", err)
	}

	// Basic structure checks
	if !strings.HasPrefix(authHeader, "Signature ") {
		t.Errorf("expected header to start with 'Signature ', got: %s", authHeader)
	}
	if !strings.Contains(authHeader, testSubscriberID+"|"+testKeyID+"|ed25519") {
		t.Errorf("keyId not found in header: %s", authHeader)
	}
	if !strings.Contains(authHeader, `algorithm="ed25519"`) {
		t.Errorf("algorithm not found in header: %s", authHeader)
	}

	t.Logf("Authorization: %s", authHeader)

	// --- Verify ---
	err = Verify(samplePayload, authHeader, testPublicKey)
	if err != nil {
		t.Fatalf("Verify() error: %v", err)
	}
}

func TestSignPayloadDetailed(t *testing.T) {
	s, err := New(Config{
		SubscriberID:     testSubscriberID,
		UniqueKeyID:      testKeyID,
		SigningPrivateKey: testPrivateKey,
	})
	if err != nil {
		t.Fatalf("New() error: %v", err)
	}

	result, err := s.SignPayloadDetailed(samplePayload)
	if err != nil {
		t.Fatalf("SignPayloadDetailed() error: %v", err)
	}

	if result.ExpiresAt-result.CreatedAt != 300 {
		t.Errorf("expected 300s expiry window, got %d", result.ExpiresAt-result.CreatedAt)
	}
	if result.Signature == "" {
		t.Error("expected non-empty signature")
	}
	if result.AuthorizationHeader == "" {
		t.Error("expected non-empty auth header")
	}
}

func TestVerifyRejectsTamperedPayload(t *testing.T) {
	s, err := New(Config{
		SubscriberID:     testSubscriberID,
		UniqueKeyID:      testKeyID,
		SigningPrivateKey: testPrivateKey,
	})
	if err != nil {
		t.Fatalf("New() error: %v", err)
	}

	authHeader, err := s.SignPayload(samplePayload)
	if err != nil {
		t.Fatalf("SignPayload() error: %v", err)
	}

	// Tamper with payload
	tampered := append([]byte{}, samplePayload...)
	tampered[10] = 'X'

	err = Verify(tampered, authHeader, testPublicKey)
	if err == nil {
		t.Fatal("expected verification to fail for tampered payload")
	}
}

func TestVerifyRejectsExpiredSignature(t *testing.T) {
	s, err := New(Config{
		SubscriberID:     testSubscriberID,
		UniqueKeyID:      testKeyID,
		SigningPrivateKey: testPrivateKey,
		ExpiryDuration:   1 * time.Second,
	})
	if err != nil {
		t.Fatalf("New() error: %v", err)
	}

	// Sign at a time in the past
	pastTime := time.Now().Add(-10 * time.Minute)
	result, err := s.signPayloadAt(samplePayload, pastTime)
	if err != nil {
		t.Fatalf("signPayloadAt() error: %v", err)
	}

	err = Verify(samplePayload, result.AuthorizationHeader, testPublicKey)
	if err == nil {
		t.Fatal("expected verification to fail for expired signature")
	}
	if !strings.Contains(err.Error(), "expired") {
		t.Errorf("expected 'expired' in error, got: %v", err)
	}
}

func TestVerifyRejectsWrongPublicKey(t *testing.T) {
	s, err := New(Config{
		SubscriberID:     testSubscriberID,
		UniqueKeyID:      testKeyID,
		SigningPrivateKey: testPrivateKey,
	})
	if err != nil {
		t.Fatalf("New() error: %v", err)
	}

	authHeader, err := s.SignPayload(samplePayload)
	if err != nil {
		t.Fatalf("SignPayload() error: %v", err)
	}

	// Use a different key pair
	_, wrongPriv, _ := ed25519.GenerateKey(nil)
	wrongPub := wrongPriv.Public().(ed25519.PublicKey)
	wrongPubB64 := base64.StdEncoding.EncodeToString(wrongPub)

	err = Verify(samplePayload, authHeader, wrongPubB64)
	if err == nil {
		t.Fatal("expected verification to fail for wrong public key")
	}
}

func TestNewValidatesConfig(t *testing.T) {
	tests := []struct {
		name string
		cfg  Config
		want string
	}{
		{"missing subscriber", Config{UniqueKeyID: "k", SigningPrivateKey: testPrivateKey}, "SubscriberID"},
		{"missing keyID", Config{SubscriberID: "s", SigningPrivateKey: testPrivateKey}, "UniqueKeyID"},
		{"missing private key", Config{SubscriberID: "s", UniqueKeyID: "k"}, "SigningPrivateKey"},
		{"bad base64", Config{SubscriberID: "s", UniqueKeyID: "k", SigningPrivateKey: "not-base64!!!"}, "invalid base64"},
		{"wrong key size", Config{SubscriberID: "s", UniqueKeyID: "k", SigningPrivateKey: base64.StdEncoding.EncodeToString([]byte("short"))}, "must be 32 bytes"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := New(tt.cfg)
			if err == nil {
				t.Fatal("expected error")
			}
			if !strings.Contains(err.Error(), tt.want) {
				t.Errorf("expected error containing %q, got: %v", tt.want, err)
			}
		})
	}
}

func TestParseKeyID(t *testing.T) {
	sub, key, alg, err := ParseKeyID("p2p-trading-sandbox1.com|76EU8aUq|ed25519")
	if err != nil {
		t.Fatalf("ParseKeyID() error: %v", err)
	}
	if sub != "p2p-trading-sandbox1.com" || key != "76EU8aUq" || alg != "ed25519" {
		t.Errorf("unexpected result: %s, %s, %s", sub, key, alg)
	}

	_, _, _, err = ParseKeyID("bad-format")
	if err == nil {
		t.Fatal("expected error for bad format")
	}
}
