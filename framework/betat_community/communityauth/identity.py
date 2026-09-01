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


@dataclass(frozen=True)
class Pending:
    """A third `AuthMethod.enroll()` outcome (BLUEPRINT §03 Decision Log,
    2026-09): the applicant is neither rejected nor fully enrolled yet —
    used by `PeerVouchAuth` while a request awaits enough vouches.
    `EnrollView` maps this to HTTP 202, distinct from Rejection's 400."""
    code: str
    message: str
    request_id: int
    vouch_count: int = 0
    vouches_needed: int = 0
