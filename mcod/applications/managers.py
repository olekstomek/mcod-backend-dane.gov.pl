from mcod.core.db.managers import TrashManager
from mcod.core.managers import SoftDeletableManager, SoftDeletableQuerySet, TrashQuerySet


class ApplicationProposalQuerySetMixin:
    def with_decision(self):
        return self.exclude(decision='')

    def without_decision(self):
        return self.filter(decision='')


class ApplicationProposalQuerySet(ApplicationProposalQuerySetMixin, SoftDeletableQuerySet):
    pass


class ApplicationProposalTrashQuerySet(ApplicationProposalQuerySetMixin, TrashQuerySet):
    pass


class ApplicationProposalManagerMixin:
    def with_decision(self):
        return super().get_queryset().with_decision()

    def without_decision(self):
        return super().get_queryset().without_decision()


class ApplicationProposalManager(ApplicationProposalManagerMixin, SoftDeletableManager):
    _queryset_class = ApplicationProposalQuerySet


class ApplicationProposalTrashManager(ApplicationProposalManagerMixin, TrashManager):
    _queryset_class = ApplicationProposalTrashQuerySet
