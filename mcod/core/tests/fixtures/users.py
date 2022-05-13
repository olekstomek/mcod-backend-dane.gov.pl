import pytest

from mcod.datasets.factories import DatasetFactory
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.factories import ResourceFactory
from mcod.users.factories import AdminFactory, EditorFactory, UserFactory


@pytest.fixture
def active_user():
    return UserFactory.create(
        email='active_user@dane.gov.pl',
        password='12345.Abcde',
        state='active'
    )


@pytest.fixture
def inactive_user():
    return UserFactory.create(
        email='inactive_user@dane.gov.pl',
        password='12345.Abcde',
        state='pending'
    )


@pytest.fixture
def blocked_user():
    return UserFactory.create(
        email='blocked_user@dane.gov.pl',
        password='12345.Abcde',
        state='blocked'
    )


@pytest.fixture
def removed_user():
    return UserFactory.create(
        email='active_user@dane.gov.pl',
        password='12345.Abcde',
        is_removed=True
    )


@pytest.fixture
def active_editor():
    usr = EditorFactory.create(
        email='editor_user@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )
    org = OrganizationFactory.create(users=(usr,))
    ds = DatasetFactory.create(organization=org)
    ResourceFactory.create_batch(2, dataset=ds)
    return usr


@pytest.fixture
def active_editor_without_org():
    usr = EditorFactory.create(
        email='editor_user_wo_org@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )
    return usr


@pytest.fixture
def admin():
    usr = AdminFactory.create(
        email='admin@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )
    return usr


@pytest.fixture
def another_admin():
    return AdminFactory.create(
        email='admin_2@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )


@pytest.fixture
def inactive_admin():
    usr = AdminFactory.create(
        email='admin@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789',
        is_active=False
    )
    return usr
