# P2P Trading Inter-DISCOM – Policy Rules & Tests

## Files

| File | Purpose |
|------|---------|
| `p2p-trading-interdiscom.rego` | Policy rules (domain, version, order, catalog, test-ID consistency) |
| `p2p-trading-interdiscom_test.rego` | OPA unit tests |

## Prerequisites

Install the [OPA CLI](https://www.openpolicyagent.org/docs/latest/#running-opa):

```bash
# macOS
brew install opa

# or download directly
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_darwin_arm64_static
chmod +x opa && sudo mv opa /usr/local/bin/
```

## Running the unit tests

```bash
cd specification/policies
opa test . -v
```

Expected output:

```
data.deg.policy.test_t1_all_real_ids_pass: PASS
data.deg.policy.test_t1_all_test_ids_pass: PASS
data.deg.policy.test_t1_provider_test_buyer_real_fail: PASS
data.deg.policy.test_t1_buyer_test_provider_real_fail: PASS
data.deg.policy.test_t1_buyer_test_provider_real_fail_utility: PASS
data.deg.policy.test_t1_buyer_wrong_test_meter_fail: PASS
data.deg.policy.test_t1_mixed_buyer_utility_fail: PASS
PASS: 7/7
```

## Evaluating a real payload

Use `opa eval` with an input JSON file against the `violations` rule:

```bash
opa eval \
  -d p2p-trading-interdiscom.rego \
  --input /path/to/input.json \
  'data.deg.policy.violations'
```

An empty array (`[]`) means the payload passes all rules. Any strings in the array are violation messages.

To filter for a specific rule category (e.g. test-ID consistency):

```bash
opa eval \
  -d p2p-trading-interdiscom.rego \
  --input /path/to/input.json \
  '[v | data.deg.policy.violations[v]; startswith(v, "test consistency:")]'
```

Use `jq` to patch an existing example inline without editing files:

```bash
POLICY=p2p-trading-interdiscom.rego
EXAMPLE=../../examples/p2p-trading-interdiscom/v2/confirm-request.json

opa eval -d "$POLICY" \
  --input <(jq '
    .message.order["beckn:buyer"]["beckn:buyerAttributes"].meterId = "TEST_SELLER_METER" |
    .message.order["beckn:orderItems"][0]["beckn:orderItemAttributes"].providerAttributes.utilityId = "PVVNL"
  ' "$EXAMPLE") \
  'data.deg.policy.violations'
```

## Rule summary

### Common (all actions)
| Rule | Description |
|------|-------------|
| C1 | `context.domain` must be `beckn.one:deg:p2p-trading-interdiscom:2.0.0` |
| C2 | `context.version` must be `2.0.0` |

### Order validation (when `message.order` exists)
| Rule | Description |
|------|-------------|
| O1 | Delivery window start must be ≥ `minDeliveryLeadHours` after `context.timestamp` (default 4h) |
| O2 | Validity window end must be ≥ `minDeliveryLeadHours` before delivery start |
| O4 | Buyer `meterId` must be non-empty and differ from every provider `meterId` |
| O5 | Ordered `unitQuantity` must be ≥ 0 and < offer `applicableQuantity` |
| O6 | `priceCurrency` must be `INR` |
| O7 | Quantity `unitText` must be `kWh` |
| O8 | `utilityCustomerId` and `utilityId` must be non-empty on buyer and every provider |
| O9–O12 | `@type` and `@context` must match expected values for `EnergyCustomer`, `EnergyTradeOrder`, `EnergyTradeOffer`, `beckn:Order`, `beckn:Buyer`, `beckn:Fulfillment`, `beckn:Offer` |

### Test-ID consistency (T1)
If **any** party (buyer or any provider) uses a test identifier (`meterId` or `utilityId` starting with `TEST_`), **all** parties must use test identifiers:

| Field | Required value |
|-------|---------------|
| Buyer `meterId` | `TEST_METER_BUYER` |
| Buyer `utilityId` | `TEST_DISCOM_BUYER` |
| Provider `meterId` | must start with `TEST_` |
| Provider `utilityId` | must start with `TEST_` |

### Catalog publish (`catalog_publish` action)
| Rule | Description |
|------|-------------|
| P1–P2 | Production network items must use an approved DISCOM (`TPDDL`, `PVVNL`, `BRPL`) |
| P3–P10 | Non-production items must use `TEST_METER_SELLER` / `TEST_DISCOM_SELLER`; validity/delivery windows, currency, units, and `@type`/`@context` are validated |

## Configuration

`minDeliveryLeadHours` defaults to `4`. Override by passing a data file:

```bash
echo '{"config": {"minDeliveryLeadHours": 6}}' > /tmp/config.json

opa eval \
  -d p2p-trading-interdiscom.rego \
  -d /tmp/config.json \
  --input /path/to/input.json \
  'data.deg.policy.violations'
```
