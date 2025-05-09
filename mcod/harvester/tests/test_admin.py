from typing import Literal, Optional

import pytest
import requests_mock
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from pytest_mock import MockerFixture

from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.harvester.models import STATUS_ERROR, STATUS_OK, DataSource
from mcod.harvester.tests.utils import mocked_response
from mcod.lib.utils import get_file_content
from mcod.resources.link_validation import session
from mcod.resources.models import Resource

User = get_user_model()


post_ckan_data = {
    "name": "some_name",
    "description": "some description",
    "source_type": "ckan",
    "portal_url": "https://mcod.local",
    "api_url": "https://mcod.local",
    "frequency_in_days": 7,
    "status": "active",
    "institution_type": "other",
    "emails": "email@email.com",
    # Management form fields for `imports`
    "imports-TOTAL_FORMS": 0,
    "imports-INITIAL_FORMS": 0,
    "imports-MIN_NUM_FORMS": 0,
    "imports-MAX_NUM_FORMS": 1000,
    # Management form fields for `datasource_datasets`
    "datasource_datasets-TOTAL_FORMS": 0,
    "datasource_datasets-INITIAL_FORMS": 0,
    "datasource_datasets-MIN_NUM_FORMS": 0,
    "datasource_datasets-MAX_NUM_FORMS": 1000,
}
client = Client()
data_source_admin_url = reverse("admin:harvester_datasource_add")


class TestHarvesterImportsCkanStoCalculation:
    """
    Integration tests for verifying the automatic calculation of openness scores (STO)
    for datasets imported via a CKAN source in the Django admin interface.

    This class simulates the full flow of adding a new `DataSource` of type `ckan` through the
    admin panel, mocking external HTTP responses and file contents to control the format
    of returned resources and verify that the openness score is correctly calculated.
    """

    @staticmethod
    def create_adapter(content: bytes) -> None:
        """Register a mock GET response for a given URL using `requests_mock`."""
        adapter = requests_mock.Adapter()
        adapter.register_uri(
            "GET",
            "https://mcod.local",
            content=content,
            headers={"Content-Type": "application/csv"},
        )
        session.mount("https://mcod.local", adapter)

    @pytest.mark.parametrize("expected_openness_score, file_name", [(3, "csv2jsonld.csv"), (1, "example.pdf")])
    def test_sto_calculates_for_ckan(
        self,
        mocker: "MockerFixture",
        admin: User,
        harvester_ckan_data_with_no_resource_format: dict,
        file_name: str,
        expected_openness_score: int,
    ):
        """
        Parametrized test to verify correct calculation of the openness score (STO)
        for resources harvested from a CKAN source, based on file format.
        """
        # WHEN admin logins
        client.force_login(admin)
        # GIVEN CKAN example data
        harvester_ckan_data_with_no_resource_format[0]["resources"][0]["format"] = file_name.split(".")[-1]

        mocker.patch("mcod.harvester.utils.fetch_data", return_value=harvester_ckan_data_with_no_resource_format)
        mocker.patch("mcod.harvester.models.DataSource._validate_ckan_type", return_value=None)

        # THEN create mock response
        file_content: bytes = get_file_content(file_name)
        self.create_adapter(content=file_content)

        # WHEN request post sends to django admin page
        post_data: dict = post_ckan_data
        client.post(data_source_admin_url, data=post_data, follow=True)

        run_on_commit_events()
        resource: Resource = Resource.objects.first()

        # THEN resource is created with calculated openness score value.
        assert resource.openness_score == expected_openness_score


