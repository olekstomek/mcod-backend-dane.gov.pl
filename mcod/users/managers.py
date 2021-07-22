from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager


class MeetingQuerySet(SoftDeletableQuerySet):

    def published(self):
        return self.filter(status='published')


class MeetingFileQuerySet(SoftDeletableQuerySet):
    pass


class MeetingManager(SoftDeletableManager):
    _queryset_class = MeetingQuerySet

    def published(self):
        return super().get_queryset().published()


class MeetingDeletedManager(DeletedManager):
    _queryset_class = MeetingQuerySet


class MeetingFileManager(SoftDeletableManager):
    _queryset_class = MeetingFileQuerySet


class MeetingFileDeletedManager(DeletedManager):
    _queryset_class = MeetingFileQuerySet
