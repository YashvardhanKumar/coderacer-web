import re
from django.db import migrations


def strip_time_markers(apps, schema_editor):
    Testcase = apps.get_model("problem", "Testcase")
    pattern = re.compile(r"_TIME_\d+_[\r\n]*")
    updated = 0
    for tc in Testcase.objects.all():
        original = tc.output or ""
        cleaned = pattern.sub("", original)
        if cleaned != original:
            tc.output = cleaned
            tc.save(update_fields=["output"])
            updated += 1
    if updated:
        print(f"\n  Stripped _TIME_ markers from {updated} test case outputs.")


class Migration(migrations.Migration):
    dependencies = [
        ("problem", "0016_problem_generator_code"),
    ]
    operations = [
        migrations.RunPython(strip_time_markers, atomic=True),
    ]
