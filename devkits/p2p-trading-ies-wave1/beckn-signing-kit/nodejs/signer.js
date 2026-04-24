// Beckn protocol payload signing for DEG (Digital Energy Grid).
//
// Signs JSON payloads using Ed25519 + BLAKE2-512 and produces an Authorization
// header compatible with the Beckn protocol specification.
//
// Usage:
//
//   const signer = new PayloadSigner({
//     subscriberId:     'p2p-trading-sandbox1.com',
//     uniqueKeyId:      '76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
//     signingPrivateKey: 'Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
//   });
//
//   const authHeader = signer.signPayload(payloadBuffer);

'use strict';

const crypto = require('crypto');

// PKCS8 DER prefix for Ed25519 private key (wraps 32-byte seed).
const PKCS8_ED25519_PREFIX = Buffer.from('302e020100300506032b657004220420', 'hex');

const DEFAULT_EXPIRY_SECONDS = 300; // 5 minutes

class PayloadSigner {
  /**
   * @param {object} config
   * @param {string} config.subscriberId      - Network participant ID (e.g. "p2p-trading-sandbox1.com")
   * @param {string} config.uniqueKeyId       - Unique key ID registered in the Beckn registry
   * @param {string} config.signingPrivateKey  - Base64-encoded Ed25519 seed (32 bytes)
   * @param {number} [config.expirySeconds=300] - Signature validity window in seconds (default 5 minutes)
   */
  constructor(config) {
    if (!config.subscriberId) {
      throw new Error('signer: subscriberId is required');
    }
    if (!config.uniqueKeyId) {
      throw new Error('signer: uniqueKeyId is required');
    }
    if (!config.signingPrivateKey) {
      throw new Error('signer: signingPrivateKey is required');
    }

    let seed;
    try {
      seed = Buffer.from(config.signingPrivateKey, 'base64');
    } catch (e) {
      throw new Error(`signer: invalid base64 private key: ${e.message}`);
    }

    // Validate that the base64 round-trips cleanly (rejects non-base64 input).
    if (seed.toString('base64') !== config.signingPrivateKey) {
      throw new Error('signer: invalid base64 private key: input is not valid base64');
    }

    if (seed.length !== 32) {
      throw new Error(`signer: private key seed must be 32 bytes, got ${seed.length}`);
    }

    this._subscriberId = config.subscriberId;
    this._uniqueKeyId = config.uniqueKeyId;
    this._privateKey = crypto.createPrivateKey({
      key: Buffer.concat([PKCS8_ED25519_PREFIX, seed]),
      format: 'der',
      type: 'pkcs8',
    });
    this._expirySeconds = config.expirySeconds ?? DEFAULT_EXPIRY_SECONDS;
  }

  /**
   * Sign a JSON payload and return the Authorization header value.
   * @param {Buffer|string} body - Raw JSON payload
   * @returns {string} Authorization header value
   */
  signPayload(body) {
    return this.signPayloadDetailed(body).authorizationHeader;
  }

  /**
   * Sign a JSON payload and return full signing details.
   * @param {Buffer|string} body - Raw JSON payload
   * @returns {{ authorizationHeader: string, createdAt: number, expiresAt: number, signature: string }}
   */
  signPayloadDetailed(body) {
    const now = Math.floor(Date.now() / 1000);
    return this._signPayloadAt(body, now);
  }

  /**
   * Sign at a specific Unix timestamp (used for deterministic testing).
   * @param {Buffer|string} body
   * @param {number} nowUnix - Unix timestamp in seconds
   * @returns {{ authorizationHeader: string, createdAt: number, expiresAt: number, signature: string }}
   */
  _signPayloadAt(body, nowUnix) {
    const createdAt = nowUnix;
    const expiresAt = nowUnix + this._expirySeconds;

    const bodyBuf = Buffer.isBuffer(body) ? body : Buffer.from(body);
    const signingString = buildSigningString(bodyBuf, createdAt, expiresAt);

    const sig = crypto.sign(null, Buffer.from(signingString), this._privateKey);
    const sigB64 = sig.toString('base64');

    const header =
      `Signature keyId="${this._subscriberId}|${this._uniqueKeyId}|ed25519"` +
      `,algorithm="ed25519"` +
      `,created="${createdAt}"` +
      `,expires="${expiresAt}"` +
      `,headers="(created) (expires) digest"` +
      `,signature="${sigB64}"`;

    return {
      authorizationHeader: header,
      createdAt,
      expiresAt,
      signature: sigB64,
    };
  }
}

/**
 * Build the canonical signing string:
 *   (created): {timestamp}
 *   (expires): {timestamp}
 *   digest: BLAKE-512={base64_hash}
 */
function buildSigningString(body, createdAt, expiresAt) {
  const hash = crypto.createHash('blake2b512');
  hash.update(body);
  const digest = hash.digest('base64');

  return `(created): ${createdAt}\n(expires): ${expiresAt}\ndigest: BLAKE-512=${digest}`;
}

module.exports = { PayloadSigner };
