# BecknPageInfo — v1.0

Domain-neutral pagination envelope for any beckn payload that needs to ship a large collection across multiple messages.

Part of the [DEG Schema](../../) · [BecknPageInfo](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 `components.schemas.BecknPageInfo` |
| [context.jsonld](./context.jsonld) | JSON-LD context — term `PageInfo` maps to `beckn:BecknPageInfo` |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## When to embed it

**Don't, when you don't need to.** A sender that can fit the whole collection in a single message MUST omit `pageInfo`. The presence of `pageInfo` is itself the wire-level signal that the collection is partial. This keeps the common case (small cohort, single message) unchanged from today and makes paged delivery an opt-in concern.

Consumer schemas (e.g. [DemandFlexPerformance](../../DemandFlexPerformance/v2.0/)) declare `pageInfo` as **optional** on whatever object owns the paginated array.

## Modes

| Mode | Who drives | What `cursor` carries |
|---|---|---|
| **Push** (BPP-initiated) | BPP fires N back-to-back messages | Optional; receivers rely on `sequence` for ordering |
| **Pull** (BAP-initiated) | BAP issues subsequent calls (e.g. `status`) carrying `pageCursor` in tags | Required; BPP returns the next slice and the next `nextCursor` |

Either mode terminates with `isLast: true` on the final page.

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `sequence` | integer (≥0) | ✓ | Monotonic page index within a `(transactionId, collectionId)` pair. `0` is the first page. |
| `isLast` | boolean | ✓ | `true` on the final page only. Receivers defer aggregate-dependent actions (settlement, total-count checks) until this is observed. |
| `pageSize` | integer (≥1) | — | Nominal per-page element count declared by the sender. Final page MAY be smaller. |
| `total` | integer (≥0) | — | Expected element count across all pages of this delivery. May be omitted when not cheaply known. |
| `cursor` | string | — | Opaque token identifying THIS page; echoed from the previous `nextCursor` in pull mode. |
| `nextCursor` | string \| null | — | Token to use in the next pull request. `null` on the final page. |
| `collectionId` | string | — | Disambiguates which collection in the envelope this `pageInfo` belongs to when more than one paginated collection rides the same transaction. |

## Embedding pattern

`BecknPageInfo` is a **sibling** of the paginated array, not a wrapper around it. Consumer schemas keep their existing array property and add `pageInfo` next to it:

```yaml
# In the consumer schema's attributes.yaml
properties:
  meters:
    type: array
    items: { ... }
  pageInfo:
    $ref: "https://schema.nfh.global/BecknPageInfo/v1.0/attributes.yaml#/components/schemas/BecknPageInfo"
    description: Optional. Present only when the collection is paged.
```

## Minimal example — push mode, page 1 of 3

```jsonc
{
  "performanceAttributes": {
    "@type": "DemandFlexPerformance",
    "eventId": "evt-2026-04-01-001",
    "methodology": "5of10",
    "meters": [
      { "meterId": "der://meter/00001", "telemetry": { /* … */ } },
      { "meterId": "der://meter/00002", "telemetry": { /* … */ } }
      // … 3998 more on this page
    ],
    "pageInfo": {
      "@type": "PageInfo",
      "sequence": 0,
      "pageSize": 4000,
      "total": 12000,
      "isLast": false,
      "collectionId": "perf-evt-001-actuals"
    }
  }
}
```

The next push carries `sequence: 1`, then `sequence: 2` with `isLast: true`. The receiver assembles `meters[]` by sorting on `sequence` and only fires settlement once `isLast: true` is observed.

## Minimal example — pull mode, page 2 of N

BAP requests page 2 by including `pageCursor: "evt-001-p2"` in `context.tags`. BPP responds:

```jsonc
{
  "performanceAttributes": {
    "@type": "DemandFlexPerformance",
    "eventId": "evt-2026-04-01-001",
    "methodology": "5of10",
    "meters": [ /* slice for page 2 */ ],
    "pageInfo": {
      "@type": "PageInfo",
      "sequence": 1,
      "pageSize": 4000,
      "total": 12000,
      "isLast": false,
      "cursor": "evt-001-p2",
      "nextCursor": "evt-001-p3",
      "collectionId": "perf-evt-001-actuals"
    }
  }
}
```

## What the schema validator catches vs. what it doesn't

The OpenAPI 3.1.1 validator will flag:

- missing `sequence` / `isLast`
- negative `sequence` / `pageSize` / `total`
- `nextCursor` of a wrong type

It does **not** catch (these belong in consumer profiles or the policy layer):

- gap detection across pages (`sequence` is contiguous)
- `isLast` set on a non-final page
- `total` consistency with assembled count
- duplicate `(transactionId, collectionId, sequence)` deliveries

Encode those as profile-level cross-message checks where the receiver assembles.

## Off-protocol delivery (see BecknResourceRef)

For collections too large to page sanely on-protocol, the consumer schema SHOULD also allow a [BecknResourceRef](../../BecknResourceRef/v1.0/) sibling that points to a content-addressed, signed bundle. `pageInfo` is for *in-protocol* paged delivery; `BecknResourceRef` is for *off-protocol* bulk delivery. They're mutually exclusive on a given collection.

## Why this lives in the top-level schema/

Pagination is a Beckn-wide concern, not a domain-specific one. Catalog responses, search results, contract participant lists, performance telemetry — any of these may grow past a single-message budget. `BecknPageInfo` lives at the top of `specification/schema/` so any future schema (DEG or otherwise) can `$ref`-embed it without reinventing the cursor shape.
