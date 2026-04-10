# EnergyActor — v2.0

Participant identity for **utilities**, **aggregators**, **customers**, and **agents** — roles and VC references, not raw PII.

Part of [DEG schema](../../README.md) · [EnergyActor](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | JSON Schema 2020-12 for `EnergyActor` |
| [context.jsonld](./context.jsonld) | JSON-LD context (`https://schema.beckn.io/deg/EnergyActor/v2.0/`) |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Properties

| Property | Required | Description |
|----------|----------|-------------|
| `actorId` | ✅ | URI (DID, subscriber id, or energy URI) |
| `actorType` | ✅ | `person` \| `organization` \| `agent` |
| `roles` | | Role strings (network-profiled) |
| `credentials` | | Map of VC references |
| `reputation` | | Optional scores |
| `jurisdiction` | | Optional region / licensee |
| `networkCertification` | | Optional programme certification |

## Usage

- **Buyer** `buyerAttributes`, provider metadata, or standalone extension payloads.
- Aligns with **DEG-Protocol-Specification-vNext** §3.2 and **DEG-Specification-Complete-Reference** §4.1.
