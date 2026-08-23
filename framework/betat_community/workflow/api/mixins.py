"""View-level behavior shared across the workflow API's verifier-only
endpoints (queue, review). Not in common/ — only this app uses it so far
(BLUEPRINT §0 convention: used by one app → that app's api/).
"""
from rest_framework.permissions import BasePermission


class IsVerifier(BasePermission):
    """A verifier is a Django staff user (BLUEPRINT §4 Decision Log) — a
    governance role granted via the admin panel, distinct from the
    Provenancier identity model. Superusers are staff by definition."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
