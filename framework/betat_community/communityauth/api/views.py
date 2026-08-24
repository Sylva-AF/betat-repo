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
from rest_framework.response import Response
from rest_framework.views import APIView

from betat_community.common.errors import error_response
from betat_community.core.models import CommunityConfig

from ..floor import PROTOCOL_LIST
from ..identity import Rejection
from ..models import Provenancier
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
