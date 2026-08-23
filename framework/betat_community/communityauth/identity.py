"""Return types for AuthMethod.enroll()/authenticate().

Per BLUEPRINT.md §3 Decision Log ("the authenticated identity object must
match the record's format"): ProvenancierIdentity carries exactly the
PROVENANCE_SPEC.md `provenancier` block fields (identity, identity_type,
authentication_method, display_name) — no extras — so §04 can copy it
into a built record without reshaping it.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenancierIdentity:
    identity: str
    identity_type: str
    authentication_method: str
    display_name: str = ''


@dataclass(frozen=True)
class Rejection:
    code: str
    message: str
