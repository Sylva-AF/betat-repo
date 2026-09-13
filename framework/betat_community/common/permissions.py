"""Public-read / authenticated-write split (BLUEPRINT §0 convention).
`PublicReadOnly` is explicit defense-in-depth for GET-only endpoints
(federation): the project default permission is already AllowAny, so this
isn't what makes reads public — it's what stops a future edit from
accidentally adding a write handler to a public-read view without anyone
noticing, since non-safe methods are denied at the permission layer.

`IsVerifier` moved here from workflow/api/mixins.py (TODO 13, 2026-09-13)
once communityauth's new admin-dashboard endpoints needed the same
staff-only gate `workflow`'s queue/review views already used — per §0's
"used by one app → that app's api/; used by two or more → common/" rule.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class PublicReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsVerifier(BasePermission):
    """A verifier is a Django staff user (BLUEPRINT §4 Decision Log) — a
    governance role granted via the admin panel, distinct from the
    Provenancier identity model. Superusers are staff by definition."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
