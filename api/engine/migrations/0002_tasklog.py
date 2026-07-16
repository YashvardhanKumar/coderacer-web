from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("engine", "0001_initial"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="TaskLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "task_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("status", models.CharField(default="PENDING", max_length=50)),
                ("progress", models.IntegerField(default=0)),
                ("logs", models.JSONField(default=list)),
                ("result", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "task_log",
                "ordering": ["-created_at"],
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations),
    ]
