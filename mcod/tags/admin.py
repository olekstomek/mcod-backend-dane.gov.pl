from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.lib.admin_mixins import TagAutocompleteMixin, LangFieldsOnlyMixin, MCODAdminMixin
from mcod.tags.forms import TagForm
from mcod.tags.models import Tag
from mcod.unleash import is_enabled


@admin.register(Tag)
class TagAdmin(TagAutocompleteMixin, LangFieldsOnlyMixin, MCODAdminMixin, admin.ModelAdmin):
    search_fields = ['name']

    if is_enabled('S18_new_tags.be'):
        fields = ('name', 'language')
        list_display = ('name', 'language')
    else:
        fields = ('name', 'name_en')

    form = TagForm
    readonly_fields = ['language_readonly']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_enabled('S18_new_tags.be'):
            qs = qs.exclude(language='')
        else:
            qs = qs.filter(language='')
        return qs

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
        if is_enabled('S18_new_tags.be'):
            language_field = 'language'
            if obj is None and self._lang_code is not None:
                language_field = 'language_readonly'

            fieldsets = [
                (None, {'fields': ('name', language_field)})
            ]
        else:
            fieldsets = super().get_fieldsets(request, obj)

        return fieldsets

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
