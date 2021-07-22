import itertools
from collections import defaultdict

from django.core.management.base import BaseCommand

from mcod.applications.models import Application
from mcod.articles.models import Article
from mcod.datasets.models import Dataset
from mcod.tags.models import Tag


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--empty-first',
            action='store_true',
            dest='empty_first',
            help='Remove all new-style keywords first',
        )

    def handle(self, *args, **options):
        empty_first = options['empty_first']
        if empty_first:
            Tag.objects.exclude(language='').delete()

        tag_id_to_keywords = defaultdict(list)
        datasets = Dataset.raw.prefetch_related('tags')
        articles = Article.raw.prefetch_related('tags')
        applications = Application.raw.prefetch_related('tags')

        for obj in itertools.chain(datasets, articles, applications):
            for tag in obj.tags.filter(language=''):
                if tag.id not in tag_id_to_keywords:
                    if tag.name:
                        keyword_pl, _ = Tag.objects.get_or_create(name=tag.name, language='pl')
                        tag_id_to_keywords[tag.id].append(keyword_pl)

                    if tag.name_en:
                        keyword_en, _ = Tag.objects.get_or_create(name=tag.name_en, language='en')
                        tag_id_to_keywords[tag.id].append(keyword_en)

                obj.tags.add(*tag_id_to_keywords[tag.id])
