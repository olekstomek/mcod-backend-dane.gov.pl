from model_utils.managers import SoftDeletableManager

from mcod.core.db.managers import DeletedManager, DecisionSortableMixin, DecisionSortableSoftDeletableQuerySet


class AcceptedDatasetSubmissionMixin(object):

    def active(self):
        return super().get_queryset().active()

    def inactive(self):
        return super().get_queryset().inactive()


class AcceptedDatasetSubmissionQuerySet(DecisionSortableSoftDeletableQuerySet):

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class DatasetCommentManager(DecisionSortableMixin, SoftDeletableManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet


class DatasetCommentDeletedManager(DecisionSortableMixin, DeletedManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet


class DatasetSubmissionManager(DecisionSortableMixin, SoftDeletableManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet


class AcceptedDatasetSubmissionManager(AcceptedDatasetSubmissionMixin, DatasetSubmissionManager):
    _queryset_class = AcceptedDatasetSubmissionQuerySet


class DatasetSubmissionDeletedManager(DecisionSortableMixin, DeletedManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet


class AcceptedDatasetSubmissionDeletedManager(AcceptedDatasetSubmissionMixin, DatasetSubmissionDeletedManager):
    _queryset_class = AcceptedDatasetSubmissionQuerySet


class ResourceCommentManager(DecisionSortableMixin, SoftDeletableManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet


class ResourceCommentDeletedManager(DecisionSortableMixin, DeletedManager):
    _queryset_class = DecisionSortableSoftDeletableQuerySet
