# DEG Devkits

Each devkit spins up a self-contained BAP↔BPP stack for one use-case family over Beckn Protocol v2.0. They share a common topology, Quick Start, ngrok workflow, and cleanup — documented here once — and differ only in the domain-specific schemas, example payloads, and Arazzo workflows shipped per devkit.

| Devkit | Focus |
|--------|-------|
| [data-exchange](./data-exchange/) | Inline dataset delivery via DDM — meter data and regulatory (ARR) filings |
| [demand-flex](./demand-flex/) | Behavioural demand response — need, buy offer, performance |
| [ev-charging](./ev-charging/) | EV charging discovery, reservation, session, billing |
| [p2p-enrollment](./p2p-enrollment/) | Consumer enrollment to DER programmes (OTP, OAuth2) |
| [p2p-trading-ies-wave1](./p2p-trading-ies-wave1/) | Peer-to-peer trading across discoms |

Jump into a devkit's own README for the use-case table, schemas, and example payload notes; the rest of this page is the shared stack-and-runtime guide.

## Stack Topology

```
               internet (optional, via ngrok)
                          │
                  https://<public-host>/
                          │
                     :9000 (host)
                          │
                    ┌──beckn-router──┐   (Caddy; the only container on both networks)
                    │                │
              /bap/* │                │ /bpp/*
                    │                │
   ┌── bap_side ────┘                └──── bpp_side ──┐
   │  onix-bap:8081                   onix-bpp:8082   │
   │  sandbox-bap:3001                sandbox-bpp:3002│
   │  redis                           redis           │
   └──────────────────────────────────────────────────┘
```

BAP-side and BPP-side services sit on independent docker networks; the Caddy router on `:9000` is the sole bridge. All BAP↔BPP traffic passes through it, so the same container image/config runs unchanged whether you're hitting the router locally or through a public tunnel.

## Prerequisites

Git, Docker, Docker Compose, (optional) Postman, (optional) ngrok.

## Quick Start

```bash
git clone https://github.com/beckn/DEG
cd DEG/devkits
# cd specific-devkit-you-want (e.g. data-exchange, demand-flex, ev-charging, ...)
cd install
docker compose up -d

# Pick a mode for the Arazzo runner:
#   (a) Strictly local — default if PUBLIC_URL is unset or empty.
#       Caddy bridges BAP↔BPP inside docker, no internet.
export PUBLIC_URL=http://beckn-router:9000
#   (b) Over the public internet via ngrok — set PUBLIC_URL to the tunnel URL.
#       cp ngrok.yml.example ngrok.yml  # paste your authtoken
#       ngrok start --all --config ngrok.yml
# export PUBLIC_URL=https://<your-subdomain>.ngrok-free.dev

# Run automated tests (for quick devkit testing)
cd ../uc*-specific-usecase-within-devkit/workflows
PUBLIC_URL=$PUBLIC_URL ./run-arazzo.sh -w select-through-status -v

# Manual API tests
# Run postman collections for local test. Variables {{bap_host_root}} and {{bpp_host_root}} default to http://beckn-router:9000
# For testing over ngrok, change those variables to the ngrok-provided static URL.
```

`./run-arazzo.sh` with no args runs all workflows for the use case. Typical workflows: `publish-catalog`, `discover`, `select-through-status`, `<domain>-cancellation`.

## Full transaction flow (reference)

```
BPP (Provider)      Catalog Service     Discovery Service       BAP (Consumer)
    |                     |                    |                      |
    |                     |<-- subscribe ------|                      |
    |                     |   (catalog updates)|                      |
    |                     |                    |                      |
    |-- publish --------->|                    |                      |
    |   (domain catalog)  |                    |                      |
    |                     |                    |                      |
    |                     |                    |<---- discover -------|
    |                     |                    |     (search)         |
    |                     |                    |---- on_discover ---->|
    |                     |                    |     (catalog results)|
    |                     |                    |                      |
    |---------------------+--------------------+----------------------|
    |                  Direct BAP <-> BPP negotiation                 |
    |                                                                 |
    |<---- select ---------------------------------------------------|
    |---- on_select (terms) ---------------------------------------->|
    |                                                                 |
    |<---- init (details) -------------------------------------------|
    |---- on_init (ready) ------------------------------------------>|
    |                                                                 |
    |<---- confirm --------------------------------------------------|
    |---- on_confirm (active) -------------------------------------->|
    |                                                                 |
    |<---- status (check) -------------------------------------------|
    |---- on_status (PROCESSING / DELIVERED / SETTLED) ------------->|
    |                                                                 |
    |<---- cancel (optional) ----------------------------------------|
    |---- on_cancel ------------------------------------------------>|
```

