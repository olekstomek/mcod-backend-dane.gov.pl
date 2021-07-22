import json
import logging
import os
from copy import deepcopy

from celery import shared_task
from constance import config
from django.apps import apps
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from mcod import settings
from mcod.core.api.search.tasks import update_with_related_task
from mcod.resources.file_validation import analyze_resource_file
from mcod.resources.indexed_data import FileEncodingValidationError
from mcod.resources.link_validation import download_file, check_link_status
from mcod.unleash import is_enabled

logger = logging.getLogger('mcod')


@shared_task
def process_resource_from_url_task(resource_id, update_file=True, **kwargs):
    Resource = apps.get_model('resources', 'Resource')
    resource = Resource.raw.get(id=resource_id)
    if resource.is_imported_from_ckan:
        logger.debug(f'External resource imported from {resource.dataset.source} cannot be processed!')
        return {}

    if update_file:
        resource_type, options = download_file(resource.link)
        if is_enabled('S22_forced_api_type.be') and resource_type == 'website' and resource.forced_api_type:
            logger.debug("Resource of type 'website' forced into type 'api'!")
            resource_type = 'api'

        openness_score = resource.get_openness_score(options['format'])
        qs = Resource.raw.filter(id=resource_id)
        if resource_type == 'file':
            if 'filename' in options:
                qs.update(
                    file=resource.save_file(options['content'], options['filename']),
                    format=options['format'],
                    openness_score=openness_score
                )
            process_resource_file_task.s(resource_id, update_link=False, **kwargs).apply_async(
                countdown=2)
        else:  # API or WWW
            qs.update(
                type=resource_type,
                format=options['format'],
                file=None,
                file_info=None,
                file_encoding=None,
                openness_score=openness_score
            )

    resource = Resource.raw.get(id=resource_id)
    result = {
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type
    }

    if resource.type == 'file' and resource.file:
        result['path'] = resource.file.path
        result['url'] = resource.file_url

    update_with_related_task.s('resources', 'Resource', resource.id).apply_async()

    return json.dumps(result)


@shared_task
def process_resource_file_task(resource_id, update_link=True, **kwargs):
    Resource = apps.get_model('resources', 'Resource')

    resource = Resource.raw.get(id=resource_id)
    format, file_info, file_encoding, p, file_mimetype = analyze_resource_file(resource.file.file.name)

    _file_name = os.path.basename(resource.file.name)
    _file_base, _file_ext = os.path.splitext(_file_name)
    if not _file_ext and format:
        _file_name = f'{_file_name}.{format}'
        Resource.raw.filter(pk=resource_id).update(
            file=resource.save_file(resource.file, _file_name)
        )
        resource = Resource.raw.get(id=resource_id)

    Resource.raw.filter(pk=resource_id).update(
        format=format,
        file_mimetype=file_mimetype,
        file_info=file_info,
        file_encoding=file_encoding,
        type='file',
        link=resource.file_url if update_link else resource.link,
        openness_score=resource.get_openness_score(format)
    )

    resource = Resource.raw.get(id=resource_id)

    if resource.format == 'csv' and resource.file_encoding is None:
        raise FileEncodingValidationError(
            [{'code': 'unknown-encoding', 'message': 'Nie udało się wykryć kodowania pliku.'}])

    process_resource_file_data_task.s(resource_id, **kwargs).apply_async(countdown=2)
    if update_link:
        process_resource_from_url_task.s(resource_id, update_file=False, **kwargs).apply_async(
            countdown=2)

    update_with_related_task.s('resources', 'Resource', resource_id).apply_async()

    return json.dumps({
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type,
        'path': resource.file.path,
        'url': resource.file_url
    })


