from datetime import datetime
from typing import Any


class AnyDateTimeTestVariable:
    """A utility class for asserting datetime equality.

    This class serves as a flexible marker in assertions that always returns `True`
    when compared against a valid `datetime` object or its string representation
    (conforming to ISO 8601). It is particularly useful in testing scenarios where
    the exact timestamp value is unknown but its format is expected.

    The comparison `assert x == my_class_instance` will succeed if `x` is:
    - a `datetime` object instance,
    - a valid `datetime` string in ISO 8601 format (containing a 'T' separator).

    All other data types, including strings representing a date only (e.g., "2025-10-10"),
    will return `False`.

    Example:
        >>> from datetime import datetime
        >>> a = AnyDateTimeTestVariable()
        >>> a == datetime.now()
        True
        >>> a == "2025-10-30T20:45:00Z"
        True
        >>> from datetime import date
        >>> a == date(2025, 10, 30)
        False
        >>> a == "2025-10-30"
        False
    """

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, datetime):
            return True
        if isinstance(other, str):
            if "T" not in other:
                return False
            try:
                datetime.fromisoformat(other.replace("Z", "+00:00"))
                return True
            except (ValueError, TypeError):
                return False
        return False
