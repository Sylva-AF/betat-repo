"""Shared provenance-record serializer base (BLUEPRINT §0 convention:
used by two or more apps → common/). Deliberately declares no fields —
to_representation() delegates entirely to store.models.ProvenanceRecord's
own to_dict(), the same method verify_integrity() hashes and test_store.py
already exercises. Re-declaring PROVENANCE_SPEC's fields a second time
here would risk the two drifting; delegating makes drift impossible and
keeps 'no internal fields leak' (todos/06-federation.md Security notes)
enforced by a single whitelist instead of two.
"""
from rest_framework import serializers


class ProvenanceRecordSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance.to_dict()
