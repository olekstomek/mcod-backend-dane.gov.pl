from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mcod.academy.forms import CourseAdminForm, CourseModuleAdminFormSet, CourseModuleInlineAdminForm
from mcod.academy.models import Course, CourseModule, CourseTrash
from mcod.lib.admin_mixins import ActionsMixin, HistoryMixin, SoftDeleteMixin, TrashMixin, MCODAdminMixin


class CourseModuleInline(admin.TabularInline):
    form = CourseModuleInlineAdminForm
    formset = CourseModuleAdminFormSet
    model = CourseModule
    min_num = 1
    extra = 0
    verbose_name_plural = _('Sessions')
    suit_classes = 'suit-tab suit-tab-course'
    suit_form_inlines_hide_original = True
    ordering = ('start', )

    def get_formset(self, request, obj=None, **kwargs):
        # https://stackoverflow.com/questions/1206903/how-do-i-require-an-inline-in-the-django-admin/53868121#53868121
        formset = super().get_formset(request, obj=None, **kwargs)
        formset.validate_min = True
        return formset


class CourseAdminMixin(ActionsMixin):
    is_history_other = True
    search_fields = ['title']
    list_display = ('_title', 'participants_number', '_modules_count', '_venue', '_start', '_end')
    delete_selected_msg = _('Delete selected courses')

    def _end(self, obj):
        return obj._end
    _end.short_description = _('End date')
    _end.admin_order_field = '_end'

    def _modules_count(self, obj):
        return obj._modules_count
    _modules_count.short_description = _('Number of sessions')
    _modules_count.admin_order_field = '_modules_count'

    def _start(self, obj):
        return obj._start
    _start.short_description = _('Start date')
    _start.admin_order_field = '_start'

    def _course_state(self, obj):
        return obj.COURSE_STATES.get(obj._course_state, '-')
    _course_state.short_description = _('State')
    _course_state.admin_order_field = '_course_state'

    def _title(self, obj):
        return obj.title
    _title.short_description = _('Title of course')
    _title.admin_order_field = 'title'

    def _venue(self, obj):
        return obj.venue
    _venue.short_description = _('Course venue')
    _venue.admin_order_field = 'venue'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.with_schedule()


class CourseAdmin(CourseAdminMixin, HistoryMixin, SoftDeleteMixin, MCODAdminMixin, admin.ModelAdmin):

    actions_on_top = True
    fieldsets = [
        (
            None, {
                'classes': ('suit-tab', 'suit-tab-course', ),
                'fields': (
                    'title',
                    'participants_number',
                    'venue',
                    'notes',
                    'file',
                    'materials_file',
                    'status',
                )
            },
        ),
    ]
    form = CourseAdminForm
    inlines = (CourseModuleInline, )
    suit_form_tabs = (
        ('course', _('General')),
    )
    list_filter = [
        'status',
    ]


class CourseTrashAdmin(CourseAdminMixin, HistoryMixin, TrashMixin):

    readonly_fields = (
        'title',
        'participants_number',
        'venue',
        'notes',
        'file',
        'materials_file',
        'status',
    )
    fields = [field for field in readonly_fields] + ['is_removed']


admin.site.register(Course, CourseAdmin)
admin.site.register(CourseTrash, CourseTrashAdmin)
