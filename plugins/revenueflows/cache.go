package revenueflows

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"github.com/open-policy-agent/opa/v1/ast"
	"github.com/open-policy-agent/opa/v1/rego"
)

// cacheEntry holds a compiled OPA query and its metadata.
type cacheEntry struct {
	pq        rego.PreparedEvalQuery
	query     string
	fetchedAt time.Time
}

// PolicyCache is a TTL-based LRU cache for compiled rego policies.
// Keyed by policy URL.
type PolicyCache struct {
	mu      sync.RWMutex
	entries map[string]*cacheEntry
	maxSize int
	ttl     time.Duration

	fetchTimeout time.Duration
	maxFileSize  int64
}

// NewPolicyCache creates a new cache.
func NewPolicyCache(maxSize int, ttl, fetchTimeout time.Duration, maxFileSize int64) *PolicyCache {
	return &PolicyCache{
		entries:      make(map[string]*cacheEntry),
		maxSize:      maxSize,
		ttl:          ttl,
		fetchTimeout: fetchTimeout,
		maxFileSize:  maxFileSize,
	}
}

// GetOrCompile returns a compiled query for the given policy URL and OPA query path.
// Fetches and compiles on cache miss or TTL expiry.
func (c *PolicyCache) GetOrCompile(ctx context.Context, url, query string) (rego.PreparedEvalQuery, error) {
	c.mu.RLock()
	entry, ok := c.entries[url]
	c.mu.RUnlock()

	if ok && entry.query == query && time.Since(entry.fetchedAt) < c.ttl {
		return entry.pq, nil
	}

	// Cache miss or expired — fetch and compile
	return c.fetchAndCompile(ctx, url, query)
}

func (c *PolicyCache) fetchAndCompile(ctx context.Context, url, query string) (rego.PreparedEvalQuery, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Double-check after acquiring write lock
	if entry, ok := c.entries[url]; ok && entry.query == query && time.Since(entry.fetchedAt) < c.ttl {
		return entry.pq, nil
	}

	// Fetch rego source from URL
	source, err := c.fetchPolicy(ctx, url)
	if err != nil {
		return rego.PreparedEvalQuery{}, fmt.Errorf("fetch %s: %w", url, err)
	}

	// Compile
	compiler, err := ast.CompileModulesWithOpt(map[string]string{"policy.rego": source}, ast.CompileOpts{})
	if err != nil {
		return rego.PreparedEvalQuery{}, fmt.Errorf("compile %s: %w", url, err)
	}

	pq, err := rego.New(
		rego.Query(query),
		rego.Compiler(compiler),
	).PrepareForEval(ctx)
	if err != nil {
		return rego.PreparedEvalQuery{}, fmt.Errorf("prepare query %s: %w", query, err)
	}

	// Evict oldest if at capacity
	if len(c.entries) >= c.maxSize {
		var oldestKey string
		var oldestTime time.Time
		for k, v := range c.entries {
			if oldestKey == "" || v.fetchedAt.Before(oldestTime) {
				oldestKey = k
				oldestTime = v.fetchedAt
			}
		}
		if oldestKey != "" {
			delete(c.entries, oldestKey)
		}
	}

	c.entries[url] = &cacheEntry{pq: pq, query: query, fetchedAt: time.Now()}
	return pq, nil
}

func (c *PolicyCache) fetchPolicy(ctx context.Context, url string) (string, error) {
	reqCtx, cancel := context.WithTimeout(ctx, c.fetchTimeout)
	defer cancel()

	req, err := http.NewRequestWithContext(reqCtx, http.MethodGet, url, nil)
	if err != nil {
		return "", err
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("HTTP %d from %s", resp.StatusCode, url)
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, c.maxFileSize))
	if err != nil {
		return "", err
	}

	return string(body), nil
}
