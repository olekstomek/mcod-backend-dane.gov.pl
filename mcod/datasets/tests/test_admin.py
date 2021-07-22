import re

from django.test import Client
from django.urls import reverse
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import smart_text
from pytest_bdd import scenario


@scenario('features/dataset_details_admin.feature',
          'Imported dataset is not editable in admin panel')
def test_imported_dataset_is_not_editable_in_admin_panel():
    pass


@scenario('features/datasets_list_admin.feature',
          'Imported datasets are visible on list in admin panel')
def test_imported_datasets_are_visible_on_list_in_admin_panel():
    pass


# TODO: fix - not working
# def test_save_model_auto_create_name(admin, institution, tag):
#     obj = {
#         'resources-TOTAL_FORMS': '0',
#         'resources-INITIAL_FORMS': '0',
#         'resources-MIN_NUM_FORMS': '0',
#         'resources-MAX_NUM_FORMS': '1000',
#         'resources-2-TOTAL_FORMS': '0',
#         'resources-2-INITIAL_FORMS': '0',
#         'resources-2-MIN_NUM_FORMS': '0',
#         'resources-2-MAX_NUM_FORMS': '1000',
#         'title': "Test with dataset title",
#         'notes': "Tresc",
#         'status': 'published',
#         'update_frequency': 'weekly',
#         'url': 'http://www.test.pl',
#         'organization': [institution.id],
#         'tags': [tag.id],
#         # 'private': False
#     }
#
#     client = Client()
#     client.force_login(admin)
#     response = client.post(reverse('admin:datasets_dataset_add'), obj, follow=True)
#     assert response.status_code == 200
#     sl = Dataset.objects.last().slug
#     assert len(sl) > 10
#     assert sl == "test-with-dataset-title"


# TODO: fix - not working
# def test_auto_set_creator_user_and_edit_didnt_change_creator_user(admin, another_admin,
#                                                                   institution, tag):
#     obj = {
#         'resources-TOTAL_FORMS': '0',
#         'resources-INITIAL_FORMS': '0',
#         'resources-MIN_NUM_FORMS': '0',
#         'resources-MAX_NUM_FORMS': '1000',
#         'resources-2-TOTAL_FORMS': '0',
#         'resources-2-INITIAL_FORMS': '0',
#         'resources-2-MIN_NUM_FORMS': '0',
#         'resources-2-MAX_NUM_FORMS': '1000',
#         'title': "Test with dataset title",
#         'slug': "i-changed-a-name",
#         'notes': "Tresc",
#         'status': 'published',
#         'update_frequency': 'weekly',
#         'url': 'http://www.test.pl',
#         'organization': [institution.id],
#         'tags': [tag.id],
#         # 'private': 'false'
#     }
#
#     client = Client()
#     client.force_login(admin)
#     client.post(reverse('admin:datasets_dataset_add'), obj, follow=True)
#     ds_last = Dataset.objects.last()
#     assert ds_last.title == obj['title']
#     assert ds_last.created_by_id == admin.id
#
#     client = Client()
#     client.force_login(another_admin)
#     obj['title'] = 'changed title'
#     client.post(reverse('admin:datasets_dataset_change', args=[ds_last.id]), obj, follow=True)
#     ds_last = Dataset.objects.last()
#     assert ds_last.title == obj['title']
#     assert ds_last.created_by_id == admin.id
#     assert ds_last.modified_by_id == another_admin.id


