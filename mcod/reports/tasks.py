import csv
import datetime
import json
import logging
import os
from collections import OrderedDict
from pathlib import Path

from celery import shared_task, chord
from celery.signals import task_prerun, task_failure, task_success
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Count, Q, F
from django.utils.timezone import now
from django.utils.translation import get_language
from django_celery_results.models import TaskResult

from mcod import settings
from mcod.applications.serializers import ApplicationProposalCSVSerializer
from mcod.celeryapp import app
from mcod.core.serializers import csv_serializers_registry as csr
from mcod.core.utils import save_as_csv
from mcod.datasets.models import Dataset
from mcod.reports.models import Report, SummaryDailyReport
from mcod.resources.models import Resource
from mcod.resources.tasks import validate_link
from mcod.showcases.serializers import ShowcaseProposalCSVSerializer
from mcod.suggestions.serializers import DatasetSubmissionCSVSerializer
from mcod.unleash import is_enabled

User = get_user_model()
logger = logging.getLogger('mcod')


@shared_task(name='reports')
def generate_csv(pks, model_name, user_id, file_name_postfix):
    app, _model = model_name.split('.')
    model = apps.get_model(app, _model)
    serializer_cls = csr.get_serializer(model)
    if _model == 'ApplicationProposal':  # TODO: how to register it in csr?
        serializer_cls = ApplicationProposalCSVSerializer
    elif _model == 'DatasetSubmission':  # TODO: how to register it in csr?
        serializer_cls = DatasetSubmissionCSVSerializer
    elif _model == 'ShowcaseProposal':
        serializer_cls = ShowcaseProposalCSVSerializer

    if not serializer_cls:
        raise Exception('Cound not find serializer for model %s' % model_name)

    serializer = serializer_cls(many=True)
    queryset = model.objects.filter(pk__in=pks)
    data = serializer_cls(many=True).dump(queryset)
    user = User.objects.get(pk=user_id)
    file_name = f'{_model.lower()}s_{file_name_postfix}.csv'
    reports_path = os.path.join(settings.REPORTS_MEDIA_ROOT, app)
    os.makedirs(reports_path, exist_ok=True)

    file_path = os.path.join(reports_path, file_name)
    file_url_path = f'{settings.REPORTS_MEDIA}/{app}/{file_name}'

    with open(file_path, 'w') as f:
        save_as_csv(f, serializer.get_csv_headers(), data)

    return json.dumps({
        'model': model_name,
        'csv_file': file_url_path,
        'date': now().strftime('%Y.%m.%d %H:%M'),
        'user_email': user.email
    })


@shared_task
def create_no_resource_dataset_report():
    logger.debug('Running create_no_resource_dataset_report task.')
    app = 'datasets'
    file_name_postfix = now().strftime('%Y%m%d%H%M%S.%s')
    queryset =\
        Dataset.objects.annotate(
            all_resources=Count('resources__pk'),
            unpublished_resources=Count('resources__pk', filter=Q(resources__status='draft'))
        ).filter(Q(resources__isnull=True) | Q(all_resources=F('unpublished_resources')), status='published').distinct()
    serializer_cls = csr.get_serializer(Dataset)
    serializer = serializer_cls(many=True)
    data = serializer.dump(queryset)
    file_name = f'nodata_datasets_{file_name_postfix}.csv'
    reports_path = os.path.join(settings.REPORTS_MEDIA_ROOT, app)
    os.makedirs(reports_path, exist_ok=True)

    file_path = os.path.join(reports_path, file_name)
    file_url_path = f'{settings.REPORTS_MEDIA}/{app}/{file_name}'
    with open(file_path, 'w') as f:
        save_as_csv(f, serializer.get_csv_headers(), data)
    return json.dumps({
        'file': file_url_path,
        'model': 'datasets.Dataset'
    })


