# Generated by Django 2.0 on 2018-04-20 09:36

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('title', models.CharField(max_length=250, verbose_name='Title')),
                ('url', models.URLField(blank=True, null=True, verbose_name='URL')),
            ],
            options={'verbose_name': 'License', 'verbose_name_plural': 'Licenses'}
        ),

    ]