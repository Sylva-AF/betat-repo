"""Startup floor enforcement via Django's System Check Framework — runs
automatically before runserver/migrate/manage.py check, so a zero-method
or off-list config is caught before the process serves anything
(todos/03-authentication.md acceptance: "zero-method config rejected at
startup"). Registered in communityauth/apps.py's ready().

The check function queries CommunityConfig defensively: on a pre-migration
database (no table yet) or with no config saved yet, it no-ops rather than
erroring — floor enforcement only has something to check once a config
exists.
"""
from django.core.checks import Error, register
from django.db.utils import OperationalError, ProgrammingError

from .floor import validate_floor


@register()
def check_authentication_floor(app_configs, **kwargs):
    from django.core.exceptions import ValidationError

    from betat_community.core.models import CommunityConfig

    try:
        config = CommunityConfig.objects.first()
    except (OperationalError, ProgrammingError):
        return []
    if config is None:
        return []

    try:
        validate_floor(config.auth_methods)
    except ValidationError as exc:
        return [
            Error(
                '; '.join(exc.messages),
                id='communityauth.E001',
                hint='Configure at least one authentication method from communityauth.floor.PROTOCOL_LIST.',
            )
        ]
    return []
