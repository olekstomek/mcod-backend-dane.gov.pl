from django_tqdm import BaseCommand
from datetime import datetime

from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.resources.models import Resource


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'initial_date',
            type=str,
            help='Initial date for newly created date counters in format DD-MM-YYYY.'
        )
        parser.add_argument(
            '--counters_type',
            type=str,
            default='all',
            help='Type of counters to create.[views/downloads] Default value is "all"'
        )

    def init_new_counters(self, initial_date, counters_type):
        download_counters = []
        view_counters = []
        allowed_to_create = []
        if not ResourceDownloadCounter.objects.exists():
            allowed_to_create.append('downloads')
        else:
            self.stdout.write('Downloads counters already exists, not creating.')
        if not ResourceViewCounter.objects.exists():
            allowed_to_create.append('views')
        else:
            self.stdout.write('Views counters already exists, not creating.')
        if len(allowed_to_create) == 2:
            allowed_to_create.append('all')
        resources_count_values = Resource.raw.all().values('views_count', 'downloads_count', 'pk') if\
            allowed_to_create else Resource.raw.none()
        for resource_details in resources_count_values:
            if counters_type in ['downloads', 'all'] and counters_type in allowed_to_create:
                download_counters.append(ResourceDownloadCounter(
                    count=resource_details['downloads_count'], resource_id=resource_details['pk'],
                    timestamp=initial_date))
            if counters_type in ['views', 'all'] and counters_type in allowed_to_create:
                view_counters.append(ResourceViewCounter(count=resource_details['views_count'],
                                                         resource_id=resource_details['pk'],
                                                         timestamp=initial_date))
        if view_counters:
            ResourceViewCounter.objects.bulk_create(view_counters)
            self.stdout.write('Succesfully created views counters')
        if download_counters:
            ResourceDownloadCounter.objects.bulk_create(download_counters)
            self.stdout.write('Succesfully created downloads counters')

    def handle(self, *args, **options):
        initial_date_str = options['initial_date']
        counters_type = options['counters_type']
        try:
            initial_date = datetime.strptime(initial_date_str, '%d-%m-%Y')
            self.init_new_counters(initial_date, counters_type)
        except ValueError:
            self.stdout.write('Invalid date format. Valid format is DD-MM-YYYY')
