import warnings
from typing import Any, Dict, Optional

from django.utils.translation import gettext_lazy
from requests import Response

from mcod.harvester.ckan_utils import CKANPartialImportError


class CKANPartialValidationException(Exception):
    """
    Custom exception for CKAN partial validation errors.
    Stores both the error code and associated error data.
    This data is later used to generate detailed error descriptions.
    """

    def __init__(self, error_code: CKANPartialImportError, error_data: Dict[str, Any]):
        self.error_code = error_code
        self.error_data = error_data
        super().__init__(f"CKAN Partial Validation error: {error_code}.")


class XMLValidationException(Exception):
    """Custom wrapper for Exceptions, serves two purposes:
    1. wraps translation, since we localise error messages
    2. makes the error pickle'able by celery (see UnpickleableExceptionWrapper).

    Calling init with kwargs will use them with the `message_template`, while call with positional args
    will just pass it to super class.
    """

    message_template: str

    def __init__(self, *args, **kwargs):
        if args and not kwargs:
            super().__init__(*args)
        elif not args and kwargs:
            translated = gettext_lazy(self.message_template)
            formatted = translated % kwargs
            super().__init__(formatted)
        else:
            warnings.warn("XMLValidationException accepts either a message or kwargs")


class UnexpectedStatusCode(XMLValidationException):
    message_template = "%(url)s: invalid response code: %(code)s (%(reason)s)"

    def __init__(self, *args, url: str, response: Response):
        super().__init__(*args, url=url, code=response.status_code, reason=response.reason)


class XMLDoesNotMatchMD5Pattern(XMLValidationException):
    """Exception when the .md5 url response body does not contain a string that looks like an MD5
    and special case when it is empty.
    """

    message_template = "%(url)s: \"%(value)s\" is not valid MD5 hash!"  # fmt: skip

    def __init__(self, *args, url: str = "", response_body: Optional[str] = None):
        super().__init__(*args, url=url, value=self._truncate_hash_value(response_body))

    @staticmethod
    def _truncate_hash_value(response_body: Optional[str]) -> str:
        if not response_body:
            return ""
        try:
            if len(response_body) > 32:
                return f"{response_body[:40]}..."
            else:
                return response_body
        except Exception:
            # Don't fail during error handling
            return ""


class XMLMD5DoesNoMatch(XMLValidationException):
    """Remote hash value doesn't match the expected hash value we've computed."""

    message_template = "%(url)s: remote MD5 hash is not valid!"

    def __init__(self, *args, url: str = ""):
        super().__init__(*args, url=url)
