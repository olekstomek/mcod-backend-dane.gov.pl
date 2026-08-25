from typing import Any, Dict, Optional, Tuple
from unittest.mock import patch

import pytest
from django.test import override_settings
from falcon.testing import TestClient as FalconTestClient
from pytest_bdd import scenarios

from mcod.showcases.models import ShowcaseProposal

scenarios(
    "features/showcase_details_api.feature",
    "features/showcases_list_api.feature",
)


@pytest.mark.parametrize("api_version", ["1.0", "1.4"])
@pytest.mark.parametrize(
    "optional_field",
    (
        "applicant_full_name",
        "image",
        "illustrative_graphics",
        "external_datasets",
        "keywords",
    ),
)
def test_showcase_proposal_create_optional_fields(
    api_version: str,
    optional_field: str,
    api_clients: Dict[str, FalconTestClient],
    default_showcase_proposal_data: Dict[str, Any],
):
    api_client: FalconTestClient = api_clients[api_version]
    default_showcase_proposal_data.pop(optional_field)
    data = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}
    with patch("mcod.showcases.views.create_showcase_proposal_task"):
        response = api_client.simulate_post(
            path="/showcases/suggest",
            json=data,
        )
        assert response.status_code == 201


@pytest.mark.parametrize("api_version", ["1.0", "1.4"])
@pytest.mark.parametrize(
    "invalid_update",
    [
        {"author": "a" * 301},
        {"author": ""},
        {"applicant_full_name": "a" * 301},
        {"applicant_full_name": ""},
        {"category": "a" * 6},
        {"applicant_email": "not-an-email"},
        {"applicant_email": "a" * 255},
        {"applicant_email": ""},
        {"title": "a" * 301},
        {"title": None},
        {"title": ""},
        {"url": "not-a-url"},
        {"url": "a" * 2049},
        {"url": ""},
        {"url": None},
        {"notes": "a" * 3001},
        {"notes": None},
        {"notes": ""},
        {"keywords": "a" * 301},
        {"mobile_apple_url": "not-a-url"},
        {"mobile_apple_url": "a" * 2049},
        {"mobile_apple_url": ""},
        {"mobile_google_url": "not-a-url"},
        {"mobile_google_url": "a" * 2049},
        {"mobile_google_url": ""},
        {"desktop_linux_url": "not-a-url"},
        {"desktop_linux_url": "a" * 2049},
        {"desktop_linux_url": ""},
        {"desktop_macos_url": "not-a-url"},
        {"desktop_macos_url": "a" * 2049},
        {"desktop_macos_url": ""},
        {"desktop_windows_url": "not-a-url"},
        {"desktop_windows_url": "a" * 2049},
        {"desktop_windows_url": ""},
        {"is_personal_data_processing_accepted": None},
        {"is_terms_of_service_accepted": None},
    ],
)
def test_showcase_proposal_create_validation_errors(
    api_version: str,
    invalid_update: Dict[str, Optional[str]],
    api_clients: Dict[str, FalconTestClient],
    default_showcase_proposal_data: Dict[str, Optional[str]],
):
    api_client: FalconTestClient = api_clients[api_version]
    default_showcase_proposal_data.update(invalid_update)
    payload = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}

    response = api_client.simulate_post(
        path="/showcases/suggest",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize("api_version", ["1.0", "1.4"])
@pytest.mark.parametrize(
    "enabled_flag,url_fields,error_detail,error_pointer",
    [
        (
            "is_mobile_app",
            ("mobile_apple_url", "mobile_google_url"),
            "Przekazanie co najmniej jednego z: mobile_apple_url, mobile_google_url jest wymagane!",
            "/data/attributes/is_mobile_app",
        ),
        (
            "is_desktop_app",
            ("desktop_linux_url", "desktop_macos_url", "desktop_windows_url"),
            "Przekazanie co najmniej jednego z: desktop_linux_url, desktop_macos_url, desktop_windows_url jest wymagane!",
            "/data/attributes/is_desktop_app",
        ),
    ],
)
def test_showcase_proposal_create_requires_url_for_enabled_platform(
    api_version: str,
    enabled_flag: str,
    url_fields: Tuple[str, ...],
    error_detail: str,
    error_pointer: str,
    api_clients: Dict[str, FalconTestClient],
    default_showcase_proposal_data: Dict[str, Any],
):
    api_client: FalconTestClient = api_clients[api_version]
    default_showcase_proposal_data[enabled_flag] = True
    for url_field in url_fields:
        default_showcase_proposal_data.pop(url_field)

    payload = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}
    response = api_client.simulate_post(
        path="/showcases/suggest",
        json=payload,
    )

    assert response.status_code == 422
    errors = response.json["errors"]
    if api_version == "1.4":
        first_error = errors[0]
        assert first_error["title"] == "Błąd pola"
        assert first_error["detail"] == error_detail
        assert first_error["source"]["pointer"] == error_pointer
    else:
        assert errors["data"]["attributes"][enabled_flag] == error_detail


