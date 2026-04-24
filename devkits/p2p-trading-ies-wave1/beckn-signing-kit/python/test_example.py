"""Usage examples — mirrors example.test.js from the Node.js implementation."""

import json
import unittest

from . import PayloadSigner, verify


class TestUsageExamples(unittest.TestCase):
    def test_sign_and_attach_to_http_request(self):
        # 1. Configure the signer with your keys from the YAML config.
        #    These come from the simplekeymanager / degledgerrecorder config.
        signer = PayloadSigner(
            subscriber_id="p2p-trading-sandbox1.com",
            unique_key_id="76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
            signing_private_key="Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
        )

        # 2. Your beckn JSON payload (confirm, on_confirm, on_status, etc.)
        payload = json.dumps(
            {
                "context": {
                    "action": "confirm",
                    "domain": "beckn.one:deg:p2p-trading:2.0.0",
                    "bap_id": "bap.energy-consumer.com",
                },
                "message": {
                    "order": {
                        "@type": "beckn:Order",
                        "beckn:orderStatus": "CREATED",
                    },
                },
            }
        )

        # 3. Sign it — this is the entire SDK surface.
        auth_header = signer.sign_payload(payload)

        # 4. Attach to HTTP request (e.g., posting to ledger service).
        #    import requests
        #    resp = requests.post(
        #        'https://ledger.example.com/record',
        #        headers={
        #            'Content-Type': 'application/json',
        #            'Authorization': auth_header,
        #        },
        #        data=payload,
        #    )

        self.assertTrue(
            auth_header.startswith(
                'Signature keyId="p2p-trading-sandbox1.com|76EU8aUq'
            )
        )

    def test_verify_incoming_signed_request(self):
        payload = json.dumps({"context": {"action": "confirm"}})

        # Sender side: sign
        signer = PayloadSigner(
            subscriber_id="p2p-trading-sandbox1.com",
            unique_key_id="76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
            signing_private_key="Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
        )
        auth_header = signer.sign_payload(payload)

        # Receiver side: verify (look up public key from registry)
        sender_public_key = "KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE="
        verify(payload, auth_header, sender_public_key)  # raises on failure


if __name__ == "__main__":
    unittest.main()
