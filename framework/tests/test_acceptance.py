"""The seven-step acceptance test (COMMUNITY_FRAMEWORK.md "Minimal Working
Community"; BLUEPRINT §10) — the seed-release gate. Runs headless, entirely
through the public API + management commands, zero frontend work: init →
enroll → submit → review/accept → valid record in the store → served,
integrity-verified, and unmodifiable → an independent (credential-less)
reader discovers and reads it.

Dual-DB (BLUEPRINT §10 acceptance criteria: "all seven ALSO pass against
PostgreSQL"): this suite's logic is engine-agnostic — it never assumes
SQLite except in the one explicitly-gated assertion below, which checks
against `connection.vendor` and skips with a clear reason otherwise. What
this suite CANNOT do yet is actually run against PostgreSQL: settings.py's
DATABASES hardcodes `ENGINE: sqlite3` (`BETAT_DB` only overrides the
SQLite filename), and PostgreSQL's append-only enforcement (role
INSERT/SELECT-only, UPDATE/DELETE revoked) doesn't exist yet — both are
§12's deliverable ("PostgreSQL migration path"), not this section's. Once
§12 lands, this same file should pass unmodified when run with
BETAT_DB pointed at a real Postgres instance.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import Error as DjangoDBError
from django.db import connection
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from betat_community.communityauth import crypto
from betat_community.core.models import BASELINE_HI_STANDARD, CommunityConfig
from betat_community.store import store
from betat_community.store.models import ProvenanceRecord
from betat_community.workflow.models import Submission

pytestmark = pytest.mark.django_db

DECLARED_ADDITION = 'human-authored, AI-untouched'


def test_seven_step_acceptance():
    # --- Step 1: betat init + declare a standard at/above the baseline ---
    # init's operator-declaration and email steps are deliberately
    # unbypassable for a real install (anti-automation is the point) — this
    # simulates exactly what the acceptance scenario describes: an operator
    # answering them, not a script skipping them.
    with patch('builtins.input', side_effect=['yes', 'acceptance-operator@example.org']):
        call_command(
            'init',
            id='acceptance.example.org',
            name='Acceptance Test Community',
            domain='field reporting',
            content_type='text',
            store_uri='https://acceptance.example.org/store',
            hi_standard_addition=DECLARED_ADDITION,
            auth_methods=['cryptographic_signature'],
        )
    config = CommunityConfig.objects.get(id='acceptance.example.org')
    assert config.hi_standard == f'{BASELINE_HI_STANDARD}; {DECLARED_ADDITION}'
    assert config.hi_standard.startswith(BASELINE_HI_STANDARD)

    # --- Step 2: a Provenancier enrolls via a protocol-list method ---
    # CryptoKeyAuth, not PeerVouchAuth: a fresh install has no existing
    # members yet to vouch, so peer-vouch can't bootstrap the very first
    # Provenancier — this is the realistic "first enrollment ever" path.
    private_key, public_key = crypto.generate_keypair()
    proof = crypto.sign(private_key, public_key)
    enroll_response = APIClient().post(
        reverse('betat-enroll'),
        {
            'method': 'cryptographic_signature',
            'applicant': {
                'identity': 'did:key:z6MkAcceptance',
                'public_key': public_key,
                'signature': proof,
                'display_name': 'Acceptance Tester',
            },
        },
        format='json',
    )
    assert enroll_response.status_code == 201
    provenancier_token = enroll_response.data['token']
    assert enroll_response.data['authentication_method'] == 'cryptographic_signature'

    provenancier_client = APIClient()
    provenancier_client.credentials(HTTP_AUTHORIZATION=f'Token {provenancier_token}')

    # --- Step 3: submit a text contribution (content elsewhere, hash given) ---
    submit_response = provenancier_client.post(
        reverse('betat-submit'),
        {
            'title': 'Field note — acceptance run',
            'location': 'https://archive.example/acceptance-note',
            'content_hash': 'sha256:acceptancehash',
            'language': 'en',
            'declaration_accepted': True,
        },
        format='json',
    )
    assert submit_response.status_code == 201
    submission_id = submit_response.data['id']
    assert Submission.objects.get(pk=submission_id).status == Submission.STATUS_PENDING

    # --- Step 4: a verifier reviews and accepts ---
    verifier = get_user_model().objects.create_user(username='acceptance-verifier', is_staff=True)
    verifier_token = Token.objects.create(user=verifier)
    verifier_client = APIClient()
    verifier_client.credentials(HTTP_AUTHORIZATION=f'Token {verifier_token.key}')

    review_response = verifier_client.post(
        reverse('betat-review', args=[submission_id]), {'decision': 'accept'}, format='json',
    )
    assert review_response.status_code == 200
    record_id = review_response.data['record_id']
    assert record_id

    # --- Step 5: a valid PROVENANCE_SPEC v0.1 record, hi_tag:true, declared standard ---
    record = ProvenanceRecord.objects.get(record_id=record_id)
    assert record.betat_version == '0.1'
    assert record.hi_tag is True
    assert record.provenancier['identity'] == 'did:key:z6MkAcceptance'
    assert record.provenancier['authentication_method'] == 'cryptographic_signature'
    assert record.content['type'] == 'text'
    assert record.content['location'] == 'https://archive.example/acceptance-note'
    assert record.verification['verified_by'] == 'acceptance-verifier'
    assert record.declaration['custom_addition'] == config.hi_standard

    # --- Step 6: served, integrity-verified, and unmodifiable ---
    records_response = APIClient().get(reverse('betat-records'))
    assert record_id in [r['record_id'] for r in records_response.data['results']]

    detail_response = APIClient().get(reverse('betat-record-detail', args=[record_id]))
    assert detail_response.status_code == 200
    assert detail_response.data['record_id'] == record_id

    assert store.verify_integrity(record_id) is True

    # No update/delete path exists — assert the absence, don't just avoid calling it.
    with pytest.raises(Exception):
        ProvenanceRecord.objects.filter(record_id=record_id).update(hi_tag=False)
    with pytest.raises(Exception):
        record.delete()
    # No API path either. PublicReadOnly denies non-safe methods at the
    # permission layer — which runs before DRF checks whether a handler
    # even exists for the verb — so an unauthenticated write is refused
    # with 401 (DRF's permission_denied() escalates to NotAuthenticated
    # when no credentials were given and TokenAuthentication is
    # configured), not 405. Either way, the write never reaches a handler.
    assert APIClient().delete(reverse('betat-record-detail', args=[record_id])).status_code == 401
    assert APIClient().put(reverse('betat-record-detail', args=[record_id]), {}, format='json').status_code == 401
    assert APIClient().patch(reverse('betat-record-detail', args=[record_id]), {}, format='json').status_code == 401

    # Engine-specific enforcement seam (BLUEPRINT §5/§12): SQLite's guard
    # triggers are checkable now; PostgreSQL's role revocation is §12, not
    # yet built, so there is nothing to assert against on that engine yet.
    # This does NOT skip the rest of the test — steps 5/6's ORM+API checks
    # above and step 7 below are engine-agnostic and must still run.
    if connection.vendor == 'sqlite':
        with pytest.raises(DjangoDBError):
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE store_provenancerecord SET hi_tag = 0 WHERE record_id = %s', [record_id],
                )

    # --- Step 7: an independent reader, given only the host address, finds it ---
    # A fresh, credential-less client — no shortcuts, no internal APIs, just
    # the same four public endpoints any registry/crawler would call.
    crawler = APIClient()
    info = crawler.get(reverse('betat-info'))
    assert info.status_code == 200
    assert info.data['id'] == 'acceptance.example.org'

    changes = crawler.get(reverse('betat-changes'))
    assert record_id in [r['record_id'] for r in changes.data['results']]

    record_via_crawler = crawler.get(reverse('betat-record-detail', args=[record_id]))
    assert record_via_crawler.status_code == 200
    assert record_via_crawler.data['hi_tag'] is True
    assert record_via_crawler.data['declaration']['custom_addition'] == config.hi_standard
