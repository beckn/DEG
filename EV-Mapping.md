# EV Charging Mapping (v2-rc → Beckn v2)

This document provides a mapping guide for Network Participants (NPs) migrating EV charging implementations from **v2-rc** to **Beckn v2** (Final). This guide is specifically designed for NPs using the **Universal Beckn Connector (UBC)**.

---

## 2. Context

*   **v2-rc**: An older release candidate version (often referred to as v1-EOS in some devkits) which used a flatter, tag-based structure for domain-specific data.
*   **Beckn v2**: The final stable version that introduces **Global Semantic Interoperability** via JSON-LD, standardized prefixes (`beckn:`, `schema:`), and a modular "core + schema packs" model.

This document helps you migrate your payloads by providing direct field-to-field mappings and structural transformation examples.

---

## 3. Key Changes (High-Level Summary)

*   **Prefixing**: Almost all keys in v2 are prefixed (e.g., `id` → `beckn:id`, `name` → `schema:name`).
*   **Structural Nesting**: Domain-specific attributes (like connector type or power) move from flat `tags` or `attributes` into a structured `beckn:itemAttributes` object.
*   **JSON-LD Alignment**: Every major object now includes `@context` and `@type` for semantic clarity.
*   **Standardized Formats**: Time and durations follow ISO 8601 (e.g., `PT30S`, `2024-01-15T10:30:00Z`).
*   **GeoJSON Coordinates**: Location coordinates MUST be `[longitude, latitude]`.

---

## 4. Field Mapping (Core Section)

### A. Context Mapping
| v2-rc Field | Beckn v2 Field      | Type/Format Change            | Notes |
|   :---      |       :---          |          :---                 | :---  |
| `domain`    | `context.domain`    | `beckn.one:deg:ev-charging:*` | Standardized domain string. |
| `version`   | `context.version`   | `2.0.0`                       | Update protocol version. |
| `timestamp` | `context.timestamp` | ISO 8601 DateTime             | Ensure UTC (Z) suffix. |
| `ttl`       | `context.ttl`       | ISO 8601 Duration             | e.g., `PT30S` for 30 seconds. |

### B. Vehicle Details
These attributes define the vehicle types compatible with the charging service.

| v2-rc Field             | Beckn v2 Field      | Type/Format          | Notes                                     |
|       :---              |        :---         |         :---         |                  :---                     |
| `vehicle-type`          | `vehicleType`       | `Enum (String)`      | `2-WHEELER`, `3-WHEELER`, `4-WHEELER`.    |

### C. Charging Details
In v2, these reside inside `beckn:items[].beckn:itemAttributes`.

| v2-rc Field (Tags/Flat)   | Beckn v2 Field         | Type/Format     | Notes                                        |
|         :---              |          :---          |      :---       |                     :---                     |
| `connector-type`          | `connectorType`        | `Enum (String)` | `CCS2`, `Type2`, `CHAdeMO`, `GB_T`.          |
| `charger-type`            | `powerType`            | `Enum (String)` | `AC`, `DC` (or `AC_SINGLE_PHASE` etc).       |
| `power-rating`            | `maxPowerKW`           | `Number`        | Convert string "60kW" to number `60`.        |
| `availability`            | `stationStatus`        | `Enum (String)` | `Available`, `Charging`, `Offline`.          |
| `evse-id`                 | `evseId`               | `String`        | Standard OCPI/Hubject style.                 |
| `reservation-supported`   | `reservationSupported` | `Boolean`       | `true` or `false`.                           |

### D. Location & Station Details
| v2-rc Field   | Beckn v2 Field       | Parent Object            | Notes                                     |
|     :---      |         :---         |          :---            |                  :---                     |
| `gps`         | `geo.coordinates`    | `beckn:availableAt[]`    | Array `[long, lat]`. NO comma string.     |
| `address`     | `address`            | `beckn:availableAt[]`    | Nested object (street, city, etc).        |
| `station_id`  | `chargingStation.id` | `beckn:itemAttributes`   | Unique ID for the physical site.          |

---

## 5. Example Transformation

### v2-rc JSON (Before)
```json
{
  "context": { "domain": "ev-charging", "version": "1.1.0" },
  "message": {
    "catalog": {
      "items": [{
        "id": "charger-01",
        "descriptor": { "name": "Fast Charger" },
        "gps": "12.9716, 77.5946",
        "tags": [
          { "code": "connector-type", "value": "CCS2" },
          { "code": "power-rating", "value": "60kW" }
        ]
      }]
    }
  }
}
```

### Beckn v2 JSON (After)
```json
{
  "context": { "domain": "beckn.one:deg:ev-charging:*", "version": "2.0.0" },
  "message": {
    "catalogs": [{
      "beckn:items": [{
        "beckn:id": "charger-01",
        "beckn:descriptor": { "schema:name": "Fast Charger" },
        "beckn:availableAt": [{
          "geo": { "type": "Point", "coordinates": [77.5946, 12.9716] }
        }],
        "beckn:itemAttributes": {
          "@type": "ChargingService",
          "connectorType": "CCS2",
          "maxPowerKW": 60
        }
      }]
    }]
  }
}
```

---

## 6. Migration Steps

1.  **Identify Usage**: Search your codebase for manual payload construction (especially `tags` arrays).
2.  **Add Prefixes**: Update keys to include `beckn:` or `schema:` as per the v2 specification.
3.  **Nest Attributes**: Move EV-specific fields from flat tags into the `beckn:itemAttributes` block.
4.  **Format Data**: Convert numeric strings (e.g., "60kW") to numbers (`60`) and GPS strings to coordinate arrays.
5.  **Inject `@context`**: Ensure every major object has the required `@context` URL.
6.  **Validate**: Run your payload through the Beckn v2 validator or test against a v2-compliant UBC instance.

---

## 7. Deprecated / Removed Fields

| Old Field         | Status          | New Alternative                                 |
|       :---        |    :---         |           :---                                  |
| `gps` (String)    | **REMOVED**     | `geo.coordinates` (Array)                       |
| `tags` (Generic)  | **DEPRECATED**  | `beckn:itemAttributes` (Typed Object)           |
| `images` (String) | **REPLACED**    | `beckn:descriptor.schema:image` (Object/Array)  |

---

## 8. Notes & Edge Cases

> [!IMPORTANT]
> **Coordinate Order**: Always use `[longitude, latitude]`. Swapping these will place your station in the wrong hemisphere!

*   **Enums**: Values like `CCS2` are case-sensitive and must match the enum exactly.
*   **Timezones**: Always use UTC for timestamps to prevent synchronization issues between BAP and BPP.
*   **Number Precision**: Avoid sending numbers as strings. Use `60.5` instead of `"60.5"`.
