"""Beckn protocol signature verification for DEG (Digital Energy Grid).

Verifies Authorization headers produced by PayloadSigner against
the sender's Ed25519 public key.
"""

from __future__ import annotations

import base64
import re
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .signer import build_signing_string


def verify(body: bytes | str, auth_header: str, public_key_base64: str) -> None:
    """Verify that an Authorization header is a valid signature for the given body.

    Args:
        body: Raw JSON payload.
        auth_header: Authorization header value.
        public_key_base64: Base64-encoded Ed25519 public key (32 bytes).

    Raises:
        ValueError: If the header is malformed or timestamps are invalid.
        SignatureVerificationError: If the signature is invalid.
    """
    now_unix = int(time.time())
    verify_at(body, auth_header, public_key_base64, now_unix)


def verify_at(
    body: bytes | str,
    auth_header: str,
    public_key_base64: str,
    now_unix: int,
) -> None:
    """Verify at a specific Unix timestamp (useful for testing).

    Raises:
        ValueError: If the header is malformed or timestamps are invalid.
        SignatureVerificationError: If the signature is invalid.
    """
    created, expires, signature = _parse_auth_header(auth_header)

    if created > now_unix:
        raise ValueError(
            f"verifier: signature not yet valid (created {created} > now {now_unix})"
        )
    if now_unix > expires:
        raise ValueError(
            f"verifier: signature expired (expires {expires} < now {now_unix})"
        )

    try:
        sig_bytes = base64.b64decode(signature, validate=True)
    except Exception as exc:
        raise ValueError(f"verifier: invalid signature base64: {exc}") from exc

    body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
    signing_string = build_signing_string(body_bytes, created, expires)

    try:
        pub_key_bytes = base64.b64decode(public_key_base64, validate=True)
    except Exception as exc:
        raise ValueError(f"verifier: invalid public key base64: {exc}") from exc

    public_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)

    try:
        public_key.verify(sig_bytes, signing_string.encode("utf-8"))
    except Exception:
        raise SignatureVerificationError("verifier: signature verification failed")


def parse_key_id(key_id: str) -> dict[str, str]:
    """Extract subscriber_id, unique_key_id, and algorithm from a keyId field.

    Format: ``"subscriber_id|unique_key_id|algorithm"``

    Returns:
        Dict with keys ``subscriber_id``, ``unique_key_id``, ``algorithm``.
    """
    parts = key_id.split("|")
    if len(parts) != 3:
        raise ValueError(
            f"invalid keyId format, expected 'subscriber|keyId|algorithm', got \"{key_id}\""
        )
    return {
        "subscriber_id": parts[0],
        "unique_key_id": parts[1],
        "algorithm": parts[2],
    }


class SignatureVerificationError(Exception):
    """Raised when an Ed25519 signature fails verification."""


def _parse_auth_header(header: str) -> tuple[int, int, str]:
    """Parse the Authorization header to extract created, expires, and signature."""
    stripped = header
    if stripped.startswith("Signature "):
        stripped = stripped[len("Signature "):]

    params: dict[str, str] = {}
    for part in stripped.split(","):
        eq_idx = part.find("=")
        if eq_idx != -1:
            key = part[:eq_idx].strip()
            val = part[eq_idx + 1:]
            # Strip surrounding quotes.
            val = re.sub(r'^"|"$', "", val)
            params[key] = val

    if "created" not in params:
        raise ValueError("missing 'created' in auth header")
    if "expires" not in params:
        raise ValueError("missing 'expires' in auth header")
    if "signature" not in params:
        raise ValueError("missing 'signature' in auth header")

    try:
        created = int(params["created"])
    except ValueError:
        raise ValueError(f"invalid 'created' timestamp: {params['created']}")

    try:
        expires = int(params["expires"])
    except ValueError:
        raise ValueError(f"invalid 'expires' timestamp: {params['expires']}")

    return created, expires, params["signature"]
