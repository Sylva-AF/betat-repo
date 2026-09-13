"""POST /betat/enroll (BLUEPRINT §0 API table) — dispatches to the
protocol-list plugin named by `method`, returns the enrolled identity +
DRF token on success or the standard error shape on Rejection. Public
(auth: none→identity) — enrolling *is* how an applicant gets credentials.

`method` must be on both the global PROTOCOL_LIST *and* this community's
own `CommunityConfig.auth_methods` — a community that enabled only
`cryptographic_signature` must not silently also accept
`community_peer_vouching` enrollments just because that method exists
somewhere on the protocol list.
"""
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from betat_community.common.errors import error_response
from betat_community.common.permissions import IsVerifier
from betat_community.core.models import CommunityConfig

from .. import passphrase as passphrase_derivation
from ..floor import PROTOCOL_LIST
from ..identity import Pending, Rejection
from ..models import PeerVouchRequest, Provenancier
from ..plugins import CryptoKeyAuth, InstitutionalAuth, PeerVouchAuth
from .serializers import EnrollRequestSerializer, PeerVouchRequestSerializer


class EnrollView(APIView):
    def post(self, request):
        serializer = EnrollRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('invalid_request', str(serializer.errors), status.HTTP_400_BAD_REQUEST)

        method = serializer.validated_data['method']
        applicant = serializer.validated_data['applicant']

        plugin_class = PROTOCOL_LIST.get(method)
        if plugin_class is None:
            return error_response(
                'off_list_auth_method',
                f"'{method}' is not on the protocol list.",
                status.HTTP_400_BAD_REQUEST,
            )

        config = CommunityConfig.objects.first()
        if config is None:
            return error_response(
                'not_configured',
                'This install has no CommunityConfig yet — run `betat init` first.',
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if method not in config.auth_methods:
            return error_response(
                'method_not_enabled',
                f"'{method}' is on the protocol list, but this community has not enabled it.",
                status.HTTP_400_BAD_REQUEST,
            )

        result = plugin_class(config).enroll(applicant)
        if isinstance(result, Rejection):
            return error_response(result.code, result.message, status.HTTP_400_BAD_REQUEST)
        if isinstance(result, Pending):
            return Response(
                {
                    'status': result.code,
                    'request_id': result.request_id,
                    'vouch_count': result.vouch_count,
                    'vouches_needed': result.vouches_needed,
                    'message': result.message,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        provenancier = Provenancier.objects.get(identity=result.identity)
        token = Token.objects.get(user=provenancier.user)
        return Response(
            {
                'identity': result.identity,
                'identity_type': result.identity_type,
                'authentication_method': result.authentication_method,
                'display_name': result.display_name,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class CryptoKeyLoginView(APIView):
    """POST /betat/login (BLUEPRINT §0 API table) — re-derives a
    passphrase-based `cryptographic_signature` identity for a returning
    applicant and returns their existing token (BLUEPRINT §03 Decision
    Log, 2026-09; closes half of §07's "no returning-provenancier login
    flow" gap). Public (auth: none→identity), same as /enroll — logging in
    *is* how a returning applicant gets their token back into a new
    session. Compares the re-derived public key directly against what was
    recorded at enrollment rather than round-tripping through
    CryptoKeyAuth.authenticate()'s message/signature challenge, since the
    derivation is already trusted server-side. Applicants who enrolled by
    pasting their own public_key/signature (no passphrase) have nothing to
    re-derive and are not served by this endpoint."""

    def post(self, request):
        identity = (request.data.get('identity') or '').strip()
        applicant_passphrase = (request.data.get('passphrase') or '').strip()
        if not identity or not applicant_passphrase:
            return error_response(
                'missing_credentials', 'identity and passphrase are required.', status.HTTP_400_BAD_REQUEST,
            )

        config = CommunityConfig.objects.first()
        if config is None:
            return error_response(
                'not_configured', 'This install has no CommunityConfig yet.', status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            provenancier = Provenancier.objects.get(
                identity=identity, authentication_method=CryptoKeyAuth.method_name,
            )
        except Provenancier.DoesNotExist:
            return error_response('invalid_credentials', 'Invalid identity or passphrase.', status.HTTP_401_UNAUTHORIZED)

        _, derived_public_key = passphrase_derivation.derive_keypair(applicant_passphrase, config.id)
        if provenancier.verification_material.get('public_key') != derived_public_key:
            return error_response('invalid_credentials', 'Invalid identity or passphrase.', status.HTTP_401_UNAUTHORIZED)

        token = Token.objects.get(user=provenancier.user)
        return Response(
            {
                'identity': provenancier.identity,
                'identity_type': provenancier.identity_type,
                'authentication_method': provenancier.authentication_method,
                'display_name': provenancier.display_name,
                'token': token.key,
            },
            status=status.HTTP_200_OK,
        )


class ClaimEnrollmentView(APIView):
    """POST /betat/enroll/claim (TODO 13 task 3) — lets a
    community_peer_vouching/institutional_endorsement applicant who set an
    optional claim_passphrase at enroll time retrieve their pending status
    or, once promoted, their token from a *different* session/device than
    the one they enrolled from. Public (auth: none→identity), same
    category as /betat/enroll and /betat/login.

    Security design (BLUEPRINT §03 2026-09-13 Decision Log): identity and
    request_id are already effectively public — enroll_pending.html tells
    applicants to share their request ID with vouchers — so neither can be
    the proof of ownership. claim_passphrase is a separate secret only the
    applicant knows, hashed with Django's password hasher (never stored
    plaintext), checked here with a constant-time compare. Same generic
    'invalid_credentials' on every failure mode (no such identity, no
    claim passphrase ever set, wrong passphrase) — no enumeration, same
    posture as CryptoKeyLoginView."""

    def post(self, request):
        identity = (request.data.get('identity') or '').strip()
        claim_passphrase = (request.data.get('claim_passphrase') or '').strip()
        if not identity or not claim_passphrase:
            return error_response(
                'missing_credentials', 'identity and claim_passphrase are required.', status.HTTP_400_BAD_REQUEST,
            )

        provenancier = Provenancier.objects.filter(
            identity=identity,
            authentication_method__in=[PeerVouchAuth.method_name, InstitutionalAuth.method_name],
        ).first()

        if provenancier is not None:
            stored_hash = provenancier.verification_material.get('claim_passphrase_hash')
            if not stored_hash or not check_password(claim_passphrase, stored_hash):
                return error_response('invalid_credentials', 'Invalid identity or claim passphrase.', status.HTTP_401_UNAUTHORIZED)
            token = Token.objects.get(user=provenancier.user)
            return Response({
                'status': 'enrolled',
                'identity': provenancier.identity,
                'identity_type': provenancier.identity_type,
                'authentication_method': provenancier.authentication_method,
                'display_name': provenancier.display_name,
                'token': token.key,
            })

        # Not yet promoted — only PeerVouchRequest has a pending phase;
        # InstitutionalAuth enrolls synchronously, so no pending state
        # exists for it to check here.
        req = PeerVouchRequest.objects.filter(identity=identity).first()
        if req is None or not req.claim_passphrase_hash or not check_password(claim_passphrase, req.claim_passphrase_hash):
            return error_response('invalid_credentials', 'Invalid identity or claim passphrase.', status.HTTP_401_UNAUTHORIZED)

        if req.founding:
            return Response(
                {'status': 'pending_admin', 'request_id': req.pk},
                status=status.HTTP_202_ACCEPTED,
            )

        config = CommunityConfig.objects.first()
        threshold = config.peer_vouch_threshold if config else len(req.vouchers)
        return Response(
            {
                'status': 'pending_vouches',
                'request_id': req.pk,
                'vouch_count': len(req.vouchers),
                'vouches_needed': max(threshold - len(req.vouchers), 0),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class RotatePassphraseView(APIView):
    """POST /betat/rotate-passphrase (TODO 13, Provenancier passphrase
    rotation) — lets a cryptographic_signature/passphrase-derived
    Provenancier change their passphrase. Public (auth: none→identity),
    same trust model as CryptoKeyLoginView: proof of ownership IS
    re-deriving and matching the *current* passphrase, not an active
    session/token — this works even if the caller suspects their existing
    token (a separate secret from the passphrase) was the thing that
    leaked, from a device that never held that token in the first place
    (BLUEPRINT §03 2026-09-13 Decision Log).

    Rotates the DRF token as part of this operation, deliberately: leaving
    it stable would mean a stolen token keeps working after a 'security'
    passphrase rotation, which would make the whole feature cosmetic
    rather than a real compromise response.

    Out of scope: community_peer_vouching/institutional_endorsement have
    no passphrase concept to rotate here — their claim_passphrase (TODO 13
    task 3) is a different secret serving a different purpose (self-service
    status retrieval, not identity proof) and has no rotation path either,
    unaddressed by this endpoint."""

    def post(self, request):
        identity = (request.data.get('identity') or '').strip()
        current_passphrase = (request.data.get('current_passphrase') or '').strip()
        new_passphrase = (request.data.get('new_passphrase') or '').strip()
        if not identity or not current_passphrase or not new_passphrase:
            return error_response(
                'missing_credentials',
                'identity, current_passphrase, and new_passphrase are required.',
                status.HTTP_400_BAD_REQUEST,
            )
        if new_passphrase == current_passphrase:
            return error_response(
                'same_passphrase',
                'The new passphrase must be different from the current one.',
                status.HTTP_400_BAD_REQUEST,
            )

        config = CommunityConfig.objects.first()
        if config is None:
            return error_response(
                'not_configured', 'This install has no CommunityConfig yet.', status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            provenancier = Provenancier.objects.get(
                identity=identity, authentication_method=CryptoKeyAuth.method_name,
            )
        except Provenancier.DoesNotExist:
            return error_response('invalid_credentials', 'Invalid identity or current passphrase.', status.HTTP_401_UNAUTHORIZED)

        _, current_derived_public_key = passphrase_derivation.derive_keypair(current_passphrase, config.id)
        if provenancier.verification_material.get('public_key') != current_derived_public_key:
            return error_response('invalid_credentials', 'Invalid identity or current passphrase.', status.HTTP_401_UNAUTHORIZED)

        _, new_public_key = passphrase_derivation.derive_keypair(new_passphrase, config.id)
        provenancier.verification_material['public_key'] = new_public_key
        provenancier.save(update_fields=['verification_material'])

        Token.objects.filter(user=provenancier.user).delete()
        new_token = Token.objects.create(user=provenancier.user)

        return Response({
            'identity': provenancier.identity,
            'identity_type': provenancier.identity_type,
            'authentication_method': provenancier.authentication_method,
            'display_name': provenancier.display_name,
            'token': new_token.key,
        })


class PeerVouchQueueView(APIView):
    """GET /betat/vouch-requests (TODO 13 task 1) — verifier-only list of
    pending PeerVouchRequests (founding and normal, with vouch progress),
    backing bundledui's staff admin dashboard. The founding-request
    Approve action lives at POST /betat/vouch-requests/{id}/approve below.
    This is the API-layer equivalent of communityauth/admin.py's
    PeerVouchRequestAdmin list view — same data, reachable without
    Django-admin knowledge."""

    permission_classes = [IsVerifier]

    def get(self, request):
        config = CommunityConfig.objects.first()
        threshold = config.peer_vouch_threshold if config else None
        pending = PeerVouchRequest.objects.order_by('created_at')
        return Response({
            'threshold': threshold,
            'requests': PeerVouchRequestSerializer(pending, many=True).data,
        })


class ApproveFoundingRequestView(APIView):
    """POST /betat/vouch-requests/{id}/approve (TODO 13 task 1) — the
    API-layer equivalent of communityauth/admin.py's
    approve_founding_requests admin action, calling the same
    PeerVouchAuth.promote(). Rejects non-founding requests: those must
    still cross the normal peer-vouch threshold via
    POST /betat/vouch/{id} from other Provenanciers, not a staff override
    (BLUEPRINT §03's peer-vouch trust model — the dashboard shows
    non-founding requests read-only, but this endpoint enforces the same
    rule server-side rather than trusting the UI not to send the request)."""

    permission_classes = [IsVerifier]

    def post(self, request, request_id):
        try:
            req = PeerVouchRequest.objects.get(pk=request_id)
        except PeerVouchRequest.DoesNotExist:
            return error_response('not_found', 'No pending request with that id.', status.HTTP_404_NOT_FOUND)

        if not req.founding:
            return error_response(
                'not_a_founding_request',
                'Only founding-phase requests can be approved directly — this one needs peer vouches.',
                status.HTTP_400_BAD_REQUEST,
            )

        config = CommunityConfig.objects.first()
        identity = PeerVouchAuth(config).promote(req)
        return Response(
            {
                'identity': identity.identity,
                'identity_type': identity.identity_type,
                'authentication_method': identity.authentication_method,
                'display_name': identity.display_name,
            },
            status=status.HTTP_200_OK,
        )


class VouchView(APIView):
    """POST /betat/vouch/{request_id} (BLUEPRINT §0 API table) — an
    authenticated, already-enrolled Provenancier vouches for a pending
    `community_peer_vouching` request. Requires auth (unlike /enroll):
    the whole point is that the vouch is attributable to a real, already-
    verified member, not merely a name the applicant supplied."""

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            voucher = Provenancier.objects.get(user=request.user)
        except Provenancier.DoesNotExist:
            return error_response(
                'not_enrolled', 'Only an enrolled Provenancier can vouch.', status.HTTP_403_FORBIDDEN,
            )

        config = CommunityConfig.objects.first()
        if config is None:
            return error_response(
                'not_configured', 'This install has no CommunityConfig yet.', status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            result = PeerVouchAuth(config).add_vouch(request_id, voucher.identity)
        except ValueError as exc:
            return error_response('not_found', str(exc), status.HTTP_404_NOT_FOUND)

        if isinstance(result, Rejection):
            return error_response(result.code, result.message, status.HTTP_400_BAD_REQUEST)
        if isinstance(result, Pending):
            return Response(
                {
                    'status': result.code,
                    'request_id': result.request_id,
                    'vouch_count': result.vouch_count,
                    'vouches_needed': result.vouches_needed,
                    'message': result.message,
                },
                status=status.HTTP_200_OK,
            )

        provenancier = Provenancier.objects.get(identity=result.identity)
        token = Token.objects.get(user=provenancier.user)
        return Response(
            {
                'identity': result.identity,
                'identity_type': result.identity_type,
                'authentication_method': result.authentication_method,
                'display_name': result.display_name,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )
