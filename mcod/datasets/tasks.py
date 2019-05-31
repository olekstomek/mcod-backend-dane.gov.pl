from celery import shared_task
from constance import config
from django.apps import apps
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string

from mcod import settings


@shared_task
def send_dataset_comment(dataset_id, comment):
    model = apps.get_model('datasets', 'Dataset')
    dataset = model.objects.get(pk=dataset_id)

    conn = get_connection(settings.EMAIL_BACKEND)
    template_suffix = ''

    emails = [config.CONTACT_MAIL, ]
    if dataset.modified_by:
        emails.append(dataset.modified_by.email)
    else:
        emails.extend(user.email for user in dataset.organization.users.all())

    template_params = {
        'host': settings.BASE_URL,
        'title': dataset.title,
        'version': dataset.version,
        'url': dataset.url,
        'comment': comment,
    }

    if settings.DEBUG and config.TESTER_EMAIL:
        template_params['emails'] = ', '.join(emails)
        emails = [config.TESTER_EMAIL]
        template_suffix = '-test'

    msg_plain = render_to_string(f'mails/report-dataset-comment{template_suffix}.txt', template_params)
    msg_html = render_to_string(f'mails/report-dataset-comment{template_suffix}.html', template_params)

    send_mail(
        f'Zgłoszono uwagę do zbioru {dataset.title} ({dataset.version})',
        msg_plain,
        config.SUGGESTIONS_EMAIL,
        emails,
        connection=conn,
        html_message=msg_html,
    )

    return {
        'dataset': dataset_id
    }
