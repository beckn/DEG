// Package revenueflows is an onix Step plugin that computes revenue flows
// from a rego policy embedded in the contract and injects them into the message.
//
// It reads the policy URL and query path from
// message.contract.contractAttributes.policy, evaluates the rego against
// the full message, and writes the resulting revenue_flows array back into
// contractAttributes.revenueFlows.
//
// Soft failure: if anything goes wrong (fetch, compile, eval), the message
// passes through unmodified with a warning log. Never blocks delivery.
package revenueflows

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/beckn-one/beckn-onix/pkg/log"
	"github.com/beckn-one/beckn-onix/pkg/model"
	"github.com/open-policy-agent/opa/v1/rego"
)

// RevenueFlows is a Step plugin that computes and injects revenue flows.
type RevenueFlows struct {
	config *Config
	cache  *PolicyCache
}

// New creates a new RevenueFlows plugin instance.
func New(cfg map[string]string) (*RevenueFlows, error) {
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

	fmt.Printf("[RevenueFlows] Enabled=%v, actions=%v, cacheTTL=%s\n",
		config.Enabled, config.Actions, config.CacheTTL)

	return &RevenueFlows{config: config, cache: cache}, nil
}

// Run implements the Step interface.
func (rf *RevenueFlows) Run(ctx *model.StepContext) error {
	if !rf.config.Enabled {
		return nil
	}

	// Check action
	action := ExtractAction(ctx.Request.URL.Path, ctx.Body)
	if !rf.config.IsActionEnabled(action) {
		if rf.config.DebugLogging {
			log.Debugf(ctx, "RevenueFlows: action '%s' not enabled, skipping", action)
		}
		return nil
	}

	// Extract policy reference from the message
	ref := ExtractPolicyRef(ctx.Body)
	if ref == nil {
		if rf.config.DebugLogging {
			log.Debug(ctx, "RevenueFlows: no contractAttributes.policy in message, skipping")
		}
		return nil
	}

	// Check domain allowlist
	if !rf.config.IsDomainAllowed(ref.URL) {
		log.Warnf(ctx, "RevenueFlows: policy URL domain not allowed: %s", ref.URL)
		return nil
	}

	if rf.config.DebugLogging {
		log.Debugf(ctx, "RevenueFlows: evaluating %s with query %s", ref.URL, ref.QueryPath)
	}

	// Get or compile the policy
	pq, err := rf.cache.GetOrCompile(context.Background(), ref.URL, ref.QueryPath)
	if err != nil {
		log.Warnf(ctx, "RevenueFlows: failed to load policy: %v", err)
		return nil // soft failure
	}

	// Parse message as OPA input
	var input interface{}
	if err := json.Unmarshal(ctx.Body, &input); err != nil {
		log.Warnf(ctx, "RevenueFlows: failed to parse message body: %v", err)
		return nil
	}

	// Evaluate
	rs, err := pq.Eval(context.Background(), rego.EvalInput(input))
	if err != nil {
		log.Warnf(ctx, "RevenueFlows: rego evaluation failed: %v", err)
		return nil // soft failure
	}

	// Extract revenue_flows from result
	flows := extractFlows(rs)
	if flows == nil {
		if rf.config.DebugLogging {
			log.Debug(ctx, "RevenueFlows: no revenue_flows in rego result, skipping injection")
		}
		return nil
	}

	// Inject into message body
	modified, err := InjectRevenueFlows(ctx.Body, flows)
	if err != nil {
		log.Warnf(ctx, "RevenueFlows: failed to inject revenue_flows: %v", err)
		return nil // soft failure
	}

	ctx.Body = modified
	log.Infof(ctx, "RevenueFlows: injected %d revenue flow(s)", len(flows))
	return nil
}

// Close is a no-op cleanup function.
func (rf *RevenueFlows) Close() {}

// extractFlows pulls revenue_flows from the OPA result set.
// The query evaluates to the full package object; we look for the
// "revenue_flows" key within it.
func extractFlows(rs rego.ResultSet) []interface{} {
	if len(rs) == 0 || len(rs[0].Expressions) == 0 {
		return nil
	}

	val := rs[0].Expressions[0].Value

	// If the query returns the full package, result is a map
	if m, ok := val.(map[string]interface{}); ok {
		if flows, ok := m["revenue_flows"].([]interface{}); ok {
			return flows
		}
		return nil
	}

	// If the query targets revenue_flows directly, result is an array
	if flows, ok := val.([]interface{}); ok {
		return flows
	}

	return nil
}
