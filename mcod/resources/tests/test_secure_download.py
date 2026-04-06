import re

import factory
import pytest
from django.test import Client
from django.urls import reverse

from mcod.resources.factories import (
    ResourceCsvFileFactory,
    ResourceFileFactory,
    ResourceJsonFileFactory,
    ResourceXlsxFileFactory,
)
from mcod.resources.models import Resource

pytestmark = pytest.mark.django_db


@pytest.fixture
def django_client():
    return Client()


@pytest.mark.parametrize(
    "file_factory",
    (
        ResourceFileFactory,
        ResourceJsonFileFactory,
        ResourceCsvFileFactory,
        ResourceXlsxFileFactory,
    ),
)
def test_download_published_resource_returns_x_accel_header(django_client, file_factory):
    # GIVEN
    resource_file = file_factory(
        resource__status=Resource.STATUS.published,
        resource__is_removed=False,
    )

    file_path = resource_file.file.name
    url = reverse("secure_resource_download", kwargs={"file_path": file_path})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 200
    assert "X-Accel-Redirect" in response
    assert f"/protected_resources/{resource_file.file.name}" == response["X-Accel-Redirect"]
    assert response["Content-Type"] == resource_file.mimetype
    assert f"attachment; filename*=UTF-8''{resource_file.file_basename}" == response["Content-Disposition"]


def test_download_draft_resource_returns_404(django_client):
    # GIVEN
    resource_file = ResourceFileFactory(
        mimetype="text/csv",
        resource__status=Resource.STATUS.draft,
        resource__is_removed=False,
    )

    file_path = resource_file.file.name
    url = reverse("secure_resource_download", kwargs={"file_path": file_path})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 404
    assert "X-Accel-Redirect" not in response


def test_download_removed_resource_returns_404(django_client):
    # GIVEN
    resource_file = ResourceFileFactory(
        mimetype="text/csv",
        resource__status=Resource.STATUS.published,
        resource__is_removed=True,
    )

    file_path = resource_file.file.name
    url = reverse("secure_resource_download", kwargs={"file_path": file_path})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 404


def test_polish_characters_are_url_encoded(django_client):
    # GIVEN
    resource_file = ResourceFileFactory(
        file=factory.django.FileField(filename="zażółć gęślą jaźń.txt", data=b"polish chars test"),
        mimetype="text/plain",
        resource__status=Resource.STATUS.published,
        resource__is_removed=False,
    )

    file_path = resource_file.file.name
    url = reverse("secure_resource_download", kwargs={"file_path": file_path})

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"

    # X-Accel-Redirect must be URL-encoded
    content_x_accel_redirect = response["X-Accel-Redirect"]
    assert re.search(
        r"/protected_resources/\d{8}/za%C5%BC%C3%B3%C5%82%C4%87_g%C4%99%C5%9Bl%C4%85_ja%C5%BA%C5%84(_[A-Za-z0-9]+)?\.txt",
        content_x_accel_redirect,
    )
    assert "ż" not in response["X-Accel-Redirect"]
    assert " " not in response["X-Accel-Redirect"]

    # Content-Disposition — RFC 5987
    content_disposition = response["Content-Disposition"]

    assert content_disposition.startswith("attachment; filename*=UTF-8''")
    assert re.search(
        r"za%C5%BC%C3%B3%C5%82%C4%87_g%C4%99%C5%9Bl%C4%85_ja%C5%BA%C5%84(_[A-Za-z0-9]+)?\.txt",
        content_disposition,
    )

    # no raw UTF-8 in filename value
    filename_part = content_disposition.split("filename*=")[1]

    assert "ż" not in filename_part
    assert " " not in filename_part


def test_non_existent_file_returns_404(django_client):
    # GIVEN: A path that does not exist in the database
    non_existent_path = "2099/ghost_file.csv"
    url = reverse("secure_resource_download", kwargs={"file_path": non_existent_path})

    # WHEN: Requesting the file
    response = django_client.get(url)

    # THEN: 404 Not Found
    assert response.status_code == 404


def test_download_resource_without_mimetype_returns_octet_stream(django_client):
    # GIVEN
    resource_file = ResourceFileFactory(
        mimetype=None,
        resource__status=Resource.STATUS.published,
        resource__is_removed=False,
    )

    url = reverse(
        "secure_resource_download",
        kwargs={"file_path": resource_file.file.name},
    )

    # WHEN
    response = django_client.get(url)

    # THEN
    assert response.status_code == 200
    assert "X-Accel-Redirect" in response
    assert "application/octet-stream" == response["Content-Type"]
    assert f"/protected_resources/{resource_file.file.name}" == response["X-Accel-Redirect"]
    assert f"attachment; filename*=UTF-8''{resource_file.file_basename}" == response["Content-Disposition"]
