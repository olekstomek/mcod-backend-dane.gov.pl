import logging
import time

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.apps import apps
from django.utils.translation import gettext_lazy as _

from mcod.harvester.utils import (
    check_content_type,
    check_xml_filename,
    get_remote_xml_hash,
    get_xml_headers,
    retrieve_to_file,
    validate_md5,
    validate_xml,
)


logger = logging.getLogger('mcod')


@shared_task
def import_data_task(obj_id, force=False):
    data_source_model = apps.get_model('harvester.DataSource')
    obj = data_source_model.objects.active().filter(id=obj_id).first()
    if obj and (obj.import_needed() or force):
        obj.import_data()
    return {}


@shared_task
def harvester_supervisor():
    data_source_model = apps.get_model('harvester.DataSource')
    for obj in data_source_model.objects.active():
        if obj.import_needed():
            logger.debug(f'import from {obj}')
            import_data_task.s(obj.id).apply_async()
    return {}


@shared_task(bind=True)
def validate_xml_url_task(self, url):
    progress_recorder = ProgressRecorder(self)

    check_xml_filename(url)
    time.sleep(1)
    progress_recorder.set_progress(1, 7, description=_('Checking of file name'))

    html_headers = get_xml_headers(url)
    time.sleep(1)
    progress_recorder.set_progress(2, 7, description=_('Fetching of HTTP headers'))

    check_content_type(html_headers)
    time.sleep(1)
    progress_recorder.set_progress(3, 7, description=_('Checking of content type'))

    remote_hash_url, remote_hash = get_remote_xml_hash(url)
    time.sleep(1)
    progress_recorder.set_progress(4, 7, description=_('Checking of MD5 file'))

    filename, headers = retrieve_to_file(url)
    time.sleep(1)
    progress_recorder.set_progress(5, 7, description=_('Downloading of xml file'))

    source_hash = validate_md5(filename, remote_hash)
    time.sleep(1)
    progress_recorder.set_progress(6, 7, description=_('Validation of MD5'))

    validate_xml(filename)
    time.sleep(1)
    progress_recorder.set_progress(7, 7, description=_('Validation of xml file'))

    time.sleep(1)
    if source_hash:
        return {'source_hash': source_hash}
    return {}
