package revenueflows

import (
	"strconv"
	"strings"
	"time"
)

// Config holds configuration for the RevenueFlows plugin.
type Config struct {
	// Enabled controls whether the plugin is active.
	Enabled bool

	// Actions is the list of beckn actions that trigger revenue flow computation.
	// Default: ["on_status"]
	Actions []string

	// CacheTTL is how long a compiled rego policy is cached before re-fetch.
	// Default: 5 minutes.
	CacheTTL time.Duration

	// MaxCacheEntries is the LRU bound on cached compiled policies.
	// Default: 50.
	MaxCacheEntries int

	// PolicyFetchTimeout is the HTTP timeout for fetching rego from a URL.
	// Default: 30 seconds.
	PolicyFetchTimeout time.Duration

	// MaxPolicySize is the maximum rego file size in bytes.
	// Default: 1 MB.
	MaxPolicySize int64

	// DebugLogging enables verbose logging.
	DebugLogging bool

	// AllowedDomains restricts which domains rego can be fetched from.
	// Empty = allow all. Comma-separated list.
	AllowedDomains []string
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		Enabled:            true,
		Actions:            []string{"on_status"},
		CacheTTL:           5 * time.Minute,
		MaxCacheEntries:    50,
		PolicyFetchTimeout: 30 * time.Second,
		MaxPolicySize:      1 << 20, // 1 MB
		DebugLogging:       false,
	}
}

// ParseConfig parses the plugin configuration map.
func ParseConfig(cfg map[string]string) (*Config, error) {
	config := DefaultConfig()

	if enabled, ok := cfg["enabled"]; ok {
		config.Enabled = enabled == "true" || enabled == "1"
	}

	if actions, ok := cfg["actions"]; ok && actions != "" {
		list := strings.Split(actions, ",")
		config.Actions = make([]string, 0, len(list))
		for _, a := range list {
			a = strings.TrimSpace(a)
			if a != "" {
				config.Actions = append(config.Actions, a)
			}
		}
	}

	if ttl, ok := cfg["cacheTTL"]; ok && ttl != "" {
		seconds, err := strconv.Atoi(ttl)
		if err != nil {
			d, err2 := time.ParseDuration(ttl)
			if err2 != nil {
				return nil, err
			}
			config.CacheTTL = d
		} else {
			config.CacheTTL = time.Duration(seconds) * time.Second
		}
	}

	if max, ok := cfg["maxCacheEntries"]; ok && max != "" {
		n, err := strconv.Atoi(max)
		if err != nil {
			return nil, err
		}
		config.MaxCacheEntries = n
	}

	if debug, ok := cfg["debugLogging"]; ok {
		config.DebugLogging = debug == "true" || debug == "1"
	}

	if domains, ok := cfg["allowedDomains"]; ok && domains != "" {
		for _, d := range strings.Split(domains, ",") {
			d = strings.TrimSpace(d)
			if d != "" {
				config.AllowedDomains = append(config.AllowedDomains, d)
			}
		}
	}

	return config, nil
}

// IsActionEnabled checks if the given action is in the configured list.
func (c *Config) IsActionEnabled(action string) bool {
	for _, a := range c.Actions {
		if a == action {
			return true
		}
	}
	return false
}

// IsDomainAllowed checks if the URL domain is in the allowed list.
// Returns true if no domain restriction is configured.
func (c *Config) IsDomainAllowed(url string) bool {
	if len(c.AllowedDomains) == 0 {
		return true
	}
	for _, d := range c.AllowedDomains {
		if strings.Contains(url, d) {
			return true
		}
	}
	return false
}
