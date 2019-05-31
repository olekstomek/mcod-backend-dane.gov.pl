from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, AdminPasswordChangeForm

from mcod.reports.admin import ExportCsvMixin
from mcod.lib.admin_mixins import HistoryMixin
from mcod.users.models import User
from mcod.users.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
import copy


# admin.site.disable_action('delete_selected')


@admin.register(User)
class UserAdmin(HistoryMixin, ExportCsvMixin, UserAdmin):
    actions_on_top = True
    list_display = ["email", "fullname", "state", "last_login", "is_staff", "is_superuser"]

    fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "email",
                    "password",
                ]
            }

        ),
        (
            _("Personal info"),
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "fullname",
                    ("phone", "phone_internal"),
                ]
            }

        ),
        (
            _("Permisions"),
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "is_staff",
                    "is_superuser",
                    "state",
                ]
            }

        ),
        (
            _("Organizations"),
            {
                'classes': ('suit-tab', 'suit-tab-organizations',),
                'fields': ("organizations",)
            }

        )
    ]

    add_fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "email",
                    "password1",
                    "password2"
                ]
            }

        ),
        (
            _("Personal info"),
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "fullname",
                    ("phone", "phone_internal"),
                ]
            }

        ),
        (
            _("Permisions"),
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': [
                    "is_staff",
                    "is_superuser",
                    "state",
                ]
            }

        ),
        (
            _("Organizations"),
            {
                'classes': ('suit-tab', 'suit-tab-organizations',),
                'fields': ("organizations",)
            }

        )
    ]

    ordering = ('email',)
    search_fields = ["email", "fullname"]
    list_filter = ["state", "is_staff", "is_superuser"]

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    suit_form_tabs = (
        ('general', _('General')),
        ('organizations', _('Institutions')),
    )

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        form = super(UserAdmin, self).get_form(request, obj, **kwargs)
        form.declared_fields['phone'].required = form.base_fields['fullname'].required = request.user.is_normal_staff
        return form

    @property
    def suit_form_tabs(self):
        tabs = [
            ('general', _('General')),
        ]
        if self._request.user.is_superuser:
            tabs += [('organizations', _('Institutions'))]
        return tabs

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super(UserAdmin, self).get_fieldsets(request, obj))
        if not request.user.is_superuser:
            fieldsets[2] = (None, {'fields': []})
        return fieldsets

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request).exclude(is_removed=True)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    # def has_delete_permission(self, request, obj=None):
    #     return False
