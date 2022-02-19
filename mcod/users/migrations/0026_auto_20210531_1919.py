# Generated by Django 2.2.9 on 2021-05-31 17:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mcod.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_auto_20210423_1750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='agent_organization_main',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='agent_organization_main_users', to='organizations.Organization', verbose_name='main organization of agent'),
        ),
        migrations.AlterField(
            model_name='user',
            name='extra_agent_of',
            field=models.ForeignKey(blank=True, limit_choices_to=mcod.users.models.agents_choices, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='extra_agent', to=settings.AUTH_USER_MODEL, verbose_name='extra agent of'),
        ),
    ]