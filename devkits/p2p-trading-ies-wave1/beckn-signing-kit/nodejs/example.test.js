'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { PayloadSigner, verify } = require('./index');

describe('usage examples', () => {
  it('sign and attach to HTTP request', () => {
    // 1. Configure the signer with your keys from the YAML config.
    //    These come from the simplekeymanager / degledgerrecorder config.
    const signer = new PayloadSigner({
      subscriberId: 'p2p-trading-sandbox1.com',
      uniqueKeyId: '76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
      signingPrivateKey: 'Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
    });

    // 2. Your beckn JSON payload (confirm, on_confirm, on_status, etc.)
    const payload = JSON.stringify({
      context: {
        action: 'confirm',
        domain: 'beckn.one:deg:p2p-trading:2.0.0',
        bap_id: 'bap.energy-consumer.com',
      },
      message: {
        order: { '@type': 'beckn:Order', 'beckn:orderStatus': 'CREATED' },
      },
    });

    // 3. Sign it — this is the entire SDK surface.
    const authHeader = signer.signPayload(payload);

    // 4. Attach to HTTP request (e.g., posting to ledger service).
    //    const res = await fetch('https://ledger.example.com/record', {
    //      method: 'POST',
    //      headers: {
    //        'Content-Type': 'application/json',
    //        'Authorization': authHeader,
    //      },
    //      body: payload,
    //    });

    assert.ok(authHeader.startsWith('Signature keyId="p2p-trading-sandbox1.com|76EU8aUq'));
  });

  it('verify an incoming signed request', () => {
    const payload = JSON.stringify({ context: { action: 'confirm' } });

    // Sender side: sign
    const signer = new PayloadSigner({
      subscriberId: 'p2p-trading-sandbox1.com',
      uniqueKeyId: '76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
      signingPrivateKey: 'Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
    });
    const authHeader = signer.signPayload(payload);

    // Receiver side: verify (look up public key from registry)
    const senderPublicKey = 'KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE=';
    verify(payload, authHeader, senderPublicKey); // throws on failure

    assert.ok(true, 'Signature valid!');
  });
});
