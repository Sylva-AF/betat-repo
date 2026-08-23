"""AuthMethod — the pluggable authentication protocol.

COMMUNITY_FRAMEWORK.md "Authentication (pluggable, floored)":

    class AuthMethod(Protocol):
        def enroll(self, applicant) -> ProvenancierIdentity | Rejection: ...
        def authenticate(self, credentials) -> ProvenancierIdentity | Rejection: ...

enroll() is responsible for the full enrollment: validating the
applicant, persisting a Provenancier row (+ linked User/DRF Token so the
issued token works with ongoing TokenAuthentication), and returning the
identity. authenticate() re-derives/re-verifies an identity from raw
credentials without creating anything new — used directly by tests and
available to later sections that need method-specific re-verification
beyond "the token is valid".
"""
import abc


class AuthMethod(abc.ABC):
    method_name = None  # must be a communityauth.floor.PROTOCOL_LIST key

    def __init__(self, config):
        self.config = config

    @abc.abstractmethod
    def enroll(self, applicant):
        """applicant: dict of plugin-specific fields. Returns
        ProvenancierIdentity on success, Rejection otherwise."""

    @abc.abstractmethod
    def authenticate(self, credentials):
        """credentials: dict of plugin-specific fields. Returns
        ProvenancierIdentity on success, Rejection otherwise."""
