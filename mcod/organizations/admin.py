import nested_admin
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rules.contrib.admin import ObjectPermissionsModelAdmin, ObjectPermissionsStackedInline

from mcod.datasets.forms import AddDatasetForm, DatasetListForm
from mcod.datasets.models import Dataset
from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin
from mcod.organizations.forms import OrganizationForm
from mcod.organizations.models import Organization, OrganizationTrash
from mcod.reports.admin import ExportCsvMixin
from mcod.users.models import User

task_status_to_css_class = {
    'SUCCESS': 'fas fa-check-circle text-success',
    'PENDING': 'fas fa-question-circle text-warning',
    'FAILURE': 'fas fa-times-circle text-error',
    None: 'fas fa-minus-circle text-light'
}


class ChangeDatasetStacked(nested_admin.NestedStackedInline, ObjectPermissionsStackedInline):
    template = 'admin/datasets/inline-list.html'
    show_change_link = True

    fields = (
        "title",
        "modified",
        'organization',
        'category',
    )

    sortable = 'modified'

    readonly_fields = (
        "title",
        "modified",
        'organization',
        'category',
    )
    max_num = 0
    min_num = 0
    extra = 3
    suit_classes = 'suit-tab suit-tab-datasets'

    model = Dataset
    form = DatasetListForm

    def _format_list_status(self, val):
        return format_html('<i class="%s"></i>' % task_status_to_css_class[val])

    def link_status(self, obj):
        return self._format_list_status(obj._link_status)

    link_status.admin_order_field = '_link_status'
    link_status.short_description = format_html('<i class="fas fa-link"></i>')

    def file_status(self, obj):
        return self._format_list_status(obj._file_status)

    file_status.admin_order_field = '_file_status'
    file_status.short_description = format_html('<i class="fas fa-file"></i>')

    def data_status(self, obj):
        return self._format_list_status(obj._data_status)

    data_status.admin_order_field = '_data_status'
    data_status.short_description = format_html('<i class="fas fa-table"></i>')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(is_removed=True)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def _get_form_for_get_fields(self, request, obj=None):
        return self.get_formset(request, obj, fields=None).form

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }


class AddDatasetStacked(nested_admin.NestedStackedInline, ObjectPermissionsStackedInline):
    template = 'admin/datasets/inline-new.html'
    show_change_link = False
    prepopulated_fields = {"slug": ("title",)}
    model = Dataset
    form = AddDatasetForm
    suit_classes = 'suit-tab suit-tab-datasets'
    fields = ('title', 'notes', 'url', 'customfields', 'update_frequency', 'category', 'status', "tags",
              "license_condition_source",
              "license_condition_modification",
              "license_condition_responsibilities",
              "license_condition_db_or_copyrighted"
              )
    autocomplete_fields = ['tags', ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.none()

    extra = 0

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }


class UserInline(nested_admin.NestedStackedInline):
    model = User.organizations.through
    extra = 1
    suit_classes = 'suit-tab suit-tab-users'


