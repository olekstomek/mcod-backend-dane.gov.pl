# Generated by Django 2.2.9 on 2022-04-25 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0056_auto_20220421_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplement',
            name='language',
            field=models.CharField(choices=[('pl', 'Polish'), ('en', 'English')], default='pl', max_length=2, verbose_name='language'),
        ),
    ]