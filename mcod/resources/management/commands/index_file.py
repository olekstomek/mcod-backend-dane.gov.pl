from django.apps import apps
from django.core.management.base import CommandError
from django_tqdm import BaseCommand

from mcod.resources.tasks import process_resource_file_data_task
from django.conf import settings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--pks', type=str)
        parser.add_argument(
            '--async',
            action='store_const',
            dest='async',
            const=True,
            help="Use celery task"
        )

    def handle(self, *args, **options):
        if not options['pks']:
            raise CommandError(
                "No resource id specified. You must provide at least one."
            )
        Resource = apps.get_model('resources', 'Resource')
        asnc = options.get('async') or False
        if not asnc:
            settings.CELERY_TASK_ALWAYS_EAGER = True

        pks = (int(pk) for pk in options['pks'].split(','))
        queryset = Resource.objects.with_tabular_data(pks=pks)

        progress_bar = self.tqdm(desc="Indexing", total=queryset.count())

        for res in queryset:
            process_resource_file_data_task.delay(res.id, update_verification_date=False)
            progress_bar.update(1)

        print('Done.')
