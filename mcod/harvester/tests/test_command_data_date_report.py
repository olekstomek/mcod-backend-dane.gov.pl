import hashlib
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import List
from uuid import uuid4

import pandas as pd
import pytest
from django.db.models import QuerySet
from requests_mock import Mocker

from mcod.datasets.factories import DatasetFactory
from mcod.harvester.factories import CKANDataSourceFactory, XMLDataSourceFactory
from mcod.harvester.management.commands.generate_data_date_report import (
    FIELD_NAMES_REPORT,
    fetch_remote_data_date,
    find_resources,
    main,
)
from mcod.harvester.models import DataSource
from mcod.lib.utils import get_file_content
from mcod.resources.factories import ResourceFactory


@pytest.fixture(scope="function")
def xml_datasource_with_resources() -> List[DataSource]:
    xmls = XMLDataSourceFactory.create_batch(5)
    for idx, datasource in enumerate(xmls):
        ds1 = DatasetFactory.create(
            ext_ident=lambda: f"xml-{idx}-d",
            source=datasource,
        )
        ResourceFactory.create(
            ext_ident=lambda: f"{ds1.ext_ident}-1",
            dataset=ds1,
        )
    return xmls


@pytest.fixture(scope="function")
def ckan_datasource() -> DataSource:
    "Creates some resources that should be filtered out"
    ckan = CKANDataSourceFactory.create()
    ds1 = DatasetFactory.create(
        ext_ident="ckan-1-d",
        source=ckan,
    )
    ResourceFactory.create(
        ext_ident=lambda: f"{ds1.ext_ident}-1",
        dataset=ds1,
    )
    ResourceFactory.create_batch(10)
    return ds1


@pytest.mark.usefixtures("ckan_datasource", "xml_datasource_with_resources")
def test_resource_selection():
    # WHEN
    found: QuerySet = find_resources(not_newer_than=date.today() + timedelta(days=1))
    # THEN
    assert found.count() == 5  # number of resources in the fixture xml_datasource_with_resources: DataSource
    assert all([r["resource_ext_ident"].startswith("xml") for r in found])
    # and
    assert all([r["xml_url"].startswith("http") for r in found])


@pytest.mark.usefixtures("ckan_datasource", "xml_datasource_with_resources")
def test_resource_selection_limit(xml_datasource_with_resources: List[DataSource]):
    # WHEN
    found: QuerySet = find_resources(not_newer_than=date.today() + timedelta(days=1), offset=1, limit=2)
    # THEN
    assert found.count() == 2
    assert [r["resource_ext_ident"] for r in found] == ["xml-1-d-1", "xml-2-d-1"]


@pytest.fixture
def mocked_xml_url(requests_mock: Mocker) -> str:
    # Given
    xml_url = f"https://example.dane.gov.pl/{uuid4()}.xml"
    # and file content
    schema_version = "1.13"
    xml_file_name = f"import_example{schema_version}.xml"
    _set_up_mocks_for_file(requests_mock, Path("harvester") / xml_file_name, xml_url)
    # and finally
    return xml_url


def _set_up_mocks_for_file(requests_mock: Mocker, xml_file: Path, xml_url: str):
    xml_file_content: bytes = get_file_content(xml_file)
    # then intercept urls
    _headers = {"content-type": "application/xml"}
    requests_mock.head(xml_url, headers=_headers)
    requests_mock.get(xml_url, headers=_headers, content=xml_file_content)
    # and md5
    xml_file_md5 = hashlib.md5(xml_file_content).hexdigest().encode("utf-8")
    xml_url_md5 = xml_url.replace(".xml", ".md5")
    # then intercept url
    requests_mock.get(xml_url_md5, headers={}, content=xml_file_md5)


