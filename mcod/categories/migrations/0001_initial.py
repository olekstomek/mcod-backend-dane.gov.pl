# Generated by Django 2.0.4 on 2018-04-26 09:53

from django.db import migrations, models
import django.utils.timezone
import mcod.core.storages
import model_utils.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('status', model_utils.fields.StatusField(choices=[('published', 'Published'), ('draft', 'Draft')],
                                                          default='published', max_length=100, no_check_for_status=True,
                                                          verbose_name='status')),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status',
                                                                   verbose_name='status changed')),
                ('is_removed', models.BooleanField(default=False)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('title', models.TextField(verbose_name='Title')),
                ('description', models.TextField(null=True, verbose_name='Description')),
                ('color', models.CharField(default='#000000', max_length=20, null=True, verbose_name='Color')),
                ('image', models.ImageField(blank=True, max_length=200, null=True,
                                            storage=mcod.core.storages.CommonStorage(base_url=None,
                                                                                     location=None),
                                            upload_to='', verbose_name='Image URL')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'db_table': 'category',
            },
        ),
    ]
