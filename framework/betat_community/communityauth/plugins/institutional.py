"""InstitutionalAuth — identity endorsed by a trusted institution
(COMMUNITY_FRAMEWORK.md). The community configures which institutions it
trusts and their public keys in CommunityConfig.trusted_institutions
(JSONField: {institution_id: public_key_hex}). An applicant enrolls with
an institution-issued signature over their own identity string; the same
Ed25519 scheme as CryptoKeyAuth (crypto.py), keyed by the institution's
public key rather than the applicant's own.

authenticate() re-checks the institution is still trusted and re-verifies
the endorsement against the *current* trusted_institutions entry — an
institution removed or rekeyed after enrollment stops authenticating,
even though the original enroll() succeeded.
"""
from .. import crypto
from ..base import AuthMethod
from ..enrollment import persist_provenancier
from ..identity import ProvenancierIdentity, Rejection
from ..models import Provenancier


class InstitutionalAuth(AuthMethod):
    method_name = 'institutional_endorsement'

    def _trusted_public_key(self, institution_id):
        return (self.config.trusted_institutions or {}).get(institution_id)

    def enroll(self, applicant):
        identity = (applicant.get('identity') or '').strip()
        if not identity:
            return Rejection(code='missing_identity', message='An identity/handle is required.')
        if Provenancier.objects.filter(identity=identity).exists():
            return Rejection(code='identity_taken', message='That identity is already enrolled.')

        institution_id = (applicant.get('institution_id') or '').strip()
        signature = (applicant.get('signature') or '').strip()
        if not institution_id or not signature:
            return Rejection(
                code='missing_proof',
                message='An institution_id and its signature over the identity are required.',
            )

        public_key = self._trusted_public_key(institution_id)
        if not public_key:
            return Rejection(code='untrusted_institution', message=f"'{institution_id}' is not a trusted institution.")
        if not crypto.verify(public_key, identity, signature):
            return Rejection(code='invalid_endorsement', message='signature does not verify against the institution public_key.')

        display_name = applicant.get('display_name', '')
        provenancier, _token = persist_provenancier(
            identity=identity,
            identity_type='institutional_id',
            authentication_method=self.method_name,
            display_name=display_name,
            verification_material={'institution_id': institution_id, 'signature': signature},
        )
        return ProvenancierIdentity(
            identity=provenancier.identity,
            identity_type=provenancier.identity_type,
            authentication_method=provenancier.authentication_method,
            display_name=provenancier.display_name,
        )

    def authenticate(self, credentials):
        identity = credentials.get('identity')
        try:
            record = Provenancier.objects.get(identity=identity, authentication_method=self.method_name)
        except Provenancier.DoesNotExist:
            return Rejection(code='not_enrolled', message='No enrolled Provenancier with that identity.')

        institution_id = record.verification_material.get('institution_id', '')
        signature = record.verification_material.get('signature', '')
        public_key = self._trusted_public_key(institution_id)
        if not public_key:
            return Rejection(code='untrusted_institution', message=f"'{institution_id}' is no longer a trusted institution.")
        if not crypto.verify(public_key, record.identity, signature):
            return Rejection(code='invalid_endorsement', message='endorsement no longer verifies against the current institution public_key.')

        return ProvenancierIdentity(
            identity=record.identity,
            identity_type=record.identity_type,
            authentication_method=record.authentication_method,
            display_name=record.display_name,
        )
