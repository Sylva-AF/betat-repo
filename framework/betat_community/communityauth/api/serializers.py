"""Request shape for POST /betat/enroll. `applicant` is intentionally a
plain DictField — its shape is plugin-specific (see each plugin's
enroll() docstring) and validated by the plugin itself, not here.
"""
from rest_framework import serializers

from ..models import PeerVouchRequest, Provenancier


class EnrollRequestSerializer(serializers.Serializer):
    method = serializers.CharField()
    applicant = serializers.DictField()


class ProvenancierListSerializer(serializers.ModelSerializer):
    """Backs GET /betat/provenanciers (2026-09-14) — a public, read-only
    list of enrolled identities so a community_peer_vouching/
    institutional_endorsement applicant can see real members to ask to
    vouch for them. Exposes only identity + display_name — never
    verification_material, which may hold a public key, claim passphrase
    hash, or vouchers list."""

    class Meta:
        model = Provenancier
        fields = ['identity', 'display_name']


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


class OpenVouchRequestSerializer(serializers.ModelSerializer):
    """Backs GET /betat/vouch-requests/open (TODO 14 issues 3 & 4) — the
    member-facing list of pending peer-vouch requests. Reads the caller's
    own identity and the community threshold from serializer context to
    flag `asked_me`/`already_vouched` and derive `vouches_needed`."""

    vouch_count = serializers.SerializerMethodField()
    vouches_needed = serializers.SerializerMethodField()
    asked_me = serializers.SerializerMethodField()
    already_vouched = serializers.SerializerMethodField()

    class Meta:
        model = PeerVouchRequest
        fields = [
            'id', 'identity', 'display_name', 'vouch_count', 'vouches_needed',
            'asked_me', 'already_vouched', 'created_at',
        ]

    def get_vouch_count(self, obj):
        return len(obj.vouchers)

    def get_vouches_needed(self, obj):
        threshold = self.context.get('threshold')
        if threshold is None:
            return None
        return max(threshold - len(obj.vouchers), 0)

    def get_asked_me(self, obj):
        return self.context.get('caller_identity') in obj.requested_vouchers

    def get_already_vouched(self, obj):
        return self.context.get('caller_identity') in obj.vouchers
