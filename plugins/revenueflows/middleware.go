package revenueflows

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/open-policy-agent/opa/v1/rego"
)

// NewMiddleware returns an HTTP middleware that computes revenue flows
// and injects them into the request body before passing to the next handler.
func NewMiddleware(cfg map[string]string) (func(http.Handler) http.Handler, error) {
	config, err := ParseConfig(cfg)
	if err != nil {
		return nil, fmt.Errorf("revenueflows: config: %w", err)
	}

	cache := NewPolicyCache(
		config.MaxCacheEntries,
		config.CacheTTL,
		config.PolicyFetchTimeout,
		config.MaxPolicySize,
	)

	fmt.Printf("[RevenueFlows] Middleware enabled=%v, actions=%v, cacheTTL=%s\n",
		config.Enabled, config.Actions, config.CacheTTL)

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !config.Enabled {
				next.ServeHTTP(w, r)
				return
			}

			// Read body
			body, err := io.ReadAll(r.Body)
			if err != nil {
				next.ServeHTTP(w, r)
				return
			}

			// Check action
			action := extractActionFromPathAndBody(r.URL.Path, body)
			if !config.IsActionEnabled(action) {
				// Pass through unchanged
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			// Extract policy reference
			ref := ExtractPolicyRef(body)
			if ref == nil {
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			if !config.IsDomainAllowed(ref.URL) {
				fmt.Printf("[RevenueFlows] WARN: policy URL domain not allowed: %s\n", ref.URL)
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			if config.DebugLogging {
				fmt.Printf("[RevenueFlows] Evaluating %s with query %s\n", ref.URL, ref.QueryPath)
			}

			// Get or compile policy
			pq, err := cache.GetOrCompile(r.Context(), ref.URL, ref.QueryPath)
			if err != nil {
				fmt.Printf("[RevenueFlows] WARN: failed to load policy: %v\n", err)
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			// Parse as OPA input
			var input interface{}
			if err := json.Unmarshal(body, &input); err != nil {
				fmt.Printf("[RevenueFlows] WARN: failed to parse body: %v\n", err)
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			// Evaluate
			rs, err := pq.Eval(r.Context(), regoEvalInput(input))
			if err != nil {
				fmt.Printf("[RevenueFlows] WARN: rego eval failed: %v\n", err)
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			flows := extractFlowsFromResultSet(rs)
			if flows == nil {
				if config.DebugLogging {
					fmt.Printf("[RevenueFlows] No revenue_flows in result, skipping\n")
				}
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			// Inject into body
			modified, err := InjectRevenueFlows(body, flows)
			if err != nil {
				fmt.Printf("[RevenueFlows] WARN: inject failed: %v\n", err)
				r.Body = io.NopCloser(bytes.NewReader(body))
				r.ContentLength = int64(len(body))
				next.ServeHTTP(w, r)
				return
			}

			fmt.Printf("[RevenueFlows] Injected %d revenue flow(s) for action %s\n", len(flows), action)

			// Pass modified body to next handler
			r.Body = io.NopCloser(bytes.NewReader(modified))
			r.ContentLength = int64(len(modified))
			next.ServeHTTP(w, r)
		})
	}, nil
}

// regoEvalInput wraps input for OPA evaluation.
func regoEvalInput(input interface{}) rego.EvalOption {
	return rego.EvalInput(input)
}

// extractFlowsFromResultSet pulls revenue_flows from OPA result.
func extractFlowsFromResultSet(rs rego.ResultSet) []interface{} {
	return extractFlows(rs)
}

// extractActionFromPathAndBody extracts action from URL path or body.
func extractActionFromPathAndBody(urlPath string, body []byte) string {
	parts := strings.Split(strings.TrimRight(urlPath, "/"), "/")
	if len(parts) > 0 {
		action := parts[len(parts)-1]
		if action != "" && action != "caller" && action != "receiver" {
			return action
		}
	}
	var envelope struct {
		Context struct {
			Action string `json:"action"`
		} `json:"context"`
	}
	if err := json.Unmarshal(body, &envelope); err == nil && envelope.Context.Action != "" {
		return envelope.Context.Action
	}
	return ""
}
