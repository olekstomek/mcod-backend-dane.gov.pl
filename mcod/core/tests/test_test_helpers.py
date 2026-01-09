from datetime import datetime
from typing import Any

import pytest

from mcod.core.tests.helpers.helpers import AnyDateTimeTestVariable


class TestDateTimeTestVariable:

    def test_eq_with_datetime_object(self):
        """Test equality with a standard datetime object."""
        variable = AnyDateTimeTestVariable()
        assert variable == datetime.now()

    @pytest.mark.parametrize(
        "iso_string",
        [
            "2025-10-30T20:45:00Z",
            "2025-10-30T20:45:00.123456Z",
            "2025-10-30T20:45:00+02:00",
            "2025-10-30T20:45:00",
            "2025-10-30T20:45",
            "2025-10-30T20",
        ],
    )
    def test_eq_with_valid_iso_string(self, iso_string: str):
        """Test equality with various valid ISO 8601 datetime strings."""
        variable = AnyDateTimeTestVariable()
        assert variable == iso_string

    @pytest.mark.parametrize("invalid_string", ["10:30", "2025-07-06", "pure-string"])  # pure date should be invalid
    def test_not_eq_with_invalid_iso_string(self, invalid_string: str):
        variable = AnyDateTimeTestVariable()
        assert variable != invalid_string

    @pytest.mark.parametrize(
        "invalid_variable",
        [
            1,
            2.0,
            [
                3,
            ],
            (4,),
            {"e": 5},
            {6},
        ],
    )
    def test_not_eq_with_invalid_variable_type(self, invalid_variable: Any):
        variable = AnyDateTimeTestVariable()
        assert variable != invalid_variable
