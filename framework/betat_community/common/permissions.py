"""Public-read / authenticated-write split (BLUEPRINT §0 convention).
`PublicReadOnly` is explicit defense-in-depth for GET-only endpoints
(federation): the project default permission is already AllowAny, so this
isn't what makes reads public — it's what stops a future edit from
accidentally adding a write handler to a public-read view without anyone
noticing, since non-safe methods are denied at the permission layer.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class PublicReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
