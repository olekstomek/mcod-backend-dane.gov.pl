from django.contrib import admin
from mcod.licenses.models import License


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    search_fields = ['title']
