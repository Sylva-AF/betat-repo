"""Request/response shapes for /betat/submit, /betat/queue, /betat/review/{id}.
content_type is deliberately absent from SubmitRequestSerializer — see
workflow/models.py.
"""
from rest_framework import serializers

from ..models import Submission


class SubmitRequestSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField()
    content_hash = serializers.CharField()
    language = serializers.CharField(required=False, default='en')
    declaration_accepted = serializers.BooleanField()


class ReviewRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['accept', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class SubmissionSerializer(serializers.ModelSerializer):
    provenancier_identity = serializers.CharField(source='provenancier.identity', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'provenancier_identity', 'title', 'location', 'content_hash', 'language',
            'declaration_accepted', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by',
            'rejection_reason', 'record_id',
        ]
        read_only_fields = fields
