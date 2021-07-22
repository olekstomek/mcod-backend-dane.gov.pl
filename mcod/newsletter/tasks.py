import logging

from celery import shared_task
from constance import config
from django.apps import apps
from django.core.mail import get_connection, send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _, activate


from mcod import settings

logger = logging.getLogger('mcod')


@shared_task
def remove_inactive_subscription(obj_id):
    subscription_model = apps.get_model('newsletter.Subscription')
    objs = subscription_model.objects.filter(id=obj_id, is_active=False)
    if objs.exists():
        for obj in objs:
            logger.debug(f'Inactive subscription is deleted: {obj}')
        objs.delete()
    return {}


@shared_task
def send_newsletter_mail(newsletter_id, subscription_id, html_message):
    submission_model = apps.get_model('newsletter.Submission')
    obj, created = submission_model.objects.update_or_create(
        newsletter_id=newsletter_id, subscription_id=subscription_id)
    try:
        send_mail(
            obj.newsletter.title,
            '',
            config.NEWSLETTER_EMAIL,
            [obj.subscription.email],
            connection=get_connection(settings.EMAIL_BACKEND),
            html_message=html_message,
        )
    except Exception as exc:
        obj.message = exc
        obj.save()
    return {}


@shared_task
def send_subscription_confirm_mail(obj_id):
    subscription_model = apps.get_model('newsletter.Subscription')
    objs = subscription_model.objects.filter(id=obj_id)
    if objs.exists():
        obj = objs.first()
        activate(obj.lang)
        conn = get_connection(settings.EMAIL_BACKEND)
        context = {
            'host': settings.BASE_URL,
            'url': obj.subscribe_confirm_absolute_url,
        }
        subject = _('Activating the newsletter of dane.gov.pl portal')
        message = render_to_string('newsletter/confirm_subscription.txt', context=context)
        html_message = render_to_string('newsletter/confirm_subscription.html', context=context)
        try:
            result = send_mail(
                subject,
                message,
                config.NEWSLETTER_EMAIL,
                [obj.email, ],
                connection=conn,
                html_message=html_message,
            )
            if result:
                logger.debug('Newsletter confirmation email successfully sent!')
        except Exception as exc:
            logger.error('Error during sending of newsletter confirmation email: {}'.format(exc))
        return {}


@shared_task
def send_newsletter():
    newsletter_model = apps.get_model('newsletter.Newsletter')
    for newsletter in newsletter_model.objects.to_send_today():
        newsletter.send()
    return {}
