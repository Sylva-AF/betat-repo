import pytest
from django.core.exceptions import ValidationError
from django.db import Error as DjangoDBError
from django.db import connection

from betat_community.common import hashing
from betat_community.store import store
from betat_community.store.models import ProvenanceRecord

pytestmark = pytest.mark.django_db


def _valid_record_data(**overrides):
    data = {
        'betat_version': '0.1',
        'timestamp': '2026-06-12T14:32:00Z',
        'hi_tag': True,
        'provenancier': {
            'identity': 'did:key:z6Mkftest',
            'identity_type': 'cryptographic_key',
            'authentication_method': 'cryptographic_signature',
            'display_name': 'Test Provenancier',
        },
        'content': {
            'type': 'text',
            'title': 'A test record',
            'location': 'ipfs://bafytest',
            'content_hash': 'sha256:testhash',
            'language': 'en',
        },
        'community': {
            'id': 'example.org',
            'name': 'Example Community',
            'domain': 'testing',
            'content_type': 'text',
            'store_uri': 'https://example.org/store',
        },
        'verification': {
            'method': 'cryptographic_signature',
            'verified_by': 'did:key:z6Mkftest',
            'verification_timestamp': '2026-06-12T14:32:01Z',
        },
        'declaration': {
            'text': 'I declare this content was originated by a human being.',
            'language': 'en',
        },
    }
    data.update(overrides)
    return data


def test_append_writes_valid_record():
    record = store.append(_valid_record_data())
    assert ProvenanceRecord.objects.filter(record_id=record.record_id).exists()
    assert record.hi_tag is True


def test_record_id_computed_server_side_ignores_caller_value():
    data = _valid_record_data()
    data['record_id'] = 'attacker-supplied-value'
    record = store.append(data)
    assert record.record_id != 'attacker-supplied-value'
    expected = hashing.compute_record_id({**data, 'record_id': '', 'record_signature': ''})
    assert record.record_id == expected


def test_round_trip_byte_identical():
    data = _valid_record_data()
    record = store.append(data)
    fetched = store.get(record.record_id)
    assert fetched.to_dict() == record.to_dict()
    for key in ('betat_version', 'timestamp', 'provenancier', 'content', 'community', 'verification', 'declaration'):
        assert fetched.to_dict()[key] == data[key]


def test_hi_tag_false_rejected():
    with pytest.raises(ValidationError):
        store.append(_valid_record_data(hi_tag=False))


def test_hi_tag_missing_rejected():
    data = _valid_record_data()
    del data['hi_tag']
    with pytest.raises(ValidationError):
        store.append(data)


def test_content_type_must_match_community_content_type():
    data = _valid_record_data()
    data['content'] = {**data['content'], 'type': 'creative_work'}
    with pytest.raises(ValidationError):
        store.append(data)


def test_missing_required_field_rejected():
    data = _valid_record_data()
    del data['declaration']
    with pytest.raises(ValidationError):
        store.append(data)


def test_correction_references_original():
    original = store.append(_valid_record_data())
    correction_data = _valid_record_data(
        content={**_valid_record_data()['content'], 'location': 'ipfs://different'},
        correction_of=original.record_id,
    )
    correction = store.append(correction_data)
    assert correction.correction_of_id == original.record_id
    assert original.corrections.get().record_id == correction.record_id


def test_list_records_newest_first_and_since_filter():
    r1 = store.append(_valid_record_data(timestamp='2026-01-01T00:00:00Z'))
    r2 = store.append(_valid_record_data(
        content={**_valid_record_data()['content'], 'location': 'ipfs://second'},
        timestamp='2026-02-01T00:00:00Z',
    ))
    records = store.list_records()
    assert [r.record_id for r in records] == [r2.record_id, r1.record_id]

    since_records = store.list_records(since='2026-01-15T00:00:00Z')
    assert [r.record_id for r in since_records] == [r2.record_id]


def test_verify_integrity_passes_on_clean_record():
    record = store.append(_valid_record_data())
    assert store.verify_integrity(record.record_id) is True


def test_verify_integrity_fails_on_tampered_record():
    # bulk_create bypasses the append-only guard (it's an insert, not an
    # update/delete) — used here to simulate a corrupted row without
    # fighting the guards this module deliberately makes hard to bypass.
    tampered = ProvenanceRecord(
        record_id='0' * 64,
        betat_version='0.1',
        timestamp='2026-06-12T14:32:00Z',
        hi_tag=True,
        provenancier=_valid_record_data()['provenancier'],
        content=_valid_record_data()['content'],
        community=_valid_record_data()['community'],
        verification=_valid_record_data()['verification'],
        declaration=_valid_record_data()['declaration'],
    )
    ProvenanceRecord.objects.bulk_create([tampered])
    assert store.verify_integrity('0' * 64) is False


def test_store_module_has_no_update_or_delete():
    assert not hasattr(store, 'update')
    assert not hasattr(store, 'delete')


def test_queryset_update_blocked():
    store.append(_valid_record_data())
    with pytest.raises(Exception):
        ProvenanceRecord.objects.all().update(hi_tag=False)


def test_instance_delete_blocked():
    record = store.append(_valid_record_data())
    with pytest.raises(Exception):
        record.delete()


def test_raw_sql_update_blocked_by_sqlite_trigger():
    if connection.vendor != 'sqlite':
        pytest.skip('guard trigger is the SQLite-specific enforcement seam')
    record = store.append(_valid_record_data())
    with pytest.raises(DjangoDBError):
        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE store_provenancerecord SET hi_tag = 0 WHERE record_id = %s',
                [record.record_id],
            )


def test_raw_sql_delete_blocked_by_sqlite_trigger():
    if connection.vendor != 'sqlite':
        pytest.skip('guard trigger is the SQLite-specific enforcement seam')
    record = store.append(_valid_record_data())
    with pytest.raises(DjangoDBError):
        with connection.cursor() as cursor:
            cursor.execute(
                'DELETE FROM store_provenancerecord WHERE record_id = %s',
                [record.record_id],
            )
