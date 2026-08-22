"""The append-only provenance store's sole write and read API.

append() is the ONLY way a record enters the store. There is no
update() or delete() here, deliberately — the model additionally
blocks both at the ORM level, and the (hand-off) SQLite migration
blocks both at the DB level via guard triggers. record_id is always
computed server-side in append(); any caller-supplied record_id is
ignored, since a caller-supplied hash would be an attack surface.
"""
from django.core.exceptions import ValidationError

from betat_community.common import hashing
from .models import ProvenanceRecord

DEFAULT_PAGE_SIZE = 50

REQUIRED_TOP_LEVEL = (
    'betat_version', 'timestamp', 'provenancier', 'content',
    'community', 'verification', 'declaration',
)
REQUIRED_NESTED = {
    'provenancier': ('identity', 'identity_type', 'authentication_method'),
    'content': ('type', 'location', 'content_hash', 'language'),
    'community': ('id', 'name', 'domain', 'content_type', 'store_uri'),
    'verification': ('method', 'verified_by', 'verification_timestamp'),
    'declaration': ('text', 'language'),
}


def _validate(record_data):
    if record_data.get('hi_tag') is not True:
        raise ValidationError(
            'hi_tag must be true — a record without it is not a valid '
            'Betat provenance record.',
            code='invalid_hi_tag',
        )

    for field in REQUIRED_TOP_LEVEL:
        if not record_data.get(field):
            raise ValidationError(f"'{field}' is required.", code='missing_field')

    for obj_name, obj_fields in REQUIRED_NESTED.items():
        obj = record_data.get(obj_name) or {}
        for field in obj_fields:
            if not obj.get(field):
                raise ValidationError(
                    f"'{obj_name}.{field}' is required.", code='missing_field'
                )

    if record_data['content']['type'] != record_data['community']['content_type']:
        raise ValidationError(
            'content.type must match community.content_type — a community '
            'cannot issue records outside its authorized content type.',
            code='content_type_mismatch',
        )


def append(record_data):
    """Validate, hash, and insert a new record. Returns the saved
    ProvenanceRecord. Ignores any caller-supplied record_id/record_signature
    identity beyond record_signature's opaque value — record_id is always
    recomputed here."""
    _validate(record_data)

    canonical_input = {
        'betat_version': record_data['betat_version'],
        'record_id': '',
        'timestamp': record_data['timestamp'],
        'hi_tag': True,
        'provenancier': record_data['provenancier'],
        'content': record_data['content'],
        'community': record_data['community'],
        'verification': record_data['verification'],
        'declaration': record_data['declaration'],
        'record_signature': record_data.get('record_signature', ''),
    }
    if record_data.get('correction_of'):
        canonical_input['correction_of'] = record_data['correction_of']
    if record_data.get('disputes'):
        canonical_input['disputes'] = record_data['disputes']

    record_id = hashing.compute_record_id(canonical_input)

    record = ProvenanceRecord(
        record_id=record_id,
        betat_version=record_data['betat_version'],
        timestamp=record_data['timestamp'],
        hi_tag=True,
        provenancier=record_data['provenancier'],
        content=record_data['content'],
        community=record_data['community'],
        verification=record_data['verification'],
        declaration=record_data['declaration'],
        record_signature=record_data.get('record_signature', ''),
        correction_of_id=record_data.get('correction_of') or None,
        disputes_id=record_data.get('disputes') or None,
    )
    # force_insert: record_id is a manually-assigned PK, so Django would
    # otherwise probe with an UPDATE before falling back to INSERT. append()
    # only ever creates new rows — force_insert skips the wasted probe and
    # turns a record_id collision into a clean IntegrityError instead of
    # tripping the append-only guard.
    record.save(force_insert=True)
    return record


def get(record_id):
    return ProvenanceRecord.objects.get(record_id=record_id)


def list_records(since=None, page=1, page_size=DEFAULT_PAGE_SIZE):
    """Newest-first, optionally filtered to records after `since`
    (a timestamp string, same ISO 8601 format as record.timestamp)."""
    queryset = ProvenanceRecord.objects.all()
    if since:
        queryset = queryset.filter(timestamp__gt=since)
    start = (page - 1) * page_size
    end = start + page_size
    return list(queryset[start:end])


def verify_integrity(record_id):
    """Recompute record_id from the record's current stored content and
    compare to the stored record_id. False means tampering (or a hash
    mismatch that should never happen via append())."""
    record = get(record_id)
    recomputed = hashing.compute_record_id(record.to_dict())
    return recomputed == record.record_id
