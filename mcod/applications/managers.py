from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager


class ApplicationProposalQuerySet(SoftDeletableQuerySet):

    def with_decision(self):
        return self.exclude(decision='')

    def without_decision(self):
        return self.filter(decision='')


class ApplicationProposalMixin(object):

    def with_decision(self):
        return super().get_queryset().with_decision()

    def without_decision(self):
        return super().get_queryset().without_decision()


class ApplicationProposalManager(ApplicationProposalMixin, SoftDeletableManager):
    _queryset_class = ApplicationProposalQuerySet


class ApplicationProposalDeletedManager(ApplicationProposalMixin, DeletedManager):
    _queryset_class = ApplicationProposalQuerySet
