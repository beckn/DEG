# EnergyConsentRecord — v2.0

Verifiable **consent** for energy data sharing — who, what, why, and when — with optional audit trail.

Part of [DEG schema](../../README.md) · [EnergyConsentRecord](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | JSON Schema 2020-12 |
| [context.jsonld](./context.jsonld) | JSON-LD context |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Required properties

`consentId`, `consumerId`, `dataType`, `purpose`, `grantedTo`, `validity` (`start`, `end`).

## Usage

- Linked from **EnergyCredential** / programme enrollment; telemetry and settlement gates.
- Aligns with **DEG-Protocol-Specification-vNext** §4.1 and **DEG-Specification-Complete-Reference** §4.1.
