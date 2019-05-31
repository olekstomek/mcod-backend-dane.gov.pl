import csv
import datetime
import json
import logging
import os
from collections import OrderedDict
from pathlib import Path

from celery import shared_task, task
from celery.signals import task_prerun, task_failure, task_success
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils.timezone import now
from django_celery_results.models import TaskResult

from mcod import settings
from mcod.core.serializers import csv_serializers_registry as csr
from mcod.reports.models import Report, SummaryDailyReport

User = get_user_model()
logger = logging.getLogger('mcod')


@shared_task(name='reports')
def generate_csv(pks, model_name, user_id, file_name_postfix):
    app, _model = model_name.split('.')
    model = apps.get_model(app, _model)
    serializer_cls = csr.get_serializer(model)

    if not serializer_cls:
        raise Exception('Cound not find serializer for model %s' % model_name)

    serializer = serializer_cls(many=True)
    headers = []
    for field_name, field in serializer.fields.items():
        header = field.data_key or field_name
        headers.append(header)
    queryset = model.objects.filter(pk__in=pks)
    data = serializer_cls(many=True).dump(queryset)
    user = User.objects.get(pk=user_id)
    file_name = '{}_{}.csv'.format(app, file_name_postfix)

    reports_path = os.path.join(settings.REPORTS_MEDIA_ROOT, app)
    os.makedirs(reports_path, exist_ok=True)

    file_path = os.path.join(reports_path, file_name)
    file_url_path = f'{settings.REPORTS_MEDIA}/{app}/{file_name}'

    with open(file_path, 'w') as f:
        writer = csv.DictWriter(f, delimiter=';', fieldnames=headers)
        writer.writeheader()
        for rowdict in data:
            writer.writerow(rowdict)

    return json.dumps({
        'model': model_name,
        'csv_file': file_url_path,
        'date': now().strftime('%Y.%m.%d %H:%M'),
        'user_email': user.email
    })


@task_prerun.connect(sender=generate_csv)
def append_report_task(sender, task_id, task, signal, **kwargs):
    try:
        pks, model_name, user_id, d = kwargs['args']
        task_obj = TaskResult.objects.get_task(task_id)
        task_obj.save()
        try:
            ordered_by = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            ordered_by = None
        report = Report(
            model=model_name,
            ordered_by=ordered_by,
            task=task_obj
        )
        report.save()
    except Exception as e:
        logger.error(f"reports.task: sexception on append_report_task:\n{e}")


@task_success.connect(sender=generate_csv)
def generating_report_success(sender, result, **kwargs):
    try:
        result_dict = json.loads(result)
        logger.info(f"reports.task: report generated: {result_dict.get('csv_file')}")

        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = result
        result_task.status = 'SUCCESS'
        result_task.save()

        report = Report.objects.get(task=result_task)
        report.file = result_dict.get('csv_file')
        report.save()
    except Exception as e:
        logger.error(f"reports.task: exception on generating_report_success:\n{e}")


@task_failure.connect(sender=generate_csv)
def generating_report_failure(sender, task_id, exception, args, traceback, einfo, signal, **kwargs):
    logger.debug(f"generating report failed with:\n{exception}")
    try:
        result_task = TaskResult.objects.get_task(task_id)
        result_task.status = 'FAILURE'
        result_task.save()
    except Exception as e:
        logger.error(f"reports.task: exception on generating_report_failure:\n{e}")


def dict_fetch_all(cursor):
    """Return all rows from a cursor as a OrderedDict"""
    columns = [col[0] for col in cursor.description]
    return [OrderedDict(zip(columns, row)) for row in cursor.fetchall()]


@task
def create_daily_resources_report():
    str_date = datetime.datetime.now().strftime('%Y_%m_%d_%H%M')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_zasobu,
                   NULL as link_zasobu,
                   nazwa,
                   opis,
                   typ,
                   format,
                   data_utworzenia_zasobu,
                   data_modyfikacji_zasobu,
                   stopien_otwartosci,
                   liczba_wyswietlen,
                   liczba_pobran,
                   id_zbioru_danych,
                   NULL as link_zbioru,
                   data_utworzenia_zbioru_danych,
                   data_modyfikacji_zbioru_danych,
                   liczba_obserwujacych,
                   id_instytucji,
                   NULL as link_instytucji,
                   tytul,
                   rodzaj,
                   data_utworzenia_instytucji,
                   liczba_udostepnionych_zbiorow_danych
            FROM mv_resource_dataset_organization_report
        """)
        results = dict_fetch_all(cursor)

    for r in results:
        if r['id_zasobu']:
            r['link_zasobu'] = f"{settings.BASE_URL}/dataset/{r['id_zbioru_danych']}/resource/{r['id_zasobu']}"
        if r['id_zbioru_danych']:
            r['link_zbioru'] = f"{settings.BASE_URL}/dataset/{r['id_zbioru_danych']}"
        if r['id_instytucji']:
            r['link_instytucji'] = f"{settings.BASE_URL}/institution/{r['id_instytucji']}"

    os.makedirs(Path(settings.REPORTS_MEDIA_ROOT, 'daily'), exist_ok=True)
    file_path = Path(settings.REPORTS_MEDIA[1:], 'daily', f'Zbiorczy_raport_dzienny_{str_date}.csv')
    save_path = Path(settings.REPORTS_MEDIA_ROOT, 'daily', f'Zbiorczy_raport_dzienny_{str_date}.csv')

    with open(save_path, 'w') as f:
        w = csv.DictWriter(f, results[0].keys())
        w.writeheader()
        w.writerows(results)

    SummaryDailyReport.objects.create(
        file=file_path,
        ordered_by_id=1,

    )

    return {}
