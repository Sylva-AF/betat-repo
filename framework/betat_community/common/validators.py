"""Shared field validators used by more than one app (BLUEPRINT §0
conventions: used by 2+ apps → common/). Framework-agnostic: each raises
django.core.exceptions.ValidationError, which both Django forms and DRF
serializer field ``validators=[...]`` understand (DRF's run_validators
catches Django's ValidationError and re-wraps it).
"""
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

# Schemes a content location may use: http/https/ftp for web-hosted items,
# ipfs/ipns for content-addressed storage, doi for DOIs. Deliberately an
# allowlist, not a blocklist — it forces an absolute address (a bare
# 'example.org' has no scheme and would otherwise render as a link relative
# to the community's own host) AND keeps unsafe schemes such as
# javascript:/data: out of the href the bundled UI builds from this value.
CONTENT_LOCATION_SCHEMES = ('http', 'https', 'ftp', 'ipfs', 'ipns', 'doi')


def validate_content_location(value):
    """A submitted content location must be an absolute URI that links
    straight at the item — never a bare or relative string. See BLUEPRINT
    §04's 2026-09-20 Decision Log entry: a scheme-less value (e.g.
    'bantu.org') renders as a link relative to the community's own host, so
    the record card's "Source" link resolved to
    /community/records/bantu.org instead of the external source."""
    parsed = urlparse(value)
    if parsed.scheme.lower() not in CONTENT_LOCATION_SCHEMES:
        raise ValidationError(
            'Content location must be an absolute URL that links straight to the item — '
            'include a scheme such as https://, ipfs://, or doi:. A bare domain or path '
            'is not accepted.',
            code='content_location_not_absolute',
        )
    if not (parsed.netloc or parsed.path):
        raise ValidationError(
            'Content location is missing an address after its scheme.',
            code='content_location_empty',
        )
