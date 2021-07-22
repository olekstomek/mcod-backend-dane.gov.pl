import os
import tempfile
from datetime import datetime
from dateutil.relativedelta import relativedelta
from celery import shared_task
from constance import config
from django.apps import apps
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from mcod import settings
from mcod.core.utils import save_as_csv


@shared_task
def send_dataset_comment(dataset_id, comment, lang=None):
    model = apps.get_model('datasets', 'Dataset')
    dataset = model.objects.get(pk=dataset_id)

    conn = get_connection(settings.EMAIL_BACKEND)
    template_suffix = ''

    with translation.override('pl'):
        title = dataset.title.replace('\n', ' ').replace('\r', '')
        version = _(' (version %(version)s)') % {'version': dataset.version} if dataset.version else ''
        msg_template = _('On the data set %(title)s%(version)s [%(url)s] was posted a comment:')
        msg = msg_template % {
            'title': title,
            'version': version,
            'url': dataset.frontend_absolute_url,
        }
        html_msg = msg_template % {
            'title': title,
            'version': version,
            'url': f'<a href="{dataset.frontend_absolute_url}">{dataset.frontend_absolute_url}</a>',
        }
        context = {
            'host': settings.BASE_URL,
            'url': dataset.frontend_absolute_url,
            'comment': comment,
            'dataset': dataset,
            'message': msg,
            'html_message': html_msg,
        }

        if settings.DEBUG and config.TESTER_EMAIL:
            template_suffix = '-test'

        subject = _('A comment was posted on the data set %(title)s%(version)s') % {
            'title': title,
            'version': version,
        }
        msg_plain = render_to_string(f'mails/report-dataset-comment{template_suffix}.txt', context=context)
        msg_html = render_to_string(f'mails/report-dataset-comment{template_suffix}.html', context=context)

        send_mail(
            subject,
            msg_plain,
            config.SUGGESTIONS_EMAIL,
            [config.TESTER_EMAIL] if settings.DEBUG and config.TESTER_EMAIL else dataset.comment_mail_recipients,
            connection=conn,
            html_message=msg_html,
        )

    return {
        'dataset': dataset_id
    }


def _batch_qs(qs):
    batch_size = settings.CSV_CATALOG_BATCH_SIZE
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield start, end, total, qs[start:end]


@shared_task
def create_catalog_metadata_csv_file():
    from mcod.resources.serializers import DatasetResourcesCSVSerializer
    model = apps.get_model('resources', 'Resource')
    schema = DatasetResourcesCSVSerializer(many=True)
    overall_data = []
    today = datetime.today().date()
    previous_day = today - relativedelta(days=1)
    data_qs = model.objects.with_metadata()
    for start, end, total, qs in _batch_qs(data_qs):
        overall_data.extend(qs)
    for language in settings.LANGUAGE_CODES:
        lang_catalog_path = f'{settings.DATASET_CSV_CATALOG_MEDIA_ROOT}/{language}'
        if not os.path.exists(lang_catalog_path):
            os.makedirs(lang_catalog_path)
        with translation.override(language):
            csv_data = schema.dump(overall_data)
            previous_day_file = f'{lang_catalog_path}/katalog_{previous_day}.csv'
            new_file = f'{lang_catalog_path}/katalog_{today}.csv'
            symlink_file = f'{lang_catalog_path}/katalog.csv'
            link_dir = os.path.dirname(symlink_file)
            with open(new_file, 'w') as csv_file:
                save_as_csv(csv_file, schema.get_csv_headers(), csv_data)
            if os.path.exists(previous_day_file):
                temp_link_name = tempfile.mktemp(dir=link_dir)
                os.symlink(new_file, temp_link_name)
                os.replace(temp_link_name, symlink_file)
                os.remove(previous_day_file)
            else:
                os.symlink(new_file, symlink_file)