# TODO: fix - not working
# def test_admin_can_add_tags_to_datasets(admin, tag, dataset):
#     obj = {
#         'resources-TOTAL_FORMS': '0',
#         'resources-INITIAL_FORMS': '0',
#         'resources-MIN_NUM_FORMS': '0',
#         'resources-MAX_NUM_FORMS': '1000',
#         'resources-2-TOTAL_FORMS': '0',
#         'resources-2-INITIAL_FORMS': '0',
#         'resources-2-MIN_NUM_FORMS': '0',
#         'resources-2-MAX_NUM_FORMS': '1000',
#         'title': dataset.title,
#         'slug': dataset.slug,
#         'notes': "Tresc",
#         'status': 'published',
#         'update_frequency': 'weekly',
#         'url': 'http://www.test.pl',
#         # 'private': 'false',
#         'tags': [tag.id, ],
#     }
#
#     assert tag not in dataset.tags.all()
#     client = Client()
#     client.force_login(admin)
#     client.post(reverse('admin:datasets_dataset_change', args=[dataset.id]), obj, follow=True)
#     app = Dataset.objects.get(id=dataset.id)
#     dataset.refresh_from_db()
#     # assert app.slug == "test-with-tag"
#     assert tag in app.tags.all()


# TODO: fix - not working
# def test_editor_can_add_tags_to_datasets(active_editor, dataset, tag):
#     institution = active_editor.organizations.first()
#     obj = {
#         'resources-TOTAL_FORMS': '0',
#         'resources-INITIAL_FORMS': '0',
#         'resources-MIN_NUM_FORMS': '0',
#         'resources-MAX_NUM_FORMS': '1000',
#         'resources-2-TOTAL_FORMS': '0',
#         'resources-2-INITIAL_FORMS': '0',
#         'resources-2-MIN_NUM_FORMS': '0',
#         'resources-2-MAX_NUM_FORMS': '1000',
#         'title': dataset.title,
#         'slug': dataset.slug,
#         'notes': "Tresc",
#         'status': 'published',
#         'update_frequency': 'weekly',
#         'url': 'http://www.test.pl',
#         # 'private': 'false',
#         'tags': [tag.id, ],
#         'organization': [institution.id, ],
#     }
#
#     client = Client()
#     client.force_login(active_editor)
#     response = client.post(reverse('admin:datasets_dataset_change', args=[dataset.id]), obj, follow=True)
#     assert response.status_code == 200
#     app = Dataset.objects.get(id=dataset.id)
#     tags = app.tags.all()
#     assert tag in tags


def test_deleted_resource_are_not_shown_in_dataset_resource_inline(dataset_with_resources, admin):
    dataset = dataset_with_resources
    resource = dataset.resources.first()
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:datasets_dataset_change", args=[dataset.id]))
    resource_title_on_page = linebreaksbr(resource.title)
    assert resource_title_on_page in smart_text(response.content)
    resource.delete()
    assert resource.is_removed is True
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:datasets_dataset_change", args=[dataset.id]))
    assert resource_title_on_page not in smart_text(response.content)


def test_resources_are_also_deleted_after_dataset_delete(db, dataset_with_resources, admin):
    from mcod.resources.models import Resource
    dataset = dataset_with_resources
    resource = dataset.resources.first()
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:datasets_dataset_change", args=[dataset.id]))
    resource_title_on_page = linebreaksbr(resource.title)
    assert resource_title_on_page in smart_text(response.content)
    assert resource.status == 'published'
    assert dataset.status == 'published'
    dataset.delete()
    assert dataset.is_removed is True
    vr = Resource.deleted.get(id=resource.id)
    assert vr.is_removed is True


def test_removed_datasets_are_not_in_datasets_list(db, admin, dataset):
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:datasets_dataset_changelist"))
    pattern = re.compile(r"/datasets/dataset/\d+/change")
    result = pattern.findall(smart_text(response.content))
    assert result == [f'/datasets/dataset/{dataset.id}/change']
    dataset.delete()
    response = client.get(reverse("admin:datasets_dataset_changelist"))
    result = pattern.findall(smart_text(response.content))
    assert not result


def test_dataset_resources_has_pagination(db, dataset, admin):
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:datasets_dataset_change", args=[dataset.id]))
    assert 'pagination-block' in response.content.decode()


