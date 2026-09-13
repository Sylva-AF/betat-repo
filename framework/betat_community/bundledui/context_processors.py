"""Supplies `config` to every template. base.html's nav brand and footer
(`{{ config.name }}`, `{{ config.id }}`) have referenced this variable
since §07 shipped, but nothing ever put it in context — it silently fell
through to their `|default:` fallback text on every page (BLUEPRINT §07
Decision Log, 2026-09-12). `BetatConfiguredMiddleware` guarantees a
CommunityConfig row exists on any page this reaches, but the handful of
pages exempt from that gate (the installer, the setup wizard, /admin/)
don't extend base.html and never reference `config` either — so `.first()`
returning None there is unused, not a bug to guard against.
"""
from betat_community.core.models import CommunityConfig


def config(request):
    return {'config': CommunityConfig.objects.first()}
