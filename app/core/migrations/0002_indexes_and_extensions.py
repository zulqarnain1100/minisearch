from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector

def create_indexes(apps, schema_editor):
    # Using schema_editor to create the same GIN functional/trigram indexes as in Meta
    # Some backends need explicit SQL for functional GIN + opclass.
    with schema_editor.connection.cursor() as cursor:
        # Full-text functional GIN on (title, body)
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'doc_fts_gin'
            ) THEN
                CREATE INDEX doc_fts_gin ON core_document
                USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,'')));
            END IF;
        END$$;
        """)
        # Trigram GIN on title
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'doc_title_trgm_gin'
            ) THEN
                CREATE INDEX doc_title_trgm_gin ON core_document
                USING GIN (title gin_trgm_ops);
            END IF;
        END$$;
        """)
        # Trigram GIN on body
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'doc_body_trgm_gin'
            ) THEN
                CREATE INDEX doc_body_trgm_gin ON core_document
                USING GIN (body gin_trgm_ops);
            END IF;
        END$$;
        """)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]
    operations = [
        # Safety: ensure extensions in DB (harmless if already created by your /db/01-enable-extensions.sql)
        TrigramExtension(),
        UnaccentExtension(),
        migrations.RunPython(create_indexes, migrations.RunPython.noop),
    ]

