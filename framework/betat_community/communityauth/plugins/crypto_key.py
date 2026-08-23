"""CryptoKeyAuth — identity backed by an Ed25519 keypair the applicant
controls (COMMUNITY_FRAMEWORK.md). enroll() requires a self-signed
proof-of-possession (the applicant signs their own public key with the
matching private key) — this keeps enroll() stateless, no server-side
challenge/nonce to store. authenticate() verifies a caller-supplied
message + signature against the public key recorded at enroll time.

Replay protection is NOT implemented here: the caller is responsible for
signing a fresh nonce/timestamp of their own choosing. Known, documented
simplification for the seed implementation (todos/03-authentication.md
Session handoff) — flag it in docs when §11 happens.
"""
from .. import crypto
from ..base import AuthMethod
from ..enrollment import persist_provenancier
from ..identity import ProvenancierIdentity, Rejection
from ..models import Provenancier


class CryptoKeyAuth(AuthMethod):
    method_name = 'cryptographic_signature'

    def enroll(self, applicant):
        identity = (applicant.get('identity') or '').strip()
        if not identity:
            return Rejection(code='missing_identity', message='An identity/handle is required.')
        if Provenancier.objects.filter(identity=identity).exists():
            return Rejection(code='identity_taken', message='That identity is already enrolled.')

        public_key = (applicant.get('public_key') or '').strip()
        signature = (applicant.get('signature') or '').strip()
        if not public_key or not signature:
            return Rejection(
                code='missing_proof',
                message='A public_key and a signature (over the public_key itself) are required.',
            )
        if not crypto.verify(public_key, public_key, signature):
            return Rejection(
                code='invalid_proof',
                message='signature is not a valid proof of possession of public_key.',
            )

        display_name = applicant.get('display_name', '')
        provenancier, _token = persist_provenancier(
            identity=identity,
            identity_type='cryptographic_key',
            authentication_method=self.method_name,
            display_name=display_name,
            verification_material={'public_key': public_key},
        )
        return ProvenancierIdentity(
            identity=provenancier.identity,
            identity_type=provenancier.identity_type,
            authentication_method=provenancier.authentication_method,
            display_name=provenancier.display_name,
        )

    def authenticate(self, credentials):
        identity = credentials.get('identity')
        message = credentials.get('message') or ''
        signature = credentials.get('signature') or ''
        try:
            record = Provenancier.objects.get(identity=identity, authentication_method=self.method_name)
        except Provenancier.DoesNotExist:
            return Rejection(code='not_enrolled', message='No enrolled Provenancier with that identity.')

        public_key = record.verification_material.get('public_key', '')
        if not crypto.verify(public_key, message, signature):
            return Rejection(code='invalid_signature', message='signature does not verify against the enrolled public_key.')

        return ProvenancierIdentity(
            identity=record.identity,
            identity_type=record.identity_type,
            authentication_method=record.authentication_method,
            display_name=record.display_name,
        )
