from celery import shared_task
from django.apps import apps
from django.core.mail import get_connection, EmailMultiAlternatives
from django.conf import settings
from constance import config
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


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
