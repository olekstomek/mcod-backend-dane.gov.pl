# Generated by Django 2.0.4 on 2019-02-05 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0010_create_article_category_and_make_relations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='articles.ArticleCategory', verbose_name='Category'),
        ),
    ]
