"""betat announce — pings the registry: "new records available — crawl me
now" (COMMUNITY_FRAMEWORK.md "Discoverability commands"). The registry's
own announce endpoint contract isn't defined anywhere yet — ARCHITECTURE.md
calls its registry interface a "sketch... to be refined by Contributors"
and lists only GET .../communities, GET .../communities/{id}, and
POST .../register; no announce endpoint exists in that sketch. This module
POSTs a reasonable, documented payload to BETAT_REGISTRY_URL — expect the
payload shape to need updating once the registry ships a real contract.

Uses urllib (stdlib) rather than adding an HTTP client dependency,
consistent with bundledui/rendering.py's content-hash fetch.
"""
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.utils import timezone

ANNOUNCE_TIMEOUT_SECONDS = 5


class AnnounceError(Exception):
    pass


def send_announcement(config):
    """Raises AnnounceError on any failure (no registry configured,
    unreachable, non-2xx response). The caller decides whether that's
    fatal (the `announce` command) or best-effort (auto-announce on
    accept — see workflow/api/views.py)."""
    registry_url = getattr(settings, 'BETAT_REGISTRY_URL', '') or ''
    if not registry_url:
        raise AnnounceError(
            'BETAT_REGISTRY_URL is not set — nowhere to announce to. Set it '
            'in the environment (or .env) once registered with a registry.'
        )

    payload = {
        'community_id': config.id,
        'store_uri': config.store_uri,
        'announced_at': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    request = urllib.request.Request(
        registry_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=ANNOUNCE_TIMEOUT_SECONDS) as response:
            if response.status >= 300:
                raise AnnounceError(f'Registry responded with status {response.status}.')
    except urllib.error.URLError as exc:
        raise AnnounceError(f'Could not reach registry at {registry_url}: {exc}') from exc

    return payload
