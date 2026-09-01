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
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from betat_community.common.errors import error_response
from betat_community.core.models import CommunityConfig

from .. import passphrase as passphrase_derivation
from ..floor import PROTOCOL_LIST
from ..identity import Pending, Rejection
from ..models import Provenancier
from ..plugins import CryptoKeyAuth, PeerVouchAuth
from .serializers import EnrollRequestSerializer


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
