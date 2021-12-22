import logging
import os
from datetime import datetime

from celery import shared_task
from constance import config
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from mcod.core.utils import save_as_csv, save_as_xml
from mcod.datasets.models import Dataset
from mcod.unleash import is_enabled


logger = logging.getLogger('mcod')


@shared_task
def send_dataset_comment(dataset_id, comment, lang=None):
    model = apps.get_model('datasets', 'Dataset')
    dataset = model.objects.get(pk=dataset_id)

    conn = get_connection(settings.EMAIL_BACKEND)
    template_suffix = ''

    with translation.override('pl'):
        title = dataset.title.replace('\n', ' ').replace('\r', '')
        version = _(' (version %(version)s)') % {'version': dataset.version} if dataset.version else ''
        msg_template = _('On the data set %(title)s%(version)s [%(url)s] was posted a comment:')
        msg = msg_template % {
            'title': title,
            'version': version,
            'url': dataset.frontend_absolute_url,
        }
        html_msg = msg_template % {
            'title': title,
            'version': version,
            'url': f'<a href="{dataset.frontend_absolute_url}">{dataset.frontend_absolute_url}</a>',
        }
        context = {
            'host': settings.BASE_URL,
            'url': dataset.frontend_absolute_url,
            'comment': comment,
            'dataset': dataset,
            'message': msg,
            'html_message': html_msg,
            'test': bool(settings.DEBUG and config.TESTER_EMAIL),
        }

        if settings.DEBUG and config.TESTER_EMAIL:
            template_suffix = '-test'

        subject = _('A comment was posted on the data set %(title)s%(version)s') % {
            'title': title,
            'version': version,
        }
        if is_enabled('S39_mail_layout.be'):
            _plain = 'mails/dataset-comment.txt'
            _html = 'mails/dataset-comment.html'
        else:
            _plain = f'mails/report-dataset-comment{template_suffix}.txt'
            _html = f'mails/report-dataset-comment{template_suffix}.html'
        msg_plain = render_to_string(_plain, context=context)
        msg_html = render_to_string(_html, context=context)

        send_mail(
            subject,
            msg_plain,
            config.SUGGESTIONS_EMAIL,
            [config.TESTER_EMAIL] if settings.DEBUG and config.TESTER_EMAIL else dataset.comment_mail_recipients,
            connection=conn,
            html_message=msg_html,
        )

    return {
        'dataset': dataset_id
    }


def create_catalog_metadata_file(qs_data, schema, extension, save_serialized_data_func):
    today = datetime.today().date()
    previous_day = today - relativedelta(days=1)

    for language in settings.LANGUAGE_CODES:
        lang_catalog_path = f'{settings.METADATA_MEDIA_ROOT}/{language}'
        previous_day_file = f'{lang_catalog_path}/katalog_{previous_day}.{extension}'
        new_file = f'{lang_catalog_path}/katalog_{today}.{extension}'
        symlink_file = f'{lang_catalog_path}/katalog.{extension}'

        if not os.path.exists(lang_catalog_path):
            os.makedirs(lang_catalog_path)

        with translation.override(language):
            data = schema.dump(qs_data)
            with open(new_file, 'w') as file:
                save_serialized_data_func(file, data)

        if os.path.exists(previous_day_file):
            os.remove(previous_day_file)

        if os.path.exists(new_file):
            if os.path.exists(symlink_file) or os.path.islink(symlink_file):
                os.remove(symlink_file)
            os.symlink(new_file, symlink_file)


@shared_task
def create_catalog_metadata_files():
    from mcod.datasets.serializers import DatasetXMLSerializer, DatasetResourcesCSVSerializer
    dataset_model = apps.get_model('datasets', 'Dataset')
    qs_data = dataset_model.objects.with_metadata_fetched_as_list()

    xml_schema = DatasetXMLSerializer(many=True)
    create_catalog_metadata_file(qs_data, xml_schema, 'xml', save_as_xml)

    csv_schema = DatasetResourcesCSVSerializer(many=True)

    def save_serialized_data_func(file, data):
        save_as_csv(file, csv_schema.get_csv_headers(), data)

    create_catalog_metadata_file(qs_data, csv_schema, 'csv', save_serialized_data_func)


@shared_task
def send_dataset_update_reminder():
    logger.debug('Attempting to send datasets update reminders.')
    messages = []
    conn = get_connection(settings.EMAIL_BACKEND)

    freq_updates_with_delays = {
        'yearly': {'default_delay': 7, 'relative_delta': relativedelta(years=1)},
        'everyHalfYear': {'default_delay': 7, 'relative_delta': relativedelta(months=6)},
        'quarterly': {'default_delay': 7, 'relative_delta': relativedelta(months=3)},
        'monthly': {'default_delay': 3, 'relative_delta': relativedelta(months=1)},
        'weekly': {'default_delay': 1, 'relative_delta': relativedelta(days=7)},
    }
    qs = Dataset.objects.datasets_to_notify(list(freq_updates_with_delays.keys()))
    upcoming_updates = []
    for freq, freq_details in freq_updates_with_delays.items():
        notification_delays = set(list(qs.filter(
            update_notification_frequency__isnull=False
        ).values_list('update_notification_frequency', flat=True).distinct()))
        notification_delays.add(freq_details['default_delay'])
        upcoming_updates.extend(
            [(datetime.today().date() + relativedelta(days=delay)) - freq_details['relative_delta']
             for delay in notification_delays])
    ds_to_notify = qs.filter(max_data_date__in=upcoming_updates).select_related('modified_by')
    logger.debug(f'Found {len(ds_to_notify)} datasets.')
    for ds in ds_to_notify:
        context = {'dataset_title': ds.title,
                   'url': ds.frontend_absolute_url,
                   'host': settings.BASE_URL}
        subject = ds.title.replace('\n', '').replace('\r', '')
        msg_plain = render_to_string('mails/dataset-update-reminder.txt', context=context)
        msg_html = render_to_string('mails/dataset-update-reminder.html', context=context)
        messages.append(EmailMultiAlternatives(
            subject, msg_plain, config.NO_REPLY_EMAIL,
            [ds.dataset_update_notification_recipient], alternatives=[(msg_html, 'text/html')]))
    sent_messages = conn.send_messages(messages)
    logger.debug(f'Sent {sent_messages} messages with dataset update reminder.')
