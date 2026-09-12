import pytest
from django.urls import reverse

from mcod.core.tests.fixtures import *  # noqa


@pytest.fixture
def admin_login_url() -> str:
    return reverse("admin:login")
