# EnergyResourceCommon v1.0

Canonical base schemas shared by all typed `EnergyResource` kinds.

**Canonical IRI:** `https://schema.nfh.global/EnergyResourceCommon/v1.0`

---

## Schemas

### `EnergyResourceCommon`

The structural envelope inherited by every kind via `allOf`. Defines:

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable asset identifier (IES DID convention) |
| `type` | string | Asset class discriminator — constrained to a kind-specific `enum` or `const` |
| `subResources` | array | Downward topology — child resource ids or inline EnergyResource objects |
| `parentResources` | array | Upward topology — ids of parent resources (string refs only) |
| `attributes` | object | Attribute bag — inherits `EnergyResourceCommonAttributes` via `allOf` |

### `EnergyResourceCommonAttributes`

The attribute bag base inherited inside every kind's `<Kind>Attributes` object via `allOf`. No field is required at this level.

| Field | Type | Description |
|---|---|---|
| `make` | string | Manufacturer (free text) |
| `model` | string | Model (free text) |
| `ratedPowerKw` | number ≥0 | Nameplate power in kW. Deprecated; prefer `maxExportKw` |
| `maxExportKw` | number ≥0 | Max power injected to grid (discharge / generation), kW |
| `maxImportKw` | number ≥0 | Max power drawn from grid (charge / load), kW |
| `telemetryProvider` | string | Vendor API / data-source identifier |
| `commissioningDate` | date-time | ISO 8601 asset commissioning date-time |
| `location` | object | beckn Location/2.0 shape — `geo` (GeoJSON, required) + `address` (postal, optional) |

---

## Inheritance pattern

**Kind envelope:**

```yaml
EnergyResourceMeter:
  allOf:
    - $ref: "https://schema.nfh.global/EnergyResourceCommon/v1.0/attributes.yaml#/components/schemas/EnergyResourceCommon"
    - type: object
      properties:
        type:
          const: "METER"
        attributes:
          $ref: "#/components/schemas/EnergyResourceMeterAttributes"
```

**Kind attributes bag:**

```yaml
EnergyResourceMeterAttributes:
  allOf:
    - $ref: "https://schema.nfh.global/EnergyResourceCommon/v1.0/attributes.yaml#/components/schemas/EnergyResourceCommonAttributes"
    - type: object
      additionalProperties: true
      properties:
        # Kind-specific fields only — common fields inherited above
        meterCapability: ...
```

---

## Kinds that inherit this schema

| Kind | Canonical IRI | Types |
|---|---|---|
| EnergyResourceMeter | `schema.nfh.global/EnergyResourceMeter/v1.0` | `METER` |
| EnergyResourceGenerator | `schema.nfh.global/EnergyResourceGenerator/v1.0` | `SOLAR_PV`, `WIND`, `HYDRO`, `BIOGAS`, `CHP`, `FUEL_CELL` |
| EnergyResourceStorage | `schema.nfh.global/EnergyResourceStorage/v1.0` | `BESS` |
| EnergyResourceEVCharger | `schema.nfh.global/EnergyResourceEVCharger/v1.0` | `EV_CHARGER`, `EV_V2G` |
| EnergyResourceInverter | `schema.nfh.global/EnergyResourceInverter/v1.0` | `INVERTER` |
| EnergyResourceLoad | `schema.nfh.global/EnergyResourceLoad/v1.0` | `SMART_HVAC`, `SMART_WATER_HEATER`, `CONTROLLABLE_LOAD` |
| EnergyResourceNetwork | `schema.nfh.global/EnergyResourceNetwork/v1.0` | `DT`, `BUS`, `FEEDER`, `MICROGRID` |
