from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod.categories.models import Category, CategoryTrash
from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin


@admin.register(Category)
class CategoryAdmin(LangFieldsOnlyMixin, HistoryMixin, admin.ModelAdmin):
    prepopulated_fields = {
        "slug": ("title",),
    }

    actions_on_top = True
    list_display = ['title_i18n', 'obj_history']

    fieldsets = [
        (None, {
            'classes': ('suit-tab', 'suit-tab-general',),
            'fields': [
                'title', 'slug', 'description'
            ]
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
        *LangFieldsOnlyMixin.get_traslations_tabs()
    )


@admin.register(CategoryTrash)
class CategoryTrashAdmin(TrashMixin):
    pass
