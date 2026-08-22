"""ProvenanceRecord — the permanent, append-only record layer.

Field names mirror PROVENANCE_SPEC.md v0.1 exactly; `hi_tag` and
`provenancier` are spec-permanent (root CLAUDE.md guardrails) and must
never be renamed. `store.py` is the only sanctioned write path
(append() only) — this model additionally blocks update/delete at the
ORM level as defense-in-depth on top of the SQLite guard triggers
(hand-off migration) and, later, PostgreSQL role revocation (§12).
"""
from django.db import NotSupportedError, models


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise NotSupportedError('ProvenanceRecord is append-only — update() is not supported.')

    def delete(self, *args, **kwargs):
        raise NotSupportedError('ProvenanceRecord is append-only — delete() is not supported.')


class ProvenanceRecord(models.Model):
    record_id = models.CharField(primary_key=True, max_length=64)
    betat_version = models.CharField(max_length=16)
    timestamp = models.CharField(max_length=32)
    hi_tag = models.BooleanField()

    provenancier = models.JSONField()
    content = models.JSONField()
    community = models.JSONField()
    verification = models.JSONField()
    declaration = models.JSONField()

    record_signature = models.CharField(max_length=2048, blank=True, default='')

    correction_of = models.ForeignKey(
        'self', to_field='record_id', null=True, blank=True,
        on_delete=models.PROTECT, related_name='corrections',
    )
    disputes = models.ForeignKey(
        'self', to_field='record_id', null=True, blank=True,
        on_delete=models.PROTECT, related_name='disputed_by',
    )

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ['-timestamp']

    def delete(self, *args, **kwargs):
        raise NotSupportedError('ProvenanceRecord is append-only — delete() is not supported.')

    def to_dict(self):
        """Reconstruct the full PROVENANCE_SPEC record dict — the same
        shape canonical.py hashes and (later) federation serves."""
        record = {
            'betat_version': self.betat_version,
            'record_id': self.record_id,
            'timestamp': self.timestamp,
            'hi_tag': self.hi_tag,
            'provenancier': self.provenancier,
            'content': self.content,
            'community': self.community,
            'verification': self.verification,
            'declaration': self.declaration,
            'record_signature': self.record_signature,
        }
        if self.correction_of_id:
            record['correction_of'] = self.correction_of_id
        if self.disputes_id:
            record['disputes'] = self.disputes_id
        return record

    def __str__(self):
        return self.record_id
