import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_organization_autocomplete_view(valid_organization, valid_organization2, admin_user):
    client = Client()
    client.force_login(admin_user)

    response = client.get(reverse("admin:organizations_organization_autocomplete"))

    assert len(response.json()['results']) == 2


@pytest.mark.django_db
def test_organization_autocomplete_view_editor_without_organization(valid_organization, editor_user):
    client = Client()
    client.force_login(editor_user)

    response = client.get(reverse("admin:organizations_organization_autocomplete"))

    assert response.json() == {'error': '403 Forbidden'}


@pytest.mark.django_db
def test_organization_autocomplete_view_editor_with_organization(valid_organization, valid_organization2,
                                                                 user_with_organization):
    client = Client()
    client.force_login(user_with_organization)

    response = client.get(reverse("admin:organizations_organization_autocomplete"))

    assert len(response.json()['results']) == 1
