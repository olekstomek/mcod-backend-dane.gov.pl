from django.apps import apps
from django.core.management.base import CommandError
from django_tqdm import BaseCommand

from mcod.resources.tasks import process_resource_file_data_task
from django.conf import settings

description = """
Po zmianie sposobu wyświetlania i indeksowania date i datetime stare zasoby mogą mieć problem ze zmianą typu. 
Wynika to z tego, że mają one utworzony schemat a w nim dla typów date i datetime ustawiony format 'default'.
Nowe zasoby mają ustawiony dla tych typów format 'any'. 

Te polecenie dla wybranych zasobów zmieni schemat zamieniając 'default' na 'any'.

Zostawiono tu też możliwość ustawienia innego formatu.

Dla wybranego zasobu zmiana ta powinna być możliwa też z poziomu panelu admina.
Przy zmianie schematu - jeśli kolumna jest typu date lub datetime i jej format to 'default', to zostanie on zmieniony na 'any'.
Dotyczy to tylko zasóbów z widokiem tabelarycznym. Nie ma zastosowania dla geo."""  # noqa


def update_schema(schema, dateformat, datetimeformat):
    for field in schema['fields']:
        if field['type'] == 'date':
            field['format'] = dateformat
        elif field['type'] == 'datetime':
            field['format'] = datetimeformat
        elif field['type'] == 'time':
            field['format'] = datetimeformat
    return schema


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.description = description
        parser.add_argument('--pks', type=str)
        parser.add_argument(
            '--async',
            action='store_const',
            dest='async',
            const=True,
            help="Use celery task"
        )
        parser.add_argument(
            '--dateformat',
            type=str,
            default="any",
            help="Schema datetime format - 'default' or 'any'. Now by default 'any' will be choosen"
        )
        parser.add_argument(
            '--datetimeformat',
            type=str,
            default="any",
            help="Schema datetime format - 'default' or 'any'. Now by default 'any' will be choosen"
        )
        parser.add_argument(
            '--timeformat',
            type=str,
            default="any",
            help="Schema datetime format - 'default' or 'any'. Now by default 'any' will be choosen"
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

        date_format = options['dateformat']
        datetime_format = options['datetimeformat']

        pks = (int(pk) for pk in options['pks'].split(','))
        query = Resource.objects.filter(
            pk__in=pks,
            type='file',
            format__in=('csv', 'tsv', 'xls', 'xlsx', 'ods', 'shp')).exclude(file=None).exclude(file='')

        progress_bar = self.tqdm(desc="Indexing", total=query.count())

        for res in query:
            if res.tabular_data_schema:
                tabular_data_schema = update_schema(res.tabular_data_schema, date_format, datetime_format)
                Resource.objects.filter(pk=res.id).update(tabular_data_schema=tabular_data_schema)
            process_resource_file_data_task.delay(res.id, update_verification_date=False)
            progress_bar.update(1)

        print('Done.')
