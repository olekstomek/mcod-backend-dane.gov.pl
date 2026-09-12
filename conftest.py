import os

import pytest
from django.conf import settings


def pytest_runtest_setup(item):
    """
    Fails the test if environment variable COMPONENT doesn't match component marker.
    """
    current_component = os.environ.get("COMPONENT")

    for marker in item.iter_markers():
        if marker.name == "component_cms" and current_component != settings.COMPONENT_CMS:
            pytest.fail("Test requires COMPONENT=cms. Set it as an environment variable and re-run.")
        if marker.name == "component_api" and current_component != settings.COMPONENT_API:
            pytest.fail("Test requires COMPONENT=cms. Set it as an environment variable and re-run.")
