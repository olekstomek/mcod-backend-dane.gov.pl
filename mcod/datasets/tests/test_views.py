import pytest
from django.test import Client
from django.urls import reverse
from falcon import HTTP_OK
from mcod.datasets.models import Dataset, UPDATE_FREQUENCY
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper


@pytest.mark.django_db
class TestDatasetsView(ElasticCleanHelper):
    def test_update_frequency_translations(self, client, valid_organization):
        # MCOD-1031
        for uf_code, readable in UPDATE_FREQUENCY:
            ds = Dataset(
                slug=f"test-{uf_code}-dataset",
                title=f"{readable} test name",
                organization=valid_organization,
                update_frequency=uf_code
            )
            ds.save()

            resp = client.simulate_get(f'/datasets/{ds.id}')
            assert HTTP_OK == resp.status
            body = resp.json
            assert readable == body['data']['attributes']['update_frequency']


@pytest.mark.django_db
def test_dataset_autocomplete_view(admin_user, dataset_list):
    client = Client()
    client.force_login(admin_user)

    response = client.get(reverse("dataset-autocomplete"))

    assert len(response.json()['results']) == 3


@pytest.mark.django_db
def test_dataset_autocomplete_view_for_editor_without_organization(editor_user, dataset_list):
    client = Client()
    client.force_login(editor_user)

    assert not editor_user.organizations.all()
    response = client.get(reverse("dataset-autocomplete"))

    assert len(response.json()['results']) == 0


@pytest.mark.django_db
def test_dataset_autocomplete_view_editor_with_organization(user_with_organization, valid_organization, valid_dataset):
    client = Client()
    client.force_login(user_with_organization)

    assert valid_organization in user_with_organization.organizations.all()
    response = client.get(reverse("dataset-autocomplete"))

    assert len(response.json()['results']) == 1
