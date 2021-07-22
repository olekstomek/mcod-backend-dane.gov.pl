from django.db.models import Case, CharField, Count, Max, Min, Q, When, Value
from django.utils import timezone
from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager

from mcod.core.db.managers import DeletedManager


class CourseQuerySet(SoftDeletableQuerySet):

    def published(self):
        return self.filter(status='published')

    def with_schedule(self):
        today = timezone.now().date()
        return self.annotate(
            _start=Min('modules__start', filter=Q(modules__is_removed=False)),
            _end=Max('modules__end', filter=Q(modules__is_removed=False)),
            _modules_count=Count('modules', filter=Q(modules__is_removed=False)),
            _course_state=Case(
                When(_start__lte=today, _end__gte=today, then=Value('current')),
                When(_start__gt=today, then=Value('planned')),
                When(_end__lt=today, then=Value('finished')),
                default=Value(''),
                output_field=CharField(),
            )
        )


class CourseManager(SoftDeletableManager):
    _queryset_class = CourseQuerySet

    def published(self):
        return super().get_queryset().published()

    def with_schedule(self):
        return super().get_queryset().with_schedule()


class CourseDeletedManager(DeletedManager):
    _queryset_class = CourseQuerySet

    def with_schedule(self):
        return super().get_queryset().with_schedule()
