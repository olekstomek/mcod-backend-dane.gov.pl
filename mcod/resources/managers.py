from django.apps import apps
from django.conf import settings
from django.db.models import Count, Q, Prefetch
from mcod.core.managers import SoftDeletableQuerySet, SoftDeletableManager


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


class SoftDeletableMetadataQuerySet(SoftDeletableQuerySet):

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
        return self.filter(status='published').annotate(
            resources_count=Count('dataset__resources', filter=res_filter, distinct=True),
            datasets_count=Count('dataset__organization__datasets', filter=dataset_filter, distinct=True),
            organization_resources_count=Count('dataset__organization__datasets__resources',
                                               filter=org_res_filter, distinct=True),
        ).prefetch_related(
            'dataset__organization', prefetch_tags_pl, prefetch_tags_en,
            'dataset__categories').order_by('dataset_id', 'id')


class ResourceManager(SoftDeletableManager):
    _queryset_class = SoftDeletableMetadataQuerySet

    def with_metadata(self):
        return super().get_queryset().with_metadata()

    def with_ext_http_links_only(self):
        return super().get_queryset().filter(link__startswith='http://').exclude(
            Q(link__startswith=settings.API_URL) | Q(link__startswith=settings.BASE_URL))
