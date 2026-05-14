import pytest

from mcod.settings.base import (
    url_without_schema,  # deliberate import from mcod.settings instead of django.conf
)


@pytest.mark.parametrize(
    "env_var_value, default, expected_value",
    [
        ("", "", ""),
        ("dummy", "ignored", "dummy"),
        ("https://stats.dane.gov.pl", "", "stats.dane.gov.pl"),
        ("http://stats.dane.gov.pl", "", "stats.dane.gov.pl"),
        ("//stats.dane.gov.pl", "", "//stats.dane.gov.pl"),
        ("stats.dane.gov.pl", "", "stats.dane.gov.pl"),
    ],
)
def test_url_without_schema(
    monkeypatch,
    env_var_value: str,
    default: str,
    expected_value: str,
):
    monkeypatch.setenv("MATOMO_URL", env_var_value)
    assert url_without_schema("MATOMO_URL", default=default) == expected_value


@pytest.mark.parametrize(
    "env_var_value, default, expected_value",
    [
        ("ignored", "dummy", "dummy"),
    ],
)
def test_url_without_schema_default_value(
    monkeypatch,
    env_var_value: str,
    default: str,
    expected_value: str,
):
    monkeypatch.delenv("MATOMO_URL", raising=False)
    assert url_without_schema("MATOMO_URL", default=default) == expected_value
