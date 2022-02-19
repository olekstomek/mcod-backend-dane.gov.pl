import nested_admin
from django.contrib import admin
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rules.contrib.admin import ObjectPermissionsStackedInline

from mcod.datasets.forms import DatasetForm, DatasetStackedNoSaveForm
from mcod.datasets.models import Dataset
from mcod.lib.admin_mixins import (
    AdminListMixin,
    DynamicAdminListDisplayMixin,
    HistoryMixin,
    LangFieldsOnlyMixin,
    MCODAdminMixin,
    NestedModelAdmin,
    ObjectPermissionsModelAdmin,
    StatusLabelAdminMixin,
    TrashMixin,
)
from mcod.organizations.forms import OrganizationForm
from mcod.organizations.models import Organization, OrganizationTrash
from mcod.organizations.views import OrganizationAutocompleteJsonView
from mcod.unleash import is_enabled
from mcod.users.forms import FilteredSelectMultipleCustom
from mcod.users.models import User


class ChangeDatasetStacked(AdminListMixin, nested_admin.NestedStackedInline, ObjectPermissionsStackedInline):
    template = 'admin/datasets/inline-list.html'

    fields = [
        '_title',
        'modified',
        'organization',
        'categories_list',
    ]
    readonly_fields = fields
    sortable = 'modified'
    max_num = 0
    min_num = 0
    extra = 3
    suit_classes = 'suit-tab suit-tab-datasets'

    model = Dataset
    form = DatasetStackedNoSaveForm

    def categories_list(self, instance):
        return instance.categories_list_as_html if instance.pk else '-'
    categories_list.short_description = _('Categories')

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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def _get_form_for_get_fields(self, request, obj=None):
        return self.get_formset(request, obj, fields=None).form

    def _title(self, obj):
        return obj.mark_safe('<a href="{}">{}</a>'.format(obj.admin_change_url, obj.title))
    _title.short_description = _('title')


class AddDatasetStacked(AdminListMixin, nested_admin.NestedStackedInline, ObjectPermissionsStackedInline):
    template = 'admin/datasets/inline-new.html'
    show_change_link = False
    prepopulated_fields = {"slug": ("title",)}
    model = Dataset
    extra = 0
    form = DatasetForm
    suit_classes = 'suit-tab suit-tab-datasets'
    has_dynamic_data = ['has_dynamic_data'] if is_enabled('S43_dynamic_data.be') else []
    has_high_value_data = ['has_high_value_data'] if is_enabled('S41_resource_has_high_value_data.be') else []
    fields = (
        'title',
        'notes',
        'url',
        'image',
        'customfields',
        'update_frequency',
        'categories',
        'status',
        'tags_pl',
        'tags_en',
        'license_condition_source',
        'license_condition_modification',
        'license_condition_responsibilities',
        'license_condition_db_or_copyrighted',
        'license_chosen',
        'license_condition_personal_data',
        *has_dynamic_data,
        *has_high_value_data,
    )
    autocomplete_fields = ['tags', ]

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.recreate_tags_widgets(request=request, db_field=Dataset.tags.field, admin_site=self.admin_site)
        return formset

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        formfield = super().formfield_for_manytomany(db_field, request, **kwargs)

        if db_field.name == "categories":
            attrs = {
                'data-from-box-label': _('Available categories'),
                'data-to-box-label': _('Selected categories'),
            }
            formfield.widget = admin.widgets.RelatedFieldWidgetWrapper(
                FilteredSelectMultipleCustom(formfield.label.lower(), False, attrs=attrs),
                db_field.remote_field,
                self.admin_site,
                can_add_related=False,
            )
        return formfield


class UserInline(nested_admin.NestedStackedInline):
    model = User.organizations.through
    extra = 1
    suit_classes = 'suit-tab suit-tab-users'


@admin.register(Organization)
class OrganizationAdmin(DynamicAdminListDisplayMixin, StatusLabelAdminMixin, HistoryMixin, LangFieldsOnlyMixin,
                        MCODAdminMixin, NestedModelAdmin, ObjectPermissionsModelAdmin):
    actions_on_top = True
    export_to_csv = True
    form = OrganizationForm
    inlines = [
        ChangeDatasetStacked,
        AddDatasetStacked,
    ]
    list_display = ["title", "get_photo", "short_description", "status", 'obj_history']
    list_filter = ["status"]
    prepopulated_fields = {"slug": ("title",), }
    search_fields = ["slug", "title", "description"]
    soft_delete = True
    suit_form_tabs = tuple()

    def autocomplete_view(self, request):
        return OrganizationAutocompleteJsonView.as_view(model_admin=self)(request)

    def get_photo(self, obj):
        if obj.image:
            html = """<a href="{product_url}" target="_blank">
            <img src="{photo_url}" alt="{photo_alt}" width="100" />
            </a>""".format(**{
                "product_url": obj.admin_change_url,
                "photo_url": obj.image_absolute_url,
                "photo_alt": f'Logo instytucji: {obj.title}'
            })
            return obj.mark_safe(html)
        return ''

    get_photo.short_description = _("Logo")

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        form = super().get_form(request, obj, **kwargs)
        return form

    @property
    def suit_form_tabs(self):
        suit_form_tabs = [
            ('general', _('General')),
            *LangFieldsOnlyMixin.get_translations_tabs(),
            ('contact', _('Contact')),
        ]
        if self._request.user.is_superuser:
            suit_form_tabs += [('users', _('Users'))]
        suit_form_tabs += [('datasets', _('Datasets'))]
        return suit_form_tabs

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.id:
                instance.created_by = request.user
                instance.modified_by = request.user
        super().save_formset(request, form, formset, change)

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
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user__id__in=[request.user.id])

    def get_fieldsets(self, request, obj=None):
        superuser_general_fields = (
            "institution_type",
            "title",
            "slug",
            "abbreviation",
            "status",
            "description",
            "image",
        )
        general_fields = (
            "institution_type",
            "title",
            "slug",
            "abbreviation",
            "status",
            "description_html",
            "image",
        )
        general_tab = (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': superuser_general_fields if request.user.is_superuser else general_fields,
            }
        )
        superuser_contact_fields = (
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
        contact_fields = (
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
        contact_tab = (
            _('Contact details'),
            {
                'classes': ('suit-tab', 'suit-tab-contact',),
                'fields': superuser_contact_fields if request.user.is_superuser else contact_fields,
            }
        )
        users_tab = (
            _('Users'),
            {
                'classes': ('suit-tab', 'suit-tab-users',),
                'fields': (
                    'users',
                )
            }
        )
        general_tab2 = (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': (
                    "epuap",
                    "regon",
                    "website",
                )
            }
        )
        fieldsets = [general_tab, contact_tab, users_tab, general_tab2]

        return fieldsets + self.get_translations_fieldsets()

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return [
                "institution_type",
                "title",
                "slug",
                "abbreviation",
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
        return super().get_readonly_fields(request, obj=obj)

    def get_prepopulated_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return {}
        return self.prepopulated_fields


@admin.register(OrganizationTrash)
class OrganizationTrashAdmin(HistoryMixin, TrashMixin):
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
