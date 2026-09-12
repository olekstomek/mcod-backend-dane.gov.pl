from bokeh.server.django import static_extensions
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path, re_path

from mcod.reports.views import DownloadReportFileView
from mcod.resources.views import DownloadResourceFileView
from mcod.users.views import DownloadMeetingFileView


def health_view(request):
    return JsonResponse({"status": "ok"})


common_urlpatterns = [
    re_path(r"^media/meetings/(?P<file_path>.*)$", DownloadMeetingFileView.as_view(), name="secure_meeting_download"),
    re_path(
        r"^media/resources/(?P<file_path>.*)$",
        DownloadResourceFileView.as_view(),
        name="secure_resource_download",
    ),
    re_path(
        r"^media/reports/(?P<file_path>.*)$",
        DownloadReportFileView.as_view(),
        name="secure_report_download",
    ),
    path("health/", health_view),
    path("logingovpl/", include("mcod.users.urls")),
]


def dev_static_urlpatterns():
    return (
        static_extensions()
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )
