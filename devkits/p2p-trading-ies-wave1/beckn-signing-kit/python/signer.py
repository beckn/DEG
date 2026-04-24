"""Beckn protocol payload signing for DEG (Digital Energy Grid).

Signs JSON payloads using Ed25519 + BLAKE2-512 and produces an Authorization
header compatible with the Beckn protocol specification.

Usage::

    signer = PayloadSigner(
        subscriber_id='p2p-trading-sandbox1.com',
        unique_key_id='76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ',
        signing_private_key='Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=',
    )

    auth_header = signer.sign_payload(payload_bytes)
"""

from __future__ import annotations

import base64
import hashlib
import time
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DEFAULT_EXPIRY_SECONDS = 300  # 5 minutes


@dataclass
class SignedResult:
    authorization_header: str
    created_at: int
    expires_at: int
    signature: str


class PayloadSigner:
    """Sign Beckn protocol payloads with Ed25519 + BLAKE2-512.

    Args:
        subscriber_id: Network participant ID (e.g. "p2p-trading-sandbox1.com").
        unique_key_id: Unique key ID registered in the Beckn registry.
        signing_private_key: Base64-encoded Ed25519 seed (32 bytes).
        expiry_seconds: Signature validity window in seconds (default 300).
    """

    def __init__(
        self,
        subscriber_id: str,
        unique_key_id: str,
        signing_private_key: str,
        expiry_seconds: int = DEFAULT_EXPIRY_SECONDS,
    ) -> None:
        if not subscriber_id:
            raise ValueError("signer: subscriber_id is required")
        if not unique_key_id:
            raise ValueError("signer: unique_key_id is required")
        if not signing_private_key:
            raise ValueError("signer: signing_private_key is required")

        try:
            seed = base64.b64decode(signing_private_key, validate=True)
        except Exception as exc:
            raise ValueError(f"signer: invalid base64 private key: {exc}") from exc

        # Validate that the base64 round-trips cleanly.
        if base64.b64encode(seed).decode() != signing_private_key:
            raise ValueError(
                "signer: invalid base64 private key: input is not valid base64"
            )

        if len(seed) != 32:
            raise ValueError(
                f"signer: private key seed must be 32 bytes, got {len(seed)}"
            )

        self._subscriber_id = subscriber_id
        self._unique_key_id = unique_key_id
        self._private_key = Ed25519PrivateKey.from_private_bytes(seed)
        self._expiry_seconds = expiry_seconds

    def sign_payload(self, body: bytes | str) -> str:
        """Sign a JSON payload and return the Authorization header value."""
        return self.sign_payload_detailed(body).authorization_header

    def sign_payload_detailed(self, body: bytes | str) -> SignedResult:
        """Sign a JSON payload and return full signing details."""
        now = int(time.time())
        return self._sign_payload_at(body, now)

    def _sign_payload_at(self, body: bytes | str, now_unix: int) -> SignedResult:
        """Sign at a specific Unix timestamp (used for deterministic testing)."""
        created_at = now_unix
        expires_at = now_unix + self._expiry_seconds

        body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
        signing_string = build_signing_string(body_bytes, created_at, expires_at)

        sig = self._private_key.sign(signing_string.encode("utf-8"))
        sig_b64 = base64.b64encode(sig).decode()

        header = (
            f'Signature keyId="{self._subscriber_id}|{self._unique_key_id}|ed25519"'
            f',algorithm="ed25519"'
            f',created="{created_at}"'
            f',expires="{expires_at}"'
            f',headers="(created) (expires) digest"'
            f',signature="{sig_b64}"'
        )

        return SignedResult(
            authorization_header=header,
            created_at=created_at,
            expires_at=expires_at,
            signature=sig_b64,
        )


def build_signing_string(body: bytes, created_at: int, expires_at: int) -> str:
    """Build the canonical signing string.

    Format::

        (created): {timestamp}
        (expires): {timestamp}
        digest: BLAKE-512={base64_hash}
    """
    digest = base64.b64encode(
        hashlib.blake2b(body, digest_size=64).digest()
    ).decode()

    return f"(created): {created_at}\n(expires): {expires_at}\ndigest: BLAKE-512={digest}"
