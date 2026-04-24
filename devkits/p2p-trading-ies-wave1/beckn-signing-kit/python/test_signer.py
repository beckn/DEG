"""Tests for the Beckn DEG signing kit — mirrors the Node.js / Go / C# test suites."""

import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from . import PayloadSigner, SignatureVerificationError, parse_key_id, verify, verify_at

# Test keys matching the config in local-p2p-bap.yaml (sandbox1).
TEST_SUBSCRIBER_ID = "p2p-trading-sandbox1.com"
TEST_KEY_ID = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ"
TEST_PRIVATE_KEY = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw="
TEST_PUBLIC_KEY = "KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE="

# Sample beckn payload (trimmed confirm request).
SAMPLE_PAYLOAD = json.dumps(
    {
        "context": {
            "version": "2.0.0",
            "action": "confirm",
            "timestamp": "2024-10-04T10:25:00Z",
            "message_id": "msg-confirm-001",
            "transaction_id": "txn-energy-001",
            "bap_id": "bap.energy-consumer.com",
            "bap_uri": "https://bap.energy-consumer.com",
            "bpp_id": "bpp.energy-provider.com",
            "bpp_uri": "https://bpp.energy-provider.com",
            "domain": "beckn.one:deg:p2p-trading:2.0.0",
        },
        "message": {
            "order": {
                "@type": "beckn:Order",
                "beckn:orderStatus": "CREATED",
                "beckn:seller": "provider-solar-farm-001",
            },
        },
    }
).encode()


def _make_signer(**overrides):
    kwargs = {
        "subscriber_id": TEST_SUBSCRIBER_ID,
        "unique_key_id": TEST_KEY_ID,
        "signing_private_key": TEST_PRIVATE_KEY,
    }
    kwargs.update(overrides)
    return PayloadSigner(**kwargs)


class TestPayloadSignerConstructor(unittest.TestCase):
    def test_rejects_missing_subscriber_id(self):
        with self.assertRaises(ValueError, msg="subscriber_id"):
            PayloadSigner(
                subscriber_id="",
                unique_key_id="k",
                signing_private_key=TEST_PRIVATE_KEY,
            )

    def test_rejects_missing_unique_key_id(self):
        with self.assertRaises(ValueError, msg="unique_key_id"):
            PayloadSigner(
                subscriber_id="s",
                unique_key_id="",
                signing_private_key=TEST_PRIVATE_KEY,
            )

    def test_rejects_missing_signing_private_key(self):
        with self.assertRaises(ValueError, msg="signing_private_key"):
            PayloadSigner(
                subscriber_id="s",
                unique_key_id="k",
                signing_private_key="",
            )

    def test_rejects_invalid_base64(self):
        with self.assertRaises(ValueError, msg="invalid base64"):
            PayloadSigner(
                subscriber_id="s",
                unique_key_id="k",
                signing_private_key="not-base64!!!",
            )

    def test_rejects_wrong_key_size(self):
        import base64

        short_key = base64.b64encode(b"short").decode()
        with self.assertRaises(ValueError, msg="must be 32 bytes"):
            PayloadSigner(
                subscriber_id="s",
                unique_key_id="k",
                signing_private_key=short_key,
            )


class TestSignPayload(unittest.TestCase):
    def test_produces_valid_authorization_header(self):
        signer = _make_signer()
        auth_header = signer.sign_payload(SAMPLE_PAYLOAD)

        self.assertTrue(auth_header.startswith("Signature "))
        self.assertIn(f"{TEST_SUBSCRIBER_ID}|{TEST_KEY_ID}|ed25519", auth_header)
        self.assertIn('algorithm="ed25519"', auth_header)


class TestSignPayloadDetailed(unittest.TestCase):
    def test_returns_correct_expiry_window(self):
        signer = _make_signer()
        result = signer.sign_payload_detailed(SAMPLE_PAYLOAD)

        self.assertEqual(result.expires_at - result.created_at, 300)
        self.assertTrue(result.signature)
        self.assertTrue(result.authorization_header)

    def test_respects_custom_expiry(self):
        signer = _make_signer(expiry_seconds=60)
        result = signer.sign_payload_detailed(SAMPLE_PAYLOAD)

        self.assertEqual(result.expires_at - result.created_at, 60)


class TestStringBody(unittest.TestCase):
    def test_signs_string_payload(self):
        signer = _make_signer()
        auth_header = signer.sign_payload(SAMPLE_PAYLOAD.decode())
        self.assertTrue(auth_header.startswith("Signature "))


class TestSignAndVerifyRoundTrip(unittest.TestCase):
    def test_verifies_freshly_signed_payload(self):
        signer = _make_signer()
        auth_header = signer.sign_payload(SAMPLE_PAYLOAD)

        # Should not raise.
        verify(SAMPLE_PAYLOAD, auth_header, TEST_PUBLIC_KEY)

    def test_rejects_tampered_payload(self):
        signer = _make_signer()
        auth_header = signer.sign_payload(SAMPLE_PAYLOAD)

        tampered = bytearray(SAMPLE_PAYLOAD)
        tampered[10] ^= 0xFF
        tampered = bytes(tampered)

        with self.assertRaises(SignatureVerificationError, msg="verification failed"):
            verify(tampered, auth_header, TEST_PUBLIC_KEY)

    def test_rejects_expired_signature(self):
        import time

        signer = _make_signer(expiry_seconds=1)
        past_time = int(time.time()) - 600  # 10 minutes ago
        result = signer._sign_payload_at(SAMPLE_PAYLOAD, past_time)

        with self.assertRaises(ValueError, msg="expired"):
            verify(SAMPLE_PAYLOAD, result.authorization_header, TEST_PUBLIC_KEY)

    def test_rejects_wrong_public_key(self):
        import base64

        signer = _make_signer()
        auth_header = signer.sign_payload(SAMPLE_PAYLOAD)

        # Generate a different key pair.
        wrong_key = Ed25519PrivateKey.generate()
        wrong_pub_bytes = wrong_key.public_key().public_bytes_raw()
        wrong_pub_b64 = base64.b64encode(wrong_pub_bytes).decode()

        with self.assertRaises(SignatureVerificationError, msg="verification failed"):
            verify(SAMPLE_PAYLOAD, auth_header, wrong_pub_b64)


class TestVerifyAt(unittest.TestCase):
    def test_rejects_signature_not_yet_valid(self):
        import time

        signer = _make_signer()
        future_time = int(time.time()) + 3600
        result = signer._sign_payload_at(SAMPLE_PAYLOAD, future_time)

        now_unix = int(time.time())
        with self.assertRaises(ValueError, msg="not yet valid"):
            verify_at(
                SAMPLE_PAYLOAD,
                result.authorization_header,
                TEST_PUBLIC_KEY,
                now_unix,
            )


class TestParseKeyId(unittest.TestCase):
    def test_parses_valid_key_id(self):
        result = parse_key_id("p2p-trading-sandbox1.com|76EU8aUq|ed25519")
        self.assertEqual(
            result,
            {
                "subscriber_id": "p2p-trading-sandbox1.com",
                "unique_key_id": "76EU8aUq",
                "algorithm": "ed25519",
            },
        )

    def test_rejects_invalid_format(self):
        with self.assertRaises(ValueError, msg="invalid keyId format"):
            parse_key_id("bad-format")


if __name__ == "__main__":
    unittest.main()
