"""build_record() — composes a PROVENANCE_SPEC v0.1 record dict from an
accepted Submission (BLUEPRINT §4). Pure function: takes a Submission, the
CommunityConfig, and the verifier's identity string; returns a plain dict
ready for store.append(), which computes record_id and validates it. Does
not touch the store and does not mutate the Submission — the caller
(workflow/api/views.py) is responsible for both.

record_signature is present but empty in the seed (no signing yet) — the
field is included so stored records match the spec's full field list, and
fills in once identity types that support signing wire it up.

VERIFICATION_METHOD defaults to 'editorial_review' — the one review path
the seed ships (a staff verifier accepting via /betat/review/{id}). The
record field is designed to carry other community-specific methods as they
are added (BLUEPRINT §4 Decision Log); this is the seed default, not a
permanent constant.
"""
from django.utils import timezone

DECLARATION_TEXT = (
    "I declare that this content was originated by a human being. I am "
    "that human being, or I am an authorized representative of that human "
    "being. I understand that this declaration is permanent, public, and "
    "append-only — it cannot be removed or modified."
)

VERIFICATION_METHOD = 'editorial_review'


def _iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def build_record(submission, config, verifier_identity, now=None):
    now = now or timezone.now()
    provenancier = submission.provenancier
    return {
        'betat_version': '0.1',
        'record_signature': '',          # present-but-empty: seed doesn't sign yet
        'timestamp': _iso(now),
        'hi_tag': True,
        'provenancier': {
            'identity': provenancier.identity,
            'identity_type': provenancier.identity_type,
            'authentication_method': provenancier.authentication_method,
            'display_name': provenancier.display_name,
        },
        'content': {
            'type': config.content_type,
            'title': submission.title,
            'location': submission.location,
            'content_hash': submission.content_hash,
            'language': submission.language,
        },
        'community': {
            'id': config.id,
            'name': config.name,
            'domain': config.domain,
            'content_type': config.content_type,
            'store_uri': config.store_uri,
        },
        'verification': {
            'method': VERIFICATION_METHOD,
            'verified_by': verifier_identity,
            'verification_timestamp': _iso(now),
        },
        'declaration': {
            'text': DECLARATION_TEXT,
            'language': 'en',
            'custom_addition': config.hi_standard,
        },
    }
