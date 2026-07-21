package deg.policy.p2p_trading_network

import rego.v1

# ----------------------------------------------------------------------------
# Tests for N1 role-completeness gating: the rule fires only when
# contractAttributes.roles is non-empty. Discom-internal contracts that carry no
# roles (and no participants) must pass; a partial roles list must still fail.
# ----------------------------------------------------------------------------

_all_roles := [
	{"role": "buyerPlatform"},
	{"role": "sellerPlatform"},
	{"role": "buyerDiscom"},
	{"role": "sellerDiscom"},
]

_payload(contract) := {
	"context": {"version": "2.0.0", "networkId": "indiaenergystack.in/test-ies-p2p-trading-network"},
	"message": {"contract": contract},
}

_has_missing_roles(pl) if {
	some msg in violations with input as pl
	startswith(msg, "missing required role(s)")
}

# Discom-internal on_status: a contract with no roles and no participants must
# not trip N1.
test_n1_skipped_when_no_roles if {
	pl := _payload({"commitments": [{"status": {"descriptor": {"code": "ACTIVE"}}}]})
	not _has_missing_roles(pl)
}

# An explicitly empty roles array is likewise not a trade-scope contract.
test_n1_skipped_when_roles_empty if {
	pl := _payload({"contractAttributes": {"roles": []}})
	not _has_missing_roles(pl)
}

# A full four-role contract passes N1.
test_n1_passes_when_all_roles_present if {
	pl := _payload({"contractAttributes": {"roles": _all_roles}})
	not _has_missing_roles(pl)
}

# A partial roles list still fails — completeness is enforced once any role is
# declared.
test_n1_fails_when_roles_partial if {
	pl := _payload({"contractAttributes": {"roles": [{"role": "buyerPlatform"}, {"role": "sellerPlatform"}]}})
	_has_missing_roles(pl)
}
