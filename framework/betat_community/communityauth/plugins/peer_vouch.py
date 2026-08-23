"""PeerVouchAuth — "N existing members vouch for an applicant"
(COMMUNITY_FRAMEWORK.md). N is CommunityConfig.peer_vouch_threshold
(default 2, community-configurable, never below 2 — BLUEPRINT §3
Decision Log). The weakest floor method; its strength is visible in
the record by design (todos/03-authentication.md Security notes) —
never hide that a record was peer-vouched.
"""
from ..base import AuthMethod
from ..enrollment import persist_provenancier
from ..identity import ProvenancierIdentity, Rejection
from ..models import Provenancier


class PeerVouchAuth(AuthMethod):
    method_name = 'community_peer_vouching'

    def enroll(self, applicant):
        identity = (applicant.get('identity') or '').strip()
        if not identity:
            return Rejection(code='missing_identity', message='An identity/handle is required.')
        if Provenancier.objects.filter(identity=identity).exists():
            return Rejection(code='identity_taken', message='That identity is already enrolled.')

        voucher_identities = applicant.get('vouchers') or []
        threshold = self.config.peer_vouch_threshold
        valid_vouchers = Provenancier.objects.filter(
            identity__in=voucher_identities,
            authentication_method__isnull=False,
        ).count()
        if valid_vouchers < threshold:
            return Rejection(
                code='insufficient_vouchers',
                message=f'At least {threshold} existing enrolled members must vouch; got {valid_vouchers}.',
            )

        display_name = applicant.get('display_name', '')
        provenancier, _token = persist_provenancier(
            identity=identity,
            identity_type='peer_attested',
            authentication_method=self.method_name,
            display_name=display_name,
            verification_material={'vouchers': voucher_identities},
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
        return ProvenancierIdentity(
            identity=record.identity,
            identity_type=record.identity_type,
            authentication_method=record.authentication_method,
            display_name=record.display_name,
        )
