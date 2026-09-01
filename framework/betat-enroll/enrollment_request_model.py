"""communityauth/enrollment_request_model.py

Add EnrollmentRequest to communityauth/models.py.
This is a NEW model — add it alongside the existing Provenancier model.
Run python manage.py makemigrations communityauth after adding it.

Design: enrollment is now a two-step process for peer_vouch communities:
  1. Applicant submits → EnrollmentRequest created (status=pending_vouches)
  2. Existing Provenanciers vouch → vouch count increments
  3. When vouch count reaches threshold → auto-promote to Provenancier

For bootstrap (0 existing Provenanciers) and admin-approval cases,
the verifier approves directly via the admin panel (status=pending_admin).

No changes to the existing Provenancier model or persist_provenancier().
EnrollmentRequest is a staging table that feeds into persist_provenancier()
when the threshold is met.
"""
from django.db import models


class EnrollmentRequest(models.Model):
    """
    Pending enrollment request — accumulates vouches until threshold met.
    Created by the enrollment API; promoted to Provenancier on approval.
    """

    STATUS_PENDING_VOUCHES = 'pending_vouches'
    STATUS_PENDING_ADMIN   = 'pending_admin'
    STATUS_APPROVED        = 'approved'
    STATUS_REJECTED        = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING_VOUCHES, 'Pending vouches'),
        (STATUS_PENDING_ADMIN,   'Pending admin approval'),
        (STATUS_APPROVED,        'Approved'),
        (STATUS_REJECTED,        'Rejected'),
    ]

    # Core identity fields
    display_name           = models.CharField(max_length=200)
    authentication_method  = models.CharField(max_length=50)

    # Status
    status     = models.CharField(
        max_length=30, choices=STATUS_CHOICES,
        default=STATUS_PENDING_VOUCHES,
        db_index=True,
    )

    # Peer vouch tracking — list of Provenancier PKs who vouched
    vouchers   = models.JSONField(default=list)

    # crypto_key only — public key submitted at enrollment
    # Never stores the passphrase — only the derived public key
    public_key = models.TextField(blank=True, default='')

    # institutional only
    institution_id = models.CharField(max_length=200, blank=True, default='')

    # Admin note (set by verifier when approving/rejecting)
    admin_note = models.TextField(blank=True, default='')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'EnrollmentRequest({self.display_name}, '
            f'{self.status}, vouches={self.vouch_count})'
        )

    @property
    def vouch_count(self):
        return len(self.vouchers or [])

    @property
    def vouches_needed(self):
        """How many more vouches before auto-approval."""
        from betat_community.communityauth.peer_vouch import VOUCH_THRESHOLD
        return max(0, VOUCH_THRESHOLD - self.vouch_count)

    @property
    def is_pending(self):
        return self.status in (
            self.STATUS_PENDING_VOUCHES,
            self.STATUS_PENDING_ADMIN,
        )

    def add_vouch(self, provenancier_pk):
        """
        Add a vouch from an existing Provenancier.
        Returns True if the threshold is now met (caller should promote).
        Idempotent — double-vouching by the same person is ignored.
        """
        from betat_community.communityauth.peer_vouch import VOUCH_THRESHOLD
        if provenancier_pk not in self.vouchers:
            self.vouchers = list(self.vouchers) + [provenancier_pk]
            self.save(update_fields=['vouchers', 'updated_at'])
        return self.vouch_count >= VOUCH_THRESHOLD

    def approve(self, admin_note=''):
        """Mark as approved — called after persist_provenancier() succeeds."""
        self.status     = self.STATUS_APPROVED
        self.admin_note = admin_note
        self.save(update_fields=['status', 'admin_note', 'updated_at'])

    def reject(self, admin_note=''):
        """Mark as rejected by admin."""
        self.status     = self.STATUS_REJECTED
        self.admin_note = admin_note
        self.save(update_fields=['status', 'admin_note', 'updated_at'])
