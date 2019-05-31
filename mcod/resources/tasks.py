import json

from celery import shared_task
from constance import config
from django.apps import apps
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string

from mcod import settings
from mcod.lib.utils import analyze_resource_file, download_file


@shared_task
def process_resource_from_url_task(resource_id, update_file=True, **kwargs):
    Resource = apps.get_model('resources', 'Resource')
    resource = Resource.raw.get(id=resource_id)
    openness_score = resource._openness_score if resource.format else 0
    if update_file:
        resource_type, options = download_file(resource.link)
        qs = Resource.raw.filter(id=resource_id)
        if resource_type == 'file':
            if 'filename' in options:
                qs.update(
                    file=resource.save_file(options['content'], options['filename']),
                    format=options['format'],
                    openness_score=openness_score
                )
        else:  # API or WWW
            qs.update(
                type=resource_type,
                format=options['format'],
                file=None,
                file_info=None,
                file_encoding=None,
                openness_score=openness_score
            )

        if resource.type == 'file':
            process_resource_file_task.s(resource_id, update_link=False, **kwargs).apply_async(countdown=2)

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

    return json.dumps(result)


@shared_task
def process_resource_file_task(resource_id, update_link=True, **kwargs):
    Resource = apps.get_model('resources', 'Resource')

    resource = Resource.raw.get(id=resource_id)
    format, file_info, file_encoding, p = analyze_resource_file(resource.file.file.name)

    Resource.objects.filter(pk=resource_id).update(
        format=format,
        file_info=file_info,
        file_encoding=file_encoding,
        type='file',
        link=resource.file_url if update_link else resource.link,
        openness_score=resource._openness_score if resource.format else 0
    )

    resource = Resource.raw.get(id=resource_id)

    if resource.format in ('csv', 'tsv', 'xls', 'xlsx', 'ods') and resource.file:
        process_resource_file_data_task.s(resource_id, **kwargs).apply_async(countdown=2)
    if update_link:
        process_resource_from_url_task.s(resource_id, update_file=False, **kwargs).apply_async(countdown=2)
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
    Resource = apps.get_model('resources', 'Resource')
    resource = Resource.raw.get(id=resource_id)
    if not resource.tabular_data:
        raise Exception("Nie obsługiwany format danych lub błąd w jego rozpoznaniu.")
    resource.tabular_data.validate()
    resource.tabular_data_schema = resource.tabular_data.schema

    Resource.objects.filter(pk=resource_id).update(tabular_data_schema=resource.tabular_data.schema)

    success, failed = resource.index_tabular_data(force=True)

    return json.dumps({
        'indexed': success,
        'failed': failed,
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type,
        'path': resource.file.path,
        'url': resource.file_url
    })


@shared_task
def send_resource_comment(resource_id, comment):
    model = apps.get_model('resources', 'Resource')
    resource = model.objects.get(pk=resource_id)

    conn = get_connection(settings.EMAIL_BACKEND)
    template_suffix = ''

    emails = [config.CONTACT_MAIL, ]
    if resource.modified_by:
        emails.append(resource.modified_by.email)
    else:
        emails.extend(user.email for user in resource.dataset.organization.users.all())

    template_params = {
        'host': settings.BASE_URL,
        'title': resource.title,
        'dataset_title': resource.dataset.title,
        'url': f"{settings.BASE_URL}/dataset/{resource.dataset.id}/resource/{resource.id}",
        'comment': comment,
    }

    if settings.DEBUG and config.TESTER_EMAIL:
        template_params['emails'] = ', '.join(emails)
        emails = [config.TESTER_EMAIL]
        template_suffix = '-test'

    msg_plain = render_to_string(f'mails/report-resource-comment{template_suffix}.txt', template_params)
    msg_html = render_to_string(f'mails/report-resource-comment{template_suffix}.html', template_params)

    send_mail(
        f'Zgłoszono uwagę do zasobu {resource.title}',
        msg_plain,
        config.SUGGESTIONS_EMAIL,
        emails,
        connection=conn,
        html_message=msg_html,
    )

    return {
        'resource': resource_id
    }
