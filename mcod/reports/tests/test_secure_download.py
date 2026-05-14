import uuid
from pathlib import Path
from typing import Generator
from urllib.parse import quote, unquote, urlsplit

import pytest
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from mcod.users.factories import AdminFactory, UserFactory
from mcod.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def admin_user() -> User:
    return AdminFactory()


@pytest.fixture
def regular_user() -> User:
    return UserFactory()


@pytest.fixture
def media_root_path() -> Generator[Path, None, None]:
    base_media_path = Path(settings.MEDIA_ROOT)
    target_path = base_media_path / "reports"
    target_path.mkdir(parents=True, exist_ok=True)

    with override_settings(REPORTS_MEDIA_ROOT=target_path):
        yield target_path


def create_dummy_file(media_root_path: Path, file_path: str) -> None:
    """Helper to create a dummy file in the temp media directory."""
    full_path = media_root_path / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text("dummy content")


def test_download_report_by_superuser_returns_x_accel_header(client: Client, admin_user: User, media_root_path: Path) -> None:
    # GIVEN
    client.force_login(admin_user)
    filename = f"test_report_{uuid.uuid4().hex}.csv"
    create_dummy_file(media_root_path, filename)
    url = reverse("secure_report_download", kwargs={"file_path": filename})
    # WHEN
    response = client.get(url)
    # THEN
    assert response.status_code == 200
    assert "X-Accel-Redirect" in response
    expected_redirect = f"/protected_reports/{quote(filename)}"
    assert response["X-Accel-Redirect"] == expected_redirect
    assert response["Content-Type"] == "application/octet-stream"


def test_download_report_with_special_chars(client: Client, admin_user: User, media_root_path: Path) -> None:
    # GIVEN
    client.force_login(admin_user)
    filename = f"zażółć gęślą jaźń_{uuid.uuid4().hex}.csv"
    create_dummy_file(media_root_path, filename)
    url = reverse("secure_report_download", kwargs={"file_path": filename})
    # WHEN
    response = client.get(url)
    # THEN
    assert response.status_code == 200
    assert response["X-Accel-Redirect"] == f"/protected_reports/{quote(filename)}"


def test_download_report_by_regular_user_returns_403(client: Client, regular_user: User, media_root_path: Path) -> None:
    # GIVEN
    client.force_login(regular_user)
    filename = f"test403_{uuid.uuid4().hex}.csv"
    create_dummy_file(media_root_path, filename)
    url = reverse("secure_report_download", kwargs={"file_path": filename})
    # WHEN
    response = client.get(url)
    # THEN
    assert response.status_code == 403
    assert "X-Accel-Redirect" not in response


@pytest.mark.parametrize(
    "file_subpath, expected_admin_view",
    [
        ("users/report.csv", "admin:reports_userreport_changelist"),
        ("resources/report.csv", "admin:reports_resourcereport_changelist"),
        ("datasets/report.csv", "admin:reports_datasetreport_changelist"),
        ("organizations/report.csv", "admin:reports_organizationreport_changelist"),
        ("suggestions/report.csv", "admin:reports_monitoringreport_changelist"),
        ("showcases/report.csv", "admin:reports_monitoringreport_changelist"),
        ("applications/report.csv", "admin:reports_monitoringreport_changelist"),
        ("daily/report.csv", "admin:reports_summarydailyreport_changelist"),
        ("harvester/report.csv", "admin:reports_datasourceimportreport_changelist"),
        ("other/report.csv", "admin:app_list"),  # Default fallback
    ],
)
def test_anonymous_user_redirect_logic(client: Client, file_subpath: str, expected_admin_view: str) -> None:
    """
    Tests if anonymous users are redirected to the login page with the CORRECT 'next' parameter
    corresponding to the report type.
    """
    # GIVEN
    if expected_admin_view == "admin:app_list":
        expected_next_url = reverse(expected_admin_view, args=["reports"])
    else:
        expected_next_url = reverse(expected_admin_view)
    url = reverse("secure_report_download", kwargs={"file_path": file_subpath})
    # WHEN
    response = client.get(url)
    # THEN
    assert response.status_code == 302
    login_url = reverse("login")
    # Check basic redirect to login
    assert response.url.startswith(login_url)
    # Check 'next' parameter
    decoded_url = unquote(response.url)
    assert urlsplit(decoded_url).query == f"next={expected_next_url}"


def test_download_non_existent_report_returns_404(client: Client, admin_user: User) -> None:
    # GIVEN
    client.force_login(admin_user)
    non_existent_path = "ghost_file.csv"
    url = reverse("secure_report_download", kwargs={"file_path": non_existent_path})
    # WHEN
    response = client.get(url)
    # THEN
    assert response.status_code == 404
