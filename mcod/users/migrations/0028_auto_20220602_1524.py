# Generated by Django 2.2.9 on 2022-06-02 13:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_auto_20211013_0944'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='followed_articles',
        ),
        migrations.DeleteModel(
            name='UserFollowingArticle',
        ),
    ]