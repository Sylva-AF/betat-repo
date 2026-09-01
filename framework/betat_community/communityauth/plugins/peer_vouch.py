"""PeerVouchAuth — "N existing members vouch for an applicant"
(COMMUNITY_FRAMEWORK.md). N is CommunityConfig.peer_vouch_threshold
(default 2, community-configurable, never below 2 — BLUEPRINT §3
Decision Log). The weakest floor method; its strength is visible in
the record by design (todos/03-authentication.md Security notes) —
never hide that a record was peer-vouched.

Two-phase since BLUEPRINT §03 Decision Log (2026-09): enroll() no longer
takes a trusted, applicant-supplied list of voucher identities (that
trusted the applicant's word that those people had agreed — never
confirmed). It instead opens a PeerVouchRequest with zero vouches and
returns Pending; vouches are added one at a time via add_vouch(), called
only for an authenticated caller who is themselves an enrolled
Provenancier (enforced by VouchView, not here). Threshold is always read
live from CommunityConfig.peer_vouch_threshold — never hardcoded — so a
community that raises it takes effect on the very next vouch.
"""
from ..base import AuthMethod
from ..enrollment import persist_provenancier
from ..identity import Pending, ProvenancierIdentity, Rejection
from ..models import PeerVouchRequest, Provenancier


class PeerVouchAuth(AuthMethod):
    method_name = 'community_peer_vouching'

    def enroll(self, applicant):
        identity = (applicant.get('identity') or '').strip()
        if not identity:
            return Rejection(code='missing_identity', message='An identity/handle is required.')
        if Provenancier.objects.filter(identity=identity).exists():
            return Rejection(code='identity_taken', message='That identity is already enrolled.')

        display_name = applicant.get('display_name', '')
        req, _created = PeerVouchRequest.objects.get_or_create(
            identity=identity, defaults={'display_name': display_name},
        )

        threshold = self.config.peer_vouch_threshold
        if len(req.vouchers) >= threshold:
            return self._promote(req)

        return Pending(
            code='pending_vouches',
            message=(
                f'Enrollment request received. {threshold} existing enrolled members must '
                f'vouch for you before enrollment completes. Ask them to vouch for request '
                f'ID {req.pk}.'
            ),
            request_id=req.pk,
            vouch_count=len(req.vouchers),
            vouches_needed=threshold - len(req.vouchers),
        )

    def add_vouch(self, request_id, voucher_identity):
        """Record a vouch from an authenticated, already-enrolled
        Provenancier. Idempotent (re-vouching by the same identity doesn't
        double-count); rejects a self-vouch. Returns ProvenancierIdentity
        if this vouch met the threshold, Pending otherwise, or Rejection
        for a self-vouch. Raises ValueError if request_id doesn't exist —
        the caller (VouchView) maps that to 404."""
        try:
            req = PeerVouchRequest.objects.get(pk=request_id)
        except PeerVouchRequest.DoesNotExist:
            raise ValueError(f'No pending peer-vouch request with id {request_id}.')

        if voucher_identity == req.identity:
            return Rejection(code='self_vouch', message='You cannot vouch for your own enrollment request.')

        if voucher_identity not in req.vouchers:
            req.vouchers = list(req.vouchers) + [voucher_identity]
            req.save(update_fields=['vouchers', 'updated_at'])

        threshold = self.config.peer_vouch_threshold
        if len(req.vouchers) >= threshold:
            return self._promote(req)

        return Pending(
            code='pending_vouches',
            message=f'Vouch recorded. {len(req.vouchers)} of {threshold} vouches received.',
            request_id=req.pk,
            vouch_count=len(req.vouchers),
            vouches_needed=threshold - len(req.vouchers),
        )

    def _promote(self, req):
        provenancier, _token = persist_provenancier(
            identity=req.identity,
            identity_type='peer_attested',
            authentication_method=self.method_name,
            display_name=req.display_name,
            verification_material={'vouchers': req.vouchers},
        )
        req.delete()
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
