import datetime
import json

import pytest

from mcod.core.registries import factories_registry
from mcod.datasets.factories import DatasetFactory
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.factories import ResourceFactory
from mcod.users.factories import AdminFactory, EditorFactory, UserFactory
from mcod.users.models import User

TEST_PASSWORD = "12345.Abcde"


@pytest.fixture
def active_user(test_password: str) -> User:
    return UserFactory.create(email="active_user@dane.gov.pl", password=test_password, state="active")


@pytest.fixture
def active_user_with_id(request, test_password: str) -> User:
    return UserFactory.create(id=request.param, email="active_user@dane.gov.pl", password=test_password, state="active")


@pytest.fixture
def active_user_with_last_login(test_password: str):
    return UserFactory.create(
        email="active_user@dane.gov.pl",
        password=test_password,
        state="active",
        last_login=datetime.datetime(2024, 7, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
    )


@pytest.fixture
def inactive_user(test_password: str):
    return UserFactory.create(
        email="inactive_user@dane.gov.pl",
        password=test_password,
        state="pending",
    )


@pytest.fixture
def blocked_user(test_password: str):
    return UserFactory.create(
        email="blocked_user@dane.gov.pl",
        password=test_password,
        state="blocked",
    )


@pytest.fixture
def removed_user(test_password: str):
    return UserFactory.create(email="active_user@dane.gov.pl", password=test_password, is_removed=True)


@pytest.fixture
def active_editor(test_password: str):
    usr = EditorFactory.create(
        email="editor_user@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
    )
    org = OrganizationFactory.create(users=(usr,))
    ds = DatasetFactory.create(organization=org)
    ResourceFactory.create_batch(2, dataset=ds)
    return usr


@pytest.fixture
def pending_editor(test_password: str):
    usr = EditorFactory.create(
        email="editor_user@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
        state="pending",
    )
    org = OrganizationFactory.create(users=(usr,))
    ds = DatasetFactory.create(organization=org)
    ResourceFactory.create_batch(2, dataset=ds)
    return usr


@pytest.fixture
def active_editor_without_org(test_password: str):
    usr = EditorFactory.create(
        email="editor_user_wo_org@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
    )
    return usr


@pytest.fixture
def test_password() -> str:
    return TEST_PASSWORD


@pytest.fixture
def admin(test_password: str):
    return AdminFactory.create(email="admin@dane.gov.pl", password=test_password, phone="0048123456789")


@pytest.fixture
def another_admin(test_password: str):
    return AdminFactory.create(
        email="admin_2@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
    )


@pytest.fixture
def admin_with_discourse_credentials(test_password: str) -> User:
    usr = AdminFactory.create(
        email="admin@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
        discourse_user_name="admin",
        discourse_api_key="1234567",
    )
    return usr


@pytest.fixture
def inactive_admin(test_password: str):
    usr = AdminFactory.create(
        email="admin@dane.gov.pl",
        password=test_password,
        phone="0048123456789",
        is_active=False,
    )
    return usr


def create_user_with_params(user_type, params=None):
    _factory = factories_registry.get_factory(user_type)
    kwargs = {
        "email": "{}@dane.gov.pl".format(user_type.replace(" ", "_")),
        "password": TEST_PASSWORD,
    }
    if params is not None:
        kwargs.update(json.loads(params))
    created_user = _factory(**kwargs)
    return created_user


@pytest.fixture
def test_user_pesel() -> str:
    """Returns test user pesel."""
    return "some_pesel"
