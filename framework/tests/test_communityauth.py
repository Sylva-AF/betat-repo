import dataclasses

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from betat_community.communityauth import crypto, floor, passphrase
from betat_community.communityauth.identity import Pending, ProvenancierIdentity, Rejection
from betat_community.communityauth.models import PeerVouchRequest, Provenancier
from betat_community.communityauth.plugins import CryptoKeyAuth, InstitutionalAuth, PeerVouchAuth
from betat_community.core.models import CommunityConfig

pytestmark = pytest.mark.django_db


def _config(**overrides):
    kwargs = dict(
        id='example.org',
        name='Example Community',
        domain='marine biology',
        content_type='scientific_observation',
        store_uri='https://example.org/records',
        auth_methods=['community_peer_vouching', 'cryptographic_signature', 'institutional_endorsement'],
    )
    kwargs.update(overrides)
    return CommunityConfig.objects.create(**kwargs)


def _enrolled_voucher(identity):
    """A Provenancier that already counts as an enrolled voucher for peer-vouch tests."""
    user = get_user_model().objects.create_user(username=f'user:{identity}')
    return Provenancier.objects.create(
        user=user,
        identity=identity,
        identity_type='peer_attested',
        authentication_method=PeerVouchAuth.method_name,
        display_name='',
    )


def _assert_matches_provenancier_shape(identity_obj):
    assert {f.name for f in dataclasses.fields(identity_obj)} == {
        'identity', 'identity_type', 'authentication_method', 'display_name',
    }


# --- Floor -------------------------------------------------------------

def test_protocol_list_has_exactly_the_three_seed_plugins():
    assert set(floor.PROTOCOL_LIST) == {
        'community_peer_vouching', 'cryptographic_signature', 'institutional_endorsement',
    }


def test_validate_floor_rejects_empty():
    with pytest.raises(ValidationError):
        floor.validate_floor([])


def test_validate_floor_rejects_off_list_method():
    with pytest.raises(ValidationError):
        floor.validate_floor(['government_id_verification'])


def test_validate_floor_accepts_protocol_list_methods():
    floor.validate_floor(['community_peer_vouching'])


def test_community_config_rejects_off_list_auth_method():
    with pytest.raises(ValidationError):
        _config(auth_methods=['government_id_verification'])


# --- PeerVouchAuth (two-phase, BLUEPRINT §03 Decision Log 2026-09) ------

def test_peer_vouch_enroll_returns_pending_with_zero_vouches():
    config = _config(peer_vouch_threshold=2)
    plugin = PeerVouchAuth(config)

    result = plugin.enroll({'identity': 'newcomer', 'display_name': 'Newcomer'})

    assert isinstance(result, Pending)
    assert result.code == 'pending_vouches'
    assert result.vouch_count == 0
    assert result.vouches_needed == 2
    assert PeerVouchRequest.objects.filter(identity='newcomer').exists()
    assert not Provenancier.objects.filter(identity='newcomer').exists()


def test_peer_vouch_enroll_rejects_duplicate_identity():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('existing-member')
    plugin = PeerVouchAuth(config)

    result = plugin.enroll({'identity': 'existing-member'})
    assert isinstance(result, Rejection)
    assert result.code == 'identity_taken'


def test_peer_vouch_add_vouch_progresses_and_promotes_at_threshold():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    _enrolled_voucher('voucher-two')
    plugin = PeerVouchAuth(config)
    pending = plugin.enroll({'identity': 'newcomer', 'display_name': 'Newcomer'})

    progress = plugin.add_vouch(pending.request_id, 'voucher-one')
    assert isinstance(progress, Pending)
    assert progress.vouch_count == 1
    assert progress.vouches_needed == 1

    promoted = plugin.add_vouch(pending.request_id, 'voucher-two')
    assert isinstance(promoted, ProvenancierIdentity)
    _assert_matches_provenancier_shape(promoted)
    assert promoted.identity == 'newcomer'
    assert promoted.identity_type == 'peer_attested'
    assert promoted.authentication_method == 'community_peer_vouching'
    assert Provenancier.objects.filter(identity='newcomer').exists()
    assert Token.objects.filter(user__provenancier__identity='newcomer').exists()
    assert not PeerVouchRequest.objects.filter(identity='newcomer').exists()


def test_peer_vouch_add_vouch_rejects_self_vouch():
    config = _config(peer_vouch_threshold=2)
    plugin = PeerVouchAuth(config)
    pending = plugin.enroll({'identity': 'newcomer'})

    result = plugin.add_vouch(pending.request_id, 'newcomer')
    assert isinstance(result, Rejection)
    assert result.code == 'self_vouch'


def test_peer_vouch_add_vouch_is_idempotent():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    plugin = PeerVouchAuth(config)
    pending = plugin.enroll({'identity': 'newcomer'})

    plugin.add_vouch(pending.request_id, 'voucher-one')
    result = plugin.add_vouch(pending.request_id, 'voucher-one')

    assert isinstance(result, Pending)
    assert result.vouch_count == 1


def test_peer_vouch_add_vouch_raises_for_unknown_request():
    config = _config(peer_vouch_threshold=2)
    plugin = PeerVouchAuth(config)
    with pytest.raises(ValueError):
        plugin.add_vouch(999999, 'voucher-one')


def test_peer_vouch_authenticate_success_and_rejection():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    _enrolled_voucher('voucher-two')
    plugin = PeerVouchAuth(config)
    pending = plugin.enroll({'identity': 'newcomer'})
    plugin.add_vouch(pending.request_id, 'voucher-one')
    plugin.add_vouch(pending.request_id, 'voucher-two')

    ok = plugin.authenticate({'identity': 'newcomer'})
    assert isinstance(ok, ProvenancierIdentity)
    _assert_matches_provenancier_shape(ok)

    missing = plugin.authenticate({'identity': 'nobody'})
    assert isinstance(missing, Rejection)
    assert missing.code == 'not_enrolled'


# --- /betat/enroll + /betat/vouch: the two-phase flow end to end ---------

def test_enroll_endpoint_returns_202_for_pending_peer_vouch():
    _config(auth_methods=['community_peer_vouching'], peer_vouch_threshold=2)

    response = APIClient().post(
        reverse('betat-enroll'),
        {'method': 'community_peer_vouching', 'applicant': {'identity': 'newcomer'}},
        format='json',
    )
    assert response.status_code == 202
    assert response.data['status'] == 'pending_vouches'
    assert response.data['vouches_needed'] == 2


def test_vouch_endpoint_requires_authentication():
    _config(auth_methods=['community_peer_vouching'], peer_vouch_threshold=2)
    plugin = PeerVouchAuth(CommunityConfig.objects.first())
    pending = plugin.enroll({'identity': 'newcomer'})

    response = APIClient().post(reverse('betat-vouch', args=[pending.request_id]))
    assert response.status_code == 401 or response.status_code == 403


def test_vouch_endpoint_promotes_on_threshold():
    config = _config(auth_methods=['community_peer_vouching'], peer_vouch_threshold=2)
    voucher_one = _enrolled_voucher('voucher-one')
    voucher_two = _enrolled_voucher('voucher-two')
    plugin = PeerVouchAuth(config)
    pending = plugin.enroll({'identity': 'newcomer'})

    token_one = Token.objects.create(user=voucher_one.user)
    client_one = APIClient()
    client_one.credentials(HTTP_AUTHORIZATION=f'Token {token_one.key}')
    first = client_one.post(reverse('betat-vouch', args=[pending.request_id]))
    assert first.status_code == 200
    assert first.data['vouch_count'] == 1

    token_two = Token.objects.create(user=voucher_two.user)
    client_two = APIClient()
    client_two.credentials(HTTP_AUTHORIZATION=f'Token {token_two.key}')
    second = client_two.post(reverse('betat-vouch', args=[pending.request_id]))
    assert second.status_code == 201
    assert second.data['identity'] == 'newcomer'
    assert Provenancier.objects.filter(identity='newcomer').exists()


# --- Passphrase-assisted cryptographic_signature (BLUEPRINT §03, 2026-09) -

def test_passphrase_derive_keypair_is_deterministic_per_community():
    pair_one = passphrase.derive_keypair('correct horse battery staple', 'example.org')
    pair_two = passphrase.derive_keypair('correct horse battery staple', 'example.org')
    assert pair_one == pair_two


def test_passphrase_derive_keypair_differs_across_communities():
    _, public_a = passphrase.derive_keypair('correct horse battery staple', 'example.org')
    _, public_b = passphrase.derive_keypair('correct horse battery staple', 'other.example.org')
    assert public_a != public_b


def test_crypto_key_enroll_via_passphrase_helper_matches_manual_path():
    config = _config()
    private_key, public_key = passphrase.derive_keypair('a memorable passphrase', config.id)
    proof = crypto.sign(private_key, public_key)

    plugin = CryptoKeyAuth(config)
    enrolled = plugin.enroll({'identity': 'elder-1', 'public_key': public_key, 'signature': proof})

    assert isinstance(enrolled, ProvenancierIdentity)
    assert enrolled.identity_type == 'cryptographic_key'
    assert enrolled.authentication_method == 'cryptographic_signature'

    # A returning applicant re-deriving from the same passphrase gets the same
    # public key back — this is what provenancier_login_view compares against.
    _, rederived_public_key = passphrase.derive_keypair('a memorable passphrase', config.id)
    assert rederived_public_key == public_key


def test_login_endpoint_reissues_token_for_correct_passphrase():
    config = _config()
    private_key, public_key = passphrase.derive_keypair('a memorable passphrase', config.id)
    proof = crypto.sign(private_key, public_key)
    CryptoKeyAuth(config).enroll({'identity': 'elder-1', 'public_key': public_key, 'signature': proof})

    response = APIClient().post(
        reverse('betat-login'),
        {'identity': 'elder-1', 'passphrase': 'a memorable passphrase'},
        format='json',
    )
    assert response.status_code == 200
    assert response.data['identity'] == 'elder-1'
    assert response.data['token'] == Token.objects.get(user__provenancier__identity='elder-1').key


def test_login_endpoint_rejects_wrong_passphrase():
    config = _config()
    private_key, public_key = passphrase.derive_keypair('a memorable passphrase', config.id)
    proof = crypto.sign(private_key, public_key)
    CryptoKeyAuth(config).enroll({'identity': 'elder-1', 'public_key': public_key, 'signature': proof})

    response = APIClient().post(
        reverse('betat-login'),
        {'identity': 'elder-1', 'passphrase': 'the wrong passphrase'},
        format='json',
    )
    assert response.status_code == 401
    assert response.data['error']['code'] == 'invalid_credentials'


# --- CryptoKeyAuth -------------------------------------------------------

def test_crypto_key_enroll_and_authenticate_success():
    config = _config()
    private_key, public_key = crypto.generate_keypair()
    proof = crypto.sign(private_key, public_key)

    plugin = CryptoKeyAuth(config)
    enrolled = plugin.enroll({'identity': 'did:key:z6Test', 'public_key': public_key, 'signature': proof})

    assert isinstance(enrolled, ProvenancierIdentity)
    _assert_matches_provenancier_shape(enrolled)
    assert enrolled.identity_type == 'cryptographic_key'
    assert enrolled.authentication_method == 'cryptographic_signature'

    message = 'nonce:12345'
    signature = crypto.sign(private_key, message)
    authed = plugin.authenticate({'identity': 'did:key:z6Test', 'message': message, 'signature': signature})
    assert isinstance(authed, ProvenancierIdentity)


