from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod.categories.models import Category, CategoryTrash
from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin, MCODAdminMixin


@admin.register(Category)
class CategoryAdmin(LangFieldsOnlyMixin, HistoryMixin, MCODAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {
        "slug": ("title",),
    }
    is_history_with_unknown_user_rows = True
    actions_on_top = True
    list_display = ['title_i18n', 'code', 'obj_history']

    first_section_fields = ['code', 'title', 'slug', 'description']

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
class CategoryTrashAdmin(HistoryMixin, TrashMixin):
    is_history_with_unknown_user_rows = True
    readonly_fields = (
        'code',
        'title',
        'description',
        'image',
        'status',
    )
    fields = [field for field in readonly_fields] + ['is_removed']
