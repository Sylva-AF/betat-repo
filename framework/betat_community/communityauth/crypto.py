"""Ed25519 signature helpers shared by CryptoKeyAuth and InstitutionalAuth.

Real signature verification via the `cryptography` package (PyCA) — not
hand-rolled. Keys and signatures are passed/stored as hex strings for
JSON-friendliness (applicant payloads, verification_material JSONField).
"""
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def verify(public_key_hex, message, signature_hex):
    """Return True iff signature_hex is a valid Ed25519 signature by
    public_key_hex over message (str, encoded UTF-8). Never raises —
    any malformed input is treated as a failed verification."""
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), message.encode('utf-8'))
        return True
    except (InvalidSignature, ValueError):
        return False


def generate_keypair():
    """Convenience for tests/docs: returns (private_key_hex, public_key_hex)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_hex = private_key.private_bytes_raw().hex()
    public_hex = public_key.public_bytes_raw().hex()
    return private_hex, public_hex


def sign(private_key_hex, message):
    """Convenience for tests/docs: sign message (str) with a hex private key."""
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    return private_key.sign(message.encode('utf-8')).hex()
