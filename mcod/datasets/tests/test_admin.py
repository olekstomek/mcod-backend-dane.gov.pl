import pytest
import re
from django.test import Client
from django.urls import reverse

from mcod.datasets.models import Dataset
from mcod.resources.models import Resource


@pytest.mark.django_db
def test_save_model_auto_create_name(admin_user, valid_organization, valid_tag):
    obj = {
        'resources-TOTAL_FORMS': '0',
        'resources-INITIAL_FORMS': '0',
        'resources-MIN_NUM_FORMS': '0',
        'resources-MAX_NUM_FORMS': '1000',
        'resources-2-TOTAL_FORMS': '0',
        'resources-2-INITIAL_FORMS': '0',
        'resources-2-MIN_NUM_FORMS': '0',
        'resources-2-MAX_NUM_FORMS': '1000',
        'title': "Test with dataset title",
        'notes': "Tresc",
        'status': 'published',
        'update_frequency': 'weekly',
        'url': 'http://www.test.pl',
        'organization': [valid_organization.id],
        'tags': [valid_tag.id],
        # 'private': False
    }

    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:datasets_dataset_add'), obj, follow=True)
    assert response.status_code == 200
    sl = Dataset.objects.last().slug
    assert len(sl) > 10
    assert sl != "test-with-dataset-title"


@pytest.mark.django_db
def test_auto_set_creator_user_and_edit_didnt_change_creator_user(admin_user, admin_user2,
                                                                  valid_organization, valid_tag):
    obj = {
        'resources-TOTAL_FORMS': '0',
        'resources-INITIAL_FORMS': '0',
        'resources-MIN_NUM_FORMS': '0',
        'resources-MAX_NUM_FORMS': '1000',
        'resources-2-TOTAL_FORMS': '0',
        'resources-2-INITIAL_FORMS': '0',
        'resources-2-MIN_NUM_FORMS': '0',
        'resources-2-MAX_NUM_FORMS': '1000',
        'title': "Test with dataset title",
        'slug': "i-changed-a-name",
        'notes': "Tresc",
        'status': 'published',
        'update_frequency': 'weekly',
        'url': 'http://www.test.pl',
        'organization': [valid_organization.id],
        'tags': [valid_tag.id],
        # 'private': 'false'
    }

    client = Client()
    client.force_login(admin_user)
    client.post(reverse('admin:datasets_dataset_add'), obj, follow=True)
    ds_last = Dataset.objects.last()
    assert ds_last.title == obj['title']
    assert ds_last.created_by_id == admin_user.id

    client = Client()
    client.force_login(admin_user2)
    obj['title'] = 'changed title'
    client.post(reverse('admin:datasets_dataset_change', args=[ds_last.id]), obj, follow=True)
    ds_last = Dataset.objects.last()
    assert ds_last.title == obj['title']
    assert ds_last.created_by_id == admin_user.id
    assert ds_last.modified_by_id == admin_user2.id


@pytest.mark.django_db
def test_admin_can_add_tags_to_datasets(admin_user, valid_tag, valid_dataset, valid_organization):
    obj = {
        'resources-TOTAL_FORMS': '0',
        'resources-INITIAL_FORMS': '0',
        'resources-MIN_NUM_FORMS': '0',
        'resources-MAX_NUM_FORMS': '1000',
        'resources-2-TOTAL_FORMS': '0',
        'resources-2-INITIAL_FORMS': '0',
        'resources-2-MIN_NUM_FORMS': '0',
        'resources-2-MAX_NUM_FORMS': '1000',
        'title': valid_dataset.title,
        'slug': valid_dataset.slug,
        'notes': "Tresc",
        'status': 'published',
        'update_frequency': 'weekly',
        'url': 'http://www.test.pl',
        # 'private': 'false',
        'tags': [valid_tag.id],
        'organization': [valid_organization.id],
    }

    assert valid_dataset.slug == "test-dataset-name"
    assert valid_tag not in valid_dataset.tags.all()

    client = Client()
    client.force_login(admin_user)
    client.post(reverse('admin:datasets_dataset_change', args=[valid_dataset.id]), obj, follow=True)
    app = Dataset.objects.get(id=valid_dataset.id)
    # assert app.slug == "test-with-tag"
    assert valid_tag in app.tags.all()


@pytest.mark.django_db
def test_editor_can_add_tags_to_datasets(editor_user, valid_dataset, valid_tag, valid_organization):
    obj = {
        'resources-TOTAL_FORMS': '0',
        'resources-INITIAL_FORMS': '0',
        'resources-MIN_NUM_FORMS': '0',
        'resources-MAX_NUM_FORMS': '1000',
        'resources-2-TOTAL_FORMS': '0',
        'resources-2-INITIAL_FORMS': '0',
        'resources-2-MIN_NUM_FORMS': '0',
        'resources-2-MAX_NUM_FORMS': '1000',
        'title': valid_dataset.title,
        'slug': valid_dataset.slug,
        'notes': "Tresc",
        'status': 'published',
        'update_frequency': 'weekly',
        'url': 'http://www.test.pl',
        # 'private': 'false',
        'tags': [valid_tag.id],
        'organization': [valid_organization.id],
    }

    assert valid_dataset.slug == "test-dataset-name"
    assert valid_tag not in valid_dataset.tags.all()
    editor_user.organizations.set([valid_organization])
    editor_user.save()
    assert valid_organization in editor_user.organizations.all()
    assert valid_dataset.organization == valid_organization
    client = Client()
    client.force_login(editor_user)
    response = client.post(reverse('admin:datasets_dataset_change', args=[valid_dataset.id]), obj, follow=True)
    assert response.status_code == 200
    app = Dataset.objects.get(id=valid_dataset.id)
    assert valid_tag in app.tags.all()


@pytest.mark.django_db
def test_deleted_resource_are_not_shown_in_dataset_resource_inline(valid_dataset, valid_resource, admin_user):
    assert valid_resource.dataset == valid_dataset
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:datasets_dataset_change", args=[valid_dataset.id]))
    assert valid_resource.title in str(response.content)
    valid_resource.delete()
    assert valid_resource.is_removed is True
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:datasets_dataset_change", args=[valid_dataset.id]))
    assert valid_resource.title not in str(response.content)


@pytest.mark.django_db
def test_resources_are_also_deleted_after_dataset_delete(valid_dataset, valid_resource, admin_user):
    assert valid_resource.dataset == valid_dataset
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:datasets_dataset_change", args=[valid_dataset.id]))
    assert valid_resource.title in str(response.content)
    assert valid_resource.status == 'published'
    assert valid_dataset.status == 'published'
    valid_dataset.delete()
    assert valid_dataset.is_removed is True
    vr = Resource.deleted.get(id=valid_resource.id)
    assert vr.is_removed is True


@pytest.mark.django_db
def test_removed_datasets_are_not_in_datasets_list(admin_user, valid_dataset):
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:datasets_dataset_changelist"))
    pattern = re.compile(r"/datasets/dataset/\d+/change")
    result = pattern.findall(str(response.content))
    assert result == [f'/datasets/dataset/{valid_dataset.id}/change']
    valid_dataset.delete()
    response = client.get(reverse("admin:datasets_dataset_changelist"))
    result = pattern.findall(str(response.content))
    assert not result


@pytest.mark.django_db
def test_dataset_resources_has_pagination(valid_dataset, admin_user):
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:datasets_dataset_change", args=[valid_dataset.id]))
    assert 'pagination-block' in response.content.decode()


@pytest.mark.django_db
def test_trash_for_editor(dataset_list, user_with_organization):
    dataset_list[0].delete()
    dataset_list[1].delete()

    client = Client()
    client.force_login(user_with_organization)
    response = client.get(reverse("admin:datasets_datasettrash_changelist"))
    pattern = re.compile(r"/datasets/datasettrash/\d+/change")
    result = pattern.findall(str(response.content))
    assert result == [f'/datasets/datasettrash/{dataset_list[0].id}/change']

    dataset_list[2].delete()
    response = client.get(reverse("admin:datasets_datasettrash_changelist"))
    result = pattern.findall(str(response.content))
    assert set(result) == set(f'/datasets/datasettrash/{ds.id}/change'
                              for ds in dataset_list
                              if ds.organization in user_with_organization.organizations.all())


@pytest.mark.django_db
def test_add_resource_to_dataset(admin_user, valid_organization, valid_tag):
    client = Client()
    client.force_login(admin_user)
    data = {

        'resources-TOTAL_FORMS': '0',
        'resources-INITIAL_FORMS': '0',
        'resources-MIN_NUM_FORMS': '0',
        'resources-MAX_NUM_FORMS': '1000',
        'resources-2-TOTAL_FORMS': '1',
        'resources-2-INITIAL_FORMS': '0',
        'resources-2-MIN_NUM_FORMS': '0',
        'resources-2-MAX_NUM_FORMS': '1000',
        'title': "Test with dataset title",
        'notes': "Tresc",
        'status': 'published',
        'update_frequency': 'weekly',
        'url': 'http://www.test.pl',
        'organization': [valid_organization.id],
        'tags': [valid_tag.id],
        "resources-2-0-switcher": "link",
        "resources-2-0-link": "http://test.pl",
        "resources-2-0-title": "123",
        "resources-2-0-description": "<p>123</p>",
        "resources-2-0-status": "published",
        "resources-2-0-id": "",
        "resources-2-0-dataset": "",
    }

    client.post(reverse("admin:datasets_dataset_add"), data=data, follow=True)

    ds = Dataset.objects.last()
    assert ds
    r = ds.resources.last()
    assert r.title == "123"
    assert r.created_by_id == admin_user.id
    assert r.modified_by_id == admin_user.id


@pytest.mark.django_db
class TestDatasetAndOrganization(object):

    def test_restore_dataset_from_trash_is_not_possible_without_restore_his_organization(self, valid_dataset,
                                                                                         valid_organization,
                                                                                         admin_user):
        assert not valid_dataset.organization.is_removed
        assert not valid_dataset.is_removed
        assert Dataset.objects.count() == 1
        assert Dataset.deleted.count() == 0

        valid_dataset.organization.delete()

        assert Dataset.objects.count() == 0
        assert Dataset.deleted.count() == 1

        assert valid_dataset.organization.is_removed

        ds = Dataset.deleted.first()
        assert ds.organization == valid_dataset.organization
        assert ds.is_removed

        client = Client()
        client.force_login(admin_user)
        client.post(f'/datasets/datasettrash/{ds.id}/change/', data={'is_removed': False})

        ds = Dataset.deleted.get(id=ds.id)
        assert ds.organization.is_removed

        ds.organization.is_removed = False
        ds.organization.save()

        client.post(f'/datasets/datasettrash/{ds.id}/change/', data={'is_removed': False})

        assert Dataset.objects.count() == 1
        assert Dataset.deleted.count() == 0

        ds = Dataset.objects.get(id=ds.id)
        assert not ds.is_removed

    def test_set_published_for_dataset_didnt_change_his_resources_to_publish(self, valid_dataset, valid_resource):
        assert valid_resource in valid_dataset.resources.all()
        assert valid_dataset.status == 'published'
        assert valid_dataset.resources.all().first().status == 'published'

        valid_dataset.status = "draft"
        valid_dataset.save()

        assert valid_dataset.status == 'draft'
        assert valid_dataset.resources.all().first().status == 'draft'
