from unittest.mock import MagicMock

from django.utils.translation import override
from pytest_bdd import scenarios

from mcod.harvester.factories import (
    CKANDataSourceFactory,
    DCATDataSourceFactory,
    XMLDataSourceFactory,
)

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
