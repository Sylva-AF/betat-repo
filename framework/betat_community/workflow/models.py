"""Submission — a Provenancier's pending contribution, awaiting verifier
review (COMMUNITY_FRAMEWORK.md "Submission and verification workflow";
BLUEPRINT §4). Content is NEVER uploaded here — only `location` (URI/DOI/
IPFS) and `content_hash`, taken as given at submit time (todos/04-workflow.md
Security notes). `content_type` is deliberately NOT a field: a community
verifies exactly one content type (CommunityConfig.content_type), so it is
read from config at build_record() time rather than accepted from the
submitter — see BLUEPRINT §4 Decision Log.
"""
from django.db import models


class Submission(models.Model):
    STATUS_PENDING = 'pending_review'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending review'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    provenancier = models.ForeignKey(
        'communityauth.Provenancier', on_delete=models.PROTECT, related_name='submissions',
    )
    title = models.CharField(max_length=500, blank=True, default='')
    location = models.CharField(max_length=1000)
    content_hash = models.CharField(max_length=128)
    language = models.CharField(max_length=8, default='en')
    declaration_accepted = models.BooleanField(default=False)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=200, blank=True, default='')
    rejection_reason = models.CharField(max_length=1000, blank=True, default='')
    # Set on accept — links to the ProvenanceRecord this submission produced.
    record_id = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Submission({self.pk}, {self.status})'
