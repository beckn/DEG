package degledgerrecorder

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestRewriteContextForBeckn_Wave2CamelCase(t *testing.T) {
	body := []byte(sampleWave2OnConfirm)
	out, err := RewriteContextForBeckn(body, "https://bap.example.com", "https://ies-p2p-energy-ledger.beckn.io")
	if err != nil {
		t.Fatalf("rewrite: %v", err)
	}
	var got map[string]interface{}
	if err := json.Unmarshal(out, &got); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	ctx := got["context"].(map[string]interface{})

	if v := ctx["bppUri"]; v != "https://bap.example.com/bpp/caller" {
		t.Errorf("bppUri: got %v", v)
	}
	if v := ctx["bapUri"]; v != "https://ies-p2p-energy-ledger.beckn.io/bap/receiver" {
		t.Errorf("bapUri: got %v", v)
	}
	// Other fields preserved
	if v := ctx["transactionId"]; v != "txn-p2p-001" {
		t.Errorf("transactionId clobbered: got %v", v)
	}
	if v := ctx["bapId"]; v != "bap.example.com" {
		t.Errorf("bapId clobbered: got %v", v)
	}
}

func TestRewriteContextForBeckn_TrimsTrailingSlashes(t *testing.T) {
	body := []byte(sampleWave2OnConfirm)
	out, err := RewriteContextForBeckn(body, "https://bap.example.com/", "https://ledger.example.com//")
	if err != nil {
		t.Fatalf("rewrite: %v", err)
	}
	var got map[string]interface{}
	_ = json.Unmarshal(out, &got)
	ctx := got["context"].(map[string]interface{})
	if v := ctx["bppUri"]; v != "https://bap.example.com/bpp/caller" {
		t.Errorf("bppUri trim failed: got %v", v)
	}
	if v := ctx["bapUri"]; v != "https://ledger.example.com/bap/receiver" {
		t.Errorf("bapUri trim failed: got %v", v)
	}
}

func TestRewriteContextForBeckn_SnakeCaseFallback(t *testing.T) {
	// Wave1-style snake_case context — rewrite must operate on bpp_uri/bap_uri.
	body := []byte(`{"context":{"bpp_uri":"https://x","bap_uri":"https://y","transaction_id":"t1"},"message":{"order":{}}}`)
	out, err := RewriteContextForBeckn(body, "https://sender.com", "https://ledger.com")
	if err != nil {
		t.Fatalf("rewrite: %v", err)
	}
	var got map[string]interface{}
	_ = json.Unmarshal(out, &got)
	ctx := got["context"].(map[string]interface{})
	if v := ctx["bpp_uri"]; v != "https://sender.com/bpp/caller" {
		t.Errorf("bpp_uri: got %v", v)
	}
	if v := ctx["bap_uri"]; v != "https://ledger.com/bap/receiver" {
		t.Errorf("bap_uri: got %v", v)
	}
	// Camel keys must NOT have been added.
	if _, present := ctx["bppUri"]; present {
		t.Errorf("rewrite leaked camel-case bppUri into snake-case payload")
	}
}

func TestRewriteContextForBeckn_MissingContextErrors(t *testing.T) {
	if _, err := RewriteContextForBeckn([]byte(`{}`), "h", "l"); err == nil {
		t.Errorf("expected error on missing context")
	}
}

func TestDeriveSenderHostFromWave2(t *testing.T) {
	p, err := ParseOnConfirmWave2([]byte(sampleWave2OnConfirm))
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if got := DeriveSenderHostFromWave2(p, "BUYER"); got != "https://bap.example.com" {
		t.Errorf("BUYER: got %q", got)
	}
	if got := DeriveSenderHostFromWave2(p, "SELLER"); got != "https://bpp.example.com" {
		t.Errorf("SELLER: got %q", got)
	}
	if got := DeriveSenderHostFromWave2(p, "BUYER_DISCOM"); got != "" {
		t.Errorf("unrecognized role: got %q, want empty", got)
	}
}

func TestDeriveSenderHostFromWave2_MalformedURI(t *testing.T) {
	p := &Wave2OnConfirmPayload{}
	p.Context.BapURI = "not-a-uri"
	if got := DeriveSenderHostFromWave2(p, "BUYER"); got != "" {
		t.Errorf("expected empty for unparseable URI, got %q", got)
	}
}

// Smoke: when senderHost is missing, the recorder must skip with a warning
// rather than POST garbage. We exercise that branch indirectly via the
// helpers — recorder logic is small and reads the same fields here.
func TestDeriveSenderHost_MissingURIInPayload(t *testing.T) {
	p := &Wave2OnConfirmPayload{}
	if got := DeriveSenderHostFromWave2(p, "BUYER"); got != "" {
		t.Errorf("expected empty when bapUri missing, got %q", got)
	}
	if got := DeriveSenderHostFromWave2(p, "SELLER"); got != "" {
		t.Errorf("expected empty when bppUri missing, got %q", got)
	}
}

// Defensive: rewrite leaves message untouched verbatim.
func TestRewriteContextForBeckn_MessagePreserved(t *testing.T) {
	body := []byte(sampleWave2OnConfirm)
	out, err := RewriteContextForBeckn(body, "https://x", "https://y")
	if err != nil {
		t.Fatalf("rewrite: %v", err)
	}
	if !strings.Contains(string(out), `"commitment-p2p-001"`) {
		t.Errorf("rewrite dropped or altered message body")
	}
	if !strings.Contains(string(out), `"der://meter/buyer-001"`) {
		t.Errorf("rewrite dropped participant attributes")
	}
}
