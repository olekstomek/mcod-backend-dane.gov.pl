from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager, QuerySetMixin


class GuideQuerySet(QuerySetMixin, SoftDeletableQuerySet):

    def published(self):
        return self.filter(status='published')


class GuideManagerMixin(object):
    _queryset_class = GuideQuerySet

    def get_paginated_results(self, **kwargs):
        return super().get_queryset().get_paginated_results(**kwargs)


class GuideManager(GuideManagerMixin, SoftDeletableManager):

    def published(self):
        return super().get_queryset().published()


class GuideDeletedManager(GuideManagerMixin, DeletedManager):
    pass
