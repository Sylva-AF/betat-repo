"""betat_community/common/passphrase_auth.py

Passphrase-based keypair derivation for the crypto_key authentication method.

Design: the user enters a passphrase. The system derives a deterministic
Ed25519 keypair from it using scrypt (a password-based KDF). The user
never sees hex keys — they just remember a passphrase like a password.

Key properties:
- Same passphrase + same community_id → same keypair, always
- Different community_id → different keypair (salt isolation)
- Private key is never stored — derived fresh on each use
- Passphrase sent over HTTPS, never stored on server
- Forgetting the passphrase means re-enrolling with a new one

The cryptography package is already a dependency (pyproject.toml).
No new packages required.

Relationship to content hashing:
- Content hash (SHA-256 of content at content.location) proves
  the content hasn't changed since submission — integrity
- Keypair signature proves who submitted it — authorship
- record_id (compute_record_id in common/hashing.py) is a SHA-256
  of the canonical record JSON, which includes both the content hash
  and the provenancier identity — so tampering either breaks the record_id
Together: this specific human submitted this specific content, unchanged.
"""
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat
)


# ── KDF parameters ─────────────────────────────────────────────────────────
# n=2**14 (16384): memory-hard, ~100ms on a modern server.
# Balances security against brute-force with acceptable UX latency.
# [FUTURE] Increase n for stronger security at cost of more latency.
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN   = 32   # Ed25519 private key is 32 bytes


def _make_salt(community_id: str) -> bytes:
    """
    Derive a 16-byte salt from community_id.
    Salt is public (community_id is public) but unique per community —
    so the same passphrase produces a different keypair on each community.
    This prevents a compromised passphrase on one community from exposing
    the Provenancier's identity on another.
    """
    raw = community_id.encode('utf-8')
    # Pad or truncate to exactly 16 bytes
    return (raw * ((16 // len(raw)) + 1))[:16]


def derive_keypair(passphrase: str, community_id: str):
    """
    Derive a deterministic Ed25519 keypair from a passphrase.

    Returns (private_key, public_key) — Ed25519 key objects.
    Call public_key_hex() or sign_message() instead for common operations.

    Args:
        passphrase:   The user's chosen passphrase. Never stored.
        community_id: The community's FQDN id (e.g. 'archive.example.org').
                      Used as KDF salt — isolates keys per community.
    """
    salt = _make_salt(community_id)
    kdf  = Scrypt(salt=salt, length=_KEY_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    key_bytes   = kdf.derive(passphrase.encode('utf-8'))
    private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
    public_key  = private_key.public_key()
    return private_key, public_key


def public_key_hex(passphrase: str, community_id: str) -> str:
    """
    Return the hex-encoded public key for enrollment.
    This is stored in ProvenancierIdentity — it is public.

    The Provenancier submits this during enrollment; the community
    stores it and uses it to verify their future submission signatures.
    """
    _, pub = derive_keypair(passphrase, community_id)
    return pub.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def sign_message(passphrase: str, community_id: str, message: bytes) -> str:
    """
    Sign a message with the derived private key.
    Returns a hex-encoded Ed25519 signature (64 bytes = 128 hex chars).

    Used at submission time: the message is the canonical record JSON
    (or the content hash + record metadata) that the Provenancier is
    asserting human origin for.

    The private key is derived fresh, used to sign, then discarded.
    It is never stored on the server or in the session.
    """
    priv, _ = derive_keypair(passphrase, community_id)
    return priv.sign(message).hex()


def verify_signature(public_key_hex_str: str, message: bytes, signature_hex: str) -> bool:
    """
    Verify a signature against a stored public key.
    Used by the submission view to confirm the Provenancier signed
    the content with the key they enrolled with.

    Returns True if valid, False if tampered or wrong passphrase.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        pub_bytes = bytes.fromhex(public_key_hex_str)
        pub_key   = Ed25519PublicKey.from_public_bytes(pub_bytes)
        sig_bytes = bytes.fromhex(signature_hex)
        pub_key.verify(sig_bytes, message)
        return True
    except Exception:
        return False
