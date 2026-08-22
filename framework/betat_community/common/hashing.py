"""Canonicalization + hashing for PROVENANCE_SPEC records.

Per PROVENANCE_SPEC.md "Implementation Notes": canonical form for
hashing sets record_id and record_signature to "", sorts keys
alphabetically (json.dumps sort_keys applies recursively to nested
objects), and serializes with no whitespace. record_id is the SHA-256
hex digest of that canonical UTF-8 JSON. Pure functions, no Django/DB
dependency, so hashing behavior is independently testable and stable
across Python versions.

Lives in common/ (not store/) because it's shared beyond the store —
federation validates record_id on read, workflow computes it when
building a record for store.append(). See BLUEPRINT.md §0 Decision Log
"API structure" and §5.
"""
import hashlib
import json


def canonicalize(record):
    """Return the canonical UTF-8 JSON bytes of a record dict."""
    canonical = dict(record)
    canonical['record_id'] = ''
    canonical['record_signature'] = ''
    return json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_record_id(record):
    """Return the SHA-256 hex digest of a record's canonical form."""
    return hashlib.sha256(canonicalize(record)).hexdigest()
