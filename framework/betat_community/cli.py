"""betat — thin CLI dispatcher over Django management commands.

Recognizes the commands declared in BLUEPRINT.md §1/§0 Conventions
(init, runserver, check, announce, export, start, backup). Each is
independently runnable as `manage.py <cmd>` too — this is a thinner
front door, not a separate implementation.

`check` and `shell` are deliberately NOT wrapped with betat-specific
commands of the same name — see BLUEPRINT §1 Decision Log (2026-08-30):
a management command sharing a built-in Django command's name overrides
that built-in everywhere, and a wrapper that then calls back into the
same name via call_command() recurses into itself infinitely. Use the
standard Django forms directly: `python manage.py check --deploy`,
`python manage.py shell`.
"""
import os
import sys

COMMANDS = ('init', 'runserver', 'check', 'announce', 'export', 'start', 'backup')


def _preflight_issues():
    """Return list of (issue, remedy) tuples. Empty = environment is sound.

    Runs here, before Django loads, because django.setup() itself crashes
    with a raw traceback (not a friendly message) if Python lacks sqlite3
    support — django.contrib.auth's AbstractBaseUser needs a DB backend at
    class-definition time, which happens during app loading, before any
    management command's handle() ever gets a chance to run.
    """
    issues = []
    major, minor = sys.version_info.major, sys.version_info.minor
    if (major, minor) < (3, 11):
        issues.append((
            f'Python {major}.{minor} is below the required 3.11 floor.',
            'Install Python 3.11+ via your OS package manager:\n'
            '        Rocky/RHEL: dnf install python3.11\n'
            '        Ubuntu/Debian: apt install python3.11\n'
            '        macOS: brew install python@3.11',
        ))
    try:
        import sqlite3  # noqa: F401
    except ImportError:
        issues.append((
            'SQLite is not available in this Python installation.',
            'Your Python was likely compiled from source without SQLite.\n'
            '        Install Python via your OS package manager (see above)\n'
            '        or use the official Docker image: docker run betat/community',
        ))
    return issues


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

    issues = _preflight_issues()
    if issues:
        sys.stderr.write('\nEnvironment check failed:\n')
        for i, (issue, remedy) in enumerate(issues, 1):
            sys.stderr.write(f'\n  [{i}] {issue}\n      {remedy}\n')
        sys.stderr.write('\nResolve the above, then try again.\n')
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
