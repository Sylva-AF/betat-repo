"""betat — thin CLI dispatcher over Django management commands.

Recognizes exactly the five commands declared in BLUEPRINT.md §1
(init, runserver, check, announce, export). Each is independently
runnable as `manage.py <cmd>` too — this is a thinner front door, not
a separate implementation.
"""
import os
import sys

COMMANDS = ('init', 'runserver', 'check', 'announce', 'export')


def _print_help():
    print('usage: betat <command> [options]')
    print()
    print('commands:')
    for name in COMMANDS:
        print(f'  {name}')


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betat_community.settings')

    if len(argv) < 2 or argv[1] in ('-h', '--help'):
        _print_help()
        sys.exit(0)

    if argv[1] not in COMMANDS:
        sys.stderr.write(f"betat: unknown command '{argv[1]}'\n\n")
        _print_help()
        sys.exit(1)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(argv)


if __name__ == '__main__':
    main()
