from django.core.paginator import Paginator
from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager


class OrganizationQuerySet(SoftDeletableQuerySet):

    def get_filtered_results(self, **kwargs):
        query = {}
        if 'agents__isnull' in kwargs:
            query['agents__isnull'] = kwargs['agents__isnull']
        if 'agents__id' in kwargs:
            query['agents__id'] = kwargs['agents__id']
        return self.filter(**query).order_by('title')

    def _get_page(self, queryset, page=1, per_page=20, **kwargs):
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(page)

    def get_page(self, **kwargs):
        return self._get_page(self.filter(), **kwargs)

    def get_paginated_results(self, **kwargs):
        qs = self.get_filtered_results(**kwargs)
        return self._get_page(qs, **kwargs)

    def private(self, **kwargs):
        return self.filter(institution_type=self.model.INSTITUTION_TYPE_PRIVATE)

    def public(self, **kwargs):
        return self.exclude(institution_type=self.model.INSTITUTION_TYPE_PRIVATE)


class OrganizationManagerMixin(object):
    _queryset_class = OrganizationQuerySet

    def get_paginated_results(self, **kwargs):
        return super().get_queryset().get_paginated_results(**kwargs)

    def get_page(self, **kwargs):
        return super().get_queryset().get_page(**kwargs)

    def private(self, **kwargs):
        return super().get_queryset().private(**kwargs)

    def public(self, **kwargs):
        return super().get_queryset().public(**kwargs)


class OrganizationManager(OrganizationManagerMixin, SoftDeletableManager):
    pass


class OrganizationDeletedManager(OrganizationManagerMixin, DeletedManager):
    pass
