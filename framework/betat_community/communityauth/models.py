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


class PeerVouchRequest(models.Model):
    """A `community_peer_vouching` enrollment awaiting enough vouches
    (BLUEPRINT §03 Decision Log, 2026-09). Created with zero vouches by
    `PeerVouchAuth.enroll()`; `PeerVouchAuth.add_vouch()` accumulates
    `vouchers` (a list of voucher identity strings — the same shape later
    persisted into `Provenancier.verification_material['vouchers']`) and
    promotes to a full `Provenancier` once the community's
    `CommunityConfig.peer_vouch_threshold` is met. Not itself a Provenancier
    — never counts as an enrolled identity until promoted."""

    identity = models.CharField(max_length=500, unique=True)
    display_name = models.CharField(max_length=200, blank=True, default='')
    vouchers = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'PeerVouchRequest({self.identity}, {len(self.vouchers)} vouches)'
