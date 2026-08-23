import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from betat_community.communityauth.enrollment import persist_provenancier
from betat_community.communityauth.plugins import PeerVouchAuth
from betat_community.core.models import CommunityConfig
from betat_community.store.models import ProvenanceRecord
from betat_community.workflow.models import Submission

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


def _provenancier_client(identity='researcher-1'):
    provenancier, token = persist_provenancier(
        identity=identity,
        identity_type='peer_attested',
        authentication_method=PeerVouchAuth.method_name,
        display_name='Researcher One',
        verification_material={},
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, provenancier


def _verifier_client(username='verifier-1'):
    user = get_user_model().objects.create_user(username=username, is_staff=True)
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, user


def _plain_user_client(username='plain-1'):
    user = get_user_model().objects.create_user(username=username)
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, user


def _valid_submit_payload(**overrides):
    payload = dict(
        title='Field observation',
        location='https://archive.example/obs-4471',
        content_hash='sha256:testhash',
        language='en',
        declaration_accepted=True,
    )
    payload.update(overrides)
    return payload


# --- submit ---------------------------------------------------------------

def test_submit_requires_authentication():
    _config()
    response = APIClient().post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    assert response.status_code == 401


def test_submit_rejects_non_provenancier_account():
    _config()
    client, _user = _plain_user_client()
    response = client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    assert response.status_code == 403
    assert response.data['error']['code'] == 'not_a_provenancier'


def test_submit_rejects_declaration_not_accepted():
    _config()
    client, _provenancier = _provenancier_client()
    response = client.post(
        reverse('betat-submit'), _valid_submit_payload(declaration_accepted=False), format='json',
    )
    assert response.status_code == 400
    assert response.data['error']['code'] == 'declaration_not_accepted'
    assert not Submission.objects.exists()


def test_submit_success_creates_pending_submission():
    _config()
    client, provenancier = _provenancier_client()
    response = client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    assert response.status_code == 201
    submission = Submission.objects.get()
    assert submission.status == Submission.STATUS_PENDING
    assert submission.provenancier_id == provenancier.pk
    assert submission.location == 'https://archive.example/obs-4471'


# --- queue ------------------------------------------------------------------

def test_queue_requires_verifier():
    _config()
    client, _provenancier = _provenancier_client()
    response = client.get(reverse('betat-queue'))
    assert response.status_code == 403


def test_queue_lists_only_pending():
    _config()
    p_client, provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    pending = Submission.objects.get()
    reviewed = Submission.objects.create(
        provenancier=provenancier, location='loc', content_hash='h', declaration_accepted=True,
        status=Submission.STATUS_ACCEPTED,
    )

    v_client, _verifier = _verifier_client()
    response = v_client.get(reverse('betat-queue'))
    assert response.status_code == 200
    ids = [item['id'] for item in response.data]
    assert ids == [pending.id]
    assert reviewed.id not in ids


# --- review -------------------------------------------------------------

def test_review_requires_verifier():
    _config()
    p_client, provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    submission = Submission.objects.get()

    response = p_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'accept'}, format='json')
    assert response.status_code == 403
    assert Submission.objects.get(pk=submission.id).status == Submission.STATUS_PENDING


def test_review_reject_closes_submission_without_record():
    _config()
    p_client, _provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    submission = Submission.objects.get()

    v_client, verifier = _verifier_client()
    response = v_client.post(
        reverse('betat-review', args=[submission.id]),
        {'decision': 'reject', 'reason': 'insufficient detail'},
        format='json',
    )
    assert response.status_code == 200
    submission.refresh_from_db()
    assert submission.status == Submission.STATUS_REJECTED
    assert submission.reviewed_by == verifier.username
    assert submission.rejection_reason == 'insufficient detail'
    assert submission.record_id == ''
    assert not ProvenanceRecord.objects.exists()


def test_review_accept_produces_valid_record():
    config = _config()
    p_client, provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    submission = Submission.objects.get()

    v_client, verifier = _verifier_client()
    response = v_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'accept'}, format='json')
    assert response.status_code == 200

    submission.refresh_from_db()
    assert submission.status == Submission.STATUS_ACCEPTED
    assert submission.reviewed_by == verifier.username
    assert submission.record_id

    record = ProvenanceRecord.objects.get(record_id=submission.record_id)
    assert record.hi_tag is True
    assert record.provenancier['identity'] == provenancier.identity
    assert record.provenancier['authentication_method'] == provenancier.authentication_method
    assert record.content['type'] == config.content_type
    assert record.content['location'] == 'https://archive.example/obs-4471'
    assert record.verification['verified_by'] == verifier.username
    assert record.verification['verification_timestamp']
    assert record.declaration['custom_addition'] == config.hi_standard


def test_review_already_reviewed_rejected():
    _config()
    p_client, _provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    submission = Submission.objects.get()

    v_client, _verifier = _verifier_client()
    v_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'reject'}, format='json')

    response = v_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'accept'}, format='json')
    assert response.status_code == 409
    assert response.data['error']['code'] == 'already_reviewed'


def test_review_invalid_decision_rejected():
    _config()
    p_client, _provenancier = _provenancier_client()
    p_client.post(reverse('betat-submit'), _valid_submit_payload(), format='json')
    submission = Submission.objects.get()

    v_client, _verifier = _verifier_client()
    response = v_client.post(reverse('betat-review', args=[submission.id]), {'decision': 'maybe'}, format='json')
    assert response.status_code == 400
    assert response.data['error']['code'] == 'invalid_request'
