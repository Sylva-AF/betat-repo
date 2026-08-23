from django.apps import AppConfig


class CommunityauthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'betat_community.communityauth'

    def ready(self):
        from . import checks  # noqa: F401 — import-only, registers the system check
