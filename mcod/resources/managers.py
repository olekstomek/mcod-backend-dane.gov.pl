from django.apps import apps
from django.conf import settings
from django.db.models import Count, Q, Prefetch, Manager
from mcod.core.managers import SoftDeletableQuerySet, SoftDeletableManager, RawManager
from mcod.unleash import is_enabled


class ChartQuerySet(SoftDeletableQuerySet):

    def chart_for_user(self, user):
        default = self.filter(is_default=True).last()
        if user.is_authenticated:
            user_charts = self.filter(created_by=user)
            return user_charts.filter(is_default=False).last() or user_charts.filter(is_default=True).last() or default
        return default

    def chart_to_update(self, user, is_default):
        qs = self.filter(is_default=is_default)
        return qs.filter(created_by=user).last() or (qs.last() if is_default else None)

    def published(self):
        resource_model = apps.get_model('resources.Resource')
        return self.filter(
            resource__status=resource_model.STATUS.published,
            resource__is_removed=False,
        )


class ChartManager(SoftDeletableManager):
    _queryset_class = ChartQuerySet

    def chart_for_user(self, user):
        return self.get_queryset().chart_for_user(user)

    def chart_to_update(self, user, is_default):
        return self.get_queryset().chart_to_update(user, is_default)

    def published(self):
        return self.get_queryset().published()


class PrefetchResourceFilesMixin:

    def get_files_prefetch(self):
        resource_file = apps.get_model('resources', 'ResourceFile')
        main_file = Prefetch('files', resource_file.objects.filter(is_main=True), to_attr='_cached_file')
        other_files = Prefetch('files', resource_file.objects.filter(is_main=False), to_attr='_other_files')
        return main_file, other_files


class SoftDeletableMetadataQuerySet(PrefetchResourceFilesMixin, SoftDeletableQuerySet):

    def with_metadata(self):
        tag_model = apps.get_model('tags', 'Tag')
        res_filter = Q(dataset__resources__status='published', dataset__resources__is_removed=False,
                       dataset__resources__is_permanently_removed=False)
        dataset_filter = Q(dataset__organization__datasets__status='published',
                           dataset__organization__datasets__is_removed=False,
                           dataset__organization__datasets__is_permanently_removed=False)
        org_res_filter = Q(dataset__organization__datasets__resources__status='published',
                           dataset__organization__datasets__resources__is_removed=False,
                           dataset__organization__datasets__resources__is_permanently_removed=False
                           )
        prefetch_tags_pl = Prefetch('dataset__tags', tag_model.objects.filter(language='pl'), to_attr='tags_pl')
        prefetch_tags_en = Prefetch('dataset__tags', tag_model.objects.filter(language='en'), to_attr='tags_en')
        return self.published().annotate(
            resources_count=Count('dataset__resources', filter=res_filter, distinct=True),
            datasets_count=Count('dataset__organization__datasets', filter=dataset_filter, distinct=True),
            organization_resources_count=Count('dataset__organization__datasets__resources',
                                               filter=org_res_filter, distinct=True),
        ).prefetch_related(
            'dataset__organization', prefetch_tags_pl, prefetch_tags_en,
            'dataset__categories').order_by('dataset_id', 'id')

    def with_tabular_data(self, **kwargs):
        formats = ('csv', 'tsv', 'xls', 'xlsx', 'ods', 'shp')
        query = {
            'type': 'file',
        }
        pks = kwargs.get('pks')
        if pks:
            query['pk__in'] = pks
        return self.by_formats(formats).filter(**query)

    def by_formats(self, formats):
        if is_enabled('S40_new_file_model.be'):
            return self.filter(files__isnull=False, format__in=formats).distinct()
        else:
            return self.filter(file__isnull=False, format__in=formats).exclude(file='')

    def published(self):
        return self.filter(status='published')

    def with_prefetched_files(self):
        main_file, other_files = self.get_files_prefetch()
        return self.prefetch_related(main_file, other_files)

    def with_files(self):
        return self.exclude(Q(file__isnull=True) | Q(file=''))

    def files_details_list(self, dataset_id):
        all_resource_files = self.filter(
            status='published',
            dataset_id=dataset_id
        ).with_files().values('file', 'csv_file', 'jsonld_file', 'pk', 'title')
        files_details = []
        for res in all_resource_files:
            res_files = [(res['file'], res['pk'], res['title'])]
            if res['csv_file']:
                res_files.append((res['csv_file'], res['pk'], res['title']))
            if res['jsonld_file']:
                res_files.append((res['jsonld_file'], res['pk'], res['title']))
            files_details.extend(res_files)
        return files_details


class ResourceManager(SoftDeletableManager):
    _queryset_class = SoftDeletableMetadataQuerySet

    def get_queryset(self):
        if is_enabled('S40_new_file_model.be'):
            qs = super(ResourceManager, self).get_queryset().with_prefetched_files()
        else:
            qs = super(ResourceManager, self).get_queryset()
        return qs

    def with_metadata(self):
        return super().get_queryset().with_metadata()

    def with_tabular_data(self, **kwargs):
        return super().get_queryset().with_tabular_data(**kwargs)

    def with_ext_http_links_only(self):
        return super().get_queryset().filter(link__startswith='http://').exclude(
            Q(link__startswith=settings.API_URL) | Q(link__startswith=settings.BASE_URL))

    def by_formats(self, formats):
        return super().get_queryset().by_formats(formats)

    def published(self):
        return super().get_queryset().published()

    def with_files(self):
        return super().get_queryset().with_files()

    def file_details_list(self, dataset_id):
        return super().get_queryset().file_details_list(dataset_id)


class ResourceRawManager(PrefetchResourceFilesMixin, RawManager):
    def get_queryset(self):
        main_file, other_files = self.get_files_prefetch()
        return super().get_queryset().prefetch_related(main_file, other_files)


class ResourceFileManager(Manager):

    def files_details_list(self, dataset_id):
        return self.filter(
            resource__dataset_id=dataset_id,
            resource__status='published', resource__is_removed=False
        ).values_list('file', 'resource_id', 'resource__title')
