import base64
import os
from email.mime.image import MIMEImage
from io import BytesIO

from PIL import Image
from celery import shared_task
from constance import config
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils import translation

from mcod import settings
from mcod.core.api.search import signals as search_signals


@shared_task
def create_application_proposal_task(data):
    app_proposal_model = apps.get_model('applications.ApplicationProposal')
    obj = app_proposal_model.create(data)
    return {
        'created': True if obj else False,
        'obj_id': obj.id if obj else None,
    }


@shared_task
def create_application_task(app_proposal_id):
    model = apps.get_model('applications.ApplicationProposal')
    obj = model.convert_to_application(app_proposal_id)
    return {
        'created': True if obj else False,
        'obj_id': obj.id if obj else None,
    }


@shared_task
def send_application_proposal(app_proposal):
    from mcod.datasets.models import Dataset
    conn = get_connection(settings.EMAIL_BACKEND)
    emails = [config.CONTACT_MAIL, ]

    title = app_proposal["title"]
    applicant_email = app_proposal.get('applicant_email', '')
    img_data = app_proposal.get('image')
    illustrative_graphics = app_proposal.get('illustrative_graphics')
    img_name = slugify(title) if img_data or illustrative_graphics else None

    if img_data:
        data = img_data.split(';base64,')[-1].encode('utf-8')
        image = MIMEImage(base64.b64decode(data))
        filename = f"{img_name}.{image.get_content_subtype()}"
        image.add_header('content-disposition', 'attachment', filename=filename)
        image.add_header('Content-ID', '<app-logo>')

    if illustrative_graphics:
        data = illustrative_graphics.split(';base64,')[-1].encode('utf-8')
        illustrative_graphics_img = MIMEImage(base64.b64decode(data))
        filename = f'{img_name}_illustrative-graphics.{illustrative_graphics_img.get_content_subtype()}'
        illustrative_graphics_img.add_header('content-disposition', 'attachment', filename=filename)
        illustrative_graphics_img.add_header('Content-ID', '<illustrative-graphics>')

    datasets = Dataset.objects.filter(id__in=app_proposal.get('datasets', []))
    app_proposal['datasets'] = '\n'.join(ds.frontend_absolute_url for ds in datasets)
    app_proposal['dataset_links'] = '<br />'.join(
        f"<a href=\"{ds.frontend_absolute_url}\">{ds.title}</a>\n" for ds in datasets)

    external_datasets = app_proposal.get('external_datasets', [])
    app_proposal['external_datasets'] = '\n'.join(
        f"{eds.get('title', '(nienazwany)')}: {eds.get('url', '(nie podano url)')}\n" for eds in external_datasets
    )
    app_proposal['external_dataset_links'] = '<br />'.join(
        (f"{eds.get('title')}: <a href=\"{eds.get('url')}\">{eds.get('url')}</a>\n"
         if 'url' in eds else eds.get('title'))
        for eds in external_datasets
    )
    app_proposal['keywords'] = ', '.join(app_proposal.get('keywords', tuple()))
    app_proposal['host'] = settings.BASE_URL

    if settings.DEBUG and config.TESTER_EMAIL:
        emails = [config.TESTER_EMAIL]

    with translation.override('pl'):
        msg_plain = render_to_string('mails/propose-application.txt', app_proposal)
        msg_html = render_to_string('mails/propose-application.html', app_proposal)
        mail = EmailMultiAlternatives(
            'Zgłoszono propozycję aplikacji {}'.format(title.replace('\n', ' ').replace('\r', '')),
            msg_plain,
            from_email=config.NO_REPLY_EMAIL,
            to=emails,
            connection=conn
        )
        mail.mixed_subtype = 'related'
        mail.attach_alternative(msg_html, 'text/html')
        if img_data:
            mail.attach(image)
        if illustrative_graphics:
            mail.attach(illustrative_graphics_img)
        mail.send()

    return {'application_proposed': f'{title} - {applicant_email}'}


@shared_task
def generate_logo_thumbnail_task(app_id):
    model = apps.get_model('applications', 'Application')
    instance = model.objects.get(pk=app_id)
    if instance.image:
        image = Image.open(instance.image)

        if image.mode not in ('L', 'RGB', 'RGBA'):
            image = image.convert('RGB')

        image.thumbnail(settings.THUMB_SIZE, Image.ANTIALIAS)

        temp_handle = BytesIO()
        image.save(temp_handle, 'png')
        temp_handle.seek(0)

        suf = SimpleUploadedFile(os.path.split(instance.image.name)[-1],
                                 temp_handle.read(),
                                 content_type='image/png')
        thumb_name = '.'.join(suf.name.split('.')[:-1]) + "_thumb.png"
        instance.image_thumb.save(thumb_name, suf, save=False)
    else:
        instance.image_thumb = None

    model.objects.filter(pk=app_id).update(image_thumb=instance.image_thumb)
    search_signals.update_document.send(model, instance)

    return {
        'image_thumb': instance.image_thumb_url
    }
