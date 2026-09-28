from django.db import migrations

EDITOR_GROUP_NAME = "Editor"


def create_editor_group(apps, schema_editor):
    # Grup Editor disiapkan di sini agar langsung tersedia di setiap database
    # (lokal maupun PWS). Anggotanya tetap ditetapkan lewat Django Admin.
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=EDITOR_GROUP_NAME)


def remove_editor_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=EDITOR_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("main", "0005_project_starred_by"),
    ]

    operations = [
        migrations.RunPython(create_editor_group, remove_editor_group),
    ]
