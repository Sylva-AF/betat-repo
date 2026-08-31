"""betat export — see core/export.py for the format and rationale."""
import json

from django.core.management.base import BaseCommand, CommandError

from betat_community.core.export import build_export
from betat_community.core.models import CommunityConfig


class Command(BaseCommand):
    help = "Produce a signed, integrity-verifiable dump of this community's provenance records."

    def add_arguments(self, parser):
        parser.add_argument('--output', help='Write to this file instead of stdout.')

    def handle(self, *args, **options):
        config = CommunityConfig.objects.first()
        if config is None:
            raise CommandError("No CommunityConfig for this install — run 'betat init' first.")

        export_data = build_export(config)
        payload = json.dumps(export_data, indent=2)

        if options['output']:
            with open(options['output'], 'w') as f:
                f.write(payload)
            self.stdout.write(self.style.SUCCESS(
                f"Exported {export_data['record_count']} record(s) to {options['output']}"
            ))
        else:
            self.stdout.write(payload)
