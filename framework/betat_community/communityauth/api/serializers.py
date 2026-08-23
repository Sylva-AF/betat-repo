"""Request shape for POST /betat/enroll. `applicant` is intentionally a
plain DictField — its shape is plugin-specific (see each plugin's
enroll() docstring) and validated by the plugin itself, not here.
"""
from rest_framework import serializers


class EnrollRequestSerializer(serializers.Serializer):
    method = serializers.CharField()
    applicant = serializers.DictField()
