'use strict';

const crypto = require('crypto');

// SPKI DER prefix for Ed25519 public key (wraps 32-byte raw key).
const SPKI_ED25519_PREFIX = Buffer.from('302a300506032b6570032100', 'hex');

/**
 * Verify that an Authorization header is a valid signature for the given body,
 * using the sender's base64-encoded public key. Throws on failure.
 *
 * @param {Buffer|string} body           - Raw JSON payload
 * @param {string}        authHeader     - Authorization header value
 * @param {string}        publicKeyBase64 - Base64-encoded Ed25519 public key (32 bytes)
 */
function verify(body, authHeader, publicKeyBase64) {
  const nowUnix = Math.floor(Date.now() / 1000);
  verifyAt(body, authHeader, publicKeyBase64, nowUnix);
}

/**
 * Verify at a specific Unix timestamp (useful for testing).
 *
 * @param {Buffer|string} body
 * @param {string}        authHeader
 * @param {string}        publicKeyBase64
 * @param {number}        nowUnix - Unix timestamp in seconds
 */
function verifyAt(body, authHeader, publicKeyBase64, nowUnix) {
  const { created, expires, signature } = parseAuthHeader(authHeader);

  if (created > nowUnix) {
    throw new Error(`verifier: signature not yet valid (created ${created} > now ${nowUnix})`);
  }
  if (nowUnix > expires) {
    throw new Error(`verifier: signature expired (expires ${expires} < now ${nowUnix})`);
  }

  let sigBytes;
  try {
    sigBytes = Buffer.from(signature, 'base64');
  } catch (e) {
    throw new Error(`verifier: invalid signature base64: ${e.message}`);
  }

  const bodyBuf = Buffer.isBuffer(body) ? body : Buffer.from(body);
  const signingString = buildSigningString(bodyBuf, created, expires);

  let pubKeyBytes;
  try {
    pubKeyBytes = Buffer.from(publicKeyBase64, 'base64');
  } catch (e) {
    throw new Error(`verifier: invalid public key base64: ${e.message}`);
  }

  const publicKey = crypto.createPublicKey({
    key: Buffer.concat([SPKI_ED25519_PREFIX, pubKeyBytes]),
    format: 'der',
    type: 'spki',
  });

  const valid = crypto.verify(null, Buffer.from(signingString), publicKey, sigBytes);
  if (!valid) {
    throw new Error('verifier: signature verification failed');
  }
}

/**
 * Extract subscriberID, uniqueKeyID, and algorithm from a keyId field.
 * Format: "subscriber_id|unique_key_id|algorithm"
 *
 * @param {string} keyId
 * @returns {{ subscriberId: string, uniqueKeyId: string, algorithm: string }}
 */
function parseKeyId(keyId) {
  const parts = keyId.split('|');
  if (parts.length !== 3) {
    throw new Error(`invalid keyId format, expected 'subscriber|keyId|algorithm', got "${keyId}"`);
  }
  return {
    subscriberId: parts[0],
    uniqueKeyId: parts[1],
    algorithm: parts[2],
  };
}

/**
 * Build the canonical signing string.
 */
function buildSigningString(body, createdAt, expiresAt) {
  const hash = crypto.createHash('blake2b512');
  hash.update(body);
  const digest = hash.digest('base64');

  return `(created): ${createdAt}\n(expires): ${expiresAt}\ndigest: BLAKE-512=${digest}`;
}

/**
 * Parse the Authorization header to extract created, expires, and signature.
 */
function parseAuthHeader(header) {
  const stripped = header.startsWith('Signature ') ? header.slice('Signature '.length) : header;

  const params = {};
  for (const part of stripped.split(',')) {
    const eqIdx = part.indexOf('=');
    if (eqIdx !== -1) {
      const key = part.slice(0, eqIdx).trim();
      const val = part.slice(eqIdx + 1).replace(/^"|"$/g, '');
      params[key] = val;
    }
  }

  if (!params.created) {
    throw new Error("missing 'created' in auth header");
  }
  if (!params.expires) {
    throw new Error("missing 'expires' in auth header");
  }
  if (!params.signature) {
    throw new Error("missing 'signature' in auth header");
  }

  const created = parseInt(params.created, 10);
  if (isNaN(created)) {
    throw new Error(`invalid 'created' timestamp: ${params.created}`);
  }

  const expires = parseInt(params.expires, 10);
  if (isNaN(expires)) {
    throw new Error(`invalid 'expires' timestamp: ${params.expires}`);
  }

  return { created, expires, signature: params.signature };
}

module.exports = { verify, verifyAt, parseKeyId };
