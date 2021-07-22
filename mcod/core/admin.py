from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import Group
from django.utils.translation import gettext


admin.site.unregister(Group)


class MCODChangeList(ChangeList):

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        if hasattr(self.model, 'accusative_case'):
            if self.is_popup:
                title = gettext('Select %s')
            elif self.model_admin.has_change_permission(request):
                title = gettext('Select %s to change')
            else:
                title = gettext('Select %s to view')
            self.title = title % self.model.accusative_case()


class MCODTrashChangeList(ChangeList):

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.title = self.model._meta.verbose_name_plural.capitalize()
