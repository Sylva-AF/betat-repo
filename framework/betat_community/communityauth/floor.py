"""The authentication floor: at least one configured method, always from
the protocol list, never an off-list substitute (COMMUNITY_FRAMEWORK.md
"Authentication (pluggable, floored)"). Government-ID and behavioral
attestation are roadmap stubs (todos/03-authentication.md) — never in
PROTOCOL_LIST until they ship a plugin.
"""
from django.core.exceptions import ValidationError

from .plugins import CryptoKeyAuth, InstitutionalAuth, PeerVouchAuth

PROTOCOL_LIST = {
    PeerVouchAuth.method_name: PeerVouchAuth,
    CryptoKeyAuth.method_name: CryptoKeyAuth,
    InstitutionalAuth.method_name: InstitutionalAuth,
}


def validate_floor(auth_methods):
    """auth_methods: CommunityConfig.auth_methods (list of method-name
    strings). Raises ValidationError if empty or if any entry is not in
    PROTOCOL_LIST — the floor rule enforced at config load (BLUEPRINT §3)."""
    if not auth_methods:
        raise ValidationError(
            'At least one authentication method is required.',
            code='empty_auth_methods',
        )
    off_list = [m for m in auth_methods if m not in PROTOCOL_LIST]
    if off_list:
        raise ValidationError(
            f"Authentication method(s) not on the protocol list: {', '.join(off_list)}. "
            f"Allowed: {', '.join(PROTOCOL_LIST)}.",
            code='off_list_auth_method',
        )
