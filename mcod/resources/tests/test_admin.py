from django.template.defaultfilters import linebreaksbr
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_text
from pytest_bdd import given, parsers, scenarios
import mcod.unleash
import requests_mock

from mcod.datasets.documents import Resource


@given(parsers.parse('resource is created for link {link} with {media_type} content'))
def create_resource_for_link(
        admin_context, admin, link, media_type, buzzfeed_dataset, document_docx_pack, example_xls_file, file_xml,
        file_json, multi_file_zip_pack):
    request_params = {
        'html': {'content': b'<html>test</html>', 'headers': {'Content-Type': 'text/html'}},
        'json': {'body': file_json},
        'zip': {'body': multi_file_zip_pack},
        'xls': {'body': example_xls_file},
        'xml': {'body': file_xml},
    }
    with requests_mock.mock() as m:
        params = request_params.get(media_type)
        m.get(link, **params)
        data = {
            'switcher': 'link',
            'file': '',
            'link': link,
            'title': 'Test resource',
            'description': 'description...',
            'data_date': '02.07.2019',
            'status': 'published',
            'Resource_file_tasks-TOTAL_FORMS': 3,
            'Resource_file_tasks-INITIAL_FORMS': 0,
            'Resource_file_tasks-MIN_NUM_FORMS': 0,
            'Resource_file_tasks-MAX_NUM_FORMS': 1000,
            'Resource_data_tasks-TOTAL_FORMS': 3,
            'Resource_data_tasks-INITIAL_FORMS': 0,
            'Resource_data_tasks-MIN_NUM_FORMS': 0,
            'Resource_data_tasks-MAX_NUM_FORMS': 1000,
            'Resource_link_tasks-TOTAL_FORMS': 3,
            'Resource_link_tasks-INITIAL_FORMS': 0,
            'Resource_link_tasks-MIN_NUM_FORMS': 0,
            'Resource_link_tasks-MAX_NUM_FORMS': 1000,
            'dataset': buzzfeed_dataset.id,
        }
        client = Client()
        client.force_login(admin)
        response = client.post(
            '/resources/resource/add/', data=data, follow=True)
        admin_context.response = response


scenarios(
    'features/file_validation.feature',
    'features/resource_creation.feature',
    'features/resource_openness.feature',
    'features/resource_details_admin.feature',
    'features/resources_list_admin.feature',
)


def test_editor_shouldnt_see_deleted_resources(resource, admin, active_editor):
    resource.delete()
    assert resource.is_removed is True
    resource_title_on_page = linebreaksbr(resource.title)
    client = Client()
    active_editor.organizations.set([resource.dataset.organization])
    active_editor.save()
    client.force_login(active_editor)
    response = client.get("/resources/resource/", follow=True)
    assert resource_title_on_page not in smart_text(response.content)


def test_admin_can_add_resource_based_on_other_resource(admin, dataset_with_resources):
    dataset = dataset_with_resources
    resource = dataset.resources.last()
    id_ = resource.id
    client = Client()
    client.force_login(admin)
    response = client.get(f"/resources/resource/{id_}", follow=True)
    assert response.status_code == 200
    assert '<a href="/resources/resource/add/?from_id={}" class="btn btn-high"'.format(
        id_) in smart_text(
        response.content)
    response = client.get(f"/resources/resource/add/?from_id={id_}")
    assert response.status_code == 200
    content = response.content.decode()

    # is form filled with proper data
    assert resource.title in content
    assert resource.description in content
    assert resource.status in content
    assert dataset.title in content
    assert f'value="{id_}"' in content


# TODO: fix - not working
#
# def test_editor_can_add_resource_based_on_other_resource( resource, active_editor,
#                                                          dataset):
#     id_ = resource.id
#     client = Client()
#     client.force_login(active_editor)
#     response = client.get(f"/resources/resource/{id_}", follow=True)
#     assert response.status_code == 200
#     assert '<a href="/resources/resource/add/?from_id={}" class="btn btn-high" id="duplicate_button">'.format(
#         id_) in smart_text(
#         response.content)
#     response = client.get(f"/resources/resource/add/?from_id={id_}")
#     assert response.status_code == 200
#     content = response.content.decode()
#
#     # is form filled with proper data
#     assert resource.title in content
#     assert resource.description in content
#     assert resource.status in content
#     assert dataset.title in content


def test_editor_not_in_organization_cant_see_resource_from_organizaton(active_editor, resource):
    client = Client()
    client.force_login(active_editor)
    response = client.get(f"/resources/resource/{resource.id}", follow=False)
    assert response.status_code == 301


def test_new_resource_cant_be_duplicated(resource, active_editor):
    id_ = resource.id
    client = Client()
    client.force_login(active_editor)
    response = client.get("/resources/resource/add/", follow=True)
    assert response.status_code == 200
    assert '<a href="/resources/resource/add/?from_id={}" class="btn" id="duplicate_button">'.format(
        id_) not in smart_text(
        response.content)


