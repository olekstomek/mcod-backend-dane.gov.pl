from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.lib.admin_mixins import (
    HistoryMixin,
    ModelAdmin,
    TagAutocompleteMixin,
)
from mcod.tags.forms import TagForm
from mcod.tags.models import Tag


@admin.register(Tag)
class TagAdmin(TagAutocompleteMixin, HistoryMixin, ModelAdmin):
    search_fields = ['name']

    fields = ('name', 'language')
    lang_fields = True
    list_display = ('name', 'language')

    form = TagForm
    readonly_fields = ['language_readonly']

    def language_readonly(self, instance):
        return dict(settings.LANGUAGES)[self._lang_code]
    language_readonly.short_description = _('language')

    def get_form(self, request, obj=None, change=False, **kwargs):
        self._request = request
        self._lang_code = self.lang_code()
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        form.lang_code = self._lang_code
        return form

    def get_fieldsets(self, request, obj=None):
        language_field = 'language'
        if obj is None and self._lang_code is not None:
            language_field = 'language_readonly'

        return [
            (None, {'fields': ('name', language_field)})
        ]

    def lang_code(self):
        lang = self._request.GET.get('lang')
        if lang not in settings.LANGUAGE_CODES:
            lang = None
        return lang

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        if self._lang_code is not None:
            obj.language = self._lang_code
        obj.save()
