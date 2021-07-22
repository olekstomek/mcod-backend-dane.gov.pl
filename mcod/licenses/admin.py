from django.contrib import admin
from mcod.licenses.models import License
from mcod.lib.admin_mixins import MCODAdminMixin


@admin.register(License)
class LicenseAdmin(MCODAdminMixin, admin.ModelAdmin):
    search_fields = ['title']
