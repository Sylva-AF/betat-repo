"""betat export — a signed*, integrity-verifiable dump of this community's
provenance records (COMMUNITY_FRAMEWORK.md "Discoverability commands"),
submittable to any index by any means when live crawling isn't practical.

*"Signed" here means integrity-verifiable via a recomputable SHA-256 hash
over the whole bundle (export_hash) — not an asymmetric digital signature.
No "community signing key" concept exists anywhere else in this framework
(identities belong to Provenanciers/institutions via §03, not to the
community itself); inventing one solely for export would be new,
undecided infrastructure with nowhere to store or manage it (CommunityConfig
has no private-key field). Each record already carries its own record_id
(recomputable via common/hashing.py — the same check store.verify_integrity()
performs); export_hash extends the same idea to the bundle as a whole, so
a reader can detect if the export file itself was altered in transit.
Real bundle signing, if the project wants it, is future work — not a gap
introduced here without note.
"""
import hashlib
import json

from django.utils import timezone

from betat_community.store.models import ProvenanceRecord

EXPORT_VERSION = '0.1'


def _canonical_records_json(records):
    return json.dumps(records, sort_keys=True, separators=(',', ':')).encode('utf-8')


def build_export(config):
    records = [r.to_dict() for r in ProvenanceRecord.objects.all()]
    export_hash = hashlib.sha256(_canonical_records_json(records)).hexdigest()
    return {
        'betat_export_version': EXPORT_VERSION,
        'community': {
            'id': config.id,
            'name': config.name,
            'domain': config.domain,
            'content_type': config.content_type,
            'hi_standard': config.hi_standard,
            'store_uri': config.store_uri,
        },
        'exported_at': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'record_count': len(records),
        'records': records,
        'export_hash': f'sha256:{export_hash}',
    }


def verify_export(export_data):
    """Recomputes every record's own record_id (common/hashing.py) plus
    the bundle-level export_hash. Both must hold for a valid export."""
    from betat_community.common.hashing import compute_record_id

    for record in export_data['records']:
        if compute_record_id(record) != record['record_id']:
            return False

    recomputed = hashlib.sha256(_canonical_records_json(export_data['records'])).hexdigest()
    return f'sha256:{recomputed}' == export_data['export_hash']
