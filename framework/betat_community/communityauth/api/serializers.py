"""Request shape for POST /betat/enroll. `applicant` is intentionally a
plain DictField — its shape is plugin-specific (see each plugin's
enroll() docstring) and validated by the plugin itself, not here.
"""
from rest_framework import serializers

from ..models import PeerVouchRequest


class EnrollRequestSerializer(serializers.Serializer):
    method = serializers.CharField()
    applicant = serializers.DictField()


class PeerVouchRequestSerializer(serializers.ModelSerializer):
    """Backs GET /betat/vouch-requests (TODO 13 task 1) — the staff admin
    dashboard's view of pending PeerVouchRequests. `vouch_count` is
    derived rather than stored (`len(vouchers)`, same as
    communityauth/admin.py's own `vouch_count` display column)."""

    vouch_count = serializers.SerializerMethodField()

    class Meta:
        model = PeerVouchRequest
        fields = ['id', 'identity', 'display_name', 'founding', 'vouch_count', 'created_at']

    def get_vouch_count(self, obj):
        return len(obj.vouchers)
