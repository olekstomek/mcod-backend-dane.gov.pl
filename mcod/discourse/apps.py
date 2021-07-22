from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.signals import user_logged_out
from mcod.users.signals import user_changed


class DiscourseConfig(AppConfig):
    name = 'mcod.discourse'
    verbose_name = _('Discourse Integration')

    def ready(self):
        from mcod.discourse.signals import sync_user, user_logout
        user_changed.connect(sync_user)
        user_logged_out.connect(user_logout)
