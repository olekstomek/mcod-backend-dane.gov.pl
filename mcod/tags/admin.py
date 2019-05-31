from django.contrib import admin

from mcod.lib.admin_mixins import LangFieldsOnlyMixin
from mcod.tags.forms import TagForm
from mcod.tags.models import Tag


# Register your models here.


@admin.register(Tag)
class TagAdmin(LangFieldsOnlyMixin, admin.ModelAdmin):
    search_fields = ['name']
    fields = ('name', 'name_en')
    form = TagForm

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.save()
