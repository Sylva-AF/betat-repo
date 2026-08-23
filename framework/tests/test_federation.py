import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from betat_community.common.permissions import PublicReadOnly
from betat_community.core.models import CommunityConfig
from betat_community.store import store
from betat_community.store.models import ProvenanceRecord

pytestmark = pytest.mark.django_db


def _config(**overrides):
    kwargs = dict(
        id='example.org',
        name='Example Community',
        domain='marine biology',
        content_type='scientific_observation',
        store_uri='https://example.org/records',
        auth_methods=['community_peer_vouching'],
    )
    kwargs.update(overrides)
    return CommunityConfig.objects.create(**kwargs)


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
            'type': 'scientific_observation',
            'title': 'A test record',
            'location': 'ipfs://bafytest',
            'content_hash': 'sha256:testhash',
            'language': 'en',
        },
        'community': {
            'id': 'example.org',
            'name': 'Example Community',
            'domain': 'marine biology',
            'content_type': 'scientific_observation',
            'store_uri': 'https://example.org/records',
        },
        'verification': {
            'method': 'editorial_review',
            'verified_by': 'verifier-1',
            'verification_timestamp': '2026-06-12T14:32:01Z',
        },
        'declaration': {
            'text': 'I declare this content was originated by a human being.',
            'language': 'en',
        },
    }
    data.update(overrides)
    return data


# --- /betat/info -----------------------------------------------------------

def test_info_returns_config():
    _config()
    response = APIClient().get(reverse('betat-info'))
    assert response.status_code == 200
    assert response.data['id'] == 'example.org'
    assert response.data['hi_standard']
    assert 'trusted_institutions' not in response.data
    assert 'peer_vouch_threshold' not in response.data


def test_info_returns_404_when_not_configured():
    response = APIClient().get(reverse('betat-info'))
    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_configured'


# --- /betat/records ----------------------------------------------------

def test_records_lists_newest_first():
    _config()
    older = store.append(_valid_record_data(timestamp='2026-01-01T00:00:00Z'))
    newer = store.append(_valid_record_data(
        content={**_valid_record_data()['content'], 'location': 'ipfs://second'},
        timestamp='2026-02-01T00:00:00Z',
    ))
    response = APIClient().get(reverse('betat-records'))
    assert response.status_code == 200
    ids = [r['record_id'] for r in response.data['results']]
    assert ids == [newer.record_id, older.record_id]


def test_records_hi_only_filter():
    _config()
    normal = store.append(_valid_record_data())
    tampered_hi_false = ProvenanceRecord(
        record_id='0' * 64,
        betat_version='0.1',
        timestamp='2026-06-12T14:32:00Z',
        hi_tag=False,
        provenancier=_valid_record_data()['provenancier'],
        content=_valid_record_data()['content'],
        community=_valid_record_data()['community'],
        verification=_valid_record_data()['verification'],
        declaration=_valid_record_data()['declaration'],
    )
    ProvenanceRecord.objects.bulk_create([tampered_hi_false])

    response = APIClient().get(reverse('betat-records'), {'hi_only': 'true'})
    ids = [r['record_id'] for r in response.data['results']]
    assert ids == [normal.record_id]

    response = APIClient().get(reverse('betat-records'), {'hi_only': 'false'})
    ids = [r['record_id'] for r in response.data['results']]
    assert ids == ['0' * 64]


def test_records_response_includes_no_internal_fields():
    _config()
    store.append(_valid_record_data())
    response = APIClient().get(reverse('betat-records'))
    record = response.data['results'][0]
    assert set(record) == {
        'betat_version', 'record_id', 'timestamp', 'hi_tag', 'provenancier',
        'content', 'community', 'verification', 'declaration', 'record_signature',
    }


# --- /betat/records/{id} ------------------------------------------------

def test_record_detail_returns_record():
    _config()
    record = store.append(_valid_record_data())
    response = APIClient().get(reverse('betat-record-detail', args=[record.record_id]))
    assert response.status_code == 200
    assert response.data['record_id'] == record.record_id
    assert response.data['hi_tag'] is True


def test_record_detail_404_for_unknown_id():
    _config()
    response = APIClient().get(reverse('betat-record-detail', args=['0' * 64]))
    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_found'


# --- /betat/changes ------------------------------------------------------

def test_changes_since_filters_correctly():
    _config()
    r1 = store.append(_valid_record_data(timestamp='2026-01-01T00:00:00Z'))
    r2 = store.append(_valid_record_data(
        content={**_valid_record_data()['content'], 'location': 'ipfs://second'},
        timestamp='2026-02-01T00:00:00Z',
    ))

    response = APIClient().get(reverse('betat-changes'))
    ids = {r['record_id'] for r in response.data['results']}
    assert ids == {r1.record_id, r2.record_id}

    response = APIClient().get(reverse('betat-changes'), {'since': '2026-01-15T00:00:00Z'})
    ids = [r['record_id'] for r in response.data['results']]
    assert ids == [r2.record_id]


# --- permission class ------------------------------------------------------

class _FakeRequest:
    def __init__(self, method):
        self.method = method


@pytest.mark.parametrize('method,allowed', [('GET', True), ('HEAD', True), ('OPTIONS', True), ('POST', False), ('DELETE', False)])
def test_public_read_only_permission(method, allowed):
    assert PublicReadOnly().has_permission(_FakeRequest(method), None) is allowed