def test_xml_fetch(mocked_xml_url: str):
    # WHEN
    data_date = fetch_remote_data_date(mocked_xml_url)
    # THEN
    assert data_date == [
        ("dataset_extId_ver1.13", "dataset_extId_ver1.11_res_1", date(2021, 10, 10)),
        ("dataset_extId_ver1.13", "dataset_extId_ver1.11_res_2", date(2020, 10, 10)),
        ("dataset_extId_ver1.13", "dataset_extId_ver1.11_res_3", date(2021, 10, 10)),
        ("dataset_extId_ver1.13", "dataset_extId_ver1.11_res_4", date(2021, 10, 10)),
    ]


@pytest.mark.usefixtures("xml_datasource_with_resources")
def test_main(requests_mock: Mocker):
    # GIVEN
    xml_url = f"https://example.dane.gov.pl/{uuid4()}.xml"
    test_file = Path("harvester") / "import_example1.13_data_date.xml"
    _set_up_mocks_for_file(requests_mock, test_file, xml_url)
    # and
    datasource = XMLDataSourceFactory.create(xml_url=xml_url)
    ds1 = DatasetFactory.create(
        ext_ident="xml-ds-1",
        source=datasource,
    )
    # and resource matching XML file
    ResourceFactory.create(ext_ident=f"{ds1.ext_ident}-1", dataset=ds1, data_date=date(2026, 1, 20))
    # and resource with a differing data date
    ResourceFactory.create(ext_ident=f"{ds1.ext_ident}-2", dataset=ds1, data_date=date(2026, 1, 21))
    # and resource missing from the xml
    ResourceFactory.create(ext_ident=f"{ds1.ext_ident}-3", dataset=ds1, data_date=date(2026, 1, 21))
    # f"{ds1.ext_ident}-4" exists in the xml
    # and 2nd dataset
    ds2 = DatasetFactory.create(
        ext_ident="xml-ds-2",
        source=datasource,
    )
    # and resource without data_date, neither in DB nor XML
    ResourceFactory.create(ext_ident=f"{ds2.ext_ident}-1", dataset=ds2, data_date=None)
    # and resource without data_date in XML but existing in DB
    ResourceFactory.create(ext_ident=f"{ds2.ext_ident}-2", dataset=ds2, data_date=date(2026, 1, 21))
    # and resource with data_date in XML but without in DB
    ResourceFactory.create(ext_ident=f"{ds2.ext_ident}-3", dataset=ds2, data_date=None)
    # and a datasource for which xml will error
    datasource_missing = XMLDataSourceFactory.create(xml_url=f"https://example.dane.gov.pl/{uuid4()}.xml")
    ds3 = DatasetFactory.create(
        ext_ident="xml-ds-3",
        source=datasource_missing,
    )
    ResourceFactory.create(ext_ident=f"{ds3.ext_ident}-1", dataset=ds3, data_date=date(2026, 1, 20))
    ResourceFactory.create(ext_ident=f"{ds3.ext_ident}-2", dataset=ds3, data_date=date(2026, 1, 21))
    # and
    _, csv_file_name = tempfile.mkstemp()
    # WHEN
    main(
        csv_file_name,
        dry_run=False,
        resources_not_newer_than=date.today() + timedelta(days=1),
        offset=0,
        limit=0,
    )
    # THEN
    df = pd.read_csv(csv_file_name)
    expected_rows = 5 + 3 + 3 + 2  # resources in datasets created above
    assert df.shape == (expected_rows, len(FIELD_NAMES_REPORT))
    assert [c for c in df.columns] == list(FIELD_NAMES_REPORT)
    # and
    matching_resource_line = df.loc[df["resource_ext_ident"] == "xml-ds-1-1"].to_dict("records")[0]
    assert matching_resource_line["remote_data_date"] == "2026-01-20"
    assert matching_resource_line["resource_data_date"] == "2026-01-20"
    assert matching_resource_line["dates_differ"] is False
    # and
    matching_resource_line = df.loc[df["resource_ext_ident"] == "xml-ds-2-3"].to_dict("records")[0]
    assert matching_resource_line["remote_data_date"] == "2026-01-14"
    assert matching_resource_line["dates_differ"] is True
    assert matching_resource_line["resource_data_date"] == date.today().isoformat()  # Set in Resourcepre_save
