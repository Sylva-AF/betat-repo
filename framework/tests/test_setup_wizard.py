from unittest.mock import patch

from django.urls import reverse

import pytest

from betat_community.core.models import CommunityConfig

pytestmark = pytest.mark.django_db

# example.org and localhost both resolve without a real network call
# (example.org is a live, RFC 2606 documentation domain; localhost is
# resolved locally) — same assumption test_core.py's own _init() helper
# already relies on for "example.org". The negative case is mocked, not
# a real domain: RFC 2606's .invalid TLD is supposed to guarantee
# non-resolution but real-world resolvers (corporate DNS, NXDOMAIN-
# hijacking ISPs, sandboxed containers) frequently don't honor it —
# confirmed the hard way when this test flaked green in exactly such an
# environment. Real non-resolution can't be relied on; real resolution
# of well-known domains can.
RESOLVING_DOMAIN = 'example.org'
NON_RESOLVING_DOMAIN = 'this-should-not-exist.invalid'


def _config(**overrides):
    kwargs = dict(
        id='configured.example.org',
        name='Already Configured',
        domain='marine biology',
        content_type='text',
        store_uri='https://configured.example.org/records',
        auth_methods=['cryptographic_signature'],
    )
    kwargs.update(overrides)
    return CommunityConfig.objects.create(**kwargs)


def _walk_to_step7(client, community_id=RESOLVING_DOMAIN):
    """POSTs steps 1-6 with valid data, landing the session on step 7."""
    client.post(reverse('bundledui-setup-1'))
    client.post(reverse('bundledui-setup-2'), {
        'community_id': community_id, 'name': 'Test Community', 'domain': 'testing',
    })
    client.post(reverse('bundledui-setup-3'), {
        'content_type': 'text', 'hi_standard_addition': '',
    })
    client.post(reverse('bundledui-setup-4'), {
        'store_uri': f'https://{community_id}/records',
    })
    client.post(reverse('bundledui-setup-5'), {
        'auth_methods': ['cryptographic_signature'],
    })
    client.post(reverse('bundledui-setup-6'), {
        'declaration_accepted': 'yes', 'operator_email': 'operator@example.org',
    })


# --- gating: unreachable once configured ----------------------------------

