from typing import Optional
from unittest.mock import Mock, patch

import pytest

from mcod.core.caches import flush_sessions


@pytest.mark.parametrize(
    "prefix",
    ["test_key", " ", "_", "_test_key_", " test key", "", None],
)
def test_flush_sessions(prefix: Optional[str]):
    with patch("mcod.core.caches.caches") as mock_caches:
        session_cache = Mock()
        session_cache.key_prefix = prefix

        mock_caches.__getitem__.return_value = session_cache

        flush_sessions()

    mock_caches.__getitem__.assert_called_once_with("sessions")
    if prefix:
        session_cache.delete_pattern.assert_called_once_with(f"{prefix}*")
    else:
        session_cache.delete_pattern.assert_called_once_with("*")
