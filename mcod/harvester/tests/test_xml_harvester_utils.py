import hashlib
from pathlib import Path
from uuid import uuid4

import pytest
from django.conf import settings
from requests_mock import Mocker

from mcod.harvester.exceptions import (
    UnexpectedStatusCode,
    XMLDoesNotMatchMD5Pattern,
    XMLMD5DoesNoMatch,
)
from mcod.harvester.utils import get_remote_xml_hash, validate_md5
from mcod.lib.utils import get_file_content


@pytest.fixture
def xml_file_name() -> Path:
    return Path(settings.TEST_SAMPLES_PATH) / "harvester" / "import_example1.13.xml"


@pytest.fixture
def xml_file_hash() -> str:
    """Hardcoded hash of the content of `import_example1.13.xml`, otherwise we'd be testing nothing."""
    return "eb806d3a2467a5c66a40f45d66ea5169"


def test_get_remote_xml_hash_happy_path(requests_mock: Mocker, xml_file_name: Path, xml_file_hash: str):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    # and file content
    _set_up_mocks_for_file(requests_mock, xml_file_name, xml_url)
    # When
    actual_xml_hash_url, actual_xml_hash = get_remote_xml_hash(xml_url)
    # Then
    assert actual_xml_hash_url == f"https://example.dane.gov.pl/{_nonce}.md5"
    assert actual_xml_hash == xml_file_hash


def test_get_remote_xml_hash_happy_path_extra_content_in_response(requests_mock: Mocker, xml_file_name: Path, xml_file_hash: str):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    hash_url_content = f"md5 is here: {xml_file_hash} dataset"
    # and file content
    requests_mock.get(
        hash_url,
        content=hash_url_content.encode(),
        status_code=200,
    )
    # When
    actual_xml_hash_url, actual_xml_hash = get_remote_xml_hash(xml_url)
    # Then
    assert actual_xml_hash_url == f"https://example.dane.gov.pl/{_nonce}.md5"
    assert actual_xml_hash == xml_file_hash


@pytest.mark.parametrize(
    "response_body",
    (
        "",
        "<html>",
        "abcabcts",
    ),
)
def test_get_remote_xml_hash_not_a_hash_pattern(requests_mock: Mocker, response_body: str):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    # and file content
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    requests_mock.get(hash_url, content=response_body.encode("utf-8"))
    # When
    with pytest.raises(XMLDoesNotMatchMD5Pattern) as exc:
        get_remote_xml_hash(xml_url)
    # Then
    assert str(exc.value) == f'{hash_url}: "{response_body}" nie jest poprawnym skrótem MD5!'


def test_get_remote_xml_hash_too_long(requests_mock: Mocker):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    # and file content
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    response_body = "".join(33 * ["0"])
    requests_mock.get(hash_url, content=response_body.encode("utf-8"))
    # When
    with pytest.raises(XMLDoesNotMatchMD5Pattern) as exc:
        get_remote_xml_hash(xml_url)
    # Then
    assert str(exc.value) == f'{hash_url}: "000000000000000000000000000000000..." nie jest poprawnym skrótem MD5!'


@pytest.mark.parametrize("status_code", (401, 403, 404, 500))
def test_get_remote_xml_hash_unexpected_http_code(requests_mock: Mocker, xml_file_hash: str, status_code: int):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    # and file content
    requests_mock.get(
        hash_url,
        content=xml_file_hash.encode(),
        status_code=status_code,
    )
    # When
    with pytest.raises(UnexpectedStatusCode) as exc:
        get_remote_xml_hash(xml_url)
    # Then
    assert str(exc.value) == f"{hash_url}: niewłaściwy kod odpowiedzi: {status_code} (None)"


def test_get_remote_xml_follows_redirects_and_handles_error(requests_mock: Mocker, xml_file_hash: str):
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    # and file content
    _redirected_url = "https://example.dane.gov.pl/redirected"
    requests_mock.get(
        _redirected_url,
        content=xml_file_hash.encode(),
        status_code=404,
    )
    requests_mock.get(
        hash_url,
        content=xml_file_hash.encode(),
        status_code=302,
        headers={"Location": _redirected_url},
    )
    # When
    with pytest.raises(UnexpectedStatusCode) as exc:
        get_remote_xml_hash(xml_url)
    # Then
    assert str(exc.value) == f"{hash_url}: niewłaściwy kod odpowiedzi: 404 (None)"


def test_get_remote_xml_follows_redirects_and_handles_success(requests_mock: Mocker, xml_file_hash: str):
    """
    Contrived example of misbehaving webserver. It first redirects to a pages returning non 200 but ok code,
    with the body containing hash. We should accept that.
    """
    # Given
    _nonce = str(uuid4())
    xml_url = f"https://example.dane.gov.pl/{_nonce}.xml"
    hash_url = f"https://example.dane.gov.pl/{_nonce}.md5"
    # and file content
    _redirected_url = "https://example.dane.gov.pl/redirected"
    requests_mock.get(
        _redirected_url,
        content=xml_file_hash.encode(),
        status_code=301,
    )
    requests_mock.get(
        hash_url,
        content=xml_file_hash.encode(),
        status_code=302,
        headers={"Location": _redirected_url},
    )
    # When
    _, actual_hash = get_remote_xml_hash(xml_url)
    # Then no exception raised
    assert actual_hash


def test_validate_md5_ok(xml_file_name: Path, xml_file_hash: str):
    # When
    actual_source_hash = validate_md5(
        xml_file_name,
        xml_file_hash,
        f"https://example.dane.gov.pl/{uuid4()}.md5",
    )
    # Then
    assert actual_source_hash == xml_file_hash


def test_validate_md5_error(xml_file_name: Path, xml_file_hash: str):
    # Given
    hash_url = f"https://example.dane.gov.pl/{uuid4()}.md5"
    # When
    with pytest.raises(XMLMD5DoesNoMatch) as exc:
        validate_md5(
            xml_file_name,
            "abc",
            hash_url,
        )
    # Then
    assert str(exc.value) == f"{hash_url}: zdalny skrót MD5 nie jest poprawny!"
    # And then (that's how celery rehydrates exceptions)
    assert str(exc.type(*exc.value.args)) == f"{hash_url}: zdalny skrót MD5 nie jest poprawny!"


def _set_up_mocks_for_file(requests_mock: Mocker, xml_file: Path, xml_url: str):
    # then intercept urls
    _intercept_xml_url(requests_mock, xml_file, xml_url)
    # and md5
    _intercept_md5_url(requests_mock, xml_file, xml_url)


def _intercept_md5_url(requests_mock: Mocker, xml_file: Path, xml_url: str):
    xml_file_content: bytes = xml_file.read_bytes()
    #
    xml_file_md5 = hashlib.md5(xml_file_content).hexdigest().encode("utf-8")
    xml_url_md5 = xml_url.replace(".xml", ".md5")
    # then intercept url
    requests_mock.get(xml_url_md5, headers={}, content=xml_file_md5)


def _intercept_xml_url(requests_mock: Mocker, xml_file: Path, xml_url: str):
    xml_file_content: bytes = get_file_content(xml_file)
    #
    _headers = {"content-type": "application/xml"}
    requests_mock.head(xml_url, headers=_headers)
    requests_mock.get(xml_url, headers=_headers, content=xml_file_content)
