from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from betat_community.communityauth import crypto
from betat_community.communityauth.enrollment import persist_provenancier
from betat_community.communityauth.plugins import CryptoKeyAuth
from betat_community.core.models import CommunityConfig
from betat_community.store import store
from betat_community.store.models import ProvenanceRecord
from betat_community.workflow.models import Submission

pytestmark = pytest.mark.django_db


def _config(**overrides):
    kwargs = dict(
        id='example.org',
        name='Example Community',
        domain='marine biology',
        content_type='text',
        store_uri='https://example.org/records',
        auth_methods=['cryptographic_signature'],
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
            'type': 'text',
            'title': 'A test record',
            'location': 'https://archive.example/obs-4471',
            'content_hash': 'sha256:testhash',
            'language': 'en',
        },
        'community': {
            'id': 'example.org',
            'name': 'Example Community',
            'domain': 'marine biology',
            'content_type': 'text',
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
            'custom_addition': 'human-originated, community-verified',
        },
    }
    data.update(overrides)
    return data


# --- installer (Phase 1) --------------------------------------------------
# BetatConfiguredMiddleware redirects every community-facing page to the
# installer until a CommunityConfig exists (TODO 07 amendment) — this
# supersedes the old "render an inline not-configured banner behind a
# broken nav" behavior these views used to have.

def test_enroll_page_redirects_to_installer_when_no_config(client):
    response = client.get(reverse('bundledui-enroll'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-install')


def test_landing_redirects_to_installer_when_no_config(client):
    response = client.get(reverse('bundledui-landing'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-install')


def test_installer_shown_when_not_configured(client):
    response = client.get(reverse('bundledui-install'))
    assert response.status_code == 200
    assert b'Begin setup' in response.content


def test_installer_has_no_nav(client):
    response = client.get(reverse('bundledui-install'))
    assert b'bt-nav' not in response.content


def test_installer_redirects_to_landing_once_configured(client):
    _config()
    response = client.get(reverse('bundledui-install'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-landing')


def test_admin_exempt_from_installer_redirect(client):
    response = client.get('/admin/login/')
    assert response.status_code == 200


def test_api_exempt_from_installer_redirect(client):
    # The public API's own "not configured" semantics (BLUEPRINT §06
    # Decision Log) predate this gate and must not be intercepted by it.
    response = client.get(reverse('betat-info'))
    assert response.status_code == 404


# --- enroll / submit -----------------------------------------------------

def test_enroll_page_lists_configured_auth_methods(client):
    _config(auth_methods=['cryptographic_signature'])
    response = client.get(reverse('bundledui-enroll'))
    assert response.status_code == 200
    assert b'cryptographic_signature' in response.content


def test_enroll_then_submit_flow(client):
    _config(auth_methods=['cryptographic_signature'])
    private_key, public_key = crypto.generate_keypair()
    proof = crypto.sign(private_key, public_key)

    enroll_response = client.post(reverse('bundledui-enroll'), {
        'method': 'cryptographic_signature',
        'identity': 'did:key:z6MkUiTest',
        'display_name': 'UI Tester',
        'public_key': public_key,
        'signature': proof,
    })
    assert enroll_response.status_code == 302
    assert enroll_response.url == reverse('bundledui-submit')
    assert client.session['provenancier_token']
    assert client.session['provenancier_identity'] == 'did:key:z6MkUiTest'

    submit_response = client.post(reverse('bundledui-submit'), {
        'title': 'Field note',
        'location': 'https://archive.example/note',
        'content_hash': 'sha256:abc',
        'language': 'en',
        'declaration_accepted': True,
    })
    assert submit_response.status_code == 302
    assert Submission.objects.filter(location='https://archive.example/note').exists()


def test_submit_without_enrolling_redirects_to_enroll(client):
    _config()
    response = client.get(reverse('bundledui-submit'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-enroll')


# --- verifier login / queue -----------------------------------------------

def test_verifier_login_rejects_non_staff(client):
    _config()
    get_user_model().objects.create_user(username='plain', password='pw12345!')
    response = client.post(reverse('bundledui-verifier-login'), {'username': 'plain', 'password': 'pw12345!'})
    assert response.status_code == 200  # re-renders form, no redirect
    assert not response.wsgi_request.user.is_authenticated


def test_verifier_login_success_reaches_queue(client):
    _config()
    get_user_model().objects.create_user(username='verifier', password='pw12345!', is_staff=True)
    response = client.post(reverse('bundledui-verifier-login'), {'username': 'verifier', 'password': 'pw12345!'})
    assert response.status_code == 302
    assert response.url == reverse('bundledui-queue')


def test_queue_requires_verifier_login(client):
    _config()
    response = client.get(reverse('bundledui-queue'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-verifier-login')


def test_review_action_accept_produces_record(client):
    _config(auth_methods=['cryptographic_signature'])
    provenancier, _token = persist_provenancier(
        identity='did:key:z6MkReviewer',
        identity_type='cryptographic_key',
        authentication_method=CryptoKeyAuth.method_name,
        display_name='',
        verification_material={},
    )
    submission = Submission.objects.create(
        provenancier=provenancier, location='https://archive.example/x',
        content_hash='sha256:x', declaration_accepted=True,
    )
    get_user_model().objects.create_user(username='verifier', password='pw12345!', is_staff=True)
    client.post(reverse('bundledui-verifier-login'), {'username': 'verifier', 'password': 'pw12345!'})

    response = client.post(
        reverse('bundledui-review-action', args=[submission.id]), {'decision': 'accept'},
    )
    assert response.status_code == 302
    submission.refresh_from_db()
    assert submission.status == Submission.STATUS_ACCEPTED
    record = ProvenanceRecord.objects.filter(record_id=submission.record_id).first()
    assert record is not None
    assert record.content['type'] == 'text'


# --- records list / detail ------------------------------------------------

def test_records_list_shows_records(client):
    _config()
    store.append(_valid_record_data())
    response = client.get(reverse('bundledui-records'))
    assert response.status_code == 200
    assert b'A test record' in response.content


def test_record_detail_unverified_for_unknown_id(client):
    _config()
    response = client.get(reverse('bundledui-record-detail', args=['0' * 64]))
    assert response.status_code == 200
    assert b'No provenance record found' in response.content


def test_record_detail_tampered_state(client):
    _config()
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

    response = client.get(reverse('bundledui-record-detail', args=['0' * 64]))
    assert response.status_code == 200
    assert b'failed integrity validation' in response.content


def test_record_detail_shows_verified_state(client):
    _config()
    record = store.append(_valid_record_data())
    with patch('betat_community.bundledui.views.check_content_hash', return_value='verified'):
        response = client.get(reverse('bundledui-record-detail', args=[record.record_id]))
    assert response.status_code == 200
    assert b'Content verified intact' in response.content


def test_record_detail_shows_changed_state(client):
    _config()
    record = store.append(_valid_record_data())
    with patch('betat_community.bundledui.views.check_content_hash', return_value='changed'):
        response = client.get(reverse('bundledui-record-detail', args=[record.record_id]))
    assert response.status_code == 200
    assert b'has changed since it was verified' in response.content


def test_record_detail_shows_unreachable_state(client):
    _config()
    record = store.append(_valid_record_data())
    # Mocked rather than relying on real DNS failure for a reserved
    # domain — real network calls in tests are slow and environment-
    # dependent (same reasoning as the init.py DNS-check caution).
    with patch('betat_community.bundledui.views.check_content_hash', return_value='unreachable'):
        response = client.get(reverse('bundledui-record-detail', args=[record.record_id]))
    assert response.status_code == 200
    assert b'is not currently reachable' in response.content


# --- landing / readiness checklist (§08) ----------------------------------
# landing_view's own "not configured" banner branch is no longer reachable
# through normal navigation — the installer gate intercepts '/' first (see
# test_landing_redirects_to_installer_when_no_config above).

def test_landing_shows_configured_state(client):
    config = _config(auth_methods=['cryptographic_signature'])
    response = client.get(reverse('bundledui-landing'))
    assert response.status_code == 200
    assert config.name.encode() in response.content


def test_landing_checklist_links_to_real_docs(client):
    _config(auth_methods=['cryptographic_signature'])
    response = client.get(reverse('bundledui-landing'))
    assert response.status_code == 200
    # §11 replaced the placeholder with real, resolving Framework Reference
    # pages on the public site — no more bare "betat.org" front-door link.
    assert b'betat.org/framework-cli.html' in response.content
    assert b'betat.org/framework-api.html' in response.content
    assert b'Not configured yet' not in response.content
