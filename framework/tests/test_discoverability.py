import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from betat_community.communityauth.enrollment import persist_provenancier
from betat_community.communityauth.plugins import PeerVouchAuth
from betat_community.core.announce import AnnounceError, send_announcement
from betat_community.core.export import build_export, verify_export
from betat_community.core.models import CommunityConfig
from betat_community.store import store
from betat_community.workflow.models import Submission

pytestmark = pytest.mark.django_db


def _config(**overrides):
    kwargs = dict(
        id='example.org',
        name='Example Community',
        domain='marine biology',
        content_type='text',
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


# --- export -----------------------------------------------------------

def test_build_export_empty_store_is_valid():
    config = _config()
    export_data = build_export(config)
    assert export_data['record_count'] == 0
    assert export_data['records'] == []
    assert verify_export(export_data) is True


def test_build_export_with_records_validates():
    config = _config()
    store.append(_valid_record_data())
    store.append(_valid_record_data(
        content={**_valid_record_data()['content'], 'location': 'https://archive.example/second'},
        timestamp='2026-07-01T00:00:00Z',
    ))
    export_data = build_export(config)
    assert export_data['record_count'] == 2
    assert verify_export(export_data) is True


def test_verify_export_detects_tampered_record():
    _config()
    store.append(_valid_record_data())
    export_data = build_export(CommunityConfig.objects.get())
    export_data['records'][0]['hi_tag'] = False
    assert verify_export(export_data) is False


def test_verify_export_detects_tampered_bundle_hash():
    _config()
    store.append(_valid_record_data())
    export_data = build_export(CommunityConfig.objects.get())
    export_data['export_hash'] = 'sha256:' + '0' * 64
    assert verify_export(export_data) is False


def test_export_command_requires_config():
    with pytest.raises(CommandError):
        call_command('export')


def test_export_command_writes_to_file(tmp_path):
    _config()
    store.append(_valid_record_data())
    output_path = tmp_path / 'export.json'
    call_command('export', output=str(output_path))
    data = json.loads(output_path.read_text())
    assert verify_export(data) is True
    assert data['record_count'] == 1


# --- announce ------------------------------------------------------------

def test_send_announcement_requires_registry_url():
    config = _config()
    with pytest.raises(AnnounceError):
        send_announcement(config)


def test_send_announcement_posts_payload(settings):
    settings.BETAT_REGISTRY_URL = 'https://registry.example/announce'
    config = _config()
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.status = 200
    with patch('betat_community.core.announce.urllib.request.urlopen', return_value=mock_cm):
        payload = send_announcement(config)
    assert payload['community_id'] == 'example.org'
    assert payload['store_uri'] == config.store_uri


def test_send_announcement_raises_on_unreachable_registry(settings):
    settings.BETAT_REGISTRY_URL = 'https://registry.example/announce'
    config = _config()
    import urllib.error
    with patch(
        'betat_community.core.announce.urllib.request.urlopen',
        side_effect=urllib.error.URLError('refused'),
    ):
        with pytest.raises(AnnounceError):
            send_announcement(config)


def test_announce_command_requires_config():
    with pytest.raises(CommandError):
        call_command('announce')


def test_announce_command_requires_registry_url(settings):
    settings.BETAT_REGISTRY_URL = ''
    _config()
    with pytest.raises(CommandError):
        call_command('announce')


def test_announce_command_success(settings):
    settings.BETAT_REGISTRY_URL = 'https://registry.example/announce'
    _config()
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.status = 200
    with patch('betat_community.core.announce.urllib.request.urlopen', return_value=mock_cm):
        call_command('announce')  # no exception raised = success


# --- auto-announce on accept (workflow integration) -----------------------

def _accept_a_submission():
    provenancier, token = persist_provenancier(
        identity='researcher-1', identity_type='peer_attested',
        authentication_method=PeerVouchAuth.method_name, display_name='', verification_material={},
    )
    p_client = APIClient()
    p_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    p_client.post(reverse('betat-submit'), {
        'location': 'https://archive.example/x', 'content_hash': 'sha256:x', 'declaration_accepted': True,
    }, format='json')
    submission = Submission.objects.get()

    verifier = get_user_model().objects.create_user(username='verifier-1', is_staff=True)
    verifier_token = Token.objects.create(user=verifier)
    v_client = APIClient()
    v_client.credentials(HTTP_AUTHORIZATION=f'Token {verifier_token.key}')
    return v_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'accept'}, format='json')


def test_accept_does_not_announce_when_disabled(settings):
    settings.BETAT_AUTO_ANNOUNCE = False
    _config()
    with patch('betat_community.workflow.api.views.send_announcement') as mock_announce:
        response = _accept_a_submission()
    assert response.status_code == 200
    mock_announce.assert_not_called()


def test_accept_announces_when_enabled(settings):
    settings.BETAT_AUTO_ANNOUNCE = True
    _config()
    with patch('betat_community.workflow.api.views.send_announcement') as mock_announce:
        response = _accept_a_submission()
    assert response.status_code == 200
    mock_announce.assert_called_once()


def test_accept_survives_announce_failure(settings):
    settings.BETAT_AUTO_ANNOUNCE = True
    _config()
    with patch(
        'betat_community.workflow.api.views.send_announcement',
        side_effect=AnnounceError('registry down'),
    ):
        response = _accept_a_submission()
    assert response.status_code == 200
    submission = Submission.objects.get()
    assert submission.status == Submission.STATUS_ACCEPTED