def test_setup_step1_redirects_to_landing_when_already_configured(client):
    _config()
    response = client.get(reverse('bundledui-setup-1'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-landing')


def test_setup_step7_redirects_to_landing_when_already_configured(client):
    _config()
    response = client.get(reverse('bundledui-setup-7'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-landing')


def test_installer_begin_setup_link_resolves_to_step1(client):
    response = client.get(reverse('bundledui-install'))
    assert response.status_code == 200
    assert reverse('bundledui-setup-1').encode() in response.content


# --- step 1 ----------------------------------------------------------------

def test_setup_step1_get_renders_welcome(client):
    response = client.get(reverse('bundledui-setup-1'))
    assert response.status_code == 200
    assert b'Begin' in response.content


# --- step 2: DNS validation --------------------------------------------------

def test_setup_step2_rejects_non_resolving_domain(client):
    with patch(
        'betat_community.bundledui.wizard_views._check_domain_dns',
        return_value=(False, f'{NON_RESOLVING_DOMAIN} does not resolve to any address.'),
    ):
        response = client.post(reverse('bundledui-setup-2'), {
            'community_id': NON_RESOLVING_DOMAIN, 'name': 'Test', 'domain': 'testing',
        })
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-2')
    assert 'betat_setup' not in client.session  # rejected before being saved

    # Error shows once, then is consumed (popped from session)
    first = client.get(reverse('bundledui-setup-2'))
    assert NON_RESOLVING_DOMAIN.encode() in first.content

    second = client.get(reverse('bundledui-setup-2'))
    assert NON_RESOLVING_DOMAIN.encode() not in second.content


def test_setup_step2_accepts_resolving_domain_and_advances(client):
    response = client.post(reverse('bundledui-setup-2'), {
        'community_id': RESOLVING_DOMAIN, 'name': 'Test Community', 'domain': 'testing',
    })
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-3')
    assert client.session['betat_setup']['community_id'] == RESOLVING_DOMAIN


# --- session persistence across steps (back navigation) ---------------------

def test_setup_session_prefills_fields_on_return_to_step2(client):
    client.post(reverse('bundledui-setup-2'), {
        'community_id': RESOLVING_DOMAIN, 'name': 'Test Community', 'domain': 'testing',
    })
    client.post(reverse('bundledui-setup-3'), {'content_type': 'text', 'hi_standard_addition': ''})

    response = client.get(reverse('bundledui-setup-2'))
    assert response.status_code == 200
    assert RESOLVING_DOMAIN.encode() in response.content
    assert b'Test Community' in response.content


# --- step 7: review + commit -------------------------------------------------

def test_setup_step7_redirects_to_step1_if_incomplete(client):
    response = client.get(reverse('bundledui-setup-7'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-1')


def test_setup_step7_shows_review_table(client):
    _walk_to_step7(client)
    response = client.get(reverse('bundledui-setup-7'))
    assert response.status_code == 200
    assert RESOLVING_DOMAIN.encode() in response.content
    assert b'cryptographic_signature' in response.content
    assert b'operator@example.org' in response.content


def test_setup_full_walkthrough_creates_exactly_one_config(client):
    _walk_to_step7(client)
    response = client.post(reverse('bundledui-setup-7'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-done')
    assert CommunityConfig.objects.count() == 1

    config = CommunityConfig.objects.get()
    assert config.id == RESOLVING_DOMAIN
    assert config.auth_methods == ['cryptographic_signature']
    assert 'betat_setup' not in client.session


def test_setup_done_shows_config_and_requires_one(client):
    response = client.get(reverse('bundledui-setup-done'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-1')

    _walk_to_step7(client)
    client.post(reverse('bundledui-setup-7'))
    response = client.get(reverse('bundledui-setup-done'))
    assert response.status_code == 200
    assert RESOLVING_DOMAIN.encode() in response.content


def test_setup_step7_post_rejects_race_with_second_config(client):
    # Simulates a second tab/process completing setup between this
    # session's GET and POST of step 7 — must redirect cleanly, not
    # raise an IntegrityError on a duplicate CommunityConfig.
    _walk_to_step7(client)
    _config(id='raced-in.example.org')

    response = client.post(reverse('bundledui-setup-7'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-landing')
    assert CommunityConfig.objects.count() == 1


def test_setup_step7_post_shows_clean_error_on_model_validation_failure(client):
    # "localhost" resolves (passes step 2's DNS check) but fails
    # CommunityConfig's FQDN validator (no dot) — this is exactly the
    # case _format_validation_error exists to handle cleanly instead of
    # leaking a raw ValidationError repr.
    _walk_to_step7(client, community_id='localhost')

    response = client.post(reverse('bundledui-setup-7'))
    assert response.status_code == 302
    assert response.url == reverse('bundledui-setup-7')
    assert CommunityConfig.objects.count() == 0

    follow = client.get(reverse('bundledui-setup-7'))
    assert follow.status_code == 200
    assert b'lowercase' in follow.content or b'FQDN' in follow.content


# --- .env accountability record ---------------------------------------------

def test_setup_writes_env_accountability_record(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _walk_to_step7(client)
    client.post(reverse('bundledui-setup-7'))

    env_content = (tmp_path / '.env').read_text()
    assert 'BETAT_OPERATOR_EMAIL=operator@example.org' in env_content
    assert 'BETAT_DECLARATION_ACCEPTED=true' in env_content
    assert f'BETAT_DECLARED_COMMUNITY_ID={RESOLVING_DOMAIN}' in env_content
