# Generated by Django 2.2.9 on 2021-04-15 14:39

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields
import wagtail.documents.blocks
import wagtail.embeds.blocks
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0022_auto_20210114_1130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationindexpage',
            name='under_list_cb',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock(features=['bold', 'italic', 'h2', 'h3', 'h4', 'titled_link', 'ol', 'ul', 'superscript', 'subscript', 'strikethroughdocument-link', 'lang-pl', 'lang-en'], label='Blok tekstu')), ('image', wagtail.images.blocks.ImageChooserBlock(label='Obrazek'))], blank=True, default='', help_text='Zawartość bloku, który znajdzie się pod listą aplikacji.', verbose_name='Blok pod listą aplikacji'),
        ),
        migrations.AlterField(
            model_name='applicationindexpage',
            name='under_title_cb',
            field=wagtail.core.fields.StreamField([('paragraph', wagtail.core.blocks.RichTextBlock(features=['bold', 'italic', 'h2', 'h3', 'h4', 'titled_link', 'ol', 'ul', 'superscript', 'subscript', 'strikethroughdocument-link', 'lang-pl', 'lang-en'], label='Blok tekstu')), ('image', wagtail.images.blocks.ImageChooserBlock(label='Obrazek'))], blank=True, default='', help_text='Zawartość bloku, który znajdzie się pod tytułem strony głównej (nad wyszukiwarką).', verbose_name='Blok pod tytułem'),
        ),
        migrations.AlterField(
            model_name='applicationpage',
            name='body',
            field=wagtail.core.fields.StreamField([('h1', wagtail.core.blocks.CharBlock(classname='full title', icon='fa-header', label='H1')), ('h2', wagtail.core.blocks.CharBlock(classname='full title', icon='fa-header', label='H2')), ('h3', wagtail.core.blocks.CharBlock(classname='full title', icon='fa-header', label='H3')), ('h4', wagtail.core.blocks.CharBlock(classname='full title', icon='fa-header', label='H4')), ('paragraph', wagtail.core.blocks.RichTextBlock(features=['bold', 'italic', 'h2', 'h3', 'h4', 'titled_link', 'ol', 'ul', 'superscript', 'subscript', 'strikethroughdocument-link', 'lang-pl', 'lang-en'], label='Blok tekstu')), ('image', wagtail.images.blocks.ImageChooserBlock(label='Obrazek')), ('blockquote', wagtail.core.blocks.BlockQuoteBlock(label='Cytat')), ('document', wagtail.documents.blocks.DocumentChooserBlock(label='Dokument')), ('media', wagtail.embeds.blocks.EmbedBlock(label='Media'))], help_text='Właściwa treść strony.', verbose_name='Treść'),
        ),
    ]