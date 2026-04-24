# CustomerProfile — v1.0

Core customer identity for energy credentials. Links a utility account number and meter serial number to a credential subject. Used by MeterDataGB, BillingSummary, and the Customer Credential (PR #208).

Part of the [DEG Specification](../../../../README.md) · [CustomerProfile](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1 / JSON Schema definition for `CustomerProfile` |
| [context.jsonld](./context.jsonld) | JSON-LD context mapping properties to `deg:` namespace |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary (RDFS classes and properties) |

## Properties

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `customerNumber` | string | ✅ | Utility account number assigned by the distribution company |
| `meterNumber` | string | ✅ | Unique meter serial number (max 50 chars) |
| `meterType` | string (enum) | ✅ | AMR, AMI, Electromechanical, Forward, Reverse, Bidirectional, Prepaid, NetMeter, Other |
| `idRef` | object | — | Optional identity reference: `issuedBy` (DID/URI) + `subjectId` (authority-scoped ID) |
