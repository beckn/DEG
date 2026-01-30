# EV Charging Devkit

Goal of this devkit is to enable a developer to test round trip Beckn v2.0 mock messages for **EV charging flows** between network actors (BAP - EV Driver App/Charging Finder, BPP - Charging Station Operator) on their local machine within a few minutes.

This devkit supports:
- **Charging station discovery**: Search and filter charging stations by location, connector type, power rating, and availability
- **Reservation and booking**: Reserve charging slots with time-based and quantity-based options
- **Charging session management**: Initiate, monitor, and complete charging sessions with real-time status updates
- **Payment and billing**: Handle pricing, tariffs, buyer finder fees, and transaction settlement
- **Support and cancellation**: Request support, cancel reservations, and handle dispute resolution

It is a *batteries included* sandbox environment that requires minimal setup, with environment variables and registry connections pre-configured.

## Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) & run it in background
2. Install [Git](https://git-scm.com/downloads) and ensure it's added to your system path
3. Install [Postman](https://www.postman.com/downloads/)

## Setup

1. Clone this repository and navigate to the install directory:

```bash
git clone https://github.com/Beckn-One/DEG.git
cd DEG/testnet/ev-charging-devkit/install
```

2. Start the containers:

```bash
docker compose -f ./docker-compose-adapter-ev.yml up -d
docker ps
```

Verify the following containers are running:
- `redis`
- `onix-bap`
- `onix-bpp`
- `sandbox-bap`
- `sandbox-bpp`

3. Open Postman and import the folder `DEG/testnet/ev-charging-devkit/postman` to import all collections.

## Testing the EV Charging Flow

### BAP Collection (EV Driver App initiating charging)

Use the `ev-charging:BAP-DEG` collection:

1. **discover** - Discover available charging stations
   - `time-based-ev-charging-slot-discover` - Discover stations with spatial and filter criteria

2. **select** - Select a charging station and options
   - `time-based-ev-charging-slot-select` - Select station with quantity and fulfillment mode

3. **init** - Initialize charging session
   - `init-request` - Initialize with payment and billing details

4. **confirm** - Confirm the charging reservation/session
   - `confirm-request` - Confirm reservation with authorization

5. **status** - Check charging session status
   - `status-request` - Query current session status

6. **update** - Update charging session (extend, modify)
   - `update-request` - Update session parameters

7. **cancel** - Cancel charging session
   - `cancel-request` - Cancel reservation or ongoing session

8. **rating** - Rate the charging service
   - `rating-request` - Submit rating and feedback

9. **support** - Request support
   - `support-request` - Request assistance for issues

### BPP Collection (Charging Station Operator responding)

Use the `ev-charging:BPP-DEG` collection:

1. **on_discover** - Respond to discovery requests
   - `time-based-ev-charging-slot-catalog` - Return catalog of available charging stations

2. **on_select** - Respond to selection requests
   - `time-based-ev-charging-slot-on-select` - Confirm selection with pricing

3. **on_init** - Respond to initialization requests
   - `on-init-response` - Acknowledge initialization

4. **on_confirm** - Respond to confirmation requests
   - `on-confirm-response` - Confirm reservation/session start

5. **on_status** - Respond to status queries
   - `on-status-response` - Provide current session status

6. **on_update** - Respond to update requests
   - `on-update-response` - Confirm session updates

7. **on_cancel** - Respond to cancellation requests
   - `on-cancel-response` - Confirm cancellation

8. **on_rating** - Respond to rating submissions
   - `on-rating-response` - Acknowledge rating

9. **on_support** - Respond to support requests
   - `on-support-response` - Provide support information

## Viewing Responses

The request responses will show an "Ack" message. Detailed `on_*` messages from BPP should be visible in the BAP logs:

```bash
docker logs -f onix-bap
```

## Stopping the Environment

```bash
docker compose -f ./docker-compose-adapter-ev.yml down
```

## Configuration

### Environment Variables (Pre-configured in Postman collections)

| Variable Name     | Value                                   | Notes           |
| :---------------- | :-------------------------------------- | :-------------- |
| `domain`          | `beckn.one:deg:ev-charging:2.0.0`       |                 |
| `version`         | `2.0.0`                                 |                 |
| `bap_id`          | `ev-charging.sandbox1.com`              |                 |
| `bap_uri`         | `http://onix-bap:8081/bap/receiver`     |                 |
| `bpp_id`          | `ev-charging.sandbox2.com`              |                 |
| `bpp_uri`         | `http://onix-bpp:8082/bpp/receiver`     |                 |
| `bap_adapter_url` | `http://localhost:8081/bap/caller`      | BAP collection  |
| `bpp_adapter_url` | `http://localhost:8082/bpp/caller`      | BPP collection  |
| `transaction_id`  | Auto-generated UUID                     |                 |
| `iso_date`        | Auto-generated ISO timestamp            |                 |

### Registry Configuration

This devkit reuses the DeDi registry records from other DEG devkits:
- BAP: `ev-charging.sandbox1.com` (unique keys for this domain)
- BPP: `ev-charging.sandbox2.com` (unique keys for this domain)

The test registry service is accessed at `https://api.dev.beckn.io/registry/dedi`.

## EV Charging Flow Overview

```
┌─────────────────┐                              ┌─────────────────┐
│  EV Driver App  │                              │ Charging Station │
│     (BAP)       │                              │   Operator       │
│                 │                              │     (BPP)       │
└────────┬────────┘                              └────────┬────────┘
         │                                                │
         │  /discover (location, filters)                 │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_discover (station catalog)                │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /select (station choice, quantity)            │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_select (pricing, confirmation)            │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /init (payment details)                        │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_init (ack)                                 │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /confirm (authorization)                       │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_confirm (session start)                    │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /status (polling)                              │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_status (progress updates)                  │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /update (modify session)                       │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_update (confirmation)                      │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /cancel (if needed)                            │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_cancel (refund/confirmation)              │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /rating (feedback)                             │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_rating (ack)                               │
         │◄───────────────────────────────────────────────│
```

## Troubleshooting

- **Container fails to start with schema error**: You may have a stale `fidedocker/onix-adapter` image. Pull the latest:
  ```bash
  docker pull fidedocker/onix-adapter
  ```

- **Registry lookup fails**: Ensure you have internet connectivity to `api.testnet.beckn.one`.

- **Sandbox health check fails**: Wait a few seconds for the sandbox containers to initialize, then check logs:
  ```bash
  docker logs sandbox-bap
  docker logs sandbox-bpp
  ```

## Regenerating Postman Collection

To regenerate the Postman collections for this devkit:

```bash
python3 scripts/generate_postman_collection.py --devkit ev-charging --role BAP --output-dir testnet/ev-charging-devkit/postman
python3 scripts/generate_postman_collection.py --devkit ev-charging --role BPP --output-dir testnet/ev-charging-devkit/postman
```