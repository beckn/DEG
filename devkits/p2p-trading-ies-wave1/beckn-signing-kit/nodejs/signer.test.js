'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');
const { PayloadSigner, verify, verifyAt, parseKeyId } = require('./index');

// Test keys matching the config in local-p2p-bap.yaml (sandbox1).
const TEST_SUBSCRIBER_ID = 'p2p-trading-sandbox1.com';
const TEST_KEY_ID = '76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ';
const TEST_PRIVATE_KEY = 'Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=';
const TEST_PUBLIC_KEY = 'KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE=';

// Sample beckn payload (trimmed confirm request).
const samplePayload = Buffer.from(JSON.stringify({
  context: {
    version: '2.0.0',
    action: 'confirm',
    timestamp: '2024-10-04T10:25:00Z',
    message_id: 'msg-confirm-001',
    transaction_id: 'txn-energy-001',
    bap_id: 'bap.energy-consumer.com',
    bap_uri: 'https://bap.energy-consumer.com',
    bpp_id: 'bpp.energy-provider.com',
    bpp_uri: 'https://bpp.energy-provider.com',
    domain: 'beckn.one:deg:p2p-trading:2.0.0',
  },
  message: {
    order: {
      '@type': 'beckn:Order',
      'beckn:orderStatus': 'CREATED',
      'beckn:seller': 'provider-solar-farm-001',
    },
  },
}));

function makeSigner(overrides) {
  return new PayloadSigner({
    subscriberId: TEST_SUBSCRIBER_ID,
    uniqueKeyId: TEST_KEY_ID,
    signingPrivateKey: TEST_PRIVATE_KEY,
    ...overrides,
  });
}

describe('PayloadSigner', () => {
  describe('constructor validation', () => {
    it('rejects missing subscriberId', () => {
      assert.throws(
        () => new PayloadSigner({ uniqueKeyId: 'k', signingPrivateKey: TEST_PRIVATE_KEY }),
        /subscriberId/,
      );
    });

    it('rejects missing uniqueKeyId', () => {
      assert.throws(
        () => new PayloadSigner({ subscriberId: 's', signingPrivateKey: TEST_PRIVATE_KEY }),
        /uniqueKeyId/,
      );
    });

    it('rejects missing signingPrivateKey', () => {
      assert.throws(
        () => new PayloadSigner({ subscriberId: 's', uniqueKeyId: 'k' }),
        /signingPrivateKey/,
      );
    });

    it('rejects invalid base64', () => {
      assert.throws(
        () => new PayloadSigner({ subscriberId: 's', uniqueKeyId: 'k', signingPrivateKey: 'not-base64!!!' }),
        /invalid base64/,
      );
    });

    it('rejects wrong key size', () => {
      const shortKey = Buffer.from('short').toString('base64');
      assert.throws(
        () => new PayloadSigner({ subscriberId: 's', uniqueKeyId: 'k', signingPrivateKey: shortKey }),
        /must be 32 bytes/,
      );
    });
  });

  describe('signPayload', () => {
    it('produces a valid Authorization header', () => {
      const signer = makeSigner();
      const authHeader = signer.signPayload(samplePayload);

      assert.ok(authHeader.startsWith('Signature '), 'should start with "Signature "');
      assert.ok(
        authHeader.includes(`${TEST_SUBSCRIBER_ID}|${TEST_KEY_ID}|ed25519`),
        'should contain keyId',
      );
      assert.ok(authHeader.includes('algorithm="ed25519"'), 'should contain algorithm');
    });
  });

  describe('signPayloadDetailed', () => {
    it('returns correct expiry window', () => {
      const signer = makeSigner();
      const result = signer.signPayloadDetailed(samplePayload);

      assert.equal(result.expiresAt - result.createdAt, 300, 'default expiry should be 300s');
      assert.ok(result.signature, 'signature should be non-empty');
      assert.ok(result.authorizationHeader, 'authorizationHeader should be non-empty');
    });

    it('respects custom expiry', () => {
      const signer = makeSigner({ expirySeconds: 60 });
      const result = signer.signPayloadDetailed(samplePayload);

      assert.equal(result.expiresAt - result.createdAt, 60);
    });
  });

  describe('accepts string body', () => {
    it('signs string payload identically to buffer', () => {
      const signer = makeSigner();
      const payloadStr = samplePayload.toString();

      // Both should produce valid signatures (can't compare directly due to timestamp)
      const authHeader = signer.signPayload(payloadStr);
      assert.ok(authHeader.startsWith('Signature '));
    });
  });
});

describe('sign and verify round-trip', () => {
  it('verifies a freshly signed payload', () => {
    const signer = makeSigner();
    const authHeader = signer.signPayload(samplePayload);

    // Should not throw
    verify(samplePayload, authHeader, TEST_PUBLIC_KEY);
  });

  it('rejects a tampered payload', () => {
    const signer = makeSigner();
    const authHeader = signer.signPayload(samplePayload);

    const tampered = Buffer.from(samplePayload);
    tampered[10] = tampered[10] ^ 0xff;

    assert.throws(
      () => verify(tampered, authHeader, TEST_PUBLIC_KEY),
      /verification failed/,
    );
  });

  it('rejects an expired signature', () => {
    const signer = makeSigner({ expirySeconds: 1 });
    const pastTime = Math.floor(Date.now() / 1000) - 600; // 10 minutes ago
    const result = signer._signPayloadAt(samplePayload, pastTime);

    assert.throws(
      () => verify(samplePayload, result.authorizationHeader, TEST_PUBLIC_KEY),
      /expired/,
    );
  });

  it('rejects a wrong public key', () => {
    const signer = makeSigner();
    const authHeader = signer.signPayload(samplePayload);

    // Generate a different key pair
    const { publicKey } = crypto.generateKeyPairSync('ed25519');
    const rawPub = publicKey.export({ format: 'der', type: 'spki' });
    // Extract the raw 32-byte key from SPKI DER (last 32 bytes)
    const wrongPubB64 = rawPub.subarray(rawPub.length - 32).toString('base64');

    assert.throws(
      () => verify(samplePayload, authHeader, wrongPubB64),
      /verification failed/,
    );
  });
});

describe('verifyAt', () => {
  it('rejects signature not yet valid', () => {
    const signer = makeSigner();
    const futureTime = Math.floor(Date.now() / 1000) + 3600;
    const result = signer._signPayloadAt(samplePayload, futureTime);

    // Verify at current time (before created)
    const nowUnix = Math.floor(Date.now() / 1000);
    assert.throws(
      () => verifyAt(samplePayload, result.authorizationHeader, TEST_PUBLIC_KEY, nowUnix),
      /not yet valid/,
    );
  });
});

describe('parseKeyId', () => {
  it('parses a valid keyId', () => {
    const result = parseKeyId('p2p-trading-sandbox1.com|76EU8aUq|ed25519');
    assert.deepEqual(result, {
      subscriberId: 'p2p-trading-sandbox1.com',
      uniqueKeyId: '76EU8aUq',
      algorithm: 'ed25519',
    });
  });

  it('rejects invalid format', () => {
    assert.throws(() => parseKeyId('bad-format'), /invalid keyId format/);
  });
});
