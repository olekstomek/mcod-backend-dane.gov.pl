import pytest
from django.test import Client
from django.urls import reverse
from mcod.organizations.models import Organization


@pytest.mark.django_db
def test_deleted_dataset_not_in_inlines(valid_dataset, valid_organization, admin_user):
    assert valid_dataset.organization == valid_organization
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:organizations_organization_change", args=[valid_organization.id]))
    assert valid_dataset.title in str(response.content)
    valid_dataset.delete()
    assert valid_dataset.is_removed is True
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:organizations_organization_change", args=[valid_organization.id]))
    assert valid_dataset.slug not in str(response.content)
    client = Client()
    client.force_login(admin_user)
    response = client.get("/datasets/dataset")
    assert valid_dataset.slug not in str(response.content)


@pytest.mark.django_db
def test_report_action_is_avaiable(valid_dataset, valid_organization, admin_user):
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:organizations_organization_changelist"))
    assert '<option value="export_to_csv">' in str(response.content)


@pytest.mark.django_db
def test_restore_organization_did_not_resotre_his_datasets(valid_dataset, valid_organization, admin_user):
    client = Client()
    client.force_login(admin_user)

    assert not valid_organization.is_removed
    assert valid_organization.datasets.all().count() == 1

    valid_organization.delete()

    assert valid_organization.is_removed
    assert valid_organization.datasets.all().count() == 0

    client.post(f"/organizations/organizationtrash/{valid_organization.id}/change/", data={'is_removed': False})

    org = Organization.objects.get(id=valid_organization.id)

    assert not org.is_removed
    assert org.datasets.all().count() == 0


@pytest.mark.django_db
def test_add_dataset_to_organization_from_organization_form(admin_user, valid_tag):
    client = Client()
    client.force_login(admin_user)
    data = {

        "institution_type": "local",
        "title": "Miasto Brańsk",
        "slug": "miasto-bransk",
        "status": "published",
        "description": "",
        "image": "",
        "postal_code": "17-120",
        "city": "Brańsk",
        "street_type": "ul",
        "street": "Rynek",
        "street_number": "1",
        "flat_number": "1",
        "email": "admin@bransk.eu",
        "tel": "123123123",
        "fax": "123123123",
        "epuap": "123123123",
        "regon": "123456785",
        "website": "http://bransk.eu",
        "datasets-TOTAL_FORMS": "0",
        "datasets-INITIAL_FORMS": "0",
        "datasets-MIN_NUM_FORMS": "0",
        "datasets-MAX_NUM_FORMS": "0",
        "datasets-2-TOTAL_FORMS": "1",
        "datasets-2-INITIAL_FORMS": "0",
        "datasets-2-MIN_NUM_FORMS": "0",
        "datasets-2-MAX_NUM_FORMS": "1000",
        "datasets-2-0-title": "test",
        "datasets-2-0-notes": "<p>123</p>",
        "datasets-2-0-url": "",
        "json_key[datasets-2-0-customfields]": "key",
        "json_value[datasets-2-0-customfields]": "value",
        "datasets-2-0-update_frequency": "notApplicable",
        "datasets-2-0-category": "",
        "datasets-2-0-status": "published",
        "datasets-2-0-tags": [valid_tag.id],
        "datasets-2-0-license_condition_responsibilities": "",
        "datasets-2-0-license_condition_db_or_copyrighted": "",
        "datasets-2-0-id": "",
        "datasets-2-0-organization": "",

    }

    client.post(reverse("admin:organizations_organization_add"), data=data, follow=True)

    org = Organization.objects.last()
    assert org.title == "Miasto Brańsk"
    assert org.datasets.last().title == 'test'


@pytest.mark.django_db
def test_add_dataset_to_organization_from_organization_is_not_possible_without_tags(admin_user, valid_tag):
    client = Client()
    client.force_login(admin_user)
    data = {

        "institution_type": "local",
        "title": "Miasto Brańsk",
        "slug": "miasto-bransk",
        "status": "published",
        "description": "",
        "image": "",
        "postal_code": "17-120",
        "city": "Brańsk",
        "street_type": "ul",
        "street": "Rynek",
        "street_number": "1",
        "flat_number": "1",
        "email": "admin@bransk.eu",
        "tel": "123123123",
        "fax": "123123123",
        "epuap": "123123123",
        "regon": "123456785",
        "website": "http://bransk.eu",
        "datasets-TOTAL_FORMS": "0",
        "datasets-INITIAL_FORMS": "0",
        "datasets-MIN_NUM_FORMS": "0",
        "datasets-MAX_NUM_FORMS": "0",
        "datasets-2-TOTAL_FORMS": "1",
        "datasets-2-INITIAL_FORMS": "0",
        "datasets-2-MIN_NUM_FORMS": "0",
        "datasets-2-MAX_NUM_FORMS": "1000",
        "datasets-2-0-title": "test",
        "datasets-2-0-notes": "<p>123</p>",
        "datasets-2-0-url": "",
        "json_key[datasets-2-0-customfields]": "key",
        "json_value[datasets-2-0-customfields]": "value",
        "datasets-2-0-update_frequency": "notApplicable",
        "datasets-2-0-category": "",
        "datasets-2-0-status": "published",
        # "datasets-2-0-tags": [valid_tag.id],
        "datasets-2-0-license_condition_responsibilities": "",
        "datasets-2-0-license_condition_db_or_copyrighted": "",
        "datasets-2-0-id": "",
        "datasets-2-0-organization": "",

    }

    client.post(reverse("admin:organizations_organization_add"), data=data, follow=True)

    org = Organization.objects.last()
    assert org is None
