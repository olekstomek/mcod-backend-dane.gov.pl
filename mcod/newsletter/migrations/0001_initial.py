# Generated by Django 2.2 on 2019-09-19 11:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mcod.core.storages
import mcod.newsletter.utils
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('lang', models.CharField(choices=[('pl', 'polish'), ('en', 'english')], max_length=7, verbose_name='language version')),
                ('planned_sending_date', models.DateField(verbose_name='planned sending date')),
                ('sending_date', models.DateTimeField(blank=True, null=True, verbose_name='sending date')),
                ('status', models.CharField(choices=[('awaits', 'Awaits'), ('sent', 'Sent'), ('error', 'Error')], default='awaits', max_length=7, verbose_name='status')),
                ('file', models.FileField(max_length=2000, storage=mcod.core.storages.NewsletterStorage(base_url=None, location=None), upload_to='%Y%m%d', verbose_name='file')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='newsletters_created', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='newsletters_modified', to=settings.AUTH_USER_MODEL, verbose_name='modified by')),
            ],
            options={
                'verbose_name': 'newsletter',
                'verbose_name_plural': 'newsletters',
                'db_table': 'newsletter',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('lang', models.CharField(choices=[('pl', 'polish'), ('en', 'english')], max_length=7, verbose_name='language')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email')),
                ('activation_code', models.CharField(default=mcod.newsletter.utils.make_activation_code, max_length=40, verbose_name='activation code')),
                ('is_active', models.BooleanField(db_index=True, default=False, verbose_name='is active?')),
                ('is_personal_data_processing_accepted', models.BooleanField(default=False, verbose_name='is personal data processing accepted?')),
                ('is_personal_data_use_confirmed', models.BooleanField(default=False, verbose_name='is personal data gathering accepted?')),
                ('subscribe_date', models.DateTimeField(blank=True, null=True, verbose_name='subscribe date')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='newsletter_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'subscription',
                'verbose_name_plural': 'subscriptions',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('message', models.TextField(blank=True, verbose_name='message')),
                ('newsletter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='newsletter_submissions', to='newsletter.Newsletter', verbose_name='newsletter')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_submissions', to='newsletter.Subscription', verbose_name='subscription')),
            ],
            options={
                'verbose_name': 'submission',
                'verbose_name_plural': 'submissions',
                'unique_together': {('newsletter', 'subscription')},
            },
        ),
    ]