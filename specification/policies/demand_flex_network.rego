# DEG Network Policy — Demand Flex (noop)
#
# Placeholder network policy for demand-flex devkit.
# Imposes no additional network-level constraints.
# All messages pass validation.
#
# Replace with real rules as the demand-flex network matures.

package deg.policy.demand_flex_network

import rego.v1

# No violations — all messages pass.
violations := set()
