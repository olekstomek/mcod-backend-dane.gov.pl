import os
from io import BytesIO

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

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
def send_application_proposal(data):
    model = apps.get_model('applications.ApplicationProposal')
    model.send_application_proposal_mail(data)
    title = data['title']
    applicant_email = data.get('applicant_email', '')
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