def create_resource_link_validation_report():
    app = 'resources'
    file_name_postfix = now().strftime('%Y%m%d%H%M%S.%s')
    queryset =\
        Resource.objects.filter(
            status='published', link__isnull=False, link_tasks_last_status='FAILURE'
        ).exclude(Q(link__startswith=settings.API_URL) | Q(link__startswith=settings.BASE_URL))
    serializer_cls = csr.get_serializer(Resource)
    excluded_fields =\
        ['link_is_valid', 'file_is_valid', 'data_is_valid', 'format', 'status',
         'openness_score', 'views_count', 'downloads_count']
    serializer = serializer_cls(many=True, exclude=excluded_fields)
    data = serializer.dump(queryset)
    file_name = f'brokenlinks_resources_{file_name_postfix}.csv'
    reports_path = os.path.join(settings.REPORTS_MEDIA_ROOT, app)
    os.makedirs(reports_path, exist_ok=True)

    file_path = os.path.join(reports_path, file_name)
    file_url_path = f'{settings.REPORTS_MEDIA}/{app}/{file_name}'
    with open(file_path, 'w') as f:
        save_as_csv(f, serializer.get_csv_headers(), data)
    return json.dumps({
        'file': file_url_path,
        'model': 'resources.Resource'
    })


@shared_task
def link_validation_success_callback():
    return create_resource_link_validation_report()


@shared_task
def link_validation_error_callback():
    return create_resource_link_validation_report()


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
        logger.error(f"reports.task: exception on append_report_task:\n{e}")


@shared_task
def create_resources_report_task(data, headers, report_name):
    logger.debug(f'Creating resource {report_name} report.')
    app_name = 'resources'
    file_name_postfix = now().strftime('%Y%m%d%H%M%S.%s')
    file_name = f'{report_name}_{file_name_postfix}.csv'
    reports_path = os.path.join(settings.REPORTS_MEDIA_ROOT, app_name)
    os.makedirs(reports_path, exist_ok=True)
    file_path = os.path.join(reports_path, file_name)
    file_url_path = f'{settings.REPORTS_MEDIA}/{app_name}/{file_name}'
    with open(file_path, 'w') as f:
        w = csv.DictWriter(f, headers)
        w.writeheader()
        w.writerows(data)
    return json.dumps({
        'file': file_url_path,
        'model': 'resources.Resource'
    })


@task_success.connect(sender=link_validation_success_callback)
@task_success.connect(sender=link_validation_error_callback)
@task_success.connect(sender=create_no_resource_dataset_report)
@task_success.connect(sender=create_resources_report_task)
def generating_monthly_report_success(sender, result, **kwargs):
    try:
        result_dict = json.loads(result)
        logger.info(f"reports.task: report generated: {result_dict.get('file')}")

        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = result
        result_task.status = 'SUCCESS'
        result_task.save()
        result_dict['task'] = result_task
        Report.objects.create(**result_dict)
    except Exception as e:
        logger.error(f"reports.task: exception on generating_monthly_report_success:\n{e}")


@shared_task
def validate_resources_links(ids=None):
    if ids:
        resources_ids = ids
    else:
        resources_ids = list(Resource.objects.filter(
            status='published', link__isnull=False
        ).exclude(Q(link__startswith=settings.API_URL) | Q(link__startswith=settings.BASE_URL)
                  ).values_list('pk', flat=True))
    subtasks = [validate_link.s(res_id) for res_id in resources_ids]
    callback = link_validation_success_callback.si().on_error(link_validation_error_callback.si())
    chord(subtasks, callback).apply_async()


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
@task_failure.connect(sender=create_no_resource_dataset_report)
@task_failure.connect(sender=validate_resources_links)
@task_failure.connect(sender=create_resources_report_task)
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


@app.task
def create_daily_resources_report():
    str_date = datetime.datetime.now().strftime('%Y_%m_%d_%H%M')
    if is_enabled('S16_new_date_counters.be'):
        view_name = 'mv_resource_dataset_organization_new_counters_report'
    else:
        view_name = 'mv_resource_dataset_organization_report'
    with connection.cursor() as cursor:
        cursor.execute(f"""REFRESH MATERIALIZED VIEW {view_name}""")
        cursor.execute(f"""
            SELECT id_zasobu,
                   NULL as link_zasobu,
                   nazwa,
                   opis,
                   typ,
                   format,
                   formaty_po_konwersji,
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
            FROM {view_name}
        """)
        results = dict_fetch_all(cursor)

    for r in results:
        if r['id_zasobu']:
            r['link_zasobu'] = f"{settings.BASE_URL}/{get_language()}/dataset/{r['id_zbioru_danych']}/resource/{r['id_zasobu']}"
        if r['id_zbioru_danych']:
            r['link_zbioru'] = f"{settings.BASE_URL}/{get_language()}/dataset/{r['id_zbioru_danych']}"
        if r['id_instytucji']:
            r['link_instytucji'] = f"{settings.BASE_URL}/{get_language()}/institution/{r['id_instytucji']}"

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
