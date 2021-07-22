from functools import partial
from django.db.models import Count, Q
from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager


class SoftDeletableMetadataQuerySet(SoftDeletableQuerySet):

    def with_metadata(self):
        res_filter = partial(
            Q,
            ('dataset__resources__status', 'published'),
            ('dataset__resources__is_removed', False),
        )
        dataset_filter = partial(
            Q,
            ('dataset__organization__datasets__status', 'published'),
            ('dataset__organization__datasets__is_removed', False),
        )
        return self.filter(status='published').annotate(
            resources_count=Count('dataset__resources', filter=res_filter(), distinct=True),
            datasets_count=Count('dataset__organization__datasets', filter=dataset_filter(), distinct=True)
        ).prefetch_related(
            'dataset__organization', 'dataset__tags',
            'dataset__categories').order_by('dataset_id', 'id')


class ResourceManager(SoftDeletableManager):

    _queryset_class = SoftDeletableMetadataQuerySet

    def with_metadata(self):
        return super().get_queryset().with_metadata()