# TODO: fix - not working
# def test_trash_for_editor(datasets, active_editor):
#     datasets[0].delete()
#     datasets[1].delete()
#
#     client = Client()
#     client.force_login(active_editor)
#     response = client.get(reverse("admin:datasets_datasettrash_changelist"))
#     pattern = re.compile(r"/datasets/datasettrash/\d+/change")
#     result = pattern.findall(smart_text(response.content))
#     assert result == [f'/datasets/datasettrash/{datasets[0].id}/change']
#
#     datasets[2].delete()
#     response = client.get(reverse("admin:datasets_datasettrash_changelist"))
#     result = pattern.findall(smart_text(response.content))
#     assert set(result) == set(f'/datasets/datasettrash/{ds.id}/change'
#                               for ds in datasets
#                               if ds.organization in active_editor.organizations.all())
#

# TODO: fix - not working
# def test_add_resource_to_dataset(admin, institution, tag):
#     from mcod.datasets.models import Dataset
#     client = Client()
#     client.force_login(admin)
#     data = {
#
#         'resources-TOTAL_FORMS': '0',
#         'resources-INITIAL_FORMS': '0',
#         'resources-MIN_NUM_FORMS': '0',
#         'resources-MAX_NUM_FORMS': '1000',
#         'resources-2-TOTAL_FORMS': '1',
#         'resources-2-INITIAL_FORMS': '0',
#         'resources-2-MIN_NUM_FORMS': '0',
#         'resources-2-MAX_NUM_FORMS': '1000',
#         'title': "Test with dataset title",
#         'notes': "Tresc",
#         'status': 'published',
#         'update_frequency': 'weekly',
#         'url': 'http://www.test.pl',
#         'organization': [institution.id],
#         'tags': [tag.id],
#         "resources-2-0-switcher": "link",
#         "resources-2-0-link": "http://test.pl",
#         "resources-2-0-title": "123",
#         "resources-2-0-description": "<p>123</p>",
#         "resources-2-0-status": "published",
#         "resources-2-0-id": "",
#         "resources-2-0-dataset": "",
#     }
#
#     client.post(reverse("admin:datasets_dataset_add"), data=data, follow=True)
#
#     ds = Dataset.objects.last()
#     assert ds
#     r = ds.resources.last()
#     assert r.title == "123"
#     assert r.created_by_id == admin.id
#     assert r.modified_by_id == admin.id

# TODO: fix - not working
# def test_restore_dataset_from_trash_is_not_possible_without_restore_his_organization(dataset, admin):
#     assert not dataset.organization.is_removed
#     assert not dataset.is_removed
#     assert Dataset.objects.count() == 1
#     assert Dataset.deleted.count() == 0
#
#     dataset.organization.delete()
#
#     assert Dataset.objects.count() == 0
#     assert Dataset.deleted.count() == 1
#
#     assert dataset.organization.is_removed
#
#     ds = Dataset.deleted.first()
#     assert ds.organization == dataset.organization
#     assert ds.is_removed
#
#     client = Client()
#     client.force_login(admin)
#     client.post(f'/datasets/datasettrash/{ds.id}/change/', data={'is_removed': False})
#
#     ds = Dataset.deleted.get(id=ds.id)
#     assert ds.organization.is_removed
#
#     ds.organization.is_removed = False
#     ds.organization.save()
#
#     client.post(f'/datasets/datasettrash/{ds.id}/change/', data={'is_removed': False})
#
#     assert Dataset.objects.count() == 1
#     assert Dataset.deleted.count() == 0
#
#     ds = Dataset.objects.get(id=ds.id)
#     assert not ds.is_removed


def test_set_published_for_dataset_didnt_change_his_resources_to_publish(db, dataset_with_resources):
    dataset = dataset_with_resources
    assert dataset.status == 'published'
    assert dataset.resources.all().first().status == 'published'

    dataset.status = "draft"
    dataset.save()

    assert dataset.status == 'draft'
    assert dataset.resources.first().status == 'draft'
