package revenueflows

import (
	"encoding/json"
	"testing"
)

// ---------------------------------------------------------------------------
// ExtractPolicyRef tests
// ---------------------------------------------------------------------------

func TestExtractPolicyRef_Present(t *testing.T) {
	body := []byte(`{
		"message": {
			"contract": {
				"contractAttributes": {
					"policy": {
						"url": "https://example.com/policy.rego",
						"queryPath": "data.test.violations"
					}
				}
			}
		}
	}`)

	ref := ExtractPolicyRef(body)
	if ref == nil {
		t.Fatal("expected non-nil PolicyRef")
	}
	if ref.URL != "https://example.com/policy.rego" {
		t.Errorf("URL = %q, want %q", ref.URL, "https://example.com/policy.rego")
	}
	if ref.QueryPath != "data.test.violations" {
		t.Errorf("QueryPath = %q, want %q", ref.QueryPath, "data.test.violations")
	}
}

func TestExtractPolicyRef_Missing(t *testing.T) {
	body := []byte(`{"message": {"contract": {}}}`)
	ref := ExtractPolicyRef(body)
	if ref != nil {
		t.Errorf("expected nil PolicyRef, got %+v", ref)
	}
}

func TestExtractPolicyRef_PartialMissing(t *testing.T) {
	body := []byte(`{
		"message": {
			"contract": {
				"contractAttributes": {
					"policy": { "url": "https://example.com/policy.rego" }
				}
			}
		}
	}`)
	ref := ExtractPolicyRef(body)
	if ref != nil {
		t.Errorf("expected nil PolicyRef when queryPath missing, got %+v", ref)
	}
}

// ---------------------------------------------------------------------------
// ExtractAction tests
// ---------------------------------------------------------------------------

func TestExtractAction_FromPath(t *testing.T) {
	action := ExtractAction("/bpp/caller/on_status", nil)
	if action != "on_status" {
		t.Errorf("action = %q, want %q", action, "on_status")
	}
}

func TestExtractAction_FromBody(t *testing.T) {
	body := []byte(`{"context": {"action": "on_confirm"}}`)
	action := ExtractAction("/bpp/caller", body)
	if action != "on_confirm" {
		t.Errorf("action = %q, want %q", action, "on_confirm")
	}
}

// ---------------------------------------------------------------------------
// InjectRevenueFlows tests
// ---------------------------------------------------------------------------

func TestInjectRevenueFlows(t *testing.T) {
	body := []byte(`{
		"context": {"action": "on_status"},
		"message": {
			"contract": {
				"contractAttributes": {
					"@type": "DEGContract",
					"policy": {"url": "test", "queryPath": "test"}
				}
			}
		}
	}`)

	flows := []interface{}{
		map[string]interface{}{"role": "buyer", "value": -525.0, "currency": "INR"},
		map[string]interface{}{"role": "seller", "value": 525.0, "currency": "INR"},
	}

	result, err := InjectRevenueFlows(body, flows)
	if err != nil {
		t.Fatalf("InjectRevenueFlows failed: %v", err)
	}

	// Verify the result has revenueFlows
	var payload map[string]interface{}
	if err := json.Unmarshal(result, &payload); err != nil {
		t.Fatalf("failed to parse result: %v", err)
	}

	msg := payload["message"].(map[string]interface{})
	contract := msg["contract"].(map[string]interface{})
	attrs := contract["contractAttributes"].(map[string]interface{})
	rf, ok := attrs["revenueFlows"].([]interface{})
	if !ok {
		t.Fatal("revenueFlows not found or wrong type")
	}
	if len(rf) != 2 {
		t.Errorf("len(revenueFlows) = %d, want 2", len(rf))
	}

	// Verify existing fields preserved
	if attrs["@type"] != "DEGContract" {
		t.Errorf("@type lost after injection")
	}
}

func TestInjectRevenueFlows_NoContract(t *testing.T) {
	body := []byte(`{"message": {}}`)
	_, err := InjectRevenueFlows(body, []interface{}{})
	if err == nil {
		t.Error("expected error when contract missing")
	}
}

// ---------------------------------------------------------------------------
// Config tests
// ---------------------------------------------------------------------------

func TestParseConfig_Defaults(t *testing.T) {
	cfg, err := ParseConfig(map[string]string{})
	if err != nil {
		t.Fatalf("ParseConfig failed: %v", err)
	}
	if !cfg.Enabled {
		t.Error("expected Enabled=true by default")
	}
	if len(cfg.Actions) != 1 || cfg.Actions[0] != "on_status" {
		t.Errorf("Actions = %v, want [on_status]", cfg.Actions)
	}
}

func TestParseConfig_Custom(t *testing.T) {
	cfg, err := ParseConfig(map[string]string{
		"actions":         "on_status,on_confirm",
		"cacheTTL":        "600",
		"maxCacheEntries": "100",
		"debugLogging":    "true",
		"allowedDomains":  "raw.githubusercontent.com,schema.beckn.io",
	})
	if err != nil {
		t.Fatalf("ParseConfig failed: %v", err)
	}
	if len(cfg.Actions) != 2 {
		t.Errorf("Actions = %v, want 2 items", cfg.Actions)
	}
	if cfg.MaxCacheEntries != 100 {
		t.Errorf("MaxCacheEntries = %d, want 100", cfg.MaxCacheEntries)
	}
	if !cfg.DebugLogging {
		t.Error("expected DebugLogging=true")
	}
	if len(cfg.AllowedDomains) != 2 {
		t.Errorf("AllowedDomains = %v, want 2 items", cfg.AllowedDomains)
	}
}

func TestIsDomainAllowed(t *testing.T) {
	cfg := &Config{AllowedDomains: []string{"raw.githubusercontent.com"}}
	if !cfg.IsDomainAllowed("https://raw.githubusercontent.com/beckn/DEG/policy.rego") {
		t.Error("expected allowed")
	}
	if cfg.IsDomainAllowed("https://evil.com/policy.rego") {
		t.Error("expected blocked")
	}

	// Empty = allow all
	cfg2 := &Config{}
	if !cfg2.IsDomainAllowed("https://anything.com/policy.rego") {
		t.Error("expected allowed when no restrictions")
	}
}
