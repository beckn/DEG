# espiGreenButtonWithCIM

> **Tags:** `energy`, `metering`, `green-button`, `espi`, `cim`, `iec-61968`, `iec-61970`
> **Extends:** [espiGreenButton](../espiGreenButton/)
> **Source standards:** IEC 61968-9, IEC 61970, NAESB REQ.21
> Part of the [DEG Specification](../../../README.md)

---

Optional CIM (Common Information Model) extension types for Green Button / ESPI, covering meter telemetry at consumer (AMI), distribution-transformer, and transmission levels.

All schemas here are **additive** — the base ESPI types in [espiGreenButton](../espiGreenButton/) are unchanged. These extensions add device models, SCADA telemetry, instrument transformer metadata, and event tracking from the IEC 61968/61970 standards.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.0 schema definitions for CIM extension types (38 classes) |

## Types

### Common Base
| Type | CIM Source | Description |
|------|-----------|-------------|
| `IdentifiedObject` | IEC 61970 Core | Root class with mRID, name, description |

### Device Models
| Type | CIM Source | Description |
|------|-----------|-------------|
| `EndDevice` | IEC 61968-9 | Physical metering device |
| `Meter` | IEC 61968-9 | Meter (extends EndDevice) |
| `EndDeviceInfo` | IEC 61968-9 | Device metadata (firmware, model, etc.) |
| `EndDeviceCapability` | IEC 61968-9 | 18 capability flags (demand response, pricing, etc.) |

### Metering Infrastructure
| Type | CIM Source | Description |
|------|-----------|-------------|
| `Channel` | IEC 61968-9 | Data channel within a meter |
| `Register` | IEC 61968-9 | Physical register on a meter |
| `MeterMultiplier` | IEC 61968-9 | CT/PT ratio multipliers |

### Events
| Type | CIM Source | Description |
|------|-----------|-------------|
| `EndDeviceEvent` | IEC 61968-9 | Meter event (outage, tamper, etc.) |
| `EndDeviceEventType` | IEC 61968-9 | Event classification |

### SCADA / Telemetry
| Type | CIM Source | Description |
|------|-----------|-------------|
| `Measurement` | IEC 61970 Meas | Base measurement class |
| `Analog` | IEC 61970 Meas | Continuous measurement (voltage, current, etc.) |
| `Discrete` | IEC 61970 Meas | Discrete state measurement |
| `AnalogValue` | IEC 61970 Meas | Timestamped analog reading |
| `DiscreteValue` | IEC 61970 Meas | Timestamped discrete state |
| `AccumulatorValue` | IEC 61970 Meas | Cumulative counter value |

### Instrument Transformers
| Type | CIM Source | Description |
|------|-----------|-------------|
| `CurrentTransformerInfo` | IEC 61968 Assets | CT specifications |
| `PotentialTransformerInfo` | IEC 61968 Assets | PT specifications |
| `PowerTransformerInfo` | IEC 61968 Assets | Power transformer metadata |

### Composite
| Type | Description |
|------|-------------|
| `UsagePointCIM` | Enhanced usage point with 21 properties |
| `MeterTelemetryReading` | Composite wrapper with 17 properties |

## References

- Balijepalli & Khaparde, *IEEE Systems Journal* 2013 — CIM ↔ Green Button integration
- IEC 61968-9: Metering — end device, events, channels, registers
- IEC 61970: Base/Meas — SCADA telemetry
