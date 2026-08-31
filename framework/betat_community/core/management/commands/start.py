"""betat start — start the Betat community server.

Equivalent to: python manage.py runserver
Pro-developer note: this is Django's standard runserver command.
For production, replace with gunicorn:
    gunicorn betat_community.wsgi:application --bind 0.0.0.0:8000
"""
from django.core.management.base import BaseCommand
from django.core.management      import call_command


class Command(BaseCommand):
    help = (
        'Start the Betat community server. '
        '(Equivalent to: python manage.py runserver)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'addrport', nargs='?', default='0.0.0.0:8000',
            help='Address:port to bind (default: 0.0.0.0:8000).'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            'Starting Betat community server...\n'
            '  Equivalent command: python manage.py runserver\n'
            '  For production use: '
            'gunicorn betat_community.wsgi:application\n'
        )
        call_command('runserver', options['addrport'])
