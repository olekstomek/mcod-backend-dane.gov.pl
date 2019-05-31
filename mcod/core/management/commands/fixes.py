from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from mcod.articles.models import ArticleCategory
from mcod.resources.models import Resource

from mcod.datasets.models import Dataset

task_list = ['file_tasks', 'data_tasks', 'link_tasks']


class Command(BaseCommand):
    help = 'Various fixes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_const',
            dest='action',
            const='all',
            help="Run all fixes"
        )
        parser.add_argument(
            '--searchhistories',
            action='store_const',
            dest='action',
            const='searchhistories',
            help="Run fixes for search history"
        )
        parser.add_argument(
            '--datasets',
            action='store_const',
            dest='action',
            const='datasets',
            help="Run fixes for datasets"
        )
        parser.add_argument(
            '--resources',
            action='store_const',
            dest='action',
            const='resources',
            help="Run fixes for resources"
        )

        parser.add_argument(
            '--articlecategories',
            action='store_const',
            dest='action',
            const='articlecategories',
            help='Run fixes for article categories'
        )

        parser.add_argument(
            '--resourcedatadate',
            action='store_const',
            dest='action',
            const='resourcedatadate',
            help='Run fix that set data_date for resources with files'

        )

        parser.add_argument(
            '--setverified',
            action="store_const",
            dest="action",
            const="setverified",
            help="Fix verfied for datasets and resources"
        )

    def fix_resources(self):
        from mcod.resources.models import Resource
        rs = Resource.objects.filter(dataset__is_removed=True)
        for r in rs:
            print(f"Resorce ({r.id}) is set as removed because dataset ({r.dataset.id}) is removed")
            r.is_removed = True
            r.save()
        rs = Resource.objects.filter(dataset__status="draft")
        for r in rs:
            if r.status == "published":
                print(
                    f"Status of resource ({r.id}) is change to draft because dataset ({r.dataset.id}) is draft")
                r.status = "draft"
                r.save()

    def fix_searchhistories(self):
        from mcod.searchhistories.models import SearchHistory
        print("Fixing search history")

        searchhistories = SearchHistory.objects.filter(query_sentence="*")

        for s in searchhistories:
            print(f'Removing search history id:{s.id} , url:{s.url}')
            s.delete()

        print('Done.')

    def fix_datasets(self):
        from django.db.models import CharField
        from django.db.models.functions import Length
        from mcod.datasets.models import Dataset

        ds = Dataset.objects.filter(organization__is_removed=True)
        for d in ds:
            print(f"Dataset ({d.id}) is set as removed because organization ({d.organization.id}) is removed")
            d.is_removed = True
            d.save()
        ds = Dataset.objects.filter(organization__status="draft")
        for d in ds:
            if d.status == "published":
                print(
                    f"Status of dataset ({d.id}) is changed to draft because organization ({d.organization.id}) is draft")  # noqa
                d.status = "draft"
                d.save()

        print("Fixing slugs")

        CharField.register_lookup(Length, 'length')
        datasets = Dataset.objects.filter(title__length__gt=90)
        for d in datasets:
            Dataset.objects.filter(pk=d.id).update(slug=d.get_unique_slug())

    def fix_article_categories(self):
        """Set Articles Category to base values"""
        user_id = 1

        news = ArticleCategory.objects.get(pk=1)
        news.name = "Aktualności"
        news.description = "Aktualności (dawne artykuły) - zakładka Aktualności"
        news.name_en = "News"
        news.description_en = "News - news tab"
        news.created_by_id = user_id
        news.modified_by_id = user_id
        news.save()

        help = ArticleCategory.objects.get(pk=2)
        help.name = "Pomoc"
        help.description = "Pomoc - zakładka Baza wiedzy"
        help.name_en = "Help"
        help.description_en = "Help - Knowledge base tab"
        help.created_by_id = user_id
        help.modified_by_id = user_id
        help.save()

        training = ArticleCategory.objects.get(pk=3)
        training.name = "Materiały szkoleniowe"
        training.description = "Materiały szkoleniowe - zakładka Baza wiedzy"
        training.name_en = "Training materials"
        training.description_en = "Training - Knowledge base tab"
        training.created_by_id = user_id
        training.modified_by_id = user_id
        training.save()

        question = ArticleCategory.objects.get(pk=4)
        question.name = "Często zadawane pytania"
        question.description = "Często zadawane pytania - zakładka Baza wiedzy"
        question.name_en = "FAQ"
        question.description_en = "Question - Knowledge base tab"
        question.created_by_id = user_id
        question.modified_by_id = user_id
        question.save()

        about = ArticleCategory.objects.get(pk=5)
        about.name = "O serwisie"
        about.description = "O serwisie - stopka portalu"
        about.name_en = "About"
        about.description_en = "About - portal footer"
        about.created_by_id = user_id
        about.modified_by_id = user_id
        about.save()

    def fix_resources_data_date(self):
        """
        Ustawia dla istniejących zasobów data_date na wartość z created
        """
        from mcod.resources.models import Resource
        print("Przygotowuje się do ustawienia daty danych dla istniejących zasobów ...")
        resources_with_files = Resource.raw.all()
        print(f"Do zaktualizowania: {resources_with_files.count()}")
        resources_with_files.update(data_date=F('created'))
        print("Operacja zakończona")

    def verified_for_published_datasets(self):
        # region istniejace zbiory
        print("Rozpoczynam aktualizację dat verified dla istniejących zbiorów i ich zasobów: ")
        datasets = Dataset.objects.filter(status="published")
        datasets_count = datasets.count()
        i = 0
        for dataset in datasets:
            i += 1
            print(f"Ustawiam verified dla dataset id={dataset.id:6}\t{i}/{datasets_count}")
            resources = dataset.resources.filter(status="published")
            if resources:
                resources_dates = []
                for r in resources:
                    tasks_dates = []
                    for t in task_list:
                        tasks = getattr(r, t).all()
                        if tasks:
                            last_task = tasks.latest('date_done')
                            tasks_dates.append(last_task.date_done)

                    if tasks_dates:
                        verified_date = max(tasks_dates)
                    else:
                        verified_date = r.created

                    resources_dates.append(verified_date)
                    Resource.objects.filter(pk=r.id).update(verified=verified_date)

                Dataset.objects.filter(pk=dataset.id).update(verified=max(resources_dates))

            else:
                Dataset.objects.filter(pk=dataset.id).update(verified=dataset.created)
        print("Aktualizacja verified dla istniejących zbiorów i ich zasobów zakończona")
        print()

    def verified_for_removed_resources(self):
        # usunięte zasoby
        print("Aktualizacja verified dla usuniętych zasobów")
        resources = Resource.deleted.all()
        resources_count = resources.count()
        i = 0
        for r in resources:
            i += 1
            print(f"Ustawiam verified dla zasobu id={r.id:6}\t{i}/{resources_count}")
            tasks_dates = []
            for t in task_list:
                tasks = getattr(r, t).all()
                if tasks:
                    last_task = tasks.latest('date_done')
                    tasks_dates.append(last_task.date_done)

            if tasks_dates:
                verified_date = max(tasks_dates)
            else:
                verified_date = r.created
            Resource.objects.filter(pk=r.id).update(verified=verified_date)
        print("Aktualizacja verified dla usuniętych zasobów zakończona")
        print()

    def verified_for_draft_resources(self):
        # szkice zasobów
        print("Aktualizacja verified dla szkiców zasobów")
        resources = Resource.objects.filter(status='draft')
        resources_count = resources.count()
        i = 0
        for r in resources:
            i += 1
            print(f"Ustawiam verified dla zasobu id={r.id:6}\t{i}/{resources_count}")
            tasks_dates = []
            for t in task_list:
                tasks = getattr(r, t).all()
                if tasks:
                    last_task = tasks.latest('date_done')
                    tasks_dates.append(last_task.date_done)

            if tasks_dates:
                verified_date = max(tasks_dates)
            else:
                verified_date = r.created
            Resource.objects.filter(pk=r.id).update(verified=verified_date)
        print("Aktualizacja verified dla szkiców zasobów zakończona")
        print()

    def verified_for_removed_datasets(self):
        # usunięte zbiory
        print("Aktualizacja verified dla usuniętych zbiorów")
        datasets = Dataset.deleted.all()
        datasets_count = datasets.count()
        i = 0
        for dataset in datasets:
            i += 1
            print(f"Ustawiam verified dla dataset id={dataset.id:6}\t{i}/{datasets_count}")
            Dataset.objects.filter(pk=dataset.id).update(verified=dataset.created)
        print("Aktualizacja verified dla usniętych zbiorów zakończona")
        print()

    def verified_for_draft_datasets(self):
        # szkice zbiorów
        print("Aktualizacja verified dla szkiców zbiorów")
        datasets = Dataset.objects.filter(status="draft")
        datasets_count = datasets.count()
        i = 0
        for dataset in datasets:
            i += 1
            print(f"Ustawiam verified dla dataset id={dataset.id:6}\t{i}/{datasets_count}")
            Dataset.objects.filter(pk=dataset.id).update(verified=dataset.created)
        print("Aktualizacja verified dla szkiców zbiorów zakończona")

    def fix_verified(self):
        """
        Ustawia początkową wartośc verified
        """
        self.verified_for_published_datasets()
        self.verified_for_removed_resources()
        self.verified_for_draft_resources()
        self.verified_for_removed_datasets()
        self.verified_for_draft_datasets()

    def handle(self, *args, **options):
        if not options['action']:
            raise CommandError(
                "No action specified. Must be one of"
                " '--all','--searchhistories', '--resources', '--datasets', '--articlecategories', "
                "'--resourcedatadate' ."
            )
        action = options['action']

        if action == 'all':
            self.fix_searchhistories()
            self.fix_datasets()
            self.fix_resources()
            self.fix_article_categories()
        elif action == 'searchhistories':
            self.fix_searchhistories()
        elif action == 'datasets':
            self.fix_datasets()
        elif action == 'resources':
            self.fix_resources()
        elif action == 'articlecategories':
            self.fix_article_categories()
        elif action == 'resourcedatadate':
            self.fix_resources_data_date()
        elif action == 'setverified':
            self.fix_verified()
