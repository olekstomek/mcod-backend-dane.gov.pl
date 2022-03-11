from django.core.management import BaseCommand
from tqdm import tqdm

from mcod.articles.models import Article


class Command(BaseCommand):
    help = 'Migrates all existing news to CMS (as NewsPage instances).'

    def add_arguments(self, parser):
        parser.add_argument('--pks', type=str)
        parser.add_argument(
            '-y, --yes', action='store_true', default=None,
            help='Continue without asking confirmation.', dest='yes')

    def handle(self, *args, **options):
        query = {'category__type': 'article'}
        if options['pks']:
            query['pk__in'] = (int(x) for x in options['pks'].split(',') if x)
        queryset = Article.objects.filter(**query)
        self.stdout.write(f'This action will migrate {queryset.count()} news to CMS')
        answer = options['yes']
        if answer is None:
            response = input('Are you sure you want to continue? [y/N]: ').lower().strip()
            answer = response == 'y'
        if answer:
            for obj in tqdm(queryset, desc='News'):
                obj.migrate_news_to_cms()
            self.stdout.write('Done!')
        else:
            self.stdout.write('Aborted.')
