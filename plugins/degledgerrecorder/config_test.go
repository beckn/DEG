package degledgerrecorder

import (
	"strings"
	"testing"
)

// baseValidCfg returns a minimal valid config map for a wave2/payload setup.
func baseValidCfg() map[string]string {
	return map[string]string{
		"payloadShape":    "wave2",
		"ledgerUriSource": "payload",
		"ledgerApi":       "legacy_ledger",
	}
}

func TestParseConfig_RequiresPayloadShape(t *testing.T) {
	cfg := baseValidCfg()
	delete(cfg, "payloadShape")
	if _, err := ParseConfig(cfg); err == nil {
		t.Fatalf("expected error when payloadShape is missing")
	}
}

func TestParseConfig_RequiresLedgerUriSource(t *testing.T) {
	cfg := baseValidCfg()
	delete(cfg, "ledgerUriSource")
	if _, err := ParseConfig(cfg); err == nil {
		t.Fatalf("expected error when ledgerUriSource is missing")
	}
}

func TestParseConfig_RequiresLedgerApi(t *testing.T) {
	cfg := baseValidCfg()
	delete(cfg, "ledgerApi")
	if _, err := ParseConfig(cfg); err == nil {
		t.Fatalf("expected error when ledgerApi is missing")
	}
}

func TestParseConfig_RejectsInvalidValues(t *testing.T) {
	cases := []struct {
		key, val string
	}{
		{"payloadShape", "wave99"},
		{"ledgerUriSource", "elsewhere"},
		{"ledgerApi", "rest"},
	}
	for _, c := range cases {
		cfg := baseValidCfg()
		cfg[c.key] = c.val
		_, err := ParseConfig(cfg)
		if err == nil {
			t.Errorf("expected error for %s=%s", c.key, c.val)
			continue
		}
		if !strings.Contains(err.Error(), c.key) {
			t.Errorf("error %q should mention %q", err.Error(), c.key)
		}
	}
}

func TestParseConfig_LedgerHostRequiredWhenSourceConfig(t *testing.T) {
	cfg := baseValidCfg()
	cfg["ledgerUriSource"] = "config"
	if _, err := ParseConfig(cfg); err == nil {
		t.Fatalf("expected error when ledgerUriSource=config and ledgerHost is empty")
	}

	cfg["ledgerHost"] = "https://ledger.example.com"
	got, err := ParseConfig(cfg)
	if err != nil {
		t.Fatalf("unexpected error with ledgerHost set: %v", err)
	}
	if got.LedgerHost != "https://ledger.example.com" {
		t.Errorf("LedgerHost: got %q", got.LedgerHost)
	}
}

func TestParseConfig_LedgerHostNotRequiredWhenSourcePayload(t *testing.T) {
	cfg := baseValidCfg() // ledgerUriSource=payload, no ledgerHost
	got, err := ParseConfig(cfg)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.LedgerHost != "" {
		t.Errorf("expected empty LedgerHost, got %q", got.LedgerHost)
	}
}

func TestParseConfig_AcceptsAllValidCombos(t *testing.T) {
	combos := []map[string]string{
		{"payloadShape": "wave1", "ledgerUriSource": "config", "ledgerApi": "legacy_ledger", "ledgerHost": "https://x"},
		{"payloadShape": "wave2", "ledgerUriSource": "payload", "ledgerApi": "legacy_ledger"},
		{"payloadShape": "wave2", "ledgerUriSource": "payload", "ledgerApi": "beckn"},
		{"payloadShape": "wave1", "ledgerUriSource": "config", "ledgerApi": "beckn", "ledgerHost": "https://x"},
	}
	for _, cfg := range combos {
		if _, err := ParseConfig(cfg); err != nil {
			t.Errorf("combo %+v should parse cleanly, got %v", cfg, err)
		}
	}
}
