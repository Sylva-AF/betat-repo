from django.contrib import admin

from betat_community.core.models import CommunityConfig

from .models import PeerVouchRequest
from .plugins import PeerVouchAuth


@admin.action(description='Approve selected founding-member requests')
def approve_founding_requests(modeladmin, request, queryset):
    """Promotes founding=True requests directly — the admin-approval path
    for a community's first two members (BLUEPRINT §03 Decision Log,
    2026-09-09). Non-founding requests are skipped: those still need the
    normal peer-vouch threshold, not an admin override."""
    config = CommunityConfig.objects.first()
    plugin = PeerVouchAuth(config)
    approved = skipped = 0
    for req in queryset:
        if not req.founding:
            skipped += 1
            continue
        plugin.promote(req)
        approved += 1
    if approved:
        modeladmin.message_user(request, f'Approved {approved} founding request(s).')
    if skipped:
        modeladmin.message_user(
            request,
            f'Skipped {skipped} non-founding request(s) — those need the normal peer-vouch threshold.',
            level='warning',
        )


@admin.register(PeerVouchRequest)
class PeerVouchRequestAdmin(admin.ModelAdmin):
    """Founding requests (BLUEPRINT §03 Decision Log, 2026-09-09) are
    promoted via the approve_founding_requests action above. Non-founding
    requests still promote automatically once
    CommunityConfig.peer_vouch_threshold vouches accrue via
    POST /betat/vouch/{id} — no admin action needed for those."""

    list_display = ['identity', 'display_name', 'founding_label', 'vouch_count', 'created_at']
    actions = [approve_founding_requests]

    def vouch_count(self, obj):
        return len(obj.vouchers)

    def founding_label(self, obj):
        return '⭐ Founding member' if obj.founding else ''
    founding_label.short_description = 'Type'
