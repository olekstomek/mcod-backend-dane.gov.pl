import logging
from contextlib import contextmanager
from typing import Iterator, List

from sentry_sdk import capture_exception

logger = logging.getLogger("mcod")


@contextmanager
def report_exceptions(error_message: str, suppress: bool = False) -> Iterator[List[Exception]]:
    errors: List[Exception] = []
    try:
        yield errors
    except Exception as exc:
        logger.exception(f"{error_message}: {exc}")
        capture_exception(exc)
        errors.append(exc)
        if not suppress:
            raise
