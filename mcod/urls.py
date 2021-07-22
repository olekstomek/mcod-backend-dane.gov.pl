from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.apps import apps
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from bokeh.server.django import static_extensions
from mcod.cms.views import revisions_view
from mcod.datasets.views import DatasetAutocompleteAdminView
from mcod.organizations.views import InstitutionAutocompleteAdminView, InstitutionTypeAdminView
from mcod.users.views import AdminAutocomplete, CustomAdminLoginView
from mcod.cms import urls as cms_urls
from mcod.cms.api.router import CmsApiRouter
from mcod.cms.api.views import CmsPagesViewSet, ImagesViewSet


panel_app_config = apps.get_app_config('mcod.pn_apps')

urlpatterns = []

if settings.COMPONENT == 'cms':
    api_router = CmsApiRouter('cmsapi')
    api_router.register_endpoint('pages', CmsPagesViewSet)
    api_router.register_endpoint('images', ImagesViewSet)
    api_router.register_endpoint('documents', DocumentsAPIViewSet)

    urlpatterns += [
        re_path(r'^documents/', include(wagtaildocs_urls)),
        re_path(r'^api/', api_router.urls),
        re_path(r'^hypereditor/', include('hypereditor.urls')),
        re_path(r'^admin/pages/(\d+)/revisions/(\d+)/view/$', revisions_view, name='revisions_view'),
        re_path(r'^admin/', include(wagtailadmin_urls)),
        re_path(
            r'^robots.txt',
            TemplateView.as_view(template_name="admin/robots.txt", content_type="text/plain"),
        ),
        re_path(r'', include(cms_urls)),
    ]
    urlpatterns += static(settings.IMAGES_URL, document_root=settings.IMAGES_MEDIA_ROOT)
else:
    urlpatterns += [
        path('nested_admin/', include('nested_admin.urls')),
        path('ckeditor/', include('ckeditor_uploader.urls')),
        path(
            'organization-type/',
            InstitutionTypeAdminView.as_view(),
            name='organization-type',
        ),
        path(
            'organization-autocomplete/',
            InstitutionAutocompleteAdminView.as_view(),
            name='organization-autocomplete',
        ),
        path(
            'dataset-autocomplete/',
            DatasetAutocompleteAdminView.as_view(),
            name='dataset-autocomplete',
        ),
        path(
            'admin-autocomplete/',
            AdminAutocomplete.as_view(),
            name='admin-autocomplete',
        ),
        path('i18n/', include('django.conf.urls.i18n')),
        path('login/', CustomAdminLoginView.as_view(), name='login'),
        path('', admin.site.urls, name='admin'),
        # Non-admin urls
        path('pn-apps/', include('mcod.pn_apps.urls')),
        path('discourse/', include('mcod.discourse.urls')),
        path(
            'robots.txt',
            TemplateView.as_view(template_name="admin/robots.txt", content_type="text/plain"),
        ),
    ]
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += static_extensions()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
