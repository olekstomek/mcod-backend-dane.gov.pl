from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager


class SpecialSignQuerySet(SoftDeletableQuerySet):

    def published(self):
        return self.filter(status='published')


class SpecialSignManagerMixin(object):
    _queryset_class = SpecialSignQuerySet

    def published(self):
        return super().get_queryset().published()


class SpecialSignManager(SpecialSignManagerMixin, SoftDeletableManager):
    pass


class SpecialSignDeletedManager(SpecialSignManagerMixin, DeletedManager):
    pass
