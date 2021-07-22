from django.contrib import admin
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from suit.admin import SortableStackedInline

from mcod.guides.forms import GuideForm, GuideItemForm
from mcod.guides.models import Guide, GuideItem, GuideTrash
from mcod.lib.admin_mixins import (
    ActionsMixin, CRUDMessageMixin, HistoryMixin,
    SoftDeleteMixin, TrashMixin, CreatedByDisplayAdminMixin,
    StatusLabelAdminMixin, DynamicAdminListDisplayMixin, MCODAdminMixin
)


class GuideAdminMixin(DynamicAdminListDisplayMixin, CreatedByDisplayAdminMixin,
                      StatusLabelAdminMixin, ActionsMixin, CRUDMessageMixin):
    is_history_other = True
    form = GuideForm
    search_fields = ['title']
    list_display = ('title', 'created_by', '_created', '_status')
    delete_selected_msg = _('Delete selected elements')

    def _created(self, obj):
        return obj.created_localized if obj.pk else '-'

    _created.short_description = _('creation date')
    _created.admin_order_field = 'created'

    def _created_by(self, obj):
        return obj.created_by if obj.pk else '-'

    _created_by.short_description = pgettext_lazy('masculine', 'created by')
    _created_by.admin_order_field = 'created_by'

    def _status(self, obj):
        return obj.STATUS[obj.status]

    _status.short_description = 'status'
    _status.admin_order_field = 'status'

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        return super().save_model(request, obj, form, change)


class GuideItemInline(SortableStackedInline):
    form = GuideItemForm
    fields = ['title_pl', 'title_en', 'content_pl', 'content_en', 'route', 'css_selector', 'position', 'is_optional',
              'is_clickable', 'is_expandable']
    min_num = 1
    model = GuideItem
    sortable = 'order'
    template = 'admin/guides/guide_item/stacked.html'
    extra = 0
    verbose_name = _('communique')
    verbose_name_plural = ''

    def get_formset(self, request, obj=None, **kwargs):
        # https://stackoverflow.com/questions/1206903/how-do-i-require-an-inline-in-the-django-admin/53868121#53868121
        formset = super().get_formset(request, obj=obj, **kwargs)
        formset.validate_min = True
        return formset


class GuideAdmin(GuideAdminMixin, HistoryMixin, SoftDeleteMixin, MCODAdminMixin, admin.ModelAdmin):
    fieldsets = [
        (
            None, {
                'classes': ('suit-tab', 'suit-tab-course', ),
                'fields': (
                    ('title_pl', 'title_en', 'status', '_created_by', '_created', ),
                )
            },
        ),
    ]
    inlines = (GuideItemInline, )
    suit_form_tabs = (
        ('course', _('General')),
    )
    readonly_fields = ('_created', '_created_by', )
    suit_form_includes = (
        ('admin/guides/guide/tourpicker_button.html', 'middle', 'course'),
    )


class GuideTrashAdmin(GuideAdminMixin, HistoryMixin, TrashMixin):

    readonly_fields = (
        'title_pl',
        'title_en',
        'status',
        '_created_by',
        '_created',
    )
    fields = (
        'title_pl',
        'title_en',
        'status',
        '_created_by',
        '_created',
        'is_removed',
    )


admin.site.register(Guide, GuideAdmin)
admin.site.register(GuideTrash, GuideTrashAdmin)
