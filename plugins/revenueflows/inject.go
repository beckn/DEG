package revenueflows

import (
	"encoding/json"
	"fmt"
	"strings"
)

// PolicyRef holds the policy URL and OPA query path extracted from a message.
type PolicyRef struct {
	URL       string
	QueryPath string
}

// ExtractPolicyRef reads contractAttributes.policy.url and .queryPath from
// the message body. Returns nil if not present.
func ExtractPolicyRef(body []byte) *PolicyRef {
	var envelope struct {
		Message struct {
			Contract struct {
				ContractAttributes struct {
					Policy struct {
						URL       string `json:"url"`
						QueryPath string `json:"queryPath"`
					} `json:"policy"`
				} `json:"contractAttributes"`
			} `json:"contract"`
		} `json:"message"`
	}

	if err := json.Unmarshal(body, &envelope); err != nil {
		return nil
	}

	url := envelope.Message.Contract.ContractAttributes.Policy.URL
	qp := envelope.Message.Contract.ContractAttributes.Policy.QueryPath
	if url == "" || qp == "" {
		return nil
	}

	return &PolicyRef{URL: url, QueryPath: qp}
}

// ExtractAction reads the beckn action from the URL path or context.action.
func ExtractAction(urlPath string, body []byte) string {
	// Try URL path first (e.g., /bpp/caller/on_status → on_status)
	parts := strings.Split(strings.TrimRight(urlPath, "/"), "/")
	if len(parts) > 0 {
		action := parts[len(parts)-1]
		if action != "" && action != "caller" && action != "receiver" {
			return action
		}
	}

	// Fallback: parse context.action from body
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

// InjectRevenueFlows sets message.contract.contractAttributes.revenueFlows
// in the JSON body and returns the modified bytes.
// Uses json.Number to preserve numeric precision.
func InjectRevenueFlows(body []byte, flows interface{}) ([]byte, error) {
	// Use Decoder with UseNumber to preserve numeric precision
	dec := json.NewDecoder(strings.NewReader(string(body)))
	dec.UseNumber()

	var payload map[string]interface{}
	if err := dec.Decode(&payload); err != nil {
		return nil, fmt.Errorf("failed to decode body: %w", err)
	}

	// Navigate: message → contract → contractAttributes
	message, ok := payload["message"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("message not found or not an object")
	}
	contract, ok := message["contract"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("message.contract not found or not an object")
	}
	attrs, ok := contract["contractAttributes"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("contractAttributes not found or not an object")
	}

	// Inject
	attrs["revenueFlows"] = flows

	return json.Marshal(payload)
}
