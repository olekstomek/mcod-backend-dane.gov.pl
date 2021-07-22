from django.conf import settings
from mcod.discourse import tasks as t


def sync_user(sender, user, created=False, **kwargs):
    if settings.DISCOURSE_FORUM_ENABLED:
        t.user_sync_task.s(user.id, created=created).apply_async()


def user_logout(signal, request, user, **kwargs):
    if settings.DISCOURSE_FORUM_ENABLED:
        t.user_logout_task.s(user.id).apply_async()
