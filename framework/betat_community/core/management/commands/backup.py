"""betat backup — back up the community database.

No single Django equivalent — this command selects the right
backup method for the configured database:
  SQLite:     copies betat.sqlite3 to betat.sqlite3.backup.<timestamp>
  PostgreSQL: runs pg_dump and writes to betat_backup_<timestamp>.sql

Pro-developer note: for automated backups, run this command
from a cron job or a systemd timer. For PostgreSQL, you may
prefer pg_basebackup or a managed backup service instead.
"""
import os
import shutil
import subprocess
from datetime   import datetime
from pathlib    import Path

from django.core.management.base import BaseCommand
from django.conf                 import settings


class Command(BaseCommand):
    help = (
        'Back up the community database. '
        'Supports SQLite (file copy) and PostgreSQL (pg_dump).'
    )

    def handle(self, *args, **options):
        db = settings.DATABASES.get('default', {})
        engine    = db.get('ENGINE', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if 'sqlite3' in engine:
            src  = Path(db.get('NAME', 'betat.sqlite3'))
            dest = src.parent / f'{src.stem}_backup_{timestamp}{src.suffix}'
            shutil.copy2(src, dest)
            self.stdout.write(
                self.style.SUCCESS(f'SQLite backup written to: {dest}\n')
                + '  Equivalent: cp betat.sqlite3 '
                  f'betat_backup_{timestamp}.sqlite3\n'
            )

        elif 'postgresql' in engine:
            name = db.get('NAME', 'betat')
            user = db.get('USER', '')
            host = db.get('HOST', 'localhost')
            port = db.get('PORT', '5432')
            dest = Path(f'betat_backup_{timestamp}.sql')
            env  = {**os.environ, 'PGPASSWORD': db.get('PASSWORD', '')}
            cmd  = [
                'pg_dump',
                '-h', host, '-p', str(port), '-U', user, name,
                '-f', str(dest),
            ]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'PostgreSQL backup written to: {dest}\n')
                    + f'  Equivalent: pg_dump -U {user} {name} > {dest}\n'
                )
            else:
                self.stderr.write(
                    self.style.ERROR(f'pg_dump failed:\n{result.stderr}')
                )
        else:
            self.stderr.write(
                'Unknown database engine — backup not supported.\n'
                'Pro-developer: back up manually using your database tools.\n'
            )
