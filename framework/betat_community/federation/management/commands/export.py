from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Produce a signed, integrity-verifiable dump of all records.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'betat export is scaffolded but not yet implemented — see TODO 09 '
            '(Discoverability: announce & export).'
        ))
