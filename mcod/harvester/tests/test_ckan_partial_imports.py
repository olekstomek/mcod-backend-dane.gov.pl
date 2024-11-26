from typing import Any, Dict, List
from unittest.mock import MagicMock, call, patch

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from mcod.datasets.factories import DatasetFactory
from mcod.harvester.ckan_utils import (
    CKANPartialImportError,
    format_dataset_hvd_conflict_error_details,
    format_dataset_in_trash_error_details,
    format_dataset_org_hvd_ec_conflict_error_details,
    format_invalid_license_error_details,
    format_organization_in_trash_error_details,
    format_res_hvd_conflict_error_details,
    format_res_org_hvd_ec_conflict_error_details,
)
from mcod.harvester.exceptions import CKANPartialValidationException
from mcod.harvester.factories import CKANDataSourceFactory
from mcod.harvester.models import DataSource
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.dga_constants import ALLOWED_INSTITUTIONS_TO_USE_HIGH_VALUE_DATA_FROM_EC_LIST


@pytest.mark.ckan_partial_import
class TestCKANErrorDescriptionFormatters:
    def test_format_invalid_license_error_details(self):
        error_data = [
            {
                "item_id": "dataset-id-1",
                "license_id": "some-license-id-1",
            },
            {
                "item_id": "dataset-id-2",
                "license_id": "some-license-id-2",
            },
        ]
        result = format_invalid_license_error_details(error_data)
        expected_result = (
            'Wartość w polu license_id spoza słownika CC<div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p>"
            "<p><strong>license_id:</strong> some-license-id-1</p><br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p>"
            "<p><strong>license_id:</strong> some-license-id-2</p></div>"
        )
        assert result == expected_result

    def test_format_organization_in_trash_error_details(self):
        error_data = [
            {
                "item_id": "dataset-id-1",
                "organization_title": "Org Title 1",
            },
            {
                "item_id": "dataset-id-2",
                "organization_title": "Org Title 2",
            },
        ]
        result = format_organization_in_trash_error_details(error_data)
        expected_result = (
            '<p>Instytucja znajduje się w koszu</p><div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p>"
            "<p><strong>organization.title:</strong> Org Title 1</p><br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p>"
            "<p><strong>organization.title:</strong> Org Title 2</p></div>"
        )
        assert result == expected_result

    def test_format_dataset_in_trash_error_details(self):
        error_data = [{"item_id": "dataset-id-1"}, {"item_id": "dataset-id-2"}]
        result = format_dataset_in_trash_error_details(error_data)
        expected_result = (
            '<p>Zbiór danych znajduje się w koszu</p><div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p><br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p></div>"
        )
        assert result == expected_result

    def test_format_dataset_org_hvd_ec_conflict_error_details(self):
        error_data = [{"item_id": "dataset-id-1"}, {"item_id": "dataset-id-2"}]
        result = format_dataset_org_hvd_ec_conflict_error_details(error_data)
        expected_result = (
            "<p>Instytucja typu 'prywatna' nie może wybrać wartości true w polu "
            "'has_high_value_data_from_european_commission_list' zbioru danych.</p>"
            '<div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p><br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p></div>"
        )
        assert result == expected_result

    def test_format_dataset_hvd_conflict_error_details(self):
        error_data = [{"item_id": "dataset-id-1"}, {"item_id": "dataset-id-2"}]
        result = format_dataset_hvd_conflict_error_details(error_data)
        expected_result = (
            "<p>Pole zbioru danych 'has_high_value_data' musi mieć wartość równą true, "
            "jeżeli pole 'has_high_value_data_from_european_commission_list' ma wartość true.</p>"
            '<div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p><br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p></div>"
        )
        assert result == expected_result

    def test_format_res_org_hvd_ec_conflict_error_details(self):
        error_data = [
            {"item_id": "dataset-id-1", "resources_ids": ["resource-id-1", "resource-id-2"]},
            {"item_id": "dataset-id-2", "resources_ids": ["resource-id-3"]},
        ]
        result = format_res_org_hvd_ec_conflict_error_details(error_data)
        expected_result = (
            "<p>Instytucja typu 'prywatna' nie może wybrać wartości true w polu "
            "'has_high_value_data_from_european_commission_list' zasobu.</p>"
            '<div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p>"
            "<p><strong>id zasobu:</strong> resource-id-1</p>"
            "<br>"
            "<p><strong>id zasobu:</strong> resource-id-2</p>"
            "<br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p>"
            "<p><strong>id zasobu:</strong> resource-id-3</p>"
            "</div>"
        )
        assert result == expected_result

    def test_format_res_hvd_conflict_error_details(self):
        error_data = [
            {"item_id": "dataset-id-1", "resources_ids": ["resource-id-1", "resource-id-2"]},
            {"item_id": "dataset-id-2", "resources_ids": ["resource-id-3"]},
        ]
        result = format_res_hvd_conflict_error_details(error_data)
        expected_result = (
            "<p>Pole zasobu 'has_high_value_data' musi mieć wartość równą true, jeżeli pole "
            "'has_high_value_data_from_european_commission_list' ma wartość true.</p>"
            '<div class="expandable">'
            "<p><strong>id zbioru danych:</strong> dataset-id-1</p>"
            "<p><strong>id zasobu:</strong> resource-id-1</p>"
            "<br>"
            "<p><strong>id zasobu:</strong> resource-id-2</p>"
            "<br>"
            "<p><strong>id zbioru danych:</strong> dataset-id-2</p>"
            "<p><strong>id zasobu:</strong> resource-id-3</p>"
            "</div>"
        )
        assert result == expected_result


