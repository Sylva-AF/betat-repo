"""betat init — guided setup for this install's CommunityConfig.

Domain control is *declared* here, never verified — verification happens
at registry registration (a DNS TXT challenge; see COMMUNITY_FRAMEWORK.md
"Community Identity" and the Roadmap). Nothing secret is collected here.

Added in amendment (Option C — conflict-free):
  • environment preflight (Python 3.11 floor, SQLite availability)
  • DNS resolution check on the community id
  • operator declaration of good-faith intent
  • personal contact email collection
  • .env accountability record (read by Betat staff only, never operational)
CommunityConfig remains the sole operational source of truth — unchanged.
"""
import secrets
import socket
import sys
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from betat_community.core.models import (
    BASELINE_HI_STANDARD,
    CONTENT_TYPE_CHOICES,
    CommunityConfig,
)

CONTENT_TYPE_KEYS = [key for key, _ in CONTENT_TYPE_CHOICES]

ENV_PATH = Path('.env')
MANAGE_PY_PATH = Path('manage.py')

MANAGE_PY_CONTENT = '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betat_community.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
'''

OPERATOR_DECLARATION = (
    "I declare that I am the rightful operator of the domain I have "
    "provided, that I am setting up this Betat community instance in "
    "good faith for the purpose of preserving genuine human-originated "
    "content, and that I accept responsibility for how this community "
    "is administered. I understand that Betat staff may contact me at "
    "the email I provide and may investigate communities that appear "
    "to misuse the framework."
)


# ── Preflight helpers ──────────────────────────────────────────────────────

def _preflight_issues():
    """Return list of (issue, remedy) tuples. Empty = environment is sound."""
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


def _check_domain_dns(domain):
    """Return (ok, error_str). Checks DNS resolution only — not ownership."""
    try:
        socket.getaddrinfo(domain, None)
        return True, ''
    except socket.gaierror:
        return False, f'{domain} does not resolve to any address.'


# ── Accountability helpers ─────────────────────────────────────────────────

def _validate_email(email):
    """Structural check only — @ present, dot in domain part."""
    at = email.find('@')
    if at < 1:
        return False
    domain_part = email[at + 1:]
    return '.' in domain_part and len(domain_part) > 2


def _write_env_record(community_id, operator_email):
    """Append accountability fields to .env. Never overwrites existing keys."""
    existing = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                existing[k.strip()] = v.strip()
    # Only write accountability fields — never operational config.
    # BETAT_SECRET_KEY: generated fresh if not already set (never overwrites
    # a value the operator or a prior run already put here) — matching the
    # BETAT_-prefixed env var settings.py actually reads (BLUEPRINT §12
    # Decision Log, 2026-08-30).
    existing.setdefault('BETAT_SECRET_KEY', secrets.token_urlsafe(50))
    existing.setdefault('BETAT_OPERATOR_EMAIL', operator_email)
    existing.setdefault('BETAT_DECLARATION_ACCEPTED', 'true')
    existing.setdefault('BETAT_DECLARED_COMMUNITY_ID', community_id)
    content = '\n'.join(f'{k}={v}' for k, v in existing.items()) + '\n'
    ENV_PATH.write_text(content)


def _write_manage_py():
    """Write the standard django-admin-startproject manage.py, if not already present.

    A pip install of betat-community ships only the importable
    betat_community package (see DISTRIBUTION.md, "What ships") — no
    manage.py, since that's a per-project entry point, not library code.
    betat init is the one guaranteed point where the operator has a real
    working directory, so it writes one here. From this point forward it's
    standard Django: `python manage.py migrate/createsuperuser/runserver`,
    no custom wrapper, nothing betat-specific to learn.
    """
    if MANAGE_PY_PATH.exists():
        return False
    MANAGE_PY_PATH.write_text(MANAGE_PY_CONTENT)
    MANAGE_PY_PATH.chmod(0o755)
    return True


class Command(BaseCommand):
    help = "Declare this install's community identity and write its CommunityConfig."

    def add_arguments(self, parser):
        parser.add_argument("--id", help="Community id (lowercase FQDN you control).")
        parser.add_argument("--name", help="Community display name.")
        parser.add_argument("--domain", help="Knowledge domain this community governs.")
        parser.add_argument(
            "--content-type",
            choices=CONTENT_TYPE_KEYS,
            help="PROVENANCE_SPEC content type this community verifies.",
        )
        parser.add_argument(
            "--hi-standard-addition",
            default="",
            help="Optional strengthening addition to the baseline HI standard.",
        )
        parser.add_argument(
            "--store-uri", help="Where this community's records are published."
        )
        parser.add_argument(
            "--auth-method",
            action="append",
            dest="auth_methods",
            help="An authentication method to enable (repeatable).",
        )

    def handle(self, *args, **options):
        # ── 1. Environment preflight ───────────────────────────────────────
        issues = _preflight_issues()
        if issues:
            self.stderr.write('\nEnvironment check failed:\n')
            for i, (issue, remedy) in enumerate(issues, 1):
                self.stderr.write(f'\n  [{i}] {issue}')
                self.stderr.write(f'      {remedy}')
            self.stderr.write(
                '\n\nResolve the above, then run betat init again.\n'
            )
            raise CommandError('Environment check failed — see above.')

        # ── 2. Existing config guard (unchanged from §02) ──────────────────
        if CommunityConfig.objects.exists():
            raise CommandError(
                "A CommunityConfig already exists for this install — only one "
                "is supported per install (seed assumption, BLUEPRINT §2)."
            )

        interactive = not all(
            options[key] for key in ("id", "name", "domain", "content_type", "store_uri")
        )

        # ── 3. Community id — with DNS check ──────────────────────────────
        if options["id"]:
            community_id = options["id"]
            # Non-interactive path: check DNS, warn but don't block
            ok, err = _check_domain_dns(community_id)
            if not ok:
                self.stderr.write(
                    f'\nWarning: {err}\n'
                    'Continuing because --id was supplied non-interactively.\n'
                    'Ensure the domain is real and controlled by you.\n'
                )
        else:
            # Interactive path: loop until a resolving domain is given
            while True:
                community_id = self._prompt(
                    'Community id (lowercase FQDN you control)'
                )
                self.stdout.write('  Checking domain...', ending=' ')
                self.stdout.flush()
                ok, err = _check_domain_dns(community_id)
                if ok:
                    self.stdout.write('✓  Resolves.')
                    self.stdout.write(
                        '  Note: this confirms the domain exists in DNS.\n'
                        '  Your community\'s legitimacy depends on you\n'
                        '  controlling this domain — use one you own.\n'
                    )
                    break
                self.stderr.write(f'\n  ✗  {err}')
                self.stderr.write(
                    '\n  A Betat community id must be a real domain that'
                    '\n  exists in DNS — globally unique and permanently'
                    '\n  verifiable. Register one if you do not have one,'
                    '\n  or wait up to 48 h for DNS propagation.\n'
                )

        # ── 4. Remaining prompts (unchanged from §02) ─────────────────────
        name = options["name"] or self._prompt("Community name")
        domain = options["domain"] or self._prompt("Knowledge domain governed")
        content_type = options["content_type"] or self._prompt_choice(
            "Content type", CONTENT_TYPE_KEYS
        )

        addition = options["hi_standard_addition"]
        if not addition and interactive:
            addition = self._prompt(
                "Additional HI standard qualifiers, strengthen-only "
                "(blank to keep the baseline)",
                required=False,
            )
        hi_standard = BASELINE_HI_STANDARD
        if addition:
            hi_standard = f"{BASELINE_HI_STANDARD}; {addition}"

        store_uri = options["store_uri"] or self._prompt(
            "Store URI (where this community's records are published)"
        )

        auth_methods = options["auth_methods"]
        if not auth_methods:
            raw = self._prompt("Authentication method(s), comma-separated")
            auth_methods = [m.strip() for m in raw.split(",") if m.strip()]

        # ── 5. Save CommunityConfig (unchanged from §02) ──────────────────
        config = CommunityConfig(
            id=community_id,
            name=name,
            domain=domain,
            content_type=content_type,
            hi_standard=hi_standard,
            auth_methods=auth_methods,
            store_uri=store_uri,
        )
        try:
            config.save()
        except ValidationError as exc:
            raise CommandError(self._format_validation_error(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(f"CommunityConfig written for '{config.id}'.")
        )

        # ── 6. Operator declaration (new — Option C) ───────────────────────
        self.stdout.write('\n' + '-' * 55)
        self.stdout.write('  Operator declaration')
        self.stdout.write('-' * 55)
        self.stdout.write(f'\n  "{OPERATOR_DECLARATION}"\n')

        while True:
            acceptance = input(
                '  Do you accept this declaration? [yes/no]: '
            ).strip().lower()
            if acceptance == 'yes':
                self.stdout.write('  ✓  Declaration accepted.')
                break
            if acceptance == 'no':
                self.stdout.write(
                    '\n  You must accept the declaration to complete setup.'
                    '\n  CommunityConfig has been written. To remove it and'
                    '\n  start over: python manage.py shell -c'
                    '\n  "from betat_community.core.models import'
                    ' CommunityConfig; CommunityConfig.objects.all().delete()"'
                    '\n  Then run betat init again, or Ctrl+C to exit.\n'
                )
            else:
                self.stdout.write("  Please type 'yes' to accept or 'no' to decline.")

        # ── 7. Operator email (new — Option C) ────────────────────────────
        self.stdout.write(
            '\n  Provide a personal contact email. Betat staff may use'
            '\n  this to reach you if your community is investigated.'
        )
        while True:
            operator_email = input('\n  Contact email: ').strip()
            if _validate_email(operator_email):
                self.stdout.write(f'  ✓  {operator_email}')
                break
            self.stdout.write(
                '  That does not look like a valid email address. Try again.'
            )

        # ── 8. Write .env accountability record (new — Option C) ──────────
        _write_env_record(community_id, operator_email)
        self.stdout.write('  ✓  Accountability record written to .env')

        # ── 8b. Write manage.py (new — §12) ────────────────────────────────
        if _write_manage_py():
            self.stdout.write('  ✓  manage.py written — standard Django from here')

        # ── 9. Readiness summary (unchanged from §02) ─────────────────────
        self._print_readiness(config)

    # ── Unchanged helpers from §02 ─────────────────────────────────────────

    def _prompt(self, label, required=True):
        while True:
            value = input(f"{label}: ").strip()
            if value or not required:
                return value

    def _prompt_choice(self, label, choices):
        while True:
            value = input(f"{label} ({'/'.join(choices)}): ").strip()
            if value in choices:
                return value
            self.stderr.write(f"Choose one of: {', '.join(choices)}")

    def _format_validation_error(self, exc):
        if hasattr(exc, "message_dict"):
            parts = [
                f"{field}: {'; '.join(msgs)}"
                for field, msgs in exc.message_dict.items()
            ]
            return " | ".join(parts)
        return "; ".join(exc.messages)

    def _print_readiness(self, config):
        self.stdout.write("")
        self.stdout.write("Readiness:")
        self.stdout.write(f"  [x] identity declared — id={config.id}")
        self.stdout.write(f"  [x] HI standard — {config.hi_standard}")
        self.stdout.write(f"  [x] auth method(s) — {', '.join(config.auth_methods)}")
        self.stdout.write("")
        self.stdout.write(
            "Domain control is declared, not verified. Verification happens "
            "at registry registration (a DNS TXT challenge — see Roadmap)."
        )
