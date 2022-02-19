from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--pks', type=str)
        parser.add_argument(
            '--async',
            action='store_const',
            dest='async',
            const=True,
            help='Use celery task'
        )

    def handle(self, *args, **options):
        if not options['pks']:
            raise CommandError('No resource id specified. You must provide at least one.')
        Resource = apps.get_model('resources', 'Resource')
        asnc = options.get('async') or False
        if not asnc:
            settings.CELERY_TASK_ALWAYS_EAGER = True

        queryset = Resource.objects.with_tabular_data(
            pks=(int(pk) for pk in options['pks'].split(',')))
        self.stdout.write('The action will reindex files for {} resource(s)'.format(queryset.count()))
        for obj in tqdm(queryset, desc='Indexing'):
            obj.index_file()
        self.stdout.write('Done.')
