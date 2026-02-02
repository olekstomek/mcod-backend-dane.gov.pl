import json
import logging
import os
import re
import ssl
import tempfile
from hashlib import md5
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from urllib.parse import unquote
from xml.etree import ElementTree

import requests
import xmlschema
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from requests.structures import CaseInsensitiveDict

from mcod import settings
from mcod.resources.link_validation import generate_random_user_agent
from mcod.unleash import is_enabled

xmlschema.limits.MAX_XML_DEPTH = 100  # https://xmlschema.readthedocs.io/en/latest/usage.html#limit-on-xml-data-depth

logger = logging.getLogger("mcod")

requests.packages.urllib3.disable_warnings()


try:
    # https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error/55320961#55320961
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


def make_request(url: str, head_only: bool = False, headers: Optional[dict] = None) -> requests.Response:
    opts: Dict = settings.HTTP_REQUEST_DEFAULT_PARAMS.copy()
    if headers:
        opts["headers"] = headers
    method = "HEAD" if head_only else "GET"
    response = requests.request(method, url, **opts)
    if not response.ok:
        msg = _("%(url)s: invalid response code: %(code)s (%(reason)s)")
        raise Exception(msg % {"url": url, "code": response.status_code, "reason": response.reason})
    return response


def fetch_data(url):
    r = make_request(url)
    try:
        data = json.loads(r.content)
    except Exception as exc:
        raise Exception(f"No valid JSON data in response!\n{exc}")
    data = data.get("result")
    return data["results"] if "results" in data else data


def get_xml_schema_version(*, xml_path=None, xml_url=None):
    if xml_url:
        response = make_request(xml_url)
        xml_payload = response.text
        root = ElementTree.fromstring(xml_payload)
    else:
        root = ElementTree.parse(xml_path).getroot()

    version_match = re.search(r"{urn:otwarte-dane:harvester:(.*)}", root.tag)
    if not version_match:
        raise Exception("Nie znaleziono informacji o wersji użytego schematu XSD")

    version = version_match.group(1)
    try:
        get_xml_schema_path(version)
    except KeyError:
        raise Exception(f"Niepoprawna wersja schematu XSD: {version}")

    return version


def get_xml_schema_path(version):
    versions = {}
    flag = versions.get(version)
    if flag and not is_enabled(flag):
        raise KeyError(version)
    return settings.HARVESTER_XML_VERSION_TO_SCHEMA_PATH[version]


def get_xml_schema(version):
    return xmlschema.XMLSchema(get_xml_schema_path(version))


def get_xml_as_dict(source: Union[str, Path], version: str) -> Dict:
    """
    Args:
        source: Path, filename (str), remote URL (str)
        version: one of the supported schema version, e.g. 1.13

    Returns: XML data deserialized to a Dict
    """
    schema = get_xml_schema(version)
    data = schema.to_dict(source)
    data["xsd_schema_version"] = version
    return data


def decode_xml(url):
    version = get_xml_schema_version(xml_url=url)
    return get_xml_as_dict(url, version)


class FetchedDatasets(list):
    """Wrapper over list to add metadata field
    Elements are dict.
    TODO: refactor together with import_data
    """

    xsd_schema_version: str

    def __init__(self, obj, xsd_schema_version: str):
        super().__init__(obj)
        self.xsd_schema_version = xsd_schema_version


# see base.py:HARVESTER_IMPORTERS for usages
def fetch_xml_data(url: str) -> Optional[FetchedDatasets]:
    try:
        saved_filename, xml_hash, xml_schema_version = validate_xml_url(url)
        data = get_xml_as_dict(saved_filename, xml_schema_version)
    except Exception as exc:
        raise Exception(f"XML Validation error!\n{exc}") from exc
    if isinstance(data, dict) and "dataset" in data:
        return FetchedDatasets(data["dataset"], data["xsd_schema_version"])
    else:
        return None


