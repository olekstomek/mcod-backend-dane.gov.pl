from django_tqdm import BaseCommand
from django.apps import apps
from django.db.models import F
from mcod.resources.tasks import check_link_protocol
from mcod.reports.tasks import create_link_protocol_report_task
from celery import chord


class Command(BaseCommand):

    def handle(self, *args, **options):
        Resource = apps.get_model('resources', 'Resource')
        http_resources = list(Resource.objects.with_ext_http_links_only().annotate(
            resource_id=F('pk'), organization_title=F('dataset__organization__title')).values(
            'resource_id', 'link', 'title', 'organization_title'
        ))
        self.stdout.write('Analyzing resources link protocol. Found {} resources to check'.format(len(http_resources)))
        subtasks = [check_link_protocol.s(**res_details) for res_details in http_resources]
        callback = create_link_protocol_report_task.s()
        chord(subtasks, callback).apply_async()