# TODO: fix - not working
#
# def test_trash_for_editor( db, resources, active_editor):
#     resources[0].delete()
#     resources[2].delete()
#
#     client = Client()
#     client.force_login(active_editor)
#     response = client.get(reverse("admin:resources_resourcetrash_changelist"))
#     pattern = re.compile(r"/resources/resourcetrash/\d+/change")
#     result = pattern.findall(smart_text(response.content))
#     assert result == [f'/resources/resourcetrash/{resources[0].id}/change']
#
#     resources[1].delete()
#     resources[3].delete()
#     response = client.get(reverse("admin:resources_resourcetrash_changelist"))
#     result = pattern.findall(smart_text(response.content))
#     resources = set(f'/resources/resourcetrash/{res.id}/change'
#                     for res in resources
#                     if res.dataset.organization in active_editor.organizations.all())
#     assert set(result) == resources


class TestRevalidationAction(object):
    # TODO: fix - not working
    # def test_valid_action(self, resource, admin, mocker):
    #     mocker.patch(
    #         'mcod.resources.tasks.download_file', return_value=('file', {})
    #     )
    #     counts = (resource.file_tasks.count(), resource.link_tasks.count(), resource.data_tasks.count())
    #
    #     client = Client()
    #     client.force_login(admin)
    #     _view = reverse("admin:resource-revalidate", args=[resource.id], )
    #     response = client.get(_view)
    #
    #     assert response.status_code == 302
    #     assert response.url == f"/resources/resource/{resource.id}/change/"
    #
    #     resource.refresh_from_db()
    #     counts2 = (resource.file_tasks.count(), resource.link_tasks.count(), resource.data_tasks.count())
    #     for c1, c2 in zip(counts, counts2):
    #         assert c2 == 2

    def test_no_user_action(self, resource_with_file):
        client = Client()
        response = client.get(reverse("admin:resource-revalidate", args=[resource_with_file.id], ))

        assert response.status_code == 403


class TestResourceAndDataset(object):

    def test_restore_resource_from_trash_is_not_possible_without_restore_his_dataset(self, resource, admin):
        assert resource.dataset.is_removed is False
        assert resource.is_removed is False
        assert Resource.objects.count() == 1

        resource.dataset.delete()

        assert resource.dataset.is_removed is True

        r = Resource.deleted.first()
        assert r.dataset == resource.dataset
        assert r.is_removed is True

        client = Client()
        client.force_login(admin)
        client.post(f'/resources/resourcetrash/{r.id}/change/', data={'is_removed': False})
        r = Resource.deleted.get(id=r.id)
        assert r.dataset.is_removed is True

        r.dataset.is_removed = False
        r.dataset.save()

        client.post(f'/resources/resourcetrash/{r.id}/change/', data={'is_removed': False})
        r = Resource.objects.get(id=r.id)
        assert r.dataset.is_removed is False


class TestResourceTabularDataRules(object):

    def test_verification_tabs_should_not_be_available_for_resources_without_tabular_data_schema(self, resource,
                                                                                                 admin):
        assert not resource.tabular_data_schema

        client = Client()
        client.force_login(admin)
        resp = client.get(reverse('admin:resources_resource_change', kwargs={'object_id': resource.id}))
        assert resp.status_code == 200
        assert '#rules' in resp.content.decode()
        assert 'class="disabled disabledTab"' in resp.content.decode()

    def test_verification_tabs_should_be_available_for_resources_with_tabular_data_schema(self, tabular_resource,
                                                                                          admin):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema

        client = Client()
        client.force_login(admin)
        resp = client.get(reverse('admin:resources_resource_change', kwargs={'object_id': tabular_resource.id}))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert '#rules' in content
        assert 'class="disabled disabledTab"' not in content


class TestResourceChangeType(object):

    def test_change_type_tab_should_not_be_available_for_resources_without_tabular_data_schema(self, resource,
                                                                                               admin):
        assert not resource.tabular_data_schema
        client = Client()
        client.force_login(admin)
        resp = client.get(reverse('admin:resources_resource_change', kwargs={'object_id': resource.id}))
        assert resp.status_code == 200
        assert '#types' not in resp.content.decode()

    def test_change_type_tab_should_be_available_for_resources_with_tabular_data_schema(self,
                                                                                        tabular_resource,
                                                                                        admin, monkeypatch):
        def true_is_enabled(value):
            return True

        with monkeypatch.context() as m:
            m.setattr(mcod.unleash, "is_enabled", true_is_enabled)

            tabular_resource.revalidate()
            rs = Resource.objects.get(pk=tabular_resource.id)
            assert rs.tabular_data_schema

            client = Client()
            client.force_login(admin)
            resp = client.get(reverse('admin:resources_resource_change', kwargs={'object_id': tabular_resource.id}))
            assert resp.status_code == 200
            assert '#types' in resp.content.decode()
