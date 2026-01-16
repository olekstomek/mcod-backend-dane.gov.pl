from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from django.utils.translation import override
from pytest_bdd import scenarios

from mcod.datasets.models import Dataset
from mcod.harvester.factories import (
    CKANDataSourceFactory,
    DCATDataSourceFactory,
    XMLDataSourceFactory,
)
from mcod.harvester.models import DataSource
from mcod.resources.models import Resource

scenarios("features")


class TestHarvesterDataImportErrorHandling:
    """
    Tests the harvester's ability to catch and handle any unexpected exceptions
    that occur during schema validation of imported data, ensuring a failed
    DataSourceImport object is correctly created with an appropriate error description.
    """

    def test_xml_datasource_import_data_handles_unexpected_schema_validation_error(self, mocker):
        # GIVEN
        mock_non_empty_data = MagicMock()
        mock_non_empty_data.__bool__.return_value = True

        xml_datasource = XMLDataSourceFactory(status="active")
        assert xml_datasource.imports.count() == 0

        mocker.patch("mcod.harvester.utils.fetch_xml_data", return_value=mock_non_empty_data)
        mocker.patch("mcod.harvester.serializers.XMLDatasetSchema.load", side_effect=Exception)

        # WHEN
        with override("en"):
            xml_datasource.import_data()

        # THEN
        assert xml_datasource.imports.count() == 1
        assert xml_datasource.imports.last().error_desc == "Unexpected schema validation error while import data."

    def test_ckan_datasource_import_data_handles_unexpected_schema_validation_error(self, mocker):
        # GIVEN
        mock_non_empty_data = MagicMock()
        mock_non_empty_data.__bool__.return_value = True

        ckan_datasource = CKANDataSourceFactory(status="active")
        assert ckan_datasource.imports.count() == 0

        mocker.patch("mcod.harvester.utils.fetch_data", return_value=mock_non_empty_data)
        mocker.patch("mcod.harvester.serializers.DatasetSchema.load", side_effect=Exception)

        # WHEN
        with override("en"):
            ckan_datasource.import_data()

        # THEN
        assert ckan_datasource.imports.count() == 1
        assert ckan_datasource.imports.last().error_desc == "Unexpected schema validation error while import data."

    def test_dcat_datasource_import_data_handles_unexpected_schema_validation_error(self, mocker):
        # GIVEN
        mock_non_empty_data = MagicMock()
        mock_non_empty_data.__bool__.return_value = True

        dcat_datasource = DCATDataSourceFactory(status="active")
        assert dcat_datasource.imports.count() == 0

        mocker.patch("mcod.harvester.utils.fetch_dcat_data", return_value=mock_non_empty_data)
        mocker.patch("mcod.harvester.serializers.DatasetDCATSchema.load", side_effect=Exception)

        # WHEN
        with override("en"):
            dcat_datasource.import_data()

        # THEN
        assert dcat_datasource.imports.count() == 1
        assert dcat_datasource.imports.last().error_desc == "Unexpected schema validation error while import data."


@pytest.mark.parametrize(
    "value_in_dataset, value_from_harvester, dataset_created, dataset_should_be_updated",
    [
        ("aaa", "aaa", True, False),
        ("aaa", "aaa", False, False),
        ("aaa", "bbb_different", True, False),
        ("aaa", "bbb_different", False, True),
    ],
)
def test_create_or_verify_dataset(
    value_in_dataset: str, value_from_harvester: str, dataset_created: bool, dataset_should_be_updated: bool
):
    # GIVEN
    harvester: DataSource = XMLDataSourceFactory.build(status="active")
    data_from_harvester = {"ext_ident": "some_ext_ident", "source": "some_source", "notes": value_from_harvester}

    dataset = MagicMock(spec_set=Dataset)
    dataset.ext_ident = "some_ext_ident"
    dataset.source = "some_source"
    dataset.notes = value_in_dataset

    mock_model = MagicMock(spec_set=Dataset)
    mock_model.raw.get_or_create.return_value = (dataset, dataset_created)

    with patch.object(DataSource, "dataset_model", new_callable=PropertyMock, return_value=mock_model):
        # WHEN
        harvester._create_or_update_if_changed_dataset(data=data_from_harvester)
        # THEN
        if dataset_should_be_updated:
            dataset.save.assert_called_once()
        else:
            dataset.save.assert_not_called()


@pytest.mark.parametrize(
    "title_in_resource, title_from_harvester, resource_created, resource_should_be_updated",
    [
        ("aaa", "aaa", True, False),
        ("aaa", "aaa", False, False),
        ("aaa", "bbb_different", True, False),
        ("aaa", "bbb_different", False, True),
    ],
)
def test_create_or_verify_resource(
    title_in_resource: str, title_from_harvester: str, resource_created: bool, resource_should_be_updated: bool
):
    # GIVEN
    harvester: DataSource = CKANDataSourceFactory.build(status="active")
    data_from_harvester = {"ext_ident": "some_ext_ident", "title": title_from_harvester}

    dataset = MagicMock(spec_set=Dataset)

    resource = MagicMock(spec_set=Resource)
    resource.ext_ident = "some_ext_ident"
    resource.dataset = dataset
    resource.title = title_in_resource

    mock_model = MagicMock(spec_set=Resource)
    mock_model.raw.get_or_create.return_value = (resource, resource_created)

    with patch.object(DataSource, "resource_model", new_callable=PropertyMock, return_value=mock_model):
        # WHEN
        harvester._create_or_update_if_changed_resource(dataset=dataset, data=data_from_harvester)
        # THEN
        if resource_should_be_updated:
            resource.save.assert_called_once()
        else:
            resource.save.assert_not_called()
