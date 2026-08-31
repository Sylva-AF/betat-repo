"""betat announce — see core/announce.py for the payload and rationale."""
from django.core.management.base import BaseCommand, CommandError

from betat_community.core.announce import AnnounceError, send_announcement
from betat_community.core.models import CommunityConfig


class Command(BaseCommand):
    help = 'Ping the registry: "new records available — crawl me now."'

    def handle(self, *args, **options):
        config = CommunityConfig.objects.first()
        if config is None:
            raise CommandError("No CommunityConfig for this install — run 'betat init' first.")

        try:
            payload = send_announcement(config)
        except AnnounceError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Announced '{config.id}' to the registry."))
        self.stdout.write(f'Payload: {payload}')
