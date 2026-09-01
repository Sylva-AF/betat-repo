"""Passphrase-assisted `cryptographic_signature` enrollment (BLUEPRINT §03
Decision Log, 2026-09). Derives a deterministic Ed25519 keypair from an
applicant-chosen passphrase, so applicants who can't manage a keyfile still
get a real self-held key rather than being steered off the strongest
authentication method.

This is a convenience layer in front of the existing `CryptoKeyAuth` plugin
(crypto.py) — it produces the same {public_key, signature} shape that
plugin already requires and does not change `authentication_method` or add
a new identity type. See the BLUEPRINT entry for the accepted trade-off:
the server sees the passphrase transiently (enroll + login), never persists
it or the private key, and never asks for it again per-submission.
"""
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 32  # Ed25519 private key is 32 bytes


def _salt(community_id: str) -> bytes:
    """A uniform 16-byte salt derived from community_id — not the raw id
    bytes, which for a short id would be low-entropy and patterned. The
    salt need not be secret (community_id is public); it only needs to
    differ per community so the same passphrase yields different keys."""
    return hashlib.sha256(community_id.encode('utf-8')).digest()[:16]


def derive_keypair(passphrase: str, community_id: str):
    """Deterministically derive an Ed25519 (private_key_hex, public_key_hex)
    pair from a passphrase. Same passphrase + same community_id always
    yields the same pair; a different community_id yields a different pair.
    The private key is never stored by any caller — derive, use, discard."""
    kdf = Scrypt(salt=_salt(community_id), length=_KEY_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    key_bytes = kdf.derive(passphrase.encode('utf-8'))
    private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
    public_key = private_key.public_key()
    return private_key.private_bytes_raw().hex(), public_key.public_bytes_raw().hex()
