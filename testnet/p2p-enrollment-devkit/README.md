# P2P Enrollment Devkit

Goal of this devkit is to enable a developer to test round trip Beckn v2.0 mock messages for **user enrollment flows** between network actors (BAP - Utility Portal, BPP - Program Owner) on their local machine within a few minutes.

This devkit supports:
- **OTP-based enrollment**: User authenticates via mobile OTP
- **OAuth2/OIDC-based enrollment**: User authenticates via utility's OAuth2 provider

It is a *batteries included* sandbox environment that requires minimal setup, with environment variables and registry connections pre-configured.

## Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) & run it in background
2. Install [Git](https://git-scm.com/downloads) and ensure it's added to your system path
3. Install [Postman](https://www.postman.com/downloads/)

## Setup

1. Clone this repository and navigate to the install directory:

```bash
git clone -b p2p-trading https://github.com/Beckn-One/DEG.git
cd DEG/testnet/p2p-enrollment-devkit/install
```

2. Start the containers:

```bash
docker compose -f ./docker-compose-adapter-enrollment.yml up -d
docker ps
```

Verify the following containers are running:
- `redis-enrollment`
- `onix-enrollment-bap`
- `onix-enrollment-bpp`
- `sandbox-enrollment-bap`
- `sandbox-enrollment-bpp`

3. Open Postman and import the folder `DEG/testnet/p2p-enrollment-devkit/postman` to import all collections.

## Testing the Enrollment Flow

### BAP Collection (Utility Portal initiating enrollment)

Use the `p2p-enrollment:BAP-DEG` collection:

1. **init** - Initiate enrollment with user authentication
   - `init-request-otp` - Start OTP-based enrollment (sends mobile number)
   - `init-request-oauth2` - Start OAuth2-based enrollment (sends tokens)
   - `init-request-simple-consumer` - Simple consumer enrollment
   - `init-request-prosumer-solar-battery` - Prosumer with DER enrollment

2. **confirm** - Confirm enrollment with meter selection
   - `confirm-request-otp` - Confirm OTP enrollment with OTP verification and meter selection
   - `confirm-request-oauth2` - Confirm OAuth2 enrollment with meter selection
   - `confirm-request` - Standard confirm with credentials

3. **update** - Update enrollment
   - `update-request-consent-revocation` - Revoke consent
   - `update-request-unenrollment` - Unenroll from program

### BPP Collection (Program Owner responding)

Use the `p2p-enrollment:BPP-DEG` collection:

1. **on_init** - Respond to init requests
   - `on-init-response-otp` - Return NGUID for OTP verification
   - `on-init-response-oauth2` - Return verified status with available meters
   - `on-init-response-success` - Successful verification
   - `on-init-response-conflict` - Enrollment conflict detected
   - `on-init-response-error` - Error response

2. **on_confirm** - Respond to confirm requests
   - `on-confirm-response-otp` - OTP enrollment success with credentials
   - `on-confirm-response-oauth2` - OAuth2 enrollment success
   - `on-confirm-response-success` - Standard success with credential
   - `on-confirm-response-no-meter` - Error: no meter specified

3. **on_update** - Respond to update requests
   - `on-update-response-consent-revocation` - Consent revoked
   - `on-update-response-unenrollment` - Unenrollment confirmed

## Viewing Responses

The request responses will show an "Ack" message. Detailed `on_init`, `on_confirm`, `on_update` messages from BPP should be visible in the BAP logs:

```bash
docker logs -f onix-enrollment-bap
```

## Stopping the Environment

```bash
docker compose -f ./docker-compose-adapter-enrollment.yml down
```

## Configuration

### Environment Variables (Pre-configured in Postman collections)

| Variable Name     | Value                                   | Notes           |
| :---------------- | :-------------------------------------- | :-------------- |
| `domain`          | `beckn.one:deg:p2p-enrollment:2.0.0`    |                 |
| `version`         | `2.0.0`                                 |                 |
| `bap_id`          | `p2p-enrollment-sandbox1.com`           |                 |
| `bap_uri`         | `http://onix-bap:8081/bap/receiver`     |                 |
| `bpp_id`          | `p2p-enrollment-sandbox2.com`           |                 |
| `bpp_uri`         | `http://onix-bpp:8082/bpp/receiver`     |                 |
| `bap_adapter_url` | `http://localhost:8081/bap/caller`      | BAP collection  |
| `bpp_adapter_url` | `http://localhost:8082/bpp/caller`      | BPP collection  |
| `transaction_id`  | Auto-generated UUID                     |                 |
| `iso_date`        | Auto-generated ISO timestamp            |                 |

### Registry Configuration

This devkit reuses the DeDi registry records from the P2P Trading devkit:
- BAP: `p2p-trading-sandbox1.com` (same keys, different domain)
- BPP: `p2p-trading-sandbox2.com` (same keys, different domain)

The registry service is accessed at `https://api.dev.beckn.io/registry/dedi`.

## Enrollment Flow Overview

```
┌─────────────────┐                              ┌─────────────────┐
│  Utility Portal │                              │  Program Owner  │
│     (BAP)       │                              │     (BPP)       │
└────────┬────────┘                              └────────┬────────┘
         │                                                │
         │  /init (mobile for OTP or tokens for OAuth2)   │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_init (nguid for OTP or meters for OAuth2) │
         │◄───────────────────────────────────────────────│
         │                                                │
         │  /confirm (OTP + meters or tokens + meters)    │
         │───────────────────────────────────────────────►│
         │                                                │
         │  /on_confirm (enrollment credential + status)  │
         │◄───────────────────────────────────────────────│
         │                                                │
```

## Troubleshooting

- **Container fails to start with schema error**: You may have a stale `fidedocker/onix-adapter` image. Pull the latest:
  ```bash
  docker pull fidedocker/onix-adapter
  ```

- **Registry lookup fails**: Ensure you have internet connectivity to `api.testnet.beckn.one`.

- **Sandbox health check fails**: Wait a few seconds for the sandbox containers to initialize, then check logs:
  ```bash
  docker logs sandbox-enrollment-bap
  docker logs sandbox-enrollment-bpp
  ```

## Regenerating Postman Collection

To regenerate the Postman collections for this devkit:

```bash
python3 scripts/generate_postman_collection.py --devkit p2p-enrollment --role BAP --output-dir testnet/p2p-enrollment-devkit/postman
python3 scripts/generate_postman_collection.py --devkit p2p-enrollment --role BPP --output-dir testnet/p2p-enrollment-devkit/postman
```

