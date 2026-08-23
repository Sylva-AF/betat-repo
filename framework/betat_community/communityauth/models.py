"""Provenancier — a persisted, enrolled identity.

Stores exactly the PROVENANCE_SPEC.md `provenancier` fields plus
plugin-specific verification_material (public key, vouchers, institution
id — never a secret; proof material is verified once at enroll time,
not stored). Linked 1:1 to a Django User purely to hang a DRF
authtoken.Token off it (todos/03-authentication.md: "Token issuance...
follows DRF token patterns; no custom crypto").
"""
from django.conf import settings
from django.db import models

# PROVENANCE_SPEC.md "Identity Types" — fixed enum, spec-permanent.
IDENTITY_TYPE_CHOICES = [
    ('cryptographic_key', 'Cryptographic key'),
    ('institutional_id', 'Institutional ID'),
    ('government_id', 'Government ID'),
    ('peer_attested', 'Peer attested'),
    ('pseudonymous_peer_attested', 'Pseudonymous, peer attested'),
]

# PROVENANCE_SPEC.md "Authentication Methods" — fixed enum, spec-permanent.
# Only the first three have shipped plugins (BLUEPRINT §3); the rest are
# roadmap stubs, never chosen by a working plugin.
AUTHENTICATION_METHOD_CHOICES = [
    ('cryptographic_signature', 'Cryptographic signature'),
    ('institutional_endorsement', 'Institutional endorsement'),
    ('government_id_verification', 'Government ID verification'),
    ('community_peer_vouching', 'Community peer vouching'),
    ('behavioral_attestation', 'Behavioral attestation'),
]


class Provenancier(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provenancier',
    )
    identity = models.CharField(max_length=500, unique=True)
    identity_type = models.CharField(max_length=32, choices=IDENTITY_TYPE_CHOICES)
    authentication_method = models.CharField(max_length=32, choices=AUTHENTICATION_METHOD_CHOICES)
    display_name = models.CharField(max_length=200, blank=True, default='')
    verification_material = models.JSONField(default=dict, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.identity
