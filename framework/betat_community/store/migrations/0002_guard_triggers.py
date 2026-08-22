from django.db import migrations


def create_triggers(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return  # PostgreSQL enforces append-only via role revocation instead (§12)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TRIGGER store_provenancerecord_no_update
            BEFORE UPDATE ON store_provenancerecord
            BEGIN
              SELECT RAISE(ABORT, 'ProvenanceRecord is append-only: UPDATE is not permitted.');
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER store_provenancerecord_no_delete
            BEFORE DELETE ON store_provenancerecord
            BEGIN
              SELECT RAISE(ABORT, 'ProvenanceRecord is append-only: DELETE is not permitted.');
            END;
        """)


def drop_triggers(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP TRIGGER IF EXISTS store_provenancerecord_no_update;')
        cursor.execute('DROP TRIGGER IF EXISTS store_provenancerecord_no_delete;')


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_triggers, reverse_code=drop_triggers),
    ]
