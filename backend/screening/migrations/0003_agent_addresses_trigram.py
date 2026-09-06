from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("screening", "0002_alter_entityidentifier_id_type"),
    ]

    operations = [
        # similarity() comes from pg_trgm; the fuzzy matching steps need it,
        # and the test database is built from migrations, so it belongs here.
        TrigramExtension(),
        migrations.AddField(
            model_name="agent",
            name="addresses",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