**Minimal sanity check**: from any devkit's BAP Postman collection, fire `confirm` and look for `on_confirm` arriving back. That single round-trip exercises sign → route → verify on both sides and is enough to prove the wiring end-to-end; the other steps are only needed to walk through the full protocol.

## Hosting the site (beyond the devkit)

`PUBLIC_URL` is the beckn-facing URL your BAP/BPP expose; in production it's your real HTTPS hostname, with TLS terminated somewhere in front of `beckn-router:9000`. The rest of the work is **identity**, not infrastructure:

1. **Terminate TLS in front of the router.** beckn-router (the in-stack Caddy) listens plain HTTP on `:9000` — fine for local and for ngrok (ngrok terminates TLS for you), but a real deployment needs a proper cert. Three common patterns:

   - **Host-level reverse proxy** — nginx / host Caddy / Traefik on the VM, with a Let's Encrypt cert for your hostname, `proxy_pass` → `127.0.0.1:9000`. Leaves the devkit stack unchanged.
   - **Let the devkit Caddy do TLS itself** — edit `install/Caddyfile`: drop `auto_https off`, replace `:9000` with `your.hostname.com`, publish `80:80` and `443:443` on the `beckn-router` service, and mount a persistent volume on `/data` so issued certs survive restarts. Then no extra proxy is needed.
   - **Managed edge** — Cloudflare / AWS ALB / GCP HTTPS LB / Cloudflare Tunnel. Terminate TLS at the edge, point the origin at `<your-host>:9000`. Zero changes to the stack.

2. **Create DeDi registry records** for your subscriber — one record per role (BAP, BPP) per network. See [docs.beckn.io](https://docs.beckn.io/) for the current record schema and where in the protocol flow the registry is consulted (sign/verify during every message).

3. **Update your onix config** (`config/local-*-bap.yaml`, `config/local-*-bpp.yaml`) so the identity fields match your DeDi record. The mapping:

   | DeDi registry field | Onix config field |
   |---------------------|-------------------|
   | `recordId`          | `keyId`           |
   | `subscriberId`      | `networkParticipant` |
   | `domain`            | `allowedNetworkIDs` entry (network ID in beckn context) |

4. **Ask the network namespace owner** (e.g. for `nfh.global/testnet-deg`, that's `nfh.global`) to add your subscriber record to the network's beckn reference registry. This is required whenever a network's `allowedNetworkIDs` on the adapter is non-empty — adapters reject messages from subscribers not listed there.

One beckn server can belong to multiple networks: list each one in `allowedNetworkIDs` and register a corresponding DeDi record per network.

## Over-the-internet notes

Run the stack, start ngrok, set `PUBLIC_URL=https://<tunnel>.ngrok-free.dev`, run the arazzo scripts. The runner materialises a tmpdir with a copy of the arazzo file and patched example payloads (`bapUri`/`bppUri` rewritten to the public URL) and invokes Respect against it, so sources on disk stay untouched. Watch the tunnel at `http://localhost:4040` — each transactional step shows three hops: `your curl → BAP`, `BAP → BPP`, `BPP → BAP callback`.

The `discover` step calls an external discovery service; its outcome is independent of the devkit's topology. The catalog-service subscription is a one-time network setup call (not part of the transactional flow); devkits that need it ship a `scripts/subscribe-catalog.sh`.

## Cleanup

```bash
cd install
docker compose down
pkill -f 'ngrok start'   # if ngrok was running
```

## Related

- [docs.beckn.io](https://docs.beckn.io/) — DeDi registry, subscriber identity, message signing