@pytest.mark.parametrize(
    "client_fixture,api_version",
    (
        ("client", "1.0"),
        ("client14", "1.4"),
    ),
)
@pytest.mark.parametrize(
    "base64_content_fixture,is_valid,error_message",
    (
        ("valid_jpeg_data_uri", True, None),
        ("non_image_png_data_uri", False, "Nieobsługiwany typ MIME obrazu."),
        ("html_data_uri", False, "Nieobsługiwany typ MIME obrazu."),
    ),
)
def test_showcase_proposal_image_upload_response(
    client_fixture: str,
    api_version: str,
    base64_content_fixture: str,
    is_valid: bool,
    error_message: Optional[str],
    default_showcase_proposal_data: Dict[str, Any],
    request: pytest.FixtureRequest,
    valid_jpeg_bytes: bytes,
):
    api_client: FalconTestClient = request.getfixturevalue(client_fixture)
    proposal_count = ShowcaseProposal.objects.count()
    base64_content = request.getfixturevalue(base64_content_fixture)
    default_showcase_proposal_data["image"] = base64_content
    payload = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}

    response = api_client.simulate_post(
        path="/showcases/suggest",
        json=payload,
    )

    if is_valid:
        assert response.status_code == 201
        assert ShowcaseProposal.objects.count() == proposal_count + 1
        proposal = ShowcaseProposal.objects.latest("created")
        with proposal.image.open("rb") as uploaded_image:
            assert uploaded_image.read() == valid_jpeg_bytes
    else:
        assert response.status_code == 422
        if api_version == "1.0":
            assert response.json["errors"]["data"]["attributes"]["image"] == error_message
        else:
            error = response.json["errors"][0]
            assert error["detail"] == error_message, "If message missmatch, one of the problem can be compilemessages"
            assert error["source"]["pointer"] == "/data/attributes/image"


def test_showcase_proposal_create_rejects_html_illustrative_graphics_upload(
    client14: FalconTestClient,
    default_showcase_proposal_data: Dict[str, Any],
    html_data_uri: str,
):
    default_showcase_proposal_data["illustrative_graphics"] = html_data_uri
    payload = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}

    response = client14.simulate_post(
        path="/showcases/suggest",
        json=payload,
    )

    assert response.status_code == 422
    error = response.json["errors"][0]
    assert error["detail"] == "Nieobsługiwany typ MIME obrazu."
    assert error["source"]["pointer"] == "/data/attributes/illustrative_graphics"


@pytest.mark.parametrize(
    "client_fixture,api_version",
    (
        ("client", "1.0"),
        ("client14", "1.4"),
    ),
)
def test_showcase_proposal_create_rejects_too_long_image_bytes(
    client_fixture: str,
    api_version: str,
    default_showcase_proposal_data: Dict[str, Any],
    request: pytest.FixtureRequest,
    valid_jpeg_data_uri: str,
):
    api_client: FalconTestClient = request.getfixturevalue(client_fixture)
    default_showcase_proposal_data["image"] = valid_jpeg_data_uri
    payload = {"data": {"type": "showcaseproposal", "attributes": default_showcase_proposal_data}}

    with override_settings(IMAGE_UPLOAD_MAX_SIZE=1):
        response = api_client.simulate_post(
            path="/showcases/suggest",
            json=payload,
        )

    assert response.status_code == 422
    if api_version == "1.0":
        assert response.json["errors"]["data"]["attributes"]["image"] == ["Plik jest za duży, maksymalny rozmiar to 1 bajtów."]
    else:
        error = response.json["errors"][0]
        assert error["detail"] == "Plik jest za duży, maksymalny rozmiar to 1 bajtów."
        assert error["source"]["pointer"] == "/data/attributes/image"
