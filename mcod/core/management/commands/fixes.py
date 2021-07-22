import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from mcod import settings
from mcod.articles.models import ArticleCategory
from mcod.cms.models import FormPageSubmission
from mcod.cms.models.formpage import Formset
from mcod.datasets.models import Dataset
from mcod.resources.models import Resource
from mcod.resources.tasks import (
    process_resource_file_task,
    update_resource_validation_results_task,
    update_resource_has_table_has_map_task,
)

task_list = ['file_tasks', 'data_tasks', 'link_tasks']

MEDIA_PATH = '/usr/src/mcod_backend/media/'


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
            '--migratefollowings',
            action='store_const',
            dest='action',
            const='migratefollowings',
            help='Copy following to subscriptions'

        )

        parser.add_argument(
            '--setverified',
            action="store_const",
            dest="action",
            const="setverified",
            help="Fix verfied for datasets and resources"
        )

        parser.add_argument(
            '--resourcesformats',
            action="store_const",
            dest="action",
            const="resourcesformats",
            help="Run fixes for resources formats"
        )

        parser.add_argument(
            '--resources-links',
            action='store_const',
            dest='action',
            const='resources-links',
            help='Run fixes for resources links',
        )

        parser.add_argument(
            '--resources-validation-results',
            action='store_const',
            dest='action',
            const='resources-validation-results',
            help='Updates link_tasks_last_status, file_tasks_last_status, data_tasks_last_status of resources',
        )

        parser.add_argument(
            '--resources-has-table-has-map',
            action='store_const',
            dest='action',
            const='resources-has-table-has-map',
            help='Updates has_table and has_map attributes of resources',
        )

        parser.add_argument(
            '--submissions-to-new-format',
            action='store_const',
            dest='action',
            const='submissions-to-new-format',
            help='Converts FormDataSubmissions form_data field to new format',
        )

        parser.add_argument(
            '--submissions-to-old-format',
            action='store_const',
            dest='action',
            const='submissions-to-old-format',
            help='Converts FormDataSubmissions form_data field to old format',
        )

        parser.add_argument(
            '--submissions-formdata-save',
            action='store_const',
            dest='action',
            const='submissions-formdata-save',
            help='Saves FormDataSubmissions form_data field to file',
        )

        parser.add_argument(
            '--submissions-formdata-load',
            action='store_const',
            dest='action',
            const='submissions-formdata-load',
            help='Loads data from file into FormDataSubmissions form_data field',
        )

    def fix_resources(self):
        rs = Resource.objects.filter(dataset__is_removed=True)
        for r in rs:
            print(f"Resource ({r.id}) is set as removed because dataset ({r.dataset.id}) is removed")
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
        print("Przygotowuje się do ustawienia daty danych dla istniejących zasobów ...")
        resources_with_files = Resource.raw.all()
        print(f"Do zaktualizowania: {resources_with_files.count()}")
        resources_with_files.update(data_date=F('created'))
        print("Operacja zakończona")

    def fix_resources_validation_results(self):
        resources = Resource.raw.order_by('id')
        for obj in resources:
            update_resource_validation_results_task.s(obj.id).apply_async()

    def fix_resources_has_table_has_map(self):
        resources = Resource.raw.order_by('id')
        for obj in resources:
            update_resource_has_table_has_map_task.s(obj.id).apply_async()

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

    def fix_followings(self):
        from mcod.users.models import UserFollowingApplication, UserFollowingArticle, UserFollowingDataset
        from mcod.watchers.models import Subscription, ModelWatcher
        for following in UserFollowingArticle.objects.all():
            watcher, _ = ModelWatcher.objects.get_or_create_from_instance(following.article)
            Subscription.objects.get_or_create(
                user=following.follower,
                watcher=watcher,
                name='article-%i' % following.article.id
            )

        for following in UserFollowingApplication.objects.all():
            watcher, _ = ModelWatcher.objects.get_or_create_from_instance(following.application)
            Subscription.objects.get_or_create(
                user=following.follower,
                watcher=watcher,
                name='application-%i' % following.application.id
            )
        for following in UserFollowingDataset.objects.all():
            watcher, _ = ModelWatcher.objects.get_or_create_from_instance(following.dataset)
            Subscription.objects.get_or_create(
                user=following.follower,
                watcher=watcher,
                name='dataset-%i' % following.dataset.id
            )

    def fix_resources_links(self):
        self.stdout.write('Fixing of resources broken links - with . (dot) suffix.')
        counter = 0
        for obj in Resource.objects.filter(link__endswith='.'):
            if obj.file_url.startswith(settings.API_URL) and obj.format:
                broken_link = obj.link
                fixed_link = f'{obj.link}{obj.format}'
                obj.link = fixed_link
                obj.save()
                counter += 1
                self.stdout.write(f'Resource with id: {obj.id} link changed from {broken_link} to {fixed_link}')
        self.stdout.write(f'Number of fixes: {counter}')

    def fix_resources_formats(self):
        print("Fixing invalid resource formats (with format='True')")

        objs = Resource.raw.filter(format='True')
        for obj in objs:
            print(f'Resource with invalid format found: id:{obj.id} , format:{obj.format}')
            process_resource_file_task.s(obj.id, update_link=False).apply_async(
                countdown=1)
        if objs.count():
            print('Done.')
        else:
            print('Resources with format=\'True\' was not found.')

    def convert_form_page_submissions_to_new_format(self):
        print('Converting FormPageSubmissions form_data to NEW format.')
        for submission in FormPageSubmission.objects.all():
            print(f"FormPageSubmission's ({submission.id}) form_data is:\n{submission.form_data}")
            submission_modified = False
            formsets = Formset.objects.filter(page=submission.page)
            for question in formsets:
                question_id = str(question.ident)

                results = submission.form_data.get(question_id)
                if isinstance(results, list):
                    fields_ids = (field.id for field in question.fields)
                    submission.form_data[question_id] = dict(zip(fields_ids, results))
                    submission_modified = True

            if submission_modified:
                submission.save()
                print(f"Converted FormPageSubmission's ({submission.id}) form_data to:\n{submission.form_data}")

    def convert_form_page_submissions_to_old_format(self):
        print('Converting FormPageSubmissions form_data to OLD format.')
        for submission in FormPageSubmission.objects.all():
            print(f"FormPageSubmission's ({submission.id}) form_data is:\n{submission.form_data}")
            submission_modified = False
            formsets = Formset.objects.filter(page=submission.page)
            for question in formsets:
                question_id = str(question.ident)

                results = submission.form_data.get(question_id)
                if isinstance(results, dict):
                    new_results = [None] * len(question.fields)
                    field_id_to_index_map = {
                        field.id: index
                        for index, field in enumerate(question.fields)
                    }

                    for field_id, result in results.items():
                        field_index = field_id_to_index_map[field_id]
                        new_results[field_index] = result

                    submission.form_data[question_id] = new_results
                    submission_modified = True

            if submission_modified:
                submission.save()
                print(f"Converted FormPageSubmission's ({submission.id}) form_data to:\n{submission.form_data}")

    def save_form_page_submissions_form_data_to_file(self):
        Path(MEDIA_PATH).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(MEDIA_PATH, 'FormPageSubmissions.json')
        print(f'Saving FormPageSubmissions form_data to file:{filepath}')
        data = json.dumps({
            submission.id: submission.form_data
            for submission in FormPageSubmission.objects.all()
        })
        print(data)
        with open(filepath, 'w') as file:
            file.write(data)

    def load_form_page_submissions_form_data_from_file(self):
        filepath = os.path.join(MEDIA_PATH, 'FormPageSubmissions.json')
        print(f'Loading FormPageSubmissions form_data from file:{filepath}')
        with open(filepath) as file:
            data = json.load(file)

        for submission_id, form_data in data.items():
            submission = FormPageSubmission.objects.get(id=submission_id)
            print(f"FormPageSubmission's ({submission.id}) form_data before load:\n{submission.form_data}")
            submission.form_data = form_data
            submission.save()
            print(f"FormPageSubmission's ({submission.id}) form_data after load:\n{submission.form_data}")

    def handle(self, *args, **options):
        if not options['action']:
            raise CommandError(
                "No action specified. Must be one of"
                " '--all','--searchhistories', '--resources', '--datasets', '--articlecategories', "
                "'--resourcedatadate', '--resourcesformats', '--migratefollowings', '--setverified', "
                "'--resources-links', '--resources-validation-results', '--resources-has-table-has-map', "
                "'--submissions-to-new-format', '--submissions-to-old-format', "
                "'--submissions-formdata-save', '--submissions-formdata-load'."
            )
        action = options['action']

        actions = {
            'articlecategories': self.fix_article_categories,
            'datasets': self.fix_datasets,
            'resources-links': self.fix_resources_links,
            'migratefollowings': self.fix_followings,
            'resourcedatadate': self.fix_resources_data_date,
            'resources': self.fix_resources,
            'resourcesformats': self.fix_resources_formats,
            'searchhistories': self.fix_searchhistories,
            'setverified': self.fix_verified,
            'resources-validation-results': self.fix_resources_validation_results,
            'resources-has-table-has-map': self.fix_resources_has_table_has_map,
            'submissions-to-new-format': self.convert_form_page_submissions_to_new_format,
            'submissions-to-old-format': self.convert_form_page_submissions_to_old_format,
            'submissions-formdata-save': self.save_form_page_submissions_form_data_to_file,
            'submissions-formdata-load': self.load_form_page_submissions_form_data_from_file,
        }
        if action == 'all':
            self.fix_searchhistories()
            self.fix_datasets()
            self.fix_resources()
            self.fix_article_categories()
        elif action in actions.keys():
            actions[action]()
