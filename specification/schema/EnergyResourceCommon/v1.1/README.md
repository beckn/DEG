# EnergyResourceCommon v1.1

Canonical base schemas shared by all typed `EnergyResource` kinds.

**Canonical IRI:** `https://schema.nfh.global/EnergyResourceCommon/v1.1`

---

## v1.1 changes

Power dimensioning fields now use `QuantitativeValue {value, unit}` instead of plain numbers with unit-suffixed names:

| v1.0 (scalar) | v1.1 (QuantitativeValue) | unit enum |
|---|---|---|
| `ratedPowerKw` | `ratedPower` | `W \| kW \| MW` |
| `maxExportKw` | `maxExport` | `W \| kW \| MW` |
| `maxImportKw` | `maxImport` | `W \| kW \| MW` |

Unit aliases (`W`, `kW`, `MW`, `kWh`, `MWh`, `kVA`, `MVA`, `kVAR`, `MVAR`, `V`, `kV`) are defined in the JSON-LD context and mapped to QUDT IRIs.

Optional administrative attributes added (non-breaking; all optional):

| Field | Standard | Notes |
|---|---|---|
| `serialNumber` | CIM `EndDeviceInfo.serialNumber` (IEC 61968-9) | Equipment-nameplate device serial; distinct from the network DID in `id` |
| `inspection` | IEEE 1547-2018 Cl. 11; CEA Connectivity Regs 2013 | Commissioning / safety inspection record `{date, result, inspectorId}` |
| `aggregator` | IEEE 2030.5; IEC 61850-7-420 | Demand-flex enrolment block `{id, name, controllable, enrolledOn}` |

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
| `ratedPower` | QuantitativeValue | Nameplate power. Deprecated; prefer `maxExport` |
| `maxExport` | QuantitativeValue | Max power injected to grid (discharge / generation). `unit: W\|kW\|MW` |
| `maxImport` | QuantitativeValue | Max power drawn from grid (charge / load). `unit: W\|kW\|MW` |
| `telemetryProvider` | string | Vendor API / data-source identifier |
| `commissioningDate` | date-time | ISO 8601 asset commissioning date-time |
| `location` | object | beckn Location/2.0 shape — `geo` (GeoJSON, required) + `address` (postal, optional) |
| `serialNumber` | string | Manufacturer-assigned device serial from the equipment nameplate. Distinct from `id` (network-issued DID). CIM: `cim:EndDeviceInfo.serialNumber` (IEC 61968-9) |
| `inspection` | object | Commissioning / safety inspection record: `{date, result: pass\|fail\|conditional, inspectorId}`. IEEE 1547-2018 Cl. 11; CEA Connectivity Regulations 2013 (amd. 2018) |
| `aggregator` | object | Third-party demand-flex enrolment: `{id (URI), name, controllable (bool), enrolledOn (date)}`. `controllable: false` = observation-only. IEEE 2030.5 / IEC 61850-7-420 |

---

## Inheritance pattern

**Kind envelope:**

```yaml
EnergyResourceMeter:
  allOf:
    - $ref: "https://schema.nfh.global/EnergyResourceCommon/v1.1/attributes.yaml#/components/schemas/EnergyResourceCommon"
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
    - $ref: "https://schema.nfh.global/EnergyResourceCommon/v1.1/attributes.yaml#/components/schemas/EnergyResourceCommonAttributes"
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
| EnergyResourceMeter | `schema.nfh.global/EnergyResourceMeter/v1.1` | `METER` |
| EnergyResourceGenerator | `schema.nfh.global/EnergyResourceGenerator/v1.1` | `SOLAR_PV`, `WIND`, `HYDRO`, `BIOGAS`, `CHP`, `FUEL_CELL` |
| EnergyResourceStorage | `schema.nfh.global/EnergyResourceStorage/v1.1` | `BESS` |
| EnergyResourceEVCharger | `schema.nfh.global/EnergyResourceEVCharger/v1.1` | `EV_CHARGER`, `EV_V2G` |
| EnergyResourceInverter | `schema.nfh.global/EnergyResourceInverter/v1.1` | `INVERTER` |
| EnergyResourceLoad | `schema.nfh.global/EnergyResourceLoad/v1.1` | `SMART_HVAC`, `SMART_WATER_HEATER`, `CONTROLLABLE_LOAD` |
| EnergyResourceNetwork | `schema.nfh.global/EnergyResourceNetwork/v1.1` | `DT`, `BUS`, `FEEDER`, `MICROGRID` |
