# Generated by Django 2.0.4 on 2018-08-09 13:26

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('histories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryIndexSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_indexed', models.DateTimeField()),
            ],
        )
    ]