def test_crypto_key_enroll_rejects_invalid_proof():
    config = _config()
    _, public_key = crypto.generate_keypair()
    other_private_key, _ = crypto.generate_keypair()
    bogus_proof = crypto.sign(other_private_key, public_key)

    plugin = CryptoKeyAuth(config)
    result = plugin.enroll({'identity': 'did:key:z6Test', 'public_key': public_key, 'signature': bogus_proof})
    assert isinstance(result, Rejection)
    assert result.code == 'invalid_proof'


def test_crypto_key_authenticate_rejects_bad_signature():
    config = _config()
    private_key, public_key = crypto.generate_keypair()
    proof = crypto.sign(private_key, public_key)
    plugin = CryptoKeyAuth(config)
    plugin.enroll({'identity': 'did:key:z6Test', 'public_key': public_key, 'signature': proof})

    other_private_key, _ = crypto.generate_keypair()
    bad_signature = crypto.sign(other_private_key, 'nonce:12345')
    result = plugin.authenticate({'identity': 'did:key:z6Test', 'message': 'nonce:12345', 'signature': bad_signature})
    assert isinstance(result, Rejection)
    assert result.code == 'invalid_signature'


# --- InstitutionalAuth ---------------------------------------------------

def test_institutional_enroll_and_authenticate_success():
    institution_private_key, institution_public_key = crypto.generate_keypair()
    config = _config(trusted_institutions={'uni.example.edu': institution_public_key})

    endorsement = crypto.sign(institution_private_key, 'researcher-1')
    plugin = InstitutionalAuth(config)
    enrolled = plugin.enroll({
        'identity': 'researcher-1',
        'institution_id': 'uni.example.edu',
        'signature': endorsement,
    })

    assert isinstance(enrolled, ProvenancierIdentity)
    _assert_matches_provenancier_shape(enrolled)
    assert enrolled.identity_type == 'institutional_id'
    assert enrolled.authentication_method == 'institutional_endorsement'

    authed = plugin.authenticate({'identity': 'researcher-1'})
    assert isinstance(authed, ProvenancierIdentity)


def test_institutional_enroll_rejects_untrusted_institution():
    config = _config(trusted_institutions={})
    plugin = InstitutionalAuth(config)
    result = plugin.enroll({'identity': 'researcher-1', 'institution_id': 'unknown.edu', 'signature': 'x'})
    assert isinstance(result, Rejection)
    assert result.code == 'untrusted_institution'


def test_institutional_authenticate_rejects_after_institution_untrusted():
    institution_private_key, institution_public_key = crypto.generate_keypair()
    config = _config(trusted_institutions={'uni.example.edu': institution_public_key})
    endorsement = crypto.sign(institution_private_key, 'researcher-1')
    plugin = InstitutionalAuth(config)
    plugin.enroll({'identity': 'researcher-1', 'institution_id': 'uni.example.edu', 'signature': endorsement})

    config.trusted_institutions = {}
    config.save()
    result = InstitutionalAuth(config).authenticate({'identity': 'researcher-1'})
    assert isinstance(result, Rejection)
    assert result.code == 'untrusted_institution'


# --- EnrollView: protocol-list membership is necessary, not sufficient ----

def test_enroll_endpoint_rejects_method_not_enabled_for_community():
    # community_peer_vouching is on the global protocol list but was never
    # enabled by this community — /betat/enroll must still refuse it.
    _config(auth_methods=['cryptographic_signature'])

    response = APIClient().post(
        reverse('betat-enroll'),
        {'method': 'community_peer_vouching', 'applicant': {'identity': 'newcomer'}},
        format='json',
    )
    assert response.status_code == 400
    assert response.data['error']['code'] == 'method_not_enabled'
    assert not Provenancier.objects.filter(identity='newcomer').exists()