def mock_data(url):
    with open("mcod/harvester/fixtures/mock2.json") as mock_file:
        data = json.loads(mock_file.read())
        data = data.get("result")
        return data["results"] if "results" in data else data


def validate_xml(xml_path: Union[str, Path]) -> str:
    """
    Args:
        xml_path: Path to file containing the XML content

    Returns: Schema version as a str
    Raises XMLSchemaValidationError: if the schema isn't met
    Raises Exception: in case we can't infer schema version
    """
    xml_schema_version = get_xml_schema_version(xml_path=xml_path)
    xml_schema = get_xml_schema(xml_schema_version)
    xml_schema.validate(xml_path)
    return xml_schema_version


def get_remote_xml_hash(url):
    source_url_prefix, ext = os.path.splitext(url)
    xml_hash_url = f"{source_url_prefix}.md5"
    response = make_request(xml_hash_url)
    xml_hash = response.content.decode("utf-8").rstrip().lower() if response.content else None
    matches = re.finditer(r"(?=(\b[A-Fa-f0-9]{32}\b))", xml_hash)
    result = [match.group(1) for match in matches]
    if not result:
        msg = _('"%(value)s" is not valid MD5 hash!')
        value = "{}...".format(xml_hash[:40]) if len(xml_hash) > 32 else xml_hash
        raise Exception(msg % {"value": value})
    return xml_hash_url, xml_hash


def get_xml_headers(url):
    try:
        response = make_request(url, head_only=True)
    except Exception as e:
        logger.error("Fatal exception in get_xml_headers", exc_info=True)
        raise Exception(_("External resource is not available!")) from e
    return response.headers


def check_content_type(headers):
    content_type = headers.get("Content-Type", "")
    if all(["text/xml" not in content_type, "application/xml" not in content_type]):  # "text/xml; charset=utf-8".
        raise Exception(
            _("Invalid Content-Type header: '%(content_type)s'. " "Content-Type must contain 'text/xml' or 'application/xml'!")
            % {"content_type": content_type}
        )


def check_xml_filename(url):
    if url.endswith(".xml"):
        filename = os.path.basename(url)
        if " " in unquote(filename):
            raise Exception(_("Invalid file name: %(filename)s!") % {"filename": filename})


def retrieve_to_file(url: str) -> Tuple[str, Dict[str, str]]:
    headers = {"User-Agent": generate_random_user_agent()}
    response = make_request(url, headers=headers)
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp_file:
        for chunk in response.iter_content(chunk_size=512):
            tmp_file.write(chunk)
    return tmp_file.name, response.headers


def validate_md5(filename: str, remote_xml_hash: str) -> str:
    m = md5()
    with open(filename, "rb") as fp:
        for chunk in fp:
            m.update(chunk)
    xml_hash = m.hexdigest()
    if xml_hash != remote_xml_hash:
        raise Exception(_("Remote MD5 hash is not valid!"))
    return xml_hash


def validate_xml_url(url: str) -> Tuple[Union[str, Path], str, str]:
    """
    Checks performed:
    - url has to respond to head
    - filename has to end in `.xml`
    - sensible content-type header
    - md5 sum (using a transformed url)
    - XSD validation

    Args:
        url: Remote url to the XML file

    Returns: A tuple of
     1. path to the temporary file containing downloaded content
     2. md5 digest
     3. schema version
    """
    try:
        check_xml_filename(url)
        headers: CaseInsensitiveDict = get_xml_headers(url)
        check_content_type(headers)
        _, remote_hash = get_remote_xml_hash(url)
        filename: str
        filename, headers = retrieve_to_file(url)
        xml_hash: str = validate_md5(filename, remote_hash)
        xml_schema_version: str = validate_xml(filename)
    except Exception as exc:
        raise ValidationError({"xml_url": str(exc)})
    return filename, xml_hash, xml_schema_version


def fetch_dcat_data(api_url, query):
    store = SPARQLStore(query_endpoint=api_url, returnFormat="application/rdf+xml")
    results = store.query(query, DEBUG=True)
    return results.graph if results else {}
