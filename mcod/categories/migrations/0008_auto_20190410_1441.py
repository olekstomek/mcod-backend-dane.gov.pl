# Generated by Django 2.2 on 2019-04-10 12:41

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import modeltrans.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0007_auto_20190205_0935'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='published_at',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', when={'published'}),
        ),
        migrations.AddField(
            model_name='category',
            name='removed_at',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='is_removed', when={True}),
        ),
        migrations.AddField(
            model_name='category',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AddField(
            model_name='category',
            name='views_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='category',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('title', 'description', 'slug'), required_languages=(), virtual_fields=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(blank=True, default=uuid.uuid4, max_length=600),
        ),
    ]