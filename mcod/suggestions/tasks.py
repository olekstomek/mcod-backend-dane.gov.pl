import logging

from celery import shared_task
from constance import config
from dateutil import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection, EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, override

from mcod.unleash import is_enabled


User = get_user_model()
logger = logging.getLogger('mcod')


@shared_task
def create_data_suggestion(data_suggestion):
    model = apps.get_model('suggestions', 'Suggestion')
    suggestion = model()
    suggestion.notes = data_suggestion['notes']
    suggestion.save()


@shared_task
def send_data_suggestion(suggestion_id, data_suggestion):
    conn = get_connection(settings.EMAIL_BACKEND)
    emails = [config.CONTACT_MAIL, ]

    notes = data_suggestion["notes"]
    data_suggestion['host'] = settings.BASE_URL

    with override('pl'):
        msg_plain = render_to_string('mails/data-suggestion.txt', data_suggestion)
        msg_html = render_to_string('mails/data-suggestion.html', data_suggestion)

        if settings.DEBUG and config.TESTER_EMAIL:
            emails = [config.TESTER_EMAIL]

        mail = EmailMultiAlternatives(
            _('Resource demand reported'),
            msg_plain,
            from_email=config.NO_REPLY_EMAIL,
            to=emails,
            connection=conn
        )
        mail.mixed_subtype = 'related'
        mail.attach_alternative(msg_html, 'text/html')
        mail.send()

    model = apps.get_model('suggestions', 'Suggestion')
    model.objects.filter(pk=suggestion_id).update(send_date=now())
    return {'suggestion': f'{notes}'}


@shared_task
def create_dataset_suggestion(data_suggestion):
    model = apps.get_model('suggestions', 'DatasetSubmission')
    if 'submitted_by' in data_suggestion:
        user_id = data_suggestion.pop('submitted_by', None)
        user = User.objects.get(pk=user_id)
        data_suggestion['submitted_by'] = user
    submission = model(**data_suggestion)
    submission.save()


@shared_task
def send_dataset_suggestion_mail_task(obj_id):
    model = apps.get_model('suggestions', 'DatasetSubmission')
    obj = model.objects.filter(pk=obj_id).first()
    result = None
    if obj:
        conn = get_connection(settings.EMAIL_BACKEND)
        emails = [config.TESTER_EMAIL] if settings.DEBUG and config.TESTER_EMAIL else [config.CONTACT_MAIL]
        context = {'obj': obj, 'host': settings.BASE_URL}
        tmpl = 'mails/dataset-submission.html' if is_enabled('S39_mail_layout.be') else 'mails/dataset-suggestion.html'
        with override('pl'):
            msg_plain = render_to_string('mails/dataset-suggestion.txt', context)
            msg_html = render_to_string(tmpl, context)

            mail = EmailMultiAlternatives(
                _('Resource demand reported'),
                msg_plain,
                from_email=config.NO_REPLY_EMAIL,
                to=emails,
                connection=conn
            )
            mail.mixed_subtype = 'related'
            mail.attach_alternative(msg_html, 'text/html')
            result = mail.send()
    return {
        'sent': bool(result),
        'obj_id': obj.id if obj else None,
    }


@shared_task
def create_accepted_dataset_suggestion_task(obj_id):
    model = apps.get_model('suggestions.DatasetSubmission')
    obj = model.convert_to_accepted(obj_id)
    return {
        'created': bool(obj),
        'obj_id': obj.id if obj else None,
    }


@shared_task
def deactivate_accepted_dataset_submissions():
    model = apps.get_model('suggestions.AcceptedDatasetSubmission')
    published_at_limit = now() - relativedelta.relativedelta(
        days=settings.DEACTIVATE_ACCEPTED_DATASET_SUBMISSIONS_PUBLISHED_DAYS_AGO)
    objs = model.published.filter(is_active=True, published_at__lt=published_at_limit)
    for obj in objs:
        obj.is_active = False
        obj.save()
    return {'deactivated': objs.count()}


@shared_task
def send_accepted_submission_comment(comment, frontend_url, submission_title,
                                     connection_backend=settings.EMAIL_BACKEND):
    connection = get_connection(connection_backend)
    with override('pl'):
        title = submission_title.replace('\n', ' ').replace('\r', '')
        msg_template = _('On the accepted dataset submission %(title)s [%(url)s] was posted a comment:')
        msg = msg_template % {
            'title': title,
            'url': frontend_url,
        }
        html_msg = msg_template % {
            'title': title,
            'url': f'<a href="{frontend_url}">{frontend_url}</a>',
        }
        context = {
            'host': settings.BASE_URL,
            'url': frontend_url,
            'comment': comment,
            'submission_title': title,
            'message': msg,
            'html_message': html_msg,
        }

        subject = _('A comment was posted on the accepted dataset submission %(title)s') % {
            'title': title}
        msg_plain = render_to_string(
            'mails/accepted-dataset-submission-comment.txt', context=context)
        msg_html = render_to_string(
            'mails/accepted-dataset-submission-comment.html', context=context)
        recipient_list = [config.TESTER_EMAIL] if settings.DEBUG and config.TESTER_EMAIL else [
            config.CONTACT_MAIL]
        try:
            send_mail(
                subject,
                msg_plain,
                config.SUGGESTIONS_EMAIL,
                recipient_list,
                connection=connection,
                html_message=msg_html,
            )
        except Exception as err:
            msg = 'Error during sending of an email comment for accepted submission {}: {}'.format(
                title, err)
            logger.error(msg)
