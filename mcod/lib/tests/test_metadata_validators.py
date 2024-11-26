import pytest
from django.core.exceptions import ValidationError

from mcod.lib.metadata_validators import (
    validate_conflicting_high_value_data_flags,
    validate_high_value_data_from_ec_list_organization,
)
from mcod.organizations.models import Organization


@pytest.mark.parametrize(
    ("has_high_value_data", "has_high_value_data_from_ec_list", "validation_exc_occurred"),
    [
        (True, True, False),
        (False, False, False),
        (True, False, False),
        (True, None, False),
        (False, None, False),
        (None, True, True),  # conflicting
        (None, False, False),
        (None, None, False),
        (False, True, True),  # conflicting
    ],
)
def test_validate_conflicting_high_value_data_flags(
    has_high_value_data: bool,
    has_high_value_data_from_ec_list: bool,
    validation_exc_occurred: bool,
):
    if validation_exc_occurred:
        with pytest.raises(ValidationError):
            validate_conflicting_high_value_data_flags(
                has_high_value_data,
                has_high_value_data_from_ec_list,
            )
    else:
        validate_conflicting_high_value_data_flags(
            has_high_value_data,
            has_high_value_data_from_ec_list,
        )


@pytest.mark.parametrize(
    ("has_high_value_data_from_ec_list", "organization_type", "should_raise"),
    [
        # Test cases where ValidationError should be raised
        (True, Organization.INSTITUTION_TYPE_PRIVATE, True),
        # Test cases where ValidationError should not be raised
        (True, Organization.INSTITUTION_TYPE_LOCAL, False),
        (True, Organization.INSTITUTION_TYPE_STATE, False),
        (True, Organization.INSTITUTION_TYPE_OTHER, False),
        (False, Organization.INSTITUTION_TYPE_PRIVATE, False),
        (False, Organization.INSTITUTION_TYPE_OTHER, False),
        (False, Organization.INSTITUTION_TYPE_LOCAL, False),
        (False, Organization.INSTITUTION_TYPE_STATE, False),
        (None, Organization.INSTITUTION_TYPE_PRIVATE, False),
        (None, Organization.INSTITUTION_TYPE_OTHER, False),
        (None, Organization.INSTITUTION_TYPE_LOCAL, False),
        (None, Organization.INSTITUTION_TYPE_STATE, False),
    ],
)
def test_validate_high_value_data_from_ec_list(
    has_high_value_data_from_ec_list: bool,
    organization_type: str,
    should_raise: bool,
):
    """
    Tests the validation of high-value data eligibility based on organization
    type. Validates that ValidationError is raised only for private and other
    types when high-value data from EC list is set to True.
    """
    if should_raise:
        with pytest.raises(ValidationError):
            validate_high_value_data_from_ec_list_organization(
                has_high_value_data_from_ec_list,
                organization_type,
            )
    else:
        validate_high_value_data_from_ec_list_organization(
            has_high_value_data_from_ec_list,
            organization_type,
        )
