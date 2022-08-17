import logging
import os
import zipfile
from datetime import datetime
from shutil import disk_usage

from celery_singleton import Singleton
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.utils import translation

from mcod.core import storages
from mcod.core.tasks import extended_shared_task
from mcod.core.utils import clean_filename, save_as_csv, save_as_xml

logger = logging.getLogger('mcod')


@extended_shared_task
def send_dataset_comment(dataset_id, comment):
    model = apps.get_model('datasets', 'Dataset')
    dataset = model.objects.get(pk=dataset_id)
    dataset.send_dataset_comment_mail(comment)
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


@extended_shared_task
def create_catalog_metadata_files():
    from mcod.datasets.serializers import DatasetResourcesCSVSerializer, DatasetXMLSerializer
    dataset_model = apps.get_model('datasets', 'Dataset')
    qs_data = dataset_model.objects.with_metadata_fetched_as_list()

    xml_schema = DatasetXMLSerializer(many=True)
    create_catalog_metadata_file(qs_data, xml_schema, 'xml', save_as_xml)

    csv_schema = DatasetResourcesCSVSerializer(many=True)

    def save_serialized_data_func(file, data):
        save_as_csv(file, csv_schema.get_csv_headers(), data)

    create_catalog_metadata_file(qs_data, csv_schema, 'csv', save_serialized_data_func)


@extended_shared_task
def send_dataset_update_reminder():
    logger.debug('Attempting to send datasets update reminders.')
    dataset_model = apps.get_model('datasets', 'Dataset')
    ds_to_notify = dataset_model.objects.datasets_to_notify()
    logger.debug(f'Found {len(ds_to_notify)} datasets.')
    sent_messages = dataset_model.send_dataset_update_reminder_mails(ds_to_notify)
    logger.debug(f'Sent {sent_messages} messages with dataset update reminder.')


@extended_shared_task(base=Singleton)
def archive_resources_files(dataset_id):
    free_space = disk_usage(settings.MEDIA_ROOT).free
    if free_space < settings.ALLOWED_MINIMUM_SPACE:
        logger.error('There is not enough free space on disk, archive creation is canceled.')
        raise ResourceWarning
    logger.debug(f'Updating dataset resources files archive for dataset {dataset_id}')
    dataset_model = apps.get_model('datasets', 'Dataset')
    ds = dataset_model.raw.get(pk=dataset_id)

    def create_full_file_path(_fname):
        storage_location = ds.archived_resources_files.storage.location
        full_fname = ds.archived_resources_files.field.generate_filename(ds, _fname)
        return os.path.join(storage_location, full_fname)
    creation_start = datetime.now()
    dataset_title = clean_filename(ds.title)
    tmp_filename = f'{dataset_title}_{creation_start.strftime("%Y-%m-%d-%H%M%S%f")}.zip'
    symlink_name = f'{dataset_title}.zip'
    res_storage = storages.get_storage('resources')
    full_symlink_name = ds.archived_resources_files.field.generate_filename(ds, symlink_name)
    full_file_path = create_full_file_path(tmp_filename)
    full_symlink_path = create_full_file_path(symlink_name)
    full_tmp_symlink_path = create_full_file_path('tmp_resources_files.zip')
    abs_path = os.path.dirname(full_file_path)
    os.makedirs(abs_path, exist_ok=True)
    files_details = ds.resources_files_list
    log_msg = f'Updated dataset {dataset_id} archive with {tmp_filename}'
    skipped_files = 0
    with zipfile.ZipFile(full_file_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as main_zip:
        res_location = res_storage.location
        for file_details in files_details:
            split_name = file_details[0].split('/')
            full_path = os.path.join(res_location, file_details[0])
            try:
                res_title = clean_filename(file_details[2])
                main_zip.write(
                    full_path,
                    os.path.join(f'{res_title}_{file_details[1]}', split_name[1])
                )
            except FileNotFoundError:
                skipped_files += 1
                logger.debug('Couldn\'t find file {} for resource with id {}, skipping.'.format(
                    full_path, file_details[1]))
    no_archived_files = skipped_files == len(files_details)

    if no_archived_files:
        os.remove(full_file_path)
        log_msg = f'No files archived for dataset with id {dataset_id}, archive not updated.'
    elif not ds.archived_resources_files and not no_archived_files:
        os.symlink(full_file_path, full_symlink_path)
        dataset_model.objects.filter(pk=dataset_id).update(archived_resources_files=full_symlink_name)
    elif ds.archived_resources_files and not no_archived_files:
        old_file_path = os.path.realpath(full_symlink_path)
        os.symlink(full_file_path, full_tmp_symlink_path)
        os.rename(full_tmp_symlink_path, full_symlink_path)
        os.remove(old_file_path)
    if ds.archived_resources_files and no_archived_files:
        old_file_path = os.path.realpath(full_symlink_path)
        dataset_model.objects.filter(pk=dataset_id).update(archived_resources_files=None)
        os.remove(full_symlink_path)
        os.remove(old_file_path)
        log_msg = f'Removed archive {old_file_path} from dataset {dataset_id}'
    logger.debug(log_msg)
