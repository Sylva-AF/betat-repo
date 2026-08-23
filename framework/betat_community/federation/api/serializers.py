"""CommunityConfigSerializer for GET /betat/info. Exposes exactly the
CommunityConfig fields COMMUNITY_FRAMEWORK.md's "Community configuration"
sketch defines — `peer_vouch_threshold`/`trusted_institutions` (§03
additions, operational config rather than identity) are deliberately
excluded (BLUEPRINT §6 Decision Log).
"""
from rest_framework import serializers

from betat_community.core.models import CommunityConfig


class CommunityConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityConfig
        fields = ['id', 'name', 'domain', 'content_type', 'hi_standard', 'auth_methods', 'store_uri']
