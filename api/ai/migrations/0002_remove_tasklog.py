from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_initial"),
    ]

    state_operations = [
        migrations.DeleteModel(
            name="TaskLog",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations),
    ]
