# Generated by Django 2.2.9 on 2020-10-22 11:05

from django.db import migrations


def migrate_is_representative_to_is_agent(apps, schema_editor):
    user_model = apps.get_model('users', 'User')
    users = user_model.objects.filter(is_representative=True)
    if users:
        users.update(is_agent=True)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_auto_20201022_1304'),
    ]

    operations = [
        migrations.RunPython(migrate_is_representative_to_is_agent, reverse_code=migrations.RunPython.noop),
    ]