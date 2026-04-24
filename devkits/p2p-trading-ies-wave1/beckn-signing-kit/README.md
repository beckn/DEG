# Signing Kit for adding auth header when connecting to ledger service

SDKs for sign payload using Ed25519 signature to connect to ledger service.

## What it does

**In:** JSON payload (any beckn action — `confirm`, `on_confirm`, `on_status`, etc.)
**Out:** `Authorization` header value with Ed25519 signature

```
Payload bytes  ──►  PayloadSigner.SignPayload()  ──►  Authorization header string
```

The Authorization header follows the [Beckn Protocol signing specification](https://github.com/beckn/beckn-onix):

```
Signature keyId="{subscriberId}|{keyId}|ed25519",algorithm="ed25519",created="{unix_ts}",expires="{unix_ts}",headers="(created) (expires) digest",signature="{base64_sig}"
```

## Signing algorithm

1. **BLAKE2-512** hash of the raw JSON payload body
2. Build signing string: `(created): {ts}\n(expires): {ts}\ndigest: BLAKE-512={base64_hash}`
3. **Ed25519** sign the signing string using the 32-byte private key seed
4. Format the `Authorization` header with `keyId`, timestamps, and base64 signature

## Configuration

You need three values from your beckn-onix YAML config (`simplekeymanager` or `degledgerrecorder` section):

| Field | Example | Description |
|-------|---------|-------------|
| `subscriberId` / `networkParticipant` | `p2p-trading-sandbox1.com` | Your registered network participant ID |
| `keyId` | `76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ` | Unique key ID registered in the Beckn DeDi registry |
| `signingPrivateKey` | `Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=` | Base64-encoded Ed25519 seed (32 bytes) |

These map directly to your `local-p2p-bap.yaml` config:

```yaml
# From degledgerrecorder config
signingPrivateKey: Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=
networkParticipant: p2p-trading-sandbox1.com
keyId: 76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ
```

## SDKs

### [Go](./golang/)

```go
s, _ := signer.New(signer.Config{
    SubscriberID:     "p2p-trading-sandbox1.com",
    UniqueKeyID:      "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
    SigningPrivateKey: "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
})

authHeader, _ := s.SignPayload(payloadBytes)
req.Header.Set("Authorization", authHeader)
```

**Run tests:** `cd golang && go test -v ./...`

### [ASP.NET / C#](./aspdotnet/)

```csharp
var signer = new PayloadSigner(new SignerConfig {
    SubscriberId = "p2p-trading-sandbox1.com",
    UniqueKeyId = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
    SigningPrivateKey = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
});

string authHeader = signer.SignPayload(payloadJson);
request.Headers.Add("Authorization", authHeader);
```

**Run tests:** `cd aspdotnet && dotnet test`

### [Node.js](./nodejs/)

Zero dependencies — uses Node.js built-in `crypto` (requires Node.js 18+).

```js
const { PayloadSigner } = require('@beckn/deg-discom-signing-kit');

const signer = new PayloadSigner({
    subscriberId: 'p2p-trading-sandbox1.com',
    uniqueKeyId: '76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
    signingPrivateKey: 'Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
});

const authHeader = signer.signPayload(payloadJson);
// Set on HTTP request: headers['Authorization'] = authHeader
```

**Run tests:** `cd nodejs && node --test`

### [Python](./python/)

Requires Python 3.10+ and the `cryptography` library.

```python
from python import PayloadSigner

signer = PayloadSigner(
    subscriber_id='p2p-trading-sandbox1.com',
    unique_key_id='76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
    signing_private_key='Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
)

auth_header = signer.sign_payload(payload_json)
# Set on HTTP request: headers['Authorization'] = auth_header
```

**Run tests:** `cd python && pip install -e '.[test]' && pytest -v`

## Verification (optional)

All SDKs also include a verifier to validate incoming signed requests:

```go
// Go
err := signer.Verify(body, authHeader, senderPublicKey)
```

```csharp
// C#
PayloadVerifier.Verify(body, authHeader, senderPublicKey);
```

```js
// Node.js
const { verify } = require('@beckn/deg-discom-signing-kit');
verify(body, authHeader, senderPublicKey); // throws on failure
```

```python
# Python
from python import verify
verify(body, auth_header, sender_public_key)  # raises on failure
```