@pytest.mark.parametrize(
    "url, file_name, headers, expected_status, expected_format",
    [
        ("https://mcod.local", "csv2jsonld.csv", {}, STATUS_OK, "csv"),
        ("https://mcod.local", None, {}, STATUS_OK, None),
        ("https://mcod.local", "example_dga_xls_file.xls", {}, STATUS_OK, "xls"),
        ("https://mcod.local", "example_geojson.geojson", {}, STATUS_OK, "json"),
        pytest.param(
            "https://mcod.local",
            "geo.csv",
            {},
            STATUS_OK,
            "txt",
            id="Python magic will interpret geo.csv as plain/text. We want to allow harvester to go on.",
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some.xml",
                "Content-Type": "text/pdf",
            },
            STATUS_OK,
            "pdf",
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some.xml",
            },
            STATUS_OK,
            "xml",
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Type": "text/pdf",
            },
            STATUS_OK,
            "pdf",
        ),
        ("https://mcod.local", None, {}, STATUS_OK, None),
        (
            "https://mcod.local",
            None,
            {},
            STATUS_OK,
            None,
        ),
        pytest.param(
            "https://mcod.local",
            None,
            {"Content-Disposition": "attachment; filename='" "file name.jpg" "'; filename*=UTF-8''file%20name.jpg"},
            STATUS_ERROR,
            None,
            id="Not valid header value structure. Should be double quote.",
        ),
        ("https://mcod.local/some.bat", None, {}, STATUS_ERROR, None),
        ("https://mcod.local/some.asp", None, {}, STATUS_ERROR, None),
        ("https://mcod.local/some.cgi", None, {}, STATUS_ERROR, None),
        ("https://mcod.local/some.exe", None, {}, STATUS_ERROR, None),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some.bat",
            },
            STATUS_ERROR,
            None,
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some.asp",
            },
            STATUS_ERROR,
            None,
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some.exe",
            },
            STATUS_ERROR,
            None,
        ),
        (
            "https://mcod.local",
            None,
            {
                "Content-Disposition": "attachment; filename=some_no_known.blabla",
            },
            STATUS_ERROR,
            None,
        ),
        pytest.param(
            "https://mcod.local",
            "sample.bat",
            {},
            STATUS_OK,
            None,
            id="Python magic will interpret sample.bat asx-msdos-batch, "
            "so function get_mime_type_from_magic will return None. We want allow harvester to go on.",
        ),
        ("https://mcod.local", None, {"Content-Disposition": "attachment; filename=some.bat"}, STATUS_ERROR, None),
        pytest.param(
            "https://mcod.local",
            None,
            {"Content-Type": "attachment; filename=some.bat"},
            STATUS_OK,
            None,
            id="Case when content-type returned unrecognized extension. Means we are not stopping harvester.",
        ),
        pytest.param(
            "https://mcod.local",
            None,
            {"Content-Type": "text/bat"},
            STATUS_ERROR,
            None,
            marks=pytest.mark.xfail(reason="Test will not fail, because mimetypes library wont recognize this mimetype"),
        ),
    ],
)
def test_harvester_resource_format_validation(
    mocker: MockerFixture,
    url: str,
    file_name: str,
    headers: dict,
    expected_status: Literal["ok", "error"],
    expected_format: Optional[str],
    admin: User,
    harvester_ckan_data_with_no_resource_format: dict,
):
    """
    Test `POST` behavior of CKAN data sources based on file content, headers, and filenames.

    This test validates the harvester's behavior when attempting to determine the file format of a resource
    based on various combinations of:
    - the file name (when available),
    - HTTP response headers (Content-Type, Content-Disposition),
    - and Python's file magic detection (e.g., via `mimetypes` or similar tools).

    It ensures that:
    - Files with recognized extensions or headers are assigned correct formats.
    - Files with ambiguous or unsafe formats (e.g., .bat) are either rejected or passed through based on logic.
    - No format leads to `None`, while disallowed types raise an error and mark the import as failed.

    Each test case provides:
    - `url`: The URL the resource would have been downloaded from.
    - `file_name`: Example file name if available (used for format inference).
    - `headers`: Simulated HTTP headers from the server's response.
    - `expected_status`: Expected status of the import process (DataSourceImport).
    - `expected_format`: The expected value stored in the `Resource.format` field, or `None` if not applicable.

    This test uses mocking to simulate downloading a file and skips actual HTTP or disk operations.
    """

    client.force_login(admin)
    mocker.patch("mcod.harvester.utils.fetch_data", return_value=harvester_ckan_data_with_no_resource_format)
    mocker.patch("mcod.harvester.models.DataSource._validate_ckan_type", return_value=None)
    if file_name:
        mocker.patch("mcod.lib.file_format_from_response._get_extension_from_magic", return_value=expected_format)

    if not file_name:
        file_content = b""
    else:
        file_content = get_file_content(file_name)

    response_object = mocked_response(url=url, content=file_content, headers=headers)
    mocker.patch("mcod.harvester.schema_utils.download_file", return_value=(None, {"response": response_object}))
    client.post(data_source_admin_url, data=post_ckan_data, follow=True)
    run_on_commit_events()

    datasource: DataSource = DataSource.objects.first()
    assert datasource.imports.first().status == expected_status

    if expected_format:
        assert datasource.datasource_datasets.first().resources.first().format == expected_format
    elif expected_status == STATUS_ERROR:
        assert not datasource.datasource_datasets.exists()
