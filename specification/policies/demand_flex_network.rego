# DEG Network Policy — Demand Flex (noop)
#
# Placeholder network policy for demand-flex devkit.
# Imposes no additional network-level constraints.
# All messages pass validation.
#
# Must use package deg.policy and rule "violations" — onix policyenforcer
# queries data.deg.policy.violations (same contract as p2p-trading-interdiscom.rego).
#
# Replace with real rules as the demand-flex network matures.

package deg.policy

import rego.v1

# No violations — all messages pass.
violations contains msg if {
	false
}
