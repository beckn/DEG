# Data Exchange Devkit

Beckn Protocol v2.0 devkit for inline data delivery with `DatasetItem` and `dataPayload`.

## Use Cases

| Use Case | BPP (Provider) | BAP (Consumer) | dataPayload | Description |
|---|---|---|---|---|
| [usecase1](./usecase1/) | IntelliGrid AMI Services (AMISP) | BESCOM (discom) | `IES_Report` | AMI meter data exchange delivered inline on `on_confirm` |
| [usecase2](./usecase2/) | BESCOM (discom) | APERC (state regulator) | `IES_ARR_Filing` | ARR filing submission delivered inline on `on_confirm` |

Both use cases share the same Docker infrastructure, adapter configs, and test scripts.

## Key Schemas

- `DatasetItem` from [DDM](https://github.com/beckn/DDM) provides `dataPayload` for inline delivery and `accessMethod` for delivery mode.
- `IES_Report` from [India Energy Stack](https://github.com/India-Energy-Stack/ies-docs) carries meter telemetry in OpenADR 3.1.0 format.
- `IES_ARR_Filing` from [India Energy Stack](https://github.com/India-Energy-Stack/ies-docs) carries ARR filing line items.

## Transaction Flow

```text
BPP (Provider)      Catalog Service     Discovery Service       BAP (Consumer)
    |                     |                    |                      |
    |                     |<-- subscribe ------|                      |
    |                     |   (catalog updates)|                      |
    |                     |                    |                      |
    |-- publish --------->|                    |                      |
    |   (DatasetItem      |                    |                      |
    |    catalog)         |                    |                      |
    |                     |                    |<---- discover -------|
    |                     |                    |---- on_discover ---->|
    |                     |                    |                      |
    |---------------------+--------------------+----------------------|
    |                  Direct BAP <-> BPP negotiation                 |
    |                                                                 |
    |<---- select ----------------------------------------------------|
    |---- on_select ------------------------------------------------->|
    |                                                                 |
    |<---- init ------------------------------------------------------|
    |---- on_init --------------------------------------------------->|
    |                                                                 |
    |<---- confirm ---------------------------------------------------|
    |---- on_confirm (active + inline dataPayload) ------------------>|
    |   dataPayload: IES_Report / IES_ARR_Filing                     |
    |                                                                 |
    |<---- cancel ----------------------------------------------------|
    |---- on_cancel ------------------------------------------------->|
```

## Quick Start

```bash
# 1. Start infrastructure
cd install
docker compose -f docker-compose-adapter.yml up -d

# 2. Verify services
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:3001/api/health
curl http://localhost:3002/api/health

# 3. Run the workflows
cd ../usecase1/workflows && ./run-arazzo.sh
cd ../../usecase2/workflows && ./run-arazzo.sh

# Single workflow, verbose:
./run-arazzo.sh -w select-through-confirm -v
```

## Repository Structure

- `config/` - shared adapter configs
- `install/` - Docker Compose and ngrok setup
- `scripts/` - helper scripts
- `usecase1/` - AMI meter data exchange
- `usecase2/` - ARR filing exchange

## Network Configuration

| Parameter | Value |
|---|---|
| Network ID | `nfh.global/testnet-deg` |
| BAP ID | `bap.example.com` |
| BPP ID | `bpp.example.com` |
| BAP Adapter | `http://localhost:8081/bap/caller` |
| BPP Adapter | `http://localhost:8082/bpp/caller` |

## Run over the public internet

The devkit also ships an isolated Docker setup that routes traffic through a single public URL. See `install/docker-compose-over-internet.yml` and the workflow runner notes in each use case folder.

## Regenerate Postman Collections

```bash
python3 scripts/generate_postman_collection.py --role BAP
python3 scripts/generate_postman_collection.py --role BPP
python3 scripts/generate_postman_collection.py --role BAP --usecase usecase1
```

## Related

- [DDM DatasetItem Schema](https://github.com/beckn/DDM/tree/main/specification/schema/DatasetItem/v1)
- [IES Core Schemas](https://github.com/India-Energy-Stack/ies-docs)
