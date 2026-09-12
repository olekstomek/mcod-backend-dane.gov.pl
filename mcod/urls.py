from django.conf.urls import include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.views.generic.base import TemplateView

from mcod.core.admin_metrics_view import prometheus_metrics_view
from mcod.datasets.views import ConditionLabelsAdminView, DatasetAutocompleteView
from mcod.organizations.views import InstitutionTypeAdminView, OrganizationAutocompleteView
from mcod.regions.views import RegionsAutocompleteView
from mcod.resources.views import ResourceAutocompleteView
from mcod.urls_all_components import common_urlpatterns, dev_static_urlpatterns
from mcod.users.views import (
    AdminAutocompleteView,
    AgentAutocompleteView,
    CustomAdminLoginView,
    StaffAutocompleteView,
)

urlpatterns = common_urlpatterns + [
    path("metrics/", prometheus_metrics_view),
    path("nested_admin/", include("nested_admin.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("organization-type/", InstitutionTypeAdminView.as_view(), name="organization-type"),
    path("organization-autocomplete/", OrganizationAutocompleteView.as_view(), name="organization-autocomplete"),
    path("dataset-autocomplete/", DatasetAutocompleteView.as_view(), name="dataset-autocomplete"),
    path("staff-autocomplete/", StaffAutocompleteView.as_view(), name="staff-autocomplete"),
    path("admin-autocomplete/", AdminAutocompleteView.as_view(), name="admin-autocomplete"),
    path("agent-autocomplete/", AgentAutocompleteView.as_view(), name="agent-autocomplete"),
    path("regions-autocomplete/", RegionsAutocompleteView.as_view(), name="regions-autocomplete"),
    path("resource-autocomplete/", ResourceAutocompleteView.as_view(), name="resource-autocomplete"),
    path("dataset-license-labels/", ConditionLabelsAdminView.as_view(), name="dataset-license-labels"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("login/", CustomAdminLoginView.as_view(), name="login"),
    path("", admin.site.urls, name="admin"),
    path("pn-apps/", include("mcod.pn_apps.urls")),
    path("discourse/", include("mcod.discourse.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="admin/robots.txt", content_type="text/plain"),
    ),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += dev_static_urlpatterns()
