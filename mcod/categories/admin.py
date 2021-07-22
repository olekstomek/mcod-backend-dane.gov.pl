from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod.categories.models import Category, CategoryTrash
from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin, MCODAdminMixin
from mcod.unleash import is_enabled


@admin.register(Category)
class CategoryAdmin(LangFieldsOnlyMixin, HistoryMixin, MCODAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {
        "slug": ("title",),
    }

    actions_on_top = True
    list_display = ['title_i18n', 'obj_history']

    first_section_fields = ['title', 'slug', 'description']
    if is_enabled('S19_DCAT_categories.be'):
        list_display.insert(1, 'code')
        first_section_fields.insert(0, 'code')

    fieldsets = [
        (None, {
            'classes': ('suit-tab', 'suit-tab-general',),
            'fields': first_section_fields,
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general',),
            'fields': [
                'image',
            ]
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general',),
            'fields': [
                'status',
            ]
        }),
    ]

    def get_fieldsets(self, request, obj=None):
        return self.get_translations_fieldsets() + self.fieldsets

    suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_translations_tabs()
    )


@admin.register(CategoryTrash)
class CategoryTrashAdmin(TrashMixin):
    pass
