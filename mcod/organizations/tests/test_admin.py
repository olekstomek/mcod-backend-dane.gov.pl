from django.template.defaultfilters import linebreaksbr
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_text
from pytest_bdd import scenarios

from mcod.organizations.models import Organization


scenarios(
    'features/organization_details_admin.feature',
    'features/organizations_list_admin.feature',
)


def test_deleted_dataset_not_in_inlines(dataset, admin):
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:organizations_organization_change", args=[dataset.organization_id]))
    dataset_title_on_page = linebreaksbr(dataset.title)
    assert dataset_title_on_page in smart_text(response.content)
    dataset.delete()
    assert dataset.is_removed is True
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:organizations_organization_change", args=[dataset.organization_id]))
    assert dataset.slug not in smart_text(response.content)
    client = Client()
    client.force_login(admin)
    response = client.get("/datasets/dataset")
    assert dataset.slug not in smart_text(response.content)


def test_restore_organization_did_not_restore_his_datasets(db, institution_with_datasets, admin):
    client = Client()
    client.force_login(admin)
    institution = institution_with_datasets

    assert not institution.is_removed
    assert institution.datasets.all().count() == 2

    institution.delete()

    assert institution.is_removed
    assert institution.datasets.all().count() == 0

    client.post(f"/organizations/organizationtrash/{institution.id}/change/", data={'is_removed': False})

    org = Organization.objects.get(id=institution.id)

    assert not org.is_removed
    assert org.datasets.all().count() == 0


def test_add_dataset_to_organization_from_organization_form(admin, tag, tag_pl, small_image):
    client = Client()
    client.force_login(admin)
    data = {

        "institution_type": "local",
        "title": "Miasto Brańsk",
        "slug": "miasto-bransk",
        "status": "published",
        "description": "",
        "abbreviation": "MB",
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
        "datasets-2-0-notes": "<p>more than 20 characters</p>",
        "datasets-2-0-url": "",
        "json_key[datasets-2-0-customfields]": "key",
        "json_value[datasets-2-0-customfields]": "value",
        "datasets-2-0-update_frequency": "notApplicable",
        "datasets-2-0-category": "",
        "datasets-2-0-status": "published",
        "datasets-2-0-license_condition_responsibilities": "",
        "datasets-2-0-license_condition_db_or_copyrighted": "",
        "datasets-2-0-license_condition_personal_data": "",
        "datasets-2-0-id": "",
        "datasets-2-0-organization": "",
        "datasets-2-0-image": small_image,
        "datasets-2-0-tags_pl": [tag_pl.id],

    }

    client.post(reverse("admin:organizations_organization_add"), data=data, follow=True)
    org = Organization.objects.last()
    assert org.title == "Miasto Brańsk"
    assert org.datasets.last().title == 'test'
