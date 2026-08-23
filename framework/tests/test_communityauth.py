import dataclasses

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token

from betat_community.communityauth import crypto, floor
from betat_community.communityauth.identity import ProvenancierIdentity, Rejection
from betat_community.communityauth.models import Provenancier
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


# --- PeerVouchAuth -------------------------------------------------------

def test_peer_vouch_enroll_success_below_and_above_threshold():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    _enrolled_voucher('voucher-two')

    plugin = PeerVouchAuth(config)
    result = plugin.enroll({
        'identity': 'newcomer',
        'vouchers': ['voucher-one', 'voucher-two'],
        'display_name': 'Newcomer',
    })

    assert isinstance(result, ProvenancierIdentity)
    _assert_matches_provenancier_shape(result)
    assert result.identity == 'newcomer'
    assert result.identity_type == 'peer_attested'
    assert result.authentication_method == 'community_peer_vouching'
    assert Provenancier.objects.filter(identity='newcomer').exists()
    assert Token.objects.filter(user__provenancier__identity='newcomer').exists()


def test_peer_vouch_enroll_rejects_below_threshold():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')

    plugin = PeerVouchAuth(config)
    result = plugin.enroll({'identity': 'newcomer', 'vouchers': ['voucher-one']})

    assert isinstance(result, Rejection)
    assert result.code == 'insufficient_vouchers'
    assert not Provenancier.objects.filter(identity='newcomer').exists()


def test_peer_vouch_enroll_rejects_duplicate_identity():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    _enrolled_voucher('voucher-two')
    plugin = PeerVouchAuth(config)
    plugin.enroll({'identity': 'newcomer', 'vouchers': ['voucher-one', 'voucher-two']})

    result = plugin.enroll({'identity': 'newcomer', 'vouchers': ['voucher-one', 'voucher-two']})
    assert isinstance(result, Rejection)
    assert result.code == 'identity_taken'


def test_peer_vouch_authenticate_success_and_rejection():
    config = _config(peer_vouch_threshold=2)
    _enrolled_voucher('voucher-one')
    _enrolled_voucher('voucher-two')
    plugin = PeerVouchAuth(config)
    plugin.enroll({'identity': 'newcomer', 'vouchers': ['voucher-one', 'voucher-two']})

    ok = plugin.authenticate({'identity': 'newcomer'})
    assert isinstance(ok, ProvenancierIdentity)
    _assert_matches_provenancier_shape(ok)

    missing = plugin.authenticate({'identity': 'nobody'})
    assert isinstance(missing, Rejection)
    assert missing.code == 'not_enrolled'


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
