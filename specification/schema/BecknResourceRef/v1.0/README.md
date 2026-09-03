# BecknResourceRef — v1.0

Off-protocol, content-addressed reference for delivering bulk JSON bodies without bloating the on-protocol message.

Part of the [DEG Schema](../../) · [BecknResourceRef](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 `components.schemas.BecknResourceRef` |
| [context.jsonld](./context.jsonld) | JSON-LD context — term `ResourceRef` maps to `beckn:BecknResourceRef` |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## When to use

A collection — meter IDs at confirm time, per-meter telemetry at performance time — has grown too large to ride sanely on-protocol even with [BecknPageInfo](../../BecknPageInfo/v1.0/) splitting it across messages. The sender publishes the body at a BPP-hosted URL and embeds a `BecknResourceRef` pointing at it; the on-protocol message stays small and Beckn-signed; the receiver fetches the body and verifies integrity against `contentHash`.

`BecknResourceRef` and `BecknPageInfo` are **mutually exclusive** on a given collection — pick one mode.

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `uri` | string (URI) | ✓ | HTTPS URL the receiver fetches. Access control on the URL is BPP-defined (signed URL, OAuth, etc.) — out of spec. |
| `contentHash` | string (`sha256:<64-hex>`) | ✓ | SHA-256 of the fetched body after JSON canonicalization (RFC 8785). The Beckn signature on the parent message commits the BPP to this hash. |
| `count` | integer (≥0) | ✓ | Element count in the referenced collection. Receivers MAY reject on mismatch before canonicalizing. |
| `contentType` | string | — | MIME type. Defaults to `application/ld+json`. Use `application/x-ndjson` etc. when streaming a large body. |
| `schemaContext` | string (URI) | — | JSON-LD `@context` URL the body conforms to. Useful for pre-fetch validator routing. |
| `expiresAt` | string (RFC 3339) | — | Useful for signed-URL implementations. |
| `sizeBytes` | integer (≥0) | — | Lets receivers short-circuit before downloading multi-GB bodies. |

## Integrity vs. access control

Two separable guarantees:

1. **Integrity** — the fetched body is what the BPP committed to. Handled by `contentHash` in the on-protocol payload. Because the parent message is Beckn-signed, the BPP cannot retroactively swap the body without breaking the signature chain.
2. **Access control** — only authorized parties can fetch `uri`. NOT in this schema. The BPP decides: signed URL with short expiry, mutual TLS, OAuth token derived from the BAP's subscriber ID, etc. The spec stays silent; integrity alone is enough to make the on-protocol payload auditable.

## Receiver verification recipe

```
GET uri
canonical = JCS(body)
if sha256(canonical) != contentHash.split(":")[1]:
    reject — body has been tampered with or fetched the wrong document
if "count" provided and len(body.collection) != count:
    reject — body shape disagrees with the on-protocol declaration
```

## Embedding pattern

`BecknResourceRef` is a **replacement** for the inline array, not a wrapper around it. Consumer schemas declare the ref as a sibling of the array and document via JSON-Schema `oneOf` that exactly one is present:

```yaml
# In the consumer schema's attributes.yaml
oneOf:
  - required: [participatingMeters]
  - required: [participatingMetersRef]
properties:
  participatingMeters:
    type: array
    items: { type: string }
  participatingMetersRef:
    $ref: "https://schema.nfh.global/BecknResourceRef/v1.0/attributes.yaml#/components/schemas/BecknResourceRef"
```

## Minimal example — bulk meter enrollment at confirm

```jsonc
{
  "role": "seller",
  "participantId": "greenflex-agg",
  "inputs": {
    "plannedDemandChange": { "@type": "Quantity", "unitCode": "KWH", "unitQuantity": 12500.0 },
    "participatingMetersRef": {
      "@type": "ResourceRef",
      "uri": "https://bpp.example.com/bulk/cohort-2026-04-01.jsonld",
      "contentHash": "sha256:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
      "count": 25000,
      "contentType": "application/ld+json",
      "schemaContext": "https://schema.nfh.global/DemandFlexBuyOffer/v2.0/participatingMeters.jsonld",
      "sizeBytes": 1850000,
      "expiresAt": "2026-04-08T00:00:00Z"
    },
    "participatingMetersDigest": {
      "count": 25000,
      "sha256OfSortedIds": "sha256:b3a8e0e1f9ab1bfe3a14b4e95f3a0e1c2d3f4e5a6b7c8d9e0f1a2b3c4d5e6f7a"
    }
  }
}
```

`participatingMetersDigest` is an **on-protocol** tamper-evidence anchor independent of the ref: even after the URL goes 404 years later, the digest in the signed contract still pins the cohort to a specific set of IDs.

## Why this lives in the top-level schema/

Off-protocol bulk delivery is a Beckn-wide concern (catalog payloads, contract metadata, performance telemetry, …). Lives next to [BecknPageInfo](../../BecknPageInfo/v1.0/) so any future schema can `$ref`-embed it without re-inventing the ref shape.