@pytest.fixture
def data_source() -> DataSource:
    return CKANDataSourceFactory.create(institution_type="other")


@pytest.fixture
def base_item_data() -> Dict[str, Any]:
    return {
        "ext_ident": "dataset-id-1",
    }


@pytest.fixture
def base_item_with_resources_data() -> Dict[str, Any]:
    return {
        "ext_ident": "dataset-id-1",
        "resources": [
            {
                "ext_ident": "resource-id-1",
                "has_high_value_data_from_ec_list": True,
                "has_high_value_data": True,
            },
            {
                "ext_ident": "resource-id-2",
                "has_high_value_data_from_ec_list": False,
                "has_high_value_data": False,
            },
        ],
    }


@pytest.fixture
def sample_item_resources_data() -> List[Dict[str, Any]]:
    resources = [
        {
            "ext_ident": "resource-id-1",
            "has_high_value_data_from_ec_list": True,
            "has_high_value_data": True,
        },
        {
            "ext_ident": "resource-id-2",
            "has_high_value_data_from_ec_list": False,
            "has_high_value_data": False,
        },
    ]
    return resources


@pytest.mark.ckan_partial_import
class TestDataSourceCKANPartialImports:
    ckan_licenses_whitelist = settings.CKAN_LICENSES_WHITELIST.keys()
    allowed_hvd_institution_types = ALLOWED_INSTITUTIONS_TO_USE_HIGH_VALUE_DATA_FROM_EC_LIST

    def test_get_error_description_formatters_for_all_error_codes(self):
        formatters = DataSource._get_error_description_formatters()

        all_error_codes = set(error for error in CKANPartialImportError)
        formatters_codes = set(formatters.keys())

        assert formatters_codes == all_error_codes

    @pytest.mark.parametrize("license_id", ckan_licenses_whitelist)
    def test_validate_item_license_id_valid(self, data_source: DataSource, base_item_data: Dict[str, Any], license_id: str):
        base_item_data.update({"license_id": license_id})
        data_source._ckan_validate_item_license_id(base_item_data)

    @pytest.mark.parametrize("license_id", ["", None, "not-existing-license"])
    def test_validate_item_license_id_invalid(self, data_source: DataSource, base_item_data: Dict[str, Any], license_id: str):
        base_item_data.update({"license_id": license_id})
        with pytest.raises(CKANPartialValidationException) as exc:
            data_source._ckan_validate_item_license_id(base_item_data)

        validation_exc = exc.value
        assert validation_exc.error_code == CKANPartialImportError.INVALID_LICENSE_ID
        assert validation_exc.error_data["item_id"] == base_item_data["ext_ident"]
        assert validation_exc.error_data["license_id"] == license_id

    @pytest.mark.parametrize("org_exists", (True, False))
    def test_validate_item_organization_not_in_trash_valid(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
        org_exists: bool,
    ):
        organization_title = "Organization Title"
        if org_exists:
            OrganizationFactory.create(title=organization_title)

        base_item_data.update({"organization": {"title": organization_title}})

        data_source._ckan_validate_item_organization_not_in_trash(base_item_data)

    def test_validate_item_organization_not_in_trash_invalid(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
    ):
        organization_title = "Organization Title"
        OrganizationFactory.create(title=organization_title, is_removed=True)

        base_item_data.update({"organization": {"title": organization_title}})

        with pytest.raises(CKANPartialValidationException) as exc:
            data_source._ckan_validate_item_organization_not_in_trash(base_item_data)

        validation_exc = exc.value
        assert validation_exc.error_code == CKANPartialImportError.ORGANIZATION_IN_TRASH
        assert validation_exc.error_data["item_id"] == base_item_data["ext_ident"]
        assert validation_exc.error_data["organization_title"] == organization_title

    @pytest.mark.parametrize("dataset_exists", (True, False))
    def test_validate_item_dataset_not_in_trash_valid(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
        dataset_exists: bool,
    ):
        if dataset_exists:
            DatasetFactory.create(
                ext_ident=base_item_data["ext_ident"],
                source=data_source,
            )

        data_source._ckan_validate_item_dataset_not_in_trash(base_item_data)

    def test_validate_item_dataset_not_in_trash_invalid(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
    ):
        DatasetFactory.create(
            ext_ident=base_item_data["ext_ident"],
            source=data_source,
            is_removed=True,
        )

        with pytest.raises(CKANPartialValidationException) as exc:
            data_source._ckan_validate_item_dataset_not_in_trash(base_item_data)

        validation_exc = exc.value
        assert validation_exc.error_code == CKANPartialImportError.DATASET_IN_TRASH
        assert validation_exc.error_data["item_id"] == base_item_data["ext_ident"]

    @pytest.mark.parametrize("is_conflict", (True, False))
    def test_validate_item_dataset_org_ec_conflict(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
        is_conflict: bool,
    ):
        # GIVEN
        hvd_ec = True
        institution_type = "some institution type"  # no exact check in this test

        base_item_data.update({"has_high_value_data_from_ec_list": hvd_ec})
        base_item_data.update({"organization": {"title": institution_type}})

        # Mock item institution type retriever
        data_source._get_item_institution_type = MagicMock(return_value=institution_type)

        # WHEN
        # Use patch because of no need to test validate_high_value_data_from_ec_list_organization again
        with patch("mcod.harvester.models.validate_high_value_data_from_ec_list_organization") as hvd_ec_org_validator:
            if is_conflict:
                hvd_ec_org_validator.side_effect = ValidationError(
                    "Cannot use `high_value_data_from_ec_list` for this organization type."
                )
                with pytest.raises(CKANPartialValidationException) as exc:
                    data_source._ckan_validate_item_dataset_org_ec_conflict(base_item_data)
            else:
                data_source._ckan_validate_item_dataset_org_ec_conflict(base_item_data)

        # THEN
        data_source._get_item_institution_type.assert_called_once_with(base_item_data)
        hvd_ec_org_validator.assert_called_once_with(hvd_ec, institution_type)
        if is_conflict:
            validation_exc = exc.value
            assert validation_exc.error_code == CKANPartialImportError.DATASET_ORG_EC_CONFLICT
            assert validation_exc.error_data["item_id"] == base_item_data["ext_ident"]

    @pytest.mark.parametrize("is_conflict", (True, False))
    def test_validate_item_dataset_hvd_conflict(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
        is_conflict: bool,
    ):
        # GIVEN
        hvd_ec = True
        hvd = True

        base_item_data.update({"has_high_value_data_from_ec_list": hvd_ec})
        base_item_data.update({"has_high_value_data": hvd})

        # WHEN
        # Use patch because of no need to test validate_conflicting_high_value_data_flags again
        with patch("mcod.harvester.models.validate_conflicting_high_value_data_flags") as hvd_validator:
            if is_conflict:
                hvd_validator.side_effect = ValidationError("High value data flags conflict.")
                with pytest.raises(CKANPartialValidationException) as exc:
                    data_source._ckan_validate_item_dataset_hvd_conflict(base_item_data)
            else:
                data_source._ckan_validate_item_dataset_hvd_conflict(base_item_data)

        # THEN
        hvd_validator.assert_called_once_with(hvd, hvd_ec)
        if is_conflict:
            validation_exc = exc.value
            assert validation_exc.error_code == CKANPartialImportError.DATASET_HVD_CONFLICT
            assert validation_exc.error_data["item_id"] == base_item_data["ext_ident"]

    def test_validate_item_resource_org_ec_conflict(
        self,
        data_source: DataSource,
        base_item_with_resources_data: Dict[str, Any],
    ):
        # GIVEN
        # Set only to check whether the corresponding function has been called with this parameter.
        institution_type = "some institution type"

        resources: List[Dict[str, Any]] = base_item_with_resources_data["resources"]
        base_item_with_resources_data.update({"organization": {"title": institution_type}})

        # Mock item institution type retriever
        data_source._get_item_institution_type = MagicMock(return_value=institution_type)

        # Use patch because of no need to test validate_high_value_data_from_ec_list_organization again.
        with patch("mcod.harvester.models.validate_high_value_data_from_ec_list_organization") as hvd_ec_org_validator:

            # Assume that the first resource is invalid and the second one is valid.
            # Validation function will raise exception for the first resource
            # and return None for the second one.

            # It is worth noting that the submitted metadata is not validated,
            # and only the call to the function validating it is tested.
            hvd_ec_org_validator.side_effect = [
                ValidationError("Cannot use `high_value_data_from_ec_list` for this organization type."),
                None,
            ]

            # WHEN
            with pytest.raises(CKANPartialValidationException) as exc:
                data_source._ckan_validate_item_resources_org_ec_conflict(base_item_with_resources_data)

        # THEN
        # Validator should be run for all (2) resources.
        expected_calls = [
            call(
                resources[0]["has_high_value_data_from_ec_list"],
                institution_type,
            ),
            call(
                resources[1]["has_high_value_data_from_ec_list"],
                institution_type,
            ),
        ]
        hvd_ec_org_validator.assert_has_calls(expected_calls, any_order=False)

        # Check error contains invalid resource data only.
        validation_exc = exc.value
        assert validation_exc.error_code == CKANPartialImportError.RES_ORG_EC_CONFLICT
        assert validation_exc.error_data["item_id"] == base_item_with_resources_data["ext_ident"]
        assert validation_exc.error_data["resources_ids"] == [resources[0]["ext_ident"]]

    def test_validate_item_resource_hvd_conflict(
        self,
        data_source: DataSource,
        base_item_with_resources_data: Dict[str, Any],
    ):
        # GIVEN
        resources: List[Dict[str, Any]] = base_item_with_resources_data["resources"]

        # Use patch because of no need to test validate_conflicting_high_value_data_flags again
        with patch("mcod.harvester.models.validate_conflicting_high_value_data_flags") as hvd_validator:

            # Assume that the first resource is invalid and the second one is valid.
            # Validation function will raise exception for the first resource
            # and return None for the second one.

            # It is worth noting that the submitted metadata is not validated,
            # and only the call to the function validating it is tested.
            hvd_validator.side_effect = [
                ValidationError("High value data flags conflict."),
                None,
            ]

            # WHEN
            with pytest.raises(CKANPartialValidationException) as exc:
                data_source._ckan_validate_item_resources_hvd_conflict(base_item_with_resources_data)

        # THEN
        # Validator should be run for all (2) resources.
        expected_calls = [
            call(
                resources[0]["has_high_value_data"],
                resources[0]["has_high_value_data_from_ec_list"],
            ),
            call(
                resources[1]["has_high_value_data"],
                resources[1]["has_high_value_data_from_ec_list"],
            ),
        ]
        hvd_validator.assert_has_calls(expected_calls, any_order=False)

        # Check error contains invalid resource data only.
        validation_exc = exc.value
        assert validation_exc.error_code == CKANPartialImportError.RES_HVD_CONFLICT
        assert validation_exc.error_data["item_id"] == base_item_with_resources_data["ext_ident"]
        assert validation_exc.error_data["resources_ids"] == [resources[0]["ext_ident"]]

    def test_get_item_institution_type_default_type(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
    ):
        # GIVEN
        default_institution_type = "other"  # explicit set
        data_source.institution_type = default_institution_type
        base_item_data.update({"organization": {"title": "Not existing Organization"}})

        # WHEN
        item_institution_type = data_source._get_item_institution_type(base_item_data)

        # THEN
        assert item_institution_type == default_institution_type

    def test_get_item_institution_type_existing(
        self,
        data_source: DataSource,
        base_item_data: Dict[str, Any],
    ):
        # GIVEN
        default_institution_type = "other"  # explicit set
        data_source.institution_type = default_institution_type

        organization_title = "Organization Title"
        organization_type = "private"
        OrganizationFactory.create(title=organization_title, institution_type=organization_type)

        base_item_data.update({"organization": {"title": organization_title}})

        # WHEN
        item_institution_type = data_source._get_item_institution_type(base_item_data)

        # THEN
        assert item_institution_type == organization_type
