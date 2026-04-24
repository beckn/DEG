# P2P Enrollment Devkit

Beckn Protocol v2.0 devkit for **consumer enrollment to DER programmes**. A utility portal (BAP) enrolls a consumer into a programme owned by a programme owner (BPP), with the consumer proving authorisation via OTP or OAuth2/OIDC.

For the shared stack topology, prerequisites, Quick Start, transaction flow, hosting, ngrok notes, and cleanup, see [../README.md](../README.md).

## Use Cases

| Use Case | BAP (Consumer App) | BPP (Provider) | Description |
|----------|---------------------|----------------|-------------|
| [uc1-p2p-enrollment](./uc1-p2p-enrollment/) | Utility Portal | Programme Owner | OTP or OAuth2 enrollment → consent revocation → unenrollment |

Workflows covered:
- **OTP enrollment** — init → on_init (OTP challenge) → confirm → on_confirm
- **OAuth2 enrollment** — init → on_init (OAuth2 authz) → confirm → on_confirm
- **Consent revocation** — update → on_update
- **Unenrollment** — update → on_update

## Postman

`uc1-p2p-enrollment/postman/p2p-enrollment-uc1-p2p-enrollment.{BAP,BPP}-DEG.postman_collection.json`. Collections are regenerated with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Network Configuration (defaults)

| Parameter | Value |
|-----------|-------|
| Domain | `beckn.one:deg:p2p-enrollment:2.0.0` |
| BAP ID | `p2p-enrollment-sandbox1.com` |
| BPP ID | `p2p-enrollment-sandbox2.com` |
| BAP host (router) | `http://beckn-router:9000` |
| BPP host (router) | `http://beckn-router:9000` |
| BAP adapter caller | `http://localhost:8081/bap/caller` |
| BPP adapter caller | `http://localhost:8082/bpp/caller` |

## Related

- [Enrollment examples](./uc1-p2p-enrollment/examples/) — with scenario variants (`-otp`, `-oauth2`, `-success`, `-conflict`, `-error`)
- [P2P Enrollment Arazzo workflow](./uc1-p2p-enrollment/workflows/p2p-enrollment.arazzo.yaml)
- [Data Exchange Devkit](../data-exchange/) — companion devkit for inline dataset delivery
