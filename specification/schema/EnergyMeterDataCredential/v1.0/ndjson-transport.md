# Meter Data VC — NDJSON Transport Specification

Version: 1.0.0-draft

## Overview

This specification defines how Meter Data Verifiable Credentials are delivered in bulk using [NDJSON](https://github.com/ndjson/ndjson-spec) (Newline-Delimited JSON). The credential schema (`attributes.yaml`, `context.jsonld`, `vocab.jsonld`) is unchanged — this spec covers the wire format only.

## Design Principles

- **Each line is a complete VC** — independently parseable, independently verifiable.
- **No envelope** — no wrapping feed, no array brackets, no framing overhead.
- **Streamable** — consumer can process/verify line-by-line without buffering the full response.
- **Stateless pagination** — cursor-based, no server-side session.

## Wire Format

### Content-Type

```
Content-Type: application/x-ndjson
```

### Body

Each line is a single JSON object — one `EnergyMeterDataCredential` VC as defined in `attributes.yaml`. Lines are separated by `\n` (U+000A). No trailing comma, no array brackets.

```
{"@context":[...],"id":"urn:uuid:aaa...","type":["VerifiableCredential","EnergyMeterDataCredential"],"issuer":{...},"credentialSubject":{...},"proof":{...}}
{"@context":[...],"id":"urn:uuid:bbb...","type":["VerifiableCredential","EnergyMeterDataCredential"],"issuer":{...},"credentialSubject":{...},"proof":{...}}
{"@context":[...],"id":"urn:uuid:ccc...","type":["VerifiableCredential","EnergyMeterDataCredential"],"issuer":{...},"credentialSubject":{...},"proof":{...}}
```

### Constraints

- Each line MUST be valid JSON and MUST conform to the `EnergyMeterDataCredential` schema.
- Each line MUST contain a `proof` — every VC is independently verifiable.
- Lines MUST NOT contain embedded newlines (JSON strings with `\n` must use the escaped form `\\n`).
- The stream MAY end with a trailing newline.
- Empty lines MUST be ignored by consumers.

## Ordering

Lines MUST be ordered by `credentialSubject.coveragePeriod.start` ascending (oldest first). When multiple meters are present, group by `meterNumber`, then order by `coveragePeriod.start` within each group.

```
meter-A, 2025-07-01  ← line 1
meter-A, 2025-07-02  ← line 2
meter-A, 2025-07-03  ← line 3
meter-B, 2025-07-01  ← line 4
meter-B, 2025-07-02  ← line 5
```

## HTTP API

### Endpoint

```
GET /credentials/meter-data
```

### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `meter` | string | No | Filter by meter number. Omit for all meters. |
| `consumer` | string | No | Filter by consumer number. |
| `from` | datetime | No | Coverage period start >= this value (ISO 8601). |
| `to` | datetime | No | Coverage period end <= this value (ISO 8601). |
| `limit` | integer | No | Max VCs per response. Default: 1000. Max: 10000. |
| `cursor` | string | No | Opaque cursor from previous response for pagination. |

### Example Request

```http
GET /credentials/meter-data?meter=MET2025789456123&from=2025-07-01T00:00:00Z&to=2025-07-31T23:59:59Z&limit=100
Accept: application/x-ndjson
Authorization: Bearer <token>
```

### Response Headers

```http
HTTP/1.1 200 OK
Content-Type: application/x-ndjson
Link: </credentials/meter-data?cursor=eyJ...>; rel="next"
X-Total-Count: 744
X-Cursor: eyJ...
```

| Header | Description |
|---|---|
| `Content-Type` | Always `application/x-ndjson`. |
| `Link` | Pagination. Present only if more results exist. `rel="next"` points to next page. |
| `X-Total-Count` | Optional. Total VCs matching the query (across all pages). |
| `X-Cursor` | Opaque cursor for the next page (same value as in `Link`). |

### Pagination

Cursor-based. The cursor is opaque to the client — it encodes the last VC's position. Clients follow the `Link: rel="next"` header until it's absent.

```bash
# Page 1
curl -H "Accept: application/x-ndjson" \
  "https://utility.example/credentials/meter-data?meter=MET2025789456123&limit=100"
# → 100 lines + Link header with cursor

# Page 2
curl -H "Accept: application/x-ndjson" \
  "https://utility.example/credentials/meter-data?cursor=eyJ..."
# → next 100 lines
```

### Error Responses

Errors are returned as standard JSON (not NDJSON), with an appropriate HTTP status:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_parameter",
  "message": "Parameter 'from' must be a valid ISO 8601 datetime"
}
```

## Granularity: What is one VC?

Each line (VC) covers **one meter for one IntervalBlock period** — typically one day of 15-minute readings (96 readings). This is the natural unit because:

- It matches utility billing/settlement cycles (daily batches).
- Each VC is independently revocable via `credentialStatus`.
- A single day's data (~230 bytes overhead + ~80 bytes × 96 readings ≈ **8 KB**) is small enough for individual verification but large enough to avoid per-reading VC overhead.

For a month of data for one meter, expect ~30 lines (one per day), totaling ~240 KB uncompressed.

| Period | Lines | Uncompressed | gzip (~65% reduction) |
|---|---|---|---|
| 1 day, 1 meter | 1 | ~8 KB | ~3 KB |
| 1 month, 1 meter | 30 | ~240 KB | ~84 KB |
| 1 month, 100 meters | 3,000 | ~24 MB | ~8.4 MB |
| 1 year, 100 meters | 36,500 | ~292 MB | ~102 MB |

## Compression

Servers SHOULD support `Accept-Encoding: gzip` or `br` (Brotli). NDJSON compresses well (~65-70% reduction) due to repeated structure across lines.

```http
GET /credentials/meter-data?meter=MET2025789456123
Accept: application/x-ndjson
Accept-Encoding: gzip
```

```http
HTTP/1.1 200 OK
Content-Type: application/x-ndjson
Content-Encoding: gzip
```

## Consumer Processing

### Stream processing (recommended)

```python
import json
import httpx

with httpx.stream("GET", url, headers={"Accept": "application/x-ndjson"}) as r:
    for line in r.iter_lines():
        if not line.strip():
            continue
        vc = json.loads(line)
        verify(vc["proof"])
        process(vc["credentialSubject"])
```

### Batch processing

```python
import json

vcs = [json.loads(line) for line in response.text.strip().split("\n") if line.strip()]
```

## Relationship to Existing Specs

| Concern | Spec | Changed? |
|---|---|---|
| What a VC contains | `attributes.yaml` | No |
| Semantic meaning | `context.jsonld`, `vocab.jsonld` | No |
| How VCs are delivered in bulk | **This document** | New |
| How a single VC is verified | W3C VC Data Model + proof suite | No |
| How revocation is checked | `credentialStatus` (DeDi registry) | No |

## Content Negotiation

A server MAY support multiple formats on the same endpoint via `Accept`:

| Accept | Response |
|---|---|
| `application/x-ndjson` | NDJSON stream (this spec) |
| `application/json` | JSON array of VCs (for clients that don't support streaming) |
| `application/ld+json` | Single VC (when query resolves to exactly one) |

## References

- [NDJSON Specification](https://github.com/ndjson/ndjson-spec)
- [W3C Verifiable Credentials Data Model](https://www.w3.org/TR/vc-data-model/)
- [RFC 8288 — Web Linking](https://www.rfc-editor.org/rfc/rfc8288) (Link headers)
- [RFC 6570 — URI Templates](https://www.rfc-editor.org/rfc/rfc6570)
