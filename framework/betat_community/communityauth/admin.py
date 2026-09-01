from django.contrib import admin

from .models import PeerVouchRequest


@admin.register(PeerVouchRequest)
class PeerVouchRequestAdmin(admin.ModelAdmin):
    """Read visibility only — promotion is automatic once
    CommunityConfig.peer_vouch_threshold vouches accrue via
    POST /betat/vouch/{id}; no admin approve/reject action exists
    (BLUEPRINT §03 Decision Log, 2026-09: no bootstrap/admin-approval
    path in this round)."""

    list_display = ['identity', 'display_name', 'vouch_count', 'created_at']

    def vouch_count(self, obj):
        return len(obj.vouchers)
