from mcod.core.db.managers import TrashManager
from mcod.core.managers import SoftDeletableManager, SoftDeletableQuerySet, TrashQuerySet


class MeetingQuerySetMixin:
    def published(self):
        return self.filter(status="published")


class MeetingQuerySet(MeetingQuerySetMixin, SoftDeletableQuerySet):
    pass


class MeetingTrashQuerySet(MeetingQuerySetMixin, TrashQuerySet):
    pass


class MeetingManager(SoftDeletableManager):
    _queryset_class = MeetingQuerySet

    def published(self):
        return super().get_queryset().published()


class MeetingTrashManager(TrashManager):
    _queryset_class = MeetingTrashQuerySet


class MeetingFileManager(SoftDeletableManager):
    _queryset_class = SoftDeletableQuerySet

    def filter_by_path(self, file_path):
        normalized_path = file_path[9:] if file_path.startswith("meetings/") else file_path
        return self.filter(file=normalized_path).select_related("meeting").first()


class MeetingFileTrashManager(TrashManager):
    _queryset_class = TrashQuerySet
