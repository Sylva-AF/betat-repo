"""POST /betat/submit, GET /betat/queue, POST /betat/review/{id}
(BLUEPRINT §0 API table). Submit requires an authenticated Provenancier;
queue/review require a verifier (IsVerifier — see mixins.py). Accept
builds a PROVENANCE_SPEC record via record_builder.build_record() and
appends it through store.append(); reject closes the submission with no
record — the only two review outcomes (COMMUNITY_FRAMEWORK.md review()).
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from betat_community.common.errors import error_response
from betat_community.core.models import CommunityConfig
from betat_community.store import store

from ..models import Submission
from ..record_builder import build_record
from .mixins import IsVerifier
from .serializers import ReviewRequestSerializer, SubmissionSerializer, SubmitRequestSerializer


class SubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provenancier = getattr(request.user, 'provenancier', None)
        if provenancier is None:
            return error_response(
                'not_a_provenancier',
                'This account is not an enrolled Provenancier.',
                status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('invalid_request', str(serializer.errors), status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        if data['declaration_accepted'] is not True:
            return error_response(
                'declaration_not_accepted',
                'The human-origin declaration must be accepted to submit.',
                status.HTTP_400_BAD_REQUEST,
            )

        submission = Submission.objects.create(
            provenancier=provenancier,
            title=data['title'],
            location=data['location'],
            content_hash=data['content_hash'],
            language=data['language'],
            declaration_accepted=True,
        )
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class QueueView(APIView):
    permission_classes = [IsVerifier]

    def get(self, request):
        pending = Submission.objects.filter(status=Submission.STATUS_PENDING)
        return Response(SubmissionSerializer(pending, many=True).data)


class ReviewView(APIView):
    permission_classes = [IsVerifier]

    def post(self, request, submission_id):
        try:
            submission = Submission.objects.get(pk=submission_id)
        except Submission.DoesNotExist:
            return error_response('not_found', 'No submission with that id.', status.HTTP_404_NOT_FOUND)

        if submission.status != Submission.STATUS_PENDING:
            return error_response(
                'already_reviewed',
                f"This submission was already reviewed (status={submission.status}).",
                status.HTTP_409_CONFLICT,
            )

        serializer = ReviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('invalid_request', str(serializer.errors), status.HTTP_400_BAD_REQUEST)

        decision = serializer.validated_data['decision']
        verifier_identity = request.user.username
        now = timezone.now()

        if decision == 'reject':
            submission.status = Submission.STATUS_REJECTED
            submission.reviewed_at = now
            submission.reviewed_by = verifier_identity
            submission.rejection_reason = serializer.validated_data['reason']
            submission.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'rejection_reason'])
            return Response(SubmissionSerializer(submission).data)

        try:
            config = CommunityConfig.objects.get()
        except CommunityConfig.DoesNotExist:
            return error_response(
                'not_configured',
                'This install has no CommunityConfig yet — run `betat init` first.',
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # MultipleObjectsReturned deliberately uncaught: CommunityConfig.save()
        # enforces single-config-per-install via full_clean(); more than one
        # row means that invariant was bypassed (raw SQL/fixtures), a data
        # integrity bug that should surface loudly, not a routine API error.
        record = store.append(build_record(submission, config, verifier_identity, now=now))

        submission.status = Submission.STATUS_ACCEPTED
        submission.reviewed_at = now
        submission.reviewed_by = verifier_identity
        submission.record_id = record.record_id
        submission.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'record_id'])
        return Response(SubmissionSerializer(submission).data)
