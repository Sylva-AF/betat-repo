"""GET /betat/info, /betat/records, /betat/records/{id}, /betat/changes
(BLUEPRINT §0 API table) — the community's public face. All read-only,
unauthenticated. Records are read directly off store.models.ProvenanceRecord
via standard DRF generics/pagination rather than store.py's list_records()
wrapper — see BLUEPRINT §6 Decision Log. store.get() is still used for the
single-record lookup, since that's already the right minimal primitive.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from betat_community.common.errors import error_response
from betat_community.common.permissions import PublicReadOnly
from betat_community.common.serializers import ProvenanceRecordSerializer
from betat_community.core.models import CommunityConfig
from betat_community.store import store
from betat_community.store.models import ProvenanceRecord

from .pagination import RecordPagination
from .serializers import CommunityConfigSerializer


def _parse_bool(value):
    if value is None:
        return None
    return value.strip().lower() in ('1', 'true', 'yes')


def _filtered_queryset(request):
    queryset = ProvenanceRecord.objects.all()
    since = request.query_params.get('since')
    if since:
        queryset = queryset.filter(timestamp__gt=since)
    hi_only = _parse_bool(request.query_params.get('hi_only'))
    if hi_only is not None:
        queryset = queryset.filter(hi_tag=hi_only)
    return queryset


class InfoView(APIView):
    permission_classes = [PublicReadOnly]

    def get(self, request):
        config = CommunityConfig.objects.first()
        if config is None:
            return error_response(
                'not_configured',
                'This install has no CommunityConfig yet — run `betat init` first.',
                status.HTTP_404_NOT_FOUND,
            )
        return Response(CommunityConfigSerializer(config).data)


class RecordsView(generics.ListAPIView):
    permission_classes = [PublicReadOnly]
    serializer_class = ProvenanceRecordSerializer
    pagination_class = RecordPagination

    def get_queryset(self):
        return _filtered_queryset(self.request)


class RecordDetailView(APIView):
    permission_classes = [PublicReadOnly]

    def get(self, request, record_id):
        try:
            record = store.get(record_id)
        except ProvenanceRecord.DoesNotExist:
            return error_response('not_found', 'No record with that id.', status.HTTP_404_NOT_FOUND)
        return Response(ProvenanceRecordSerializer(record).data)


class ChangesView(generics.ListAPIView):
    permission_classes = [PublicReadOnly]
    serializer_class = ProvenanceRecordSerializer
    pagination_class = RecordPagination

    def get_queryset(self):
        return _filtered_queryset(self.request)
