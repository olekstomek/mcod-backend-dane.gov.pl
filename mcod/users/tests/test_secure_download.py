import re
from urllib.parse import unquote, urlsplit

import factory
import pytest
from django.test import Client
from django.urls import reverse

from mcod.users.factories import MeetingFileFactory, UserFactory

pytestmark = pytest.mark.django_db

ENCODED_MEETING_FILENAME_PATTERN = r"za%C5%BC%C3%B3%C5%82%C4%87_g%C4%99%C5%9Bl%C4%85_ja%C5%BA%C5%84\.html"
PROTECTED_MEETING_REDIRECT_PATTERN = rf"/protected_meetings/[0-9a-f\-]+/{ENCODED_MEETING_FILENAME_PATTERN}"


@pytest.fixture
def django_client():
    return Client()


def test_download_meeting_file_returns_download_headers(django_client):
    # GIVEN
    user = UserFactory()
    django_client.force_login(user)
    meeting_file = MeetingFileFactory(
        file=factory.django.FileField(filename="meetings_xss.html", data=b"<script>alert(1)</script>")
    )
    url = reverse("secure_meeting_download", kwargs={"file_path": meeting_file.file.name})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 200
    assert response["Content-Type"] == "text/html"
    assert response["Content-Disposition"] == "attachment; filename*=UTF-8''meetings_xss.html"
    assert response["X-Accel-Redirect"] == f"/protected_meetings/{meeting_file.file.name}"


def test_download_meeting_file_supports_legacy_url_with_meetings_prefix(django_client):
    # GIVEN
    user = UserFactory()
    django_client.force_login(user)
    meeting_file = MeetingFileFactory(
        file=factory.django.FileField(filename="meetings_xss.html", data=b"<script>alert(1)</script>")
    )
    legacy_url = reverse("secure_meeting_download", kwargs={"file_path": f"meetings/{meeting_file.file.name}"})

    # WHEN
    response = django_client.get(legacy_url)

    # THEN
    assert response.status_code == 200
    assert response["X-Accel-Redirect"] == f"/protected_meetings/{meeting_file.file.name}"


def test_polish_characters_are_url_encoded_in_meeting_download(django_client):
    # GIVEN
    user = UserFactory()
    django_client.force_login(user)
    meeting_file = MeetingFileFactory(
        file=factory.django.FileField(filename="zażółć gęślą jaźń.html", data=b"<html></html>"),
    )
    url = reverse("secure_meeting_download", kwargs={"file_path": meeting_file.file.name})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 200

    # The pattern should match encoded meeting file path:
    # - /protected_meetings/<uuid>/za%C5%BC%C3%B3%C5%82%C4%87_g%C4%99%C5%9Bl%C4%85_ja%C5%BA%C5%84.html

    content_x_accel_redirect = response["X-Accel-Redirect"]
    assert re.search(PROTECTED_MEETING_REDIRECT_PATTERN, content_x_accel_redirect)
    assert "ż" not in content_x_accel_redirect
    assert " " not in content_x_accel_redirect

    # The pattern should match encoded meeting file name:
    # - attachment; filename*=UTF-8''za%C5%BC%C3%B3%C5%82%C4%87_g%C4%99%C5%9Bl%C4%85_ja%C5%BA%C5%84.html

    content_disposition = response["Content-Disposition"]
    assert content_disposition.startswith("attachment; filename*=UTF-8''")
    assert re.search(ENCODED_MEETING_FILENAME_PATTERN, content_disposition)

    filename_part = content_disposition.split("filename*=")[1]
    assert "ż" not in filename_part
    assert " " not in filename_part


def test_non_existent_meeting_file_returns_404(django_client):
    # GIVEN
    user = UserFactory()
    django_client.force_login(user)
    url = reverse("secure_meeting_download", kwargs={"file_path": "00000000-0000-0000-0000-000000000000/ghost_file.html"})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 404


def test_anonymous_user_is_redirected_to_login_for_meeting_file(django_client):
    # GIVEN
    meeting_file = MeetingFileFactory(
        file=factory.django.FileField(filename="meetings_xss.html", data=b"<script>alert(1)</script>")
    )
    url = reverse("secure_meeting_download", kwargs={"file_path": meeting_file.file.name})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 302
    login_url = reverse("login")
    redirect_url = reverse("admin:users_meeting_changelist")
    assert response.url.startswith(login_url)
    decoded_url = unquote(response.url)
    assert urlsplit(decoded_url).query == f"next={redirect_url}"
