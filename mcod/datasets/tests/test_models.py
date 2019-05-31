import pytest
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import Client

from mcod.datasets.models import Dataset
from mcod.resources.models import Resource

from mcod.users.models import User, UserFollowingDataset
from mcod.organizations.models import Organization
from bs4 import BeautifulSoup


def create_organization(param):
    org = Organization()
    org.slug = param
    org.title = param
    org.postal_code = "00-001"
    org.city = "Warszwa"
    org.street = "Królewska"
    org.street_number = "27"
    org.flat_number = "1"
    org.street_type = "ul"
    org.email = "email@email.pl"
    org.fax = "123123123"
    org.tel = "123123123"
    org.epuap = "epuap"
    org.regon = "123123123"
    org.website = "www.www.www"
    org.save()
    return org


def create_dataset(param, org):
    dataset = Dataset()
    dataset.slug = param
    dataset.title = param
    dataset.organization = org
    dataset.save()
    return dataset


def create_editor(param, org):
    usr = User.objects.create_user(param, '123!@#qweQWE')
    usr.state = 'active'
    usr.is_staff = True
    usr.phone = "+48123123123"
    usr.fullname = "Generated User"
    usr.organizations.set([org, ])
    usr.save()
    return usr


@pytest.fixture
def html_table():
    html = '''<html>
<head></head>
<body>
<table>
<tr>1</tr>
<tr>2</tr>
</table>
</body>
</html>'''
    return html


def get_datasets_list(content):
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')
    return rows


def test_get_datasets_lists(html_table):
    rows = get_datasets_list(html_table)
    assert len(rows) == 2


@pytest.mark.django_db
class TestDatasetModel(object):
    def test_cant_create_empty_dataset(self):
        with pytest.raises(ValidationError) as e:
            ds = Dataset()
            ds.full_clean()
        assert "'title'" in str(e.value)

    def test_create_dataset(self, valid_organization):
        ds = Dataset()
        ds.title = "Title"
        ds.slug = "slug"
        ds.notes = "opis"
        ds.organization = valid_organization
        ds.full_clean()
        assert ds.id is None
        ds.save()
        assert ds.id > 0

    def test_dataset_fields(self, valid_dataset):
        dataset_dict = valid_dataset.__dict__
        fields = [
            'slug',
            'title',
            'url',
            'notes',
            'license_id',
            'organization_id',
            'customfields',
            'license_condition_db_or_copyrighted',
            'license_condition_modification',
            'license_condition_original',
            'license_condition_responsibilities',
            'license_condition_source',
            'update_frequency',
            'category_id',
            'status',
        ]

        for f in fields:
            assert f in dataset_dict

    def test_delete_dataset(self, valid_dataset):
        assert valid_dataset.status == 'published'
        valid_dataset.delete()
        assert valid_dataset.is_removed is True
        with pytest.raises(ObjectDoesNotExist):
            Dataset.objects.get(id=valid_dataset.id)
        assert Dataset.raw.get(id=valid_dataset.id)

    def test_add_resource(self, valid_dataset, valid_resource2):
        assert 0 == len(valid_dataset.resources.all())
        valid_dataset.resources.set([valid_resource2])
        assert 1 == len(valid_dataset.resources.all())
        ds = Dataset.objects.get(id=valid_dataset.id)
        assert valid_resource2 in ds.resources.all()

    def test_safe_delete_dataset_also_delete_resource(self, valid_dataset, valid_resource):
        assert 'published' == valid_dataset.status
        assert 'published' == valid_dataset.resources.first().status
        assert valid_resource in valid_dataset.resources.all()
        assert 'published' == valid_dataset.resources.first().status
        valid_dataset.delete()
        assert valid_dataset.is_removed is True
        resource = Resource.deleted.get(id=valid_resource.id)
        assert resource.is_removed is True

    def test_unsafe_delete_dataset_and_its_resources(self, valid_dataset, valid_resource):
        ds_id = valid_dataset.id
        r_id = valid_resource.id
        assert valid_resource in valid_dataset.resources.all()
        valid_dataset.delete(safe=False)
        with pytest.raises(ObjectDoesNotExist):
            Dataset.objects.get(id=ds_id)
        with pytest.raises(ObjectDoesNotExist):
            Resource.objects.get(id=r_id)

    def test_restore_dataset_is_not_restoring_its_resources(self, valid_dataset, valid_resource):
        assert valid_resource in valid_dataset.resources.all()
        valid_dataset.delete()
        assert valid_resource not in Resource.objects.all()
        assert valid_resource in Resource.deleted.all()

        valid_dataset.is_removed = False
        valid_dataset.save()

        assert valid_resource not in Resource.objects.all()
        assert valid_resource in Resource.deleted.all()

    def test_set_draft_for_dataset_also_change_his_resources_to_draft(self, valid_dataset, valid_resource):
        assert valid_resource in valid_dataset.resources.all()
        assert valid_dataset.status == 'published'
        assert valid_dataset.resources.all().first().status == 'published'

        valid_dataset.status = "draft"
        valid_dataset.save()

        assert valid_dataset.status == 'draft'
        assert valid_dataset.resources.all().first().status == 'draft'

    # def test_save_with_deleted_status(self, valid_dataset, valid_resource):
    #     assert 'published' == valid_dataset.status
    #     assert 'published' == valid_dataset.resources.first().status
    #     valid_dataset.status = 'archived'
    #     valid_dataset.save()
    #     assert 'archived' == valid_dataset.status
    #     assert 'archived' == valid_dataset.resources.first().status

    # TODO: trash functionality - as MCOD-621
    # def test_save_with_deleted_status(self, valid_dataset, valid_resource):
    #     assert 'active' == valid_dataset.state
    #     assert 'active' == valid_dataset.resources.first().state
    #     valid_dataset.state = 'archived'
    #     valid_dataset.save()
    #     assert 'archived' == valid_dataset.state
    #     assert 'archived' == valid_dataset.resources.first().state


@pytest.mark.django_db
class TestDatasetsUserRoles(object):
    def test_editor_can_see_datasets_in_admin_panel(self, editor_user, valid_organization):
        client = Client()
        client.force_login(editor_user)
        editor_user.organizations.set([valid_organization])
        response = client.get("/")
        assert response.status_code == 200
        assert '/datasets/' in str(response.content)

    def test_editor_can_go_to_datasets_in_admin_panel(self, editor_user, valid_organization):
        client = Client()
        client.force_login(editor_user)
        editor_user.organizations.set([valid_organization])
        response = client.get("/datasets/")
        assert response.status_code == 200

    def test_admin_can_see_datasets_in_admin_panel(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get("/")
        assert response.status_code == 200
        assert '/datasets/' in str(response.content)

    def test_admin_can_go_to_datasets_in_admin_panel(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get("/datasets/")
        assert response.status_code == 200

    def test_editor_should_see_only_datasets_from_his_organization_admin_see_all(self, admin_user):
        # create organization 1 and 2
        org_1 = create_organization("organization 1")
        org_2 = create_organization("organization 2")

        # create dataset 1 and 2
        dataset_1 = create_dataset("dataset 1", org_1)
        dataset_2 = create_dataset("dataset 2", org_2)

        # add dataset 1 to organization 1
        assert org_1 is dataset_1.organization
        # add dataset 2 to organization 2
        assert org_2 is dataset_2.organization

        editor_1 = create_editor("editor_1@test.pl", org_1)
        editor_2 = create_editor("editor_2@test.pl", org_2)

        # create editor 1 and 2
        # add editor 1 to organization 1
        # add editor 2 to organization 2
        assert org_1 in editor_1.organizations.all()
        assert org_1 not in editor_2.organizations.all()
        assert org_2 in editor_2.organizations.all()
        assert org_2 not in editor_1.organizations.all()

        # login as admin
        # assert dataset length = 2
        client = Client()
        client.force_login(admin_user)
        response = client.get("/datasets/dataset/")
        datasets = get_datasets_list(response.content)
        assert len(datasets) == 3

        # login as editor 1
        # assert datasets length = 2
        # assert editor 1 see dataset 1
        client = Client()
        client.force_login(editor_1)
        response = client.get("/datasets/dataset/")
        datasets = get_datasets_list(response.content)
        assert len(datasets) == 2
        nr = datasets[1].find('a').get('href').split("/")[3]
        ds = Dataset.objects.get(id=int(nr))
        assert dataset_1 == ds

        # login as editor 2
        # assert datasets length = 1
        # assert editor 2 see dataset 2
        client = Client()
        client.force_login(editor_2)
        response = client.get("/datasets/dataset/")
        datasets = get_datasets_list(response.content)
        assert len(datasets) == 2
        nr = datasets[1].find('a').get('href').split("/")[3]
        ds = Dataset.objects.get(id=int(nr))
        assert dataset_2 == ds

    def test_is_license_set(self):
        dataset = Dataset()
        assert not dataset.is_license_set
        dataset.license_condition_db_or_copyrighted = "MIT"
        assert dataset.is_license_set

    def test_followers_count(self, valid_dataset, admin_user, editor_user):
        assert valid_dataset.followers_count == 0
        UserFollowingDataset(follower=admin_user, dataset=valid_dataset).save()
        assert valid_dataset.followers_count == 1
        UserFollowingDataset(follower=editor_user, dataset=valid_dataset).save()
        assert valid_dataset.followers_count == 2


@pytest.mark.django_db
class TestDatasetVerifiedDate:

    def test_new_dataset_has_verified_same_as_created(self, valid_dataset):
        assert valid_dataset.verified == valid_dataset.created

    def test_dataset_with_resource_has_verified_same_as_resourve_verified(self, valid_dataset, valid_resource):
        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)
        assert rs in ds.resources.all()
        assert ds.verified == rs.verified

    def test_dataset_verified_is_created_after_delete_all_resources(self, valid_resource, valid_dataset):
        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)
        assert valid_dataset.resources.count() == 1
        assert ds.verified == rs.verified
        assert ds.verified != ds.created
        valid_resource.delete()
        assert ds.resources.count() == 0
        ds = Dataset.objects.get(pk=valid_dataset.id)
        assert ds.verified == valid_dataset.created

    def test_dataset_verified_is_same_as_created_when_all_his_resources_are_draft(self, valid_resource, valid_dataset):
        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)
        assert rs.status == "published"
        assert ds.verified == rs.verified
        rs.status = "draft"
        rs.save()
        ds = Dataset.objects.get(pk=valid_dataset.id)
        assert ds.verified == valid_dataset.created

    def test_dataset_verified_change_after_resource_revalidate(self, valid_resource, valid_dataset):
        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)

        old = rs.verified
        assert ds.verified == old

        rs.revalidate()
        rs = Resource.objects.get(pk=valid_resource.id)

        assert old != rs.verified
        ds = Dataset.objects.get(pk=valid_dataset.id)

        assert ds.verified == rs.verified

    def test_revalidation_of_resource_when_dataset_is_in_draft_state_should_not_change_verified(self, valid_resource,
                                                                                                valid_dataset):
        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)

        assert rs.status == "published"
        assert ds.status == "published"
        assert ds.verified == rs.verified
        assert ds.verified != rs.created

        ds.status = "draft"
        ds.save()

        rs = Resource.objects.get(pk=valid_resource.id)
        ds = Dataset.objects.get(pk=valid_dataset.id)

        assert rs.status == "draft"
        assert ds.status == "draft"
        assert ds.verified == ds.created

        rs.revalidate()

        ds = Dataset.objects.get(pk=valid_dataset.id)

        assert ds.verified == ds.created
