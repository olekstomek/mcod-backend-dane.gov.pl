from django.core.paginator import Paginator
from django.db import models
from model_utils.managers import SoftDeletableQuerySet


class QuerySetMixin(object):

    def get_filtered_results(self, **kwargs):
        return self.filter()

    def _get_page(self, queryset, page=1, per_page=20, **kwargs):
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(page)

    def get_paginated_results(self, **kwargs):
        qs = self.get_filtered_results(**kwargs)
        return self._get_page(qs, **kwargs)


class DecisionSortableMixin(object):

    def with_decision(self):
        return super().get_queryset().with_decision()

    def without_decision(self):
        return super().get_queryset().without_decision()


class DecisionSortableSoftDeletableQuerySet(SoftDeletableQuerySet):

    def with_decision(self):
        return self.exclude(decision='')

    def without_decision(self):
        return self.filter(decision='')


class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_removed=True)