@shared_task
def process_resource_file_data_task(resource_id, **kwargs):
    resource_model = apps.get_model('resources', 'Resource')
    resource = resource_model.raw.get(id=resource_id)
    if not resource.is_data_processable:
        return json.dumps({})
    if not resource.data:
        raise Exception("Nieobsługiwany format danych lub błąd w jego rozpoznaniu.")

    tds = resource.tabular_data_schema or resource.data.get_schema(revalidate=True)
    if resource.from_resource and resource.from_resource.tabular_data_schema:
        old_fields = deepcopy(resource.from_resource.tabular_data_schema.get('fields'))
        for f in old_fields:
            if 'geo' in f:
                del f['geo']
        if tds.get("fields") == old_fields:
            tds = resource.from_resource.tabular_data_schema

    resource_model.objects.filter(pk=resource_id).update(tabular_data_schema=tds)
    resource = resource_model.objects.get(pk=resource_id)
    resource.data.validate()

    success, failed = resource.data.index(force=True)

    return json.dumps({
        'indexed': success,
        'failed': failed,
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type,
        'path': resource.file.path,
        'resource_id': resource_id,
        'url': resource.file_url
    })


@shared_task
def send_resource_comment(resource_id, comment, lang=None):
    model = apps.get_model('resources', 'Resource')
    resource = model.objects.get(pk=resource_id)
    conn = get_connection(settings.EMAIL_BACKEND)
    template_suffix = ''

    context = {
        'host': settings.BASE_URL,
        'resource': resource,
        'comment': comment,
    }

    if settings.DEBUG and config.TESTER_EMAIL:
        template_suffix = '-test'
    with translation.override('pl'):
        msg_plain = render_to_string(f'mails/report-resource-comment{template_suffix}.txt', context=context)
        msg_html = render_to_string(f'mails/report-resource-comment{template_suffix}.html', context=context)
        title = resource.title.replace('\n', ' ').replace('\r', '')
        subject = _('A comment was posted on the resource %(title)s') % {'title': title}
        send_mail(
            subject,
            msg_plain,
            config.SUGGESTIONS_EMAIL,
            [config.TESTER_EMAIL] if settings.DEBUG and config.TESTER_EMAIL else resource.comment_mail_recipients,
            connection=conn,
            html_message=msg_html,
        )

    return {
        'resource': resource_id
    }


@shared_task
def remove_orphaned_files_task():
    resource_model = apps.get_model('resources', 'Resource')
    resources_files = resource_model.get_resources_files()
    count = 0
    for file_path in resource_model.get_all_files():
        if file_path not in resources_files:
            resource_model.remove_orphaned_file(file_path)
            count += 1
    return {'removed_files': count}


@shared_task
def update_resource_has_table_has_map_task(resource_id):
    resource_model = apps.get_model('resources', 'Resource')
    obj = resource_model.raw.filter(id=resource_id).first()
    result = {'resource_id': resource_id}
    if obj:
        data = {}
        has_table = bool(obj.tabular_data)
        has_map = bool(obj.geo_data)
        if has_table != obj.has_table:
            data['has_table'] = has_table
        if has_map != obj.has_map:
            data['has_map'] = has_map
        if data:
            resource_model.raw.filter(id=resource_id).update(**data)
            result.update(data)
    return result


@shared_task
def update_resource_validation_results_task(resource_id):
    resource_model = apps.get_model('resources', 'Resource')
    obj = resource_model.raw.filter(id=resource_id).first()
    result = {'resource_id': resource_id}
    if obj:
        data = {}
        data_task = obj.data_tasks.last()
        file_task = obj.file_tasks.last()
        link_task = obj.link_tasks.last()
        if data_task:
            data['data_tasks_last_status'] = data_task.status
        if file_task:
            data['file_tasks_last_status'] = file_task.status
        if link_task:
            data['link_tasks_last_status'] = link_task.status
        if data:
            resource_model.raw.filter(id=resource_id).update(**data)
            result.update(data)
    return result


@shared_task
def validate_link(resource_id):
    Resource = apps.get_model('resources', 'Resource')
    resource = Resource.raw.get(id=resource_id)
    logger.debug(f'Validating link of resource with id {resource_id}')
    check_link_status(resource.link, resource.type)
    return {
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type
    }
