import logging
import os
import zipfile
from shutil import disk_usage
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
from celery_singleton import Singleton

from mcod.core.utils import save_as_csv, save_as_xml
from mcod.core import storages
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
    dataset_model = apps.get_model('datasets', 'Dataset')
    qs = dataset_model.objects.datasets_to_notify(list(freq_updates_with_delays.keys()))
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


@shared_task(base=Singleton)
def archive_resources_files(dataset_id):
    free_space = disk_usage(settings.MEDIA_ROOT).free
    if free_space < settings.ALLOWED_MINIMUM_SPACE:
        logger.error('There is not enough free space on disk, archive creation is canceled.')
        raise ResourceWarning
    logger.debug(f'Updating dataset resources files archive for dataset {dataset_id}')
    resourcefile_model = apps.get_model('resources', 'ResourceFile')
    resource_model = apps.get_model('resources', 'Resource')
    dataset_model = apps.get_model('datasets', 'Dataset')
    ds = dataset_model.raw.get(pk=dataset_id)

    def create_full_file_path(_fname):
        storage_location = ds.archived_resources_files.storage.location
        full_fname = ds.archived_resources_files.field.generate_filename(ds, _fname)
        return os.path.join(storage_location, full_fname)
    creation_start = datetime.now()
    tmp_filename = f'resources_files_{creation_start.strftime("%Y-%m-%d-%H%M%S%f")}.zip'
    symlink_name = 'resources_files.zip'
    res_storage = storages.get_storage('resources')
    full_symlink_name = ds.archived_resources_files.field.generate_filename(ds, symlink_name)

    full_file_path = create_full_file_path(tmp_filename)
    full_symlink_path = create_full_file_path(symlink_name)
    full_tmp_symlink_path = create_full_file_path('tmp_resources_files.zip')
    abs_path = os.path.dirname(full_file_path)
    os.makedirs(abs_path, exist_ok=True)
    with zipfile.ZipFile(full_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as main_zip:
        res_location = res_storage.location
        if is_enabled('S40_new_file_model.be'):
            filtered_files = resourcefile_model.objects.filter(
                resource__dataset_id=dataset_id,
                resource__status='published', resource__is_removed=False)
            file_details = filtered_files.values_list('file', 'resource_id')
        else:
            filtered_files = resource_model.objects.filter(status='published', dataset_id=dataset_id).with_files()
            all_resource_files = filtered_files.values('file', 'csv_file', 'jsonld_file', 'pk')
            file_details = []
            for res in all_resource_files:
                res_files = [(res['file'], res['pk'])]
                if res['csv_file']:
                    res_files.append((res['csv_file'], res['pk']))
                if res['jsonld_file']:
                    res_files.append((res['jsonld_file'], res['pk']))
                file_details.extend(res_files)
        for details in file_details:
            split_name = details[0].split('/')
            full_path = os.path.join(res_location, details[0])
            main_zip.write(
                full_path,
                os.path.join(f'resource_{details[1]}', split_name[1])
            )
    if not ds.archived_resources_files:
        os.symlink(full_file_path, full_symlink_path)
        dataset_model.objects.filter(pk=dataset_id).update(archived_resources_files=full_symlink_name)
    else:
        old_file_path = os.path.realpath(full_symlink_path)
        os.symlink(full_file_path, full_tmp_symlink_path)
        os.rename(full_tmp_symlink_path, full_symlink_path)
        os.remove(old_file_path)
    logger.debug(f'Updated dataset {dataset_id} archive with {tmp_filename}')
