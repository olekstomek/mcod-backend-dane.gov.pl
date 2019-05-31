from django.apps import apps
from django.conf import settings
from django_tqdm import BaseCommand

from mcod.applications.tasks import generate_logo_thumbnail_task


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--pks', type=str)
        parser.add_argument(
            '--async',
            action='store_const',
            dest='async',
            const=True,
            help="Generate using celery tasks"
        )

    def handle(self, *args, **options):
        asnc = options.get('async') or False
        if not asnc:
            settings.CELERY_TASK_ALWAYS_EAGER = True

        Application = apps.get_model('applications', 'Application')
        query = Application.objects.all()
        if options['pks']:
            pks = (int(pk) for pk in options['pks'].split(','))
            query = query.filter(pk__in=pks)

        progress_bar = self.tqdm(desc="Generating", total=query.count())
        for app in query:
            progress_bar.update(1)
            generate_logo_thumbnail_task.delay(app.id)
        print('Done.')
