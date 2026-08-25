import magic
import pytest
from django.test import override_settings

from mcod.core.image_validation import (
    INVALID_BASE64,
    INVALID_IMAGE,
    INVALID_MIME_TYPE,
    MIME_TYPE_MISMATCH,
    TOO_LONG,
    ImageValidationError,
    detect_mime_type_using_magic,
    parse_base64_image_data_uri,
    validate_image,
)


@pytest.mark.parametrize(
    "value_fixture,expected_data_fixture,expected_mime_type",
    (
        ("valid_jpeg_data_uri", "valid_jpeg_bytes", "image/jpeg"),
        ("url_quoted_text_data_uri", "url_quoted_text_bytes", "text/plain"),
    ),
)
def test_parse_base64_image_data_uri_decodes_payload(
    request,
    value_fixture,
    expected_data_fixture,
    expected_mime_type,
):
    value = request.getfixturevalue(value_fixture)
    expected_data = request.getfixturevalue(expected_data_fixture)
    decoded_data, mime_type = parse_base64_image_data_uri(value)

    assert decoded_data == expected_data
    assert mime_type == expected_mime_type


@pytest.mark.parametrize(
    "value,error_code",
    (
        ("not-a-data-uri", INVALID_MIME_TYPE),
        ("data:,AAAA", INVALID_MIME_TYPE),
        ("data:image/png;base64", INVALID_MIME_TYPE),
        ("data:image/png;base64,not valid base64", INVALID_BASE64),
    ),
)
def test_parse_base64_image_data_uri_rejects_invalid_values(value, error_code):
    with pytest.raises(ImageValidationError) as exc:
        parse_base64_image_data_uri(value)

    assert str(exc.value) == error_code


def test_detect_mime_type_using_magic_returns_detected_mime_type(mocker):
    mocker.patch("mcod.core.image_validation.magic.from_buffer", return_value="IMAGE/PNG")

    assert detect_mime_type_using_magic(b"png-bytes") == "image/png"


@pytest.mark.parametrize(
    "magic_result,error_code",
    (
        (None, INVALID_MIME_TYPE),
        (magic.MagicException("libmagic failed"), INVALID_IMAGE),
    ),
)
def test_detect_mime_type_using_magic_rejects_invalid_detection(mocker, magic_result, error_code):
    if isinstance(magic_result, Exception):
        mocker.patch("mcod.core.image_validation.magic.from_buffer", side_effect=magic_result)
    else:
        mocker.patch("mcod.core.image_validation.magic.from_buffer", return_value=magic_result)

    with pytest.raises(ImageValidationError) as exc:
        detect_mime_type_using_magic(b"broken")

    assert str(exc.value) == error_code


def test_detect_mime_type_using_magic_does_not_hide_unexpected_errors(mocker):
    mocker.patch("mcod.core.image_validation.magic.from_buffer", side_effect=TypeError)

    with pytest.raises(TypeError):
        detect_mime_type_using_magic(b"broken")


def test_validate_image_rejects_payload_over_size_limit(valid_jpeg_data_uri):
    with override_settings(IMAGE_UPLOAD_MAX_SIZE=1):
        with pytest.raises(ImageValidationError) as exc:
            validate_image(valid_jpeg_data_uri)

    assert str(exc.value) == TOO_LONG


@pytest.mark.parametrize(
    "value_fixture,error_code",
    (
        ("html_data_uri", INVALID_MIME_TYPE),
        ("non_image_png_data_uri", INVALID_MIME_TYPE),
        ("png_declared_jpeg_data_uri", MIME_TYPE_MISMATCH),
    ),
)
def test_validate_image_rejects_invalid_values(request, value_fixture, error_code):
    value = request.getfixturevalue(value_fixture)

    with pytest.raises(ImageValidationError) as exc:
        validate_image(value)

    assert str(exc.value) == error_code
