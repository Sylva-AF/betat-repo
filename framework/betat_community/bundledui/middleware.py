"""bundledui/middleware.py — the Phase 1 / Phase 2 gate (TODO 07 amendment,
2026-08-27/29). Before a CommunityConfig exists, every community-facing
page (base.html's nav links to Enroll/Submit/Review queue, none of which
work yet) redirects to the installer screen instead of rendering broken
nav. Once CommunityConfig exists, this never redirects again.

The public JSON API and Django admin are exempt so they keep their own
existing behaviour throughout: the API already has honest "not configured"
responses (404/503, BLUEPRINT §06 Decision Log) that predate this gate and
must not be intercepted by a browser-facing HTML redirect, and the
superuser must be able to log in via /admin/ during setup.
"""
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect

# Reachable regardless of configuration state:
#   - the installer screen itself (else an infinite redirect loop)
#   - /community/setup — the browser setup wizard: it must stay reachable
#     while unconfigured (that's the whole point of it), and each step
#     view redirects itself to the landing page once configured
#   - /admin/ — the superuser must be able to log in during setup
#   - /static/, /favicon — asset requests, not pages
#   - /betat/ — the public API's own "not configured" semantics, untouched
_EXEMPT_PREFIXES = (
    '/community/install',
    '/community/setup',
    '/admin/',
    '/static/',
    '/favicon',
    '/betat/',
)

# In-process cache — avoids a DB hit on every request once configured.
# Reset only on process restart in production, which is fine: a fresh
# server on a configured install does one query then caches True for the
# process lifetime. Tests run many scenarios in one process, so
# tests/conftest.py resets this before/after every test to keep them
# isolated from each other.
_configured_cache = None


class BetatConfiguredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _configured_cache

        if any(request.path_info.startswith(p) for p in _EXEMPT_PREFIXES):
            return self.get_response(request)

        if _configured_cache is None:
            from betat_community.core.models import CommunityConfig
            try:
                _configured_cache = CommunityConfig.objects.exists()
            except (OperationalError, ProgrammingError):
                # Pre-migration database (very first run) — show installer.
                _configured_cache = False

        if not _configured_cache:
            return redirect('bundledui-install')

        return self.get_response(request)