@admin.register(Organization)
class OrganizationAdmin(HistoryMixin, ExportCsvMixin, LangFieldsOnlyMixin,
                        nested_admin.NestedModelAdmin, ObjectPermissionsModelAdmin):
    actions_on_top = True
    prepopulated_fields = {"slug": ("title",), }
    list_display = ["title", "get_photo", "short_description", "status", 'obj_history']
    list_filter = ["status"]
    search_fields = ["slug", "title", "description"]

    inlines = [
        ChangeDatasetStacked,
        AddDatasetStacked,
    ]

    form = OrganizationForm
    suit_form_tabs = tuple()

    def get_photo(self, obj):
        if obj.image:
            html = """<a href="{product_url}" target="_blank">
            <img src="{photo_url}" alt="" width="100" />
            </a>""".format(**{
                "product_url": obj.get_url_path(),
                "photo_url": obj.image.url,
            })
            return mark_safe(html)
        else:
            return ""

    get_photo.short_description = _("Logo")

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        form = super().get_form(request, obj, **kwargs)
        return form

    @property
    def suit_form_tabs(self):
        suit_form_tabs = [
            ('general', _('General')),
            *LangFieldsOnlyMixin.get_traslations_tabs(),
            ('contact', _('Contact')),
        ]
        if self._request.user.is_superuser:
            suit_form_tabs += [('users', _('Users'))]
        suit_form_tabs += [('datasets', _('Datasets'))]
        return suit_form_tabs

    def save_model(self, request, obj, form, change):
        if 'slug' in form.cleaned_data:
            if form.cleaned_data['slug'] == "":
                obj.slug = slugify(form.cleaned_data['title'])
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.save()

    def get_queryset(self, request):
        self.request = request
        qs = super(OrganizationAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user__id__in=[request.user.id])

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': (
                        "institution_type",
                        "title",
                        "slug",
                        "status",
                        "description",
                        "image",
                    )
                }
            ),
            (
                _('Contact details'),
                {
                    'classes': ('suit-tab', 'suit-tab-contact',),
                    'fields': (
                        "postal_code",
                        "city",
                        "street_type",
                        "street",
                        "street_number",
                        "flat_number",
                        "email",
                        ("tel", "tel_internal"),
                        ("fax", "fax_internal"),
                    )
                }
            ),
            (
                _('Users'),
                {
                    'classes': ('suit-tab', 'suit-tab-users',),
                    'fields': (
                        'users',
                    )
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': (
                        "epuap",
                        "regon",
                        "website",

                    )
                }
            ),

        ]
        if not request.user.is_superuser:
            fieldsets = [
                (
                    None,
                    {
                        'classes': ('suit-tab', 'suit-tab-general',),
                        'fields': (
                            "institution_type",
                            "title",
                            "slug",
                            "status",
                            "description_html",
                            "image",
                        )
                    }
                ),
                (
                    _('Contact details'),
                    {
                        'classes': ('suit-tab', 'suit-tab-contact',),
                        'fields': (
                            "postal_code",
                            "city",
                            "street_type",
                            "street",
                            "street_number",
                            "flat_number",
                            "email",
                            "tel",
                            "fax",
                        )
                    }
                ),
                (
                    _('Users'),
                    {
                        'classes': ('suit-tab', 'suit-tab-users',),
                        'fields': (
                            'users',
                        )
                    }
                ),
                (
                    None,
                    {
                        'classes': ('suit-tab', 'suit-tab-general',),
                        'fields': (
                            "epuap",
                            "regon",
                            "website",

                        )
                    }
                ),

            ]

        return fieldsets + self.get_translations_fieldsets()

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:

            readonly_fields = [
                "institution_type",
                "title",
                "slug",
                "status",
                "description_html",
                "image",
                "postal_code",
                "city",
                "street_type",
                "street",
                "street_number",
                "flat_number",
                "email",
                "tel",
                "fax",
                "epuap",
                "regon",
                "website",
            ]
            return readonly_fields
        else:
            return super(OrganizationAdmin, self).get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return {}
        return self.prepopulated_fields


@admin.register(OrganizationTrash)
class OrganizationTrashAdmin(TrashMixin):
    search_fields = ['title', "city"]
    list_display = ['title', 'city']
    fields = [
        "institution_type",
        "title",
        "slug",
        "status",
        "description_html",
        "image",
        "postal_code",
        "city",
        "street_type",
        "street",
        "street_number",
        "flat_number",
        "email",
        "tel",
        "fax",
        "epuap",
        "regon",
        "website",
        "is_removed"
    ]
    readonly_fields = [
        "institution_type",
        "title",
        "slug",
        "status",
        "description_html",
        "image",
        "postal_code",
        "city",
        "street_type",
        "street",
        "street_number",
        "flat_number",
        "email",
        "tel",
        "fax",
        "epuap",
        "regon",
        "website",
    ]
