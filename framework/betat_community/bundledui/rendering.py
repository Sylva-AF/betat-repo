"""Turns a PROVENANCE_SPEC record (as served by the public API) into the
card + evidence view described in RENDERING.md, and implements its binding
integrity-state rules: validate record_id (tampered), and — for the
record-detail view only, see views.py — re-check content_hash (verified /
changed / unreachable). List views intentionally skip the live
content-hash re-check (RENDERING.md allows "periodic or on-view"; hashing
every record's external content on every paginated list load would be
slow and network-heavy for exactly the low-bandwidth operators this
project cares about) — record_id validation still applies everywhere a
record is shown, since that's a cheap local recomputation, not a fetch.
"""
import hashlib
import urllib.error
import urllib.request

from betat_community.common.hashing import compute_record_id
from betat_community.core.models import CONTENT_TYPE_CHOICES

CONTENT_TYPE_LABELS = dict(CONTENT_TYPE_CHOICES)

# Small, non-exhaustive ISO 639-1 map for the seed UI — unknown codes just
# display as-is (still correct, just less friendly) rather than guessing.
LANGUAGE_NAMES = {
    'en': 'English', 'fr': 'French', 'es': 'Spanish', 'de': 'German',
    'pt': 'Portuguese', 'ar': 'Arabic', 'zh': 'Chinese', 'sw': 'Swahili',
    'hi': 'Hindi', 'ru': 'Russian', 'ja': 'Japanese',
}

FETCH_TIMEOUT_SECONDS = 8


def record_is_tampered(record):
    """RENDERING.md 'record tripwire' — recompute record_id, compare. A
    conforming client validates this on read; a mismatch renders as
    tampered, never silently as valid."""
    return compute_record_id(record) != record.get('record_id')


def check_content_hash(content):
    """RENDERING.md 'content tripwire'. Returns 'verified', 'changed', or
    'unreachable'. Fetching content.location is inherent to this
    spec-mandated re-check, not a shortcut — the location is provenance
    data the record points to, not something the UI hosts or trusts
    blindly."""
    location = content.get('location', '')
    expected = content.get('content_hash', '')
    try:
        with urllib.request.urlopen(location, timeout=FETCH_TIMEOUT_SECONDS) as response:
            body = response.read()
    except (urllib.error.URLError, ValueError, OSError):
        return 'unreachable'

    actual = f'sha256:{hashlib.sha256(body).hexdigest()}'
    return 'verified' if actual == expected else 'changed'


def content_type_label(value):
    return CONTENT_TYPE_LABELS.get(value, value)


def language_label(code):
    return LANGUAGE_NAMES.get(code, code)
