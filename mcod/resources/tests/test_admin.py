import datetime
import re
import pytest
import logging
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_text
from pytest_bdd import given, parsers, scenarios
import mcod.unleash
import requests_mock
from django.utils.translation import gettext as _

from mcod.datasets.documents import Resource
from mcod.unleash import is_enabled

logger = logging.getLogger('mcod')


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
    'features/resource_change.feature',
    'features/resource_validation.feature',
    'features/resource_openness.feature',
    'features/resource_details_admin.feature',
    'features/resources_list_admin.feature',
)


class TestEditorAccess(object):

    def test_editor_not_in_organization_cant_see_resource_from_organizaton(self, active_editor, resource):
        client = Client()
        client.force_login(active_editor)
        response = client.get(f"/resources/resource/{resource.id}", follow=False)
        assert response.status_code == 301

    def test_trash_for_editor(self, db, active_editor, resources):
        editor_resources = Resource.objects.filter(dataset__organization_id=active_editor.organizations.all()[0].pk)
        editor_res_ids = list(editor_resources.values_list('pk', flat=True))
        editor_resources.delete()
        for res in resources:
            res.delete()
        client = Client()
        client.force_login(active_editor)
        response = client.get(reverse("admin:resources_resourcetrash_changelist"))
        pattern = re.compile(r"/resources/resourcetrash/\d+/change")
        result = pattern.findall(smart_text(response.content))
        assert all([f'/resources/resourcetrash/{res_id}/change' in result for res_id in editor_res_ids])


class TestDuplicateResource(object):

    def test_editor_can_add_resource_based_on_other_resource(self, active_editor):
        resource = Resource.objects.filter(dataset__organization_id=active_editor.organizations.all()[0].pk)[0]
        id_ = resource.id
        client = Client()
        client.force_login(active_editor)
        response = client.get(f"/resources/resource/{id_}", follow=True)
        assert response.status_code == 200
        assert '<a href="/resources/resource/add/?from_id={}" class="btn btn-high"'.format(
            id_) in smart_text(
            response.content)
        response = client.get(f"/resources/resource/add/?from_id={id_}")
        assert response.status_code == 200
        content = response.content.decode()
        assert resource.title in content
        assert resource.description in content
        assert resource.status in content
        assert resource.dataset.title in content

    def test_admin_can_add_resource_based_on_other_resource(self, admin, dataset_with_resources):
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

    def test_cant_duplicate_deleted_resource(self, admin, removed_resource):
        client = Client()
        client.force_login(admin)
        response = client.get(f"/resources/resource/add/?from_id={removed_resource.pk}")
        content = response.content.decode()
        assert removed_resource.title not in content
        assert removed_resource.description not in content
        # assert f'value="{removed_resource.pk}"' not in content  # raises errors sometimes.

    def test_cant_duplicate_imported_resource(self, admin, imported_ckan_resource):
        client = Client()
        client.force_login(admin)
        response = client.get(f"/resources/resource/add/?from_id={imported_ckan_resource.pk}")
        content = response.content.decode()
        if f'value="{imported_ckan_resource.pk}"' in content:
            logger.error("CKAN RESOURCE ID:", imported_ckan_resource.pk)
        assert imported_ckan_resource.title not in content
        assert imported_ckan_resource.description not in content
        # assert f'value="{imported_ckan_resource.pk}"' not in content  # raises errors sometimes.


class TestRevalidationAction(object):

    def test_revalidate_resource_started(self, buzzfeed_fakenews_resource, admin):
        client = Client()
        client.force_login(admin)
        response = client.get(
            reverse("admin:resource-revalidate", kwargs={'resource_id': buzzfeed_fakenews_resource.pk}),
            follow=True
        )
        content = response.content.decode()
        assert response.status_code == 200
        assert _('Task for resource revalidation queued') in content

    def test_no_user_action(self, resource_with_file):
        client = Client()
        response = client.get(reverse("admin:resource-revalidate", args=[resource_with_file.pk], ))

        assert response.status_code == 403

    def test_revalidate_error_for_resource_from_trash(self, removed_resource, admin):
        client = Client()
        client.force_login(admin)
        response = client.get(
            reverse("admin:resource-revalidate", kwargs={'resource_id': removed_resource.pk}),
            follow=True
        )
        content = response.content.decode()
        assert response.status_code == 200
        assert _('Resource with this id does not exists') in content


class TestResourceAndDataset(object):

    def test_restore_resource_from_trash_is_not_possible_without_restore_his_dataset(self, resource, admin):
        assert resource.dataset.is_removed is False
        assert resource.is_removed is False
        assert Resource.objects.count() == 1

        resource.dataset.delete()

        assert resource.dataset.is_removed is True

        r = Resource.trash.first()
        assert r.dataset == resource.dataset
        assert r.is_removed is True

        client = Client()
        client.force_login(admin)
        client.post(f'/resources/resourcetrash/{r.id}/change/', data={'is_removed': False})
        r = Resource.trash.get(id=r.id)
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
        resp = client.get(resource.admin_change_url)
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
        resp = client.get(tabular_resource.admin_change_url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert '#rules' in content
        assert 'class="disabled disabledTab"' not in content

    def test_verification_rules_validates_if_selected_properly(self, geo_tabular_data_resource, admin):
        geo_tabular_data_resource.revalidate()
        geo_tabular_data_resource.refresh_from_db()
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['test geo csv'], 'description': ['<p>cecece</p>'],
            'dataset': [geo_tabular_data_resource.dataset_id],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'show_tabular_view': ['on'],
            'rule_type_2': ['numeric'], 'rule_type_3': ['numeric'], 'schema_type_0': ['string'],
            'schema_type_1': ['string'], 'schema_type_2': ['integer'], 'schema_type_3': ['integer'],
            'geo_0': [''], 'geo_1': [''], 'geo_2': [''], 'geo_3': [''], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['4'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['4'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_verify_rules': ['']}
        resp = client.post(geo_tabular_data_resource.admin_change_url, data=data, follow=True)
        content = resp.content.decode()
        assert _('During the verification of column "{colname}" with the "{rule}" rule no errors detected'
                 ).format(colname='x', rule=_('Numeric')) in content
        assert _('During the verification of column "{colname}" with the "{rule}" rule no errors detected'
                 ).format(colname='y', rule=_('Numeric')) in content

    def test_verification_rules_shows_validation_error(self, geo_tabular_data_resource, admin):
        geo_tabular_data_resource.revalidate()
        geo_tabular_data_resource.refresh_from_db()
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['test geo csv'], 'description': ['<p>cecece</p>'],
            'dataset': [geo_tabular_data_resource.dataset_id],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'show_tabular_view': ['on'],
            'rule_type_2': ['address_feature'], 'rule_type_3': ['nip'], 'schema_type_0': ['string'],
            'schema_type_1': ['string'], 'schema_type_2': ['integer'], 'schema_type_3': ['integer'],
            'geo_0': [''], 'geo_1': [''], 'geo_2': [''], 'geo_3': [''], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['4'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['4'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_verify_rules': ['']}
        resp = client.post(geo_tabular_data_resource.admin_change_url, data=data, follow=True)
        content = resp.content.decode()
        assert _('During the verification of column "%(colname)s"'
                 ' with the rule "%(rule)s" detected errors (max 5)') % {'colname': 'x',
                                                                         'rule': _('Address feature')} in content
        assert _('During the verification of column "%(colname)s"'
                 ' with the rule "%(rule)s" detected errors (max 5)') % {'colname': 'y', 'rule': 'NIP'} in content

    def test_verification_rules_shows_validation_error_for_unknown_rule(self, resource_with_date_and_datetime, admin):
        resource_with_date_and_datetime.revalidate()
        resource_with_date_and_datetime.refresh_from_db()
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['test geo csv'], 'description': ['<p>cecece</p>'],
            'dataset': [resource_with_date_and_datetime.dataset_id],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'show_tabular_view': ['on'],
            'rule_type_1': ['unknown_rule'], 'schema_type_0': ['string'],
            'schema_type_1': ['string'],
            'geo_0': [''], 'geo_1': [''], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['4'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['4'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_verify_rules': ['']}
        resp = client.post(resource_with_date_and_datetime.admin_change_url, data=data, follow=True)
        content = resp.content.decode()
        assert _('Verification of column "{colname}" by the rule "{rule}" failed').format(
            colname='datetime', rule='unknown_rule') in content


class TestResourceChangeType(object):

    def test_change_type_tab_should_not_be_available_for_resources_without_tabular_data_schema(self, resource,
                                                                                               admin):
        assert not resource.tabular_data_schema
        client = Client()
        client.force_login(admin)
        resp = client.get(resource.admin_change_url)
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
            resp = client.get(tabular_resource.admin_change_url)
            assert resp.status_code == 200
            assert '#types' in resp.content.decode()

    def test_change_type_is_run_successfully(self, geo_tabular_data_resource, admin):
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['test geo csv'], 'description': ['<p>more than 20 characters</p>'],
            'dataset': [geo_tabular_data_resource.dataset_id],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'show_tabular_view': ['on'],
            'schema_type_0': ['string'],
            'schema_type_1': ['string'], 'schema_type_2': ['number'], 'schema_type_3': ['integer'],
            'geo_0': [''], 'geo_1': [''], 'geo_2': [''], 'geo_3': [''], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['4'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['4'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_change_type': ''}
        if is_enabled('S41_resource_has_high_value_data.be'):
            data['has_high_value_data'] = False
        resp = client.post(
            reverse('admin:resources_resource_change', kwargs={'object_id': geo_tabular_data_resource.id}), data=data,
            follow=True
        )
        content = resp.content.decode()
        assert _('Data type changed') in content


class TestResourceMapSave(object):

    def test_map_save_is_run_successfully(self, geo_tabular_data_resource, admin):
        geo_tabular_data_resource.revalidate()
        geo_tabular_data_resource.refresh_from_db()
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['test geo csv'], 'description': ['<p>more than 20 characters</p>'],
            'dataset': [geo_tabular_data_resource.dataset_id],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'show_tabular_view': ['on'],
            'schema_type_0': ['string'],
            'schema_type_1': ['string'], 'schema_type_2': ['integer'], 'schema_type_3': ['integer'],
            'geo_0': [''], 'geo_1': ['label'], 'geo_2': ['l'], 'geo_3': ['b'], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['4'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['4'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_map_save': [''],
        }
        if is_enabled('S41_resource_has_high_value_data.be'):
            data['has_high_value_data'] = False
        resp = client.post(geo_tabular_data_resource.admin_change_url, data=data, follow=True)
        content = resp.content.decode()
        assert _('Map definition saved') in content


class TestResourceChangeList(object):

    def get_filter_result_response(self, set_attrs, resource, admin, filter_name, filter_value):
        client = Client()
        if set_attrs:
            setattr(resource, set_attrs[0], set_attrs[1])
            resource.save()
        client.force_login(admin)
        full_url = f'{resource.admin_list_url()}?{filter_name}={filter_value}'
        resp = client.get(full_url)
        content = resp.content.decode()
        return content

    @pytest.mark.parametrize(
        'filter_name, filter_value, set_attrs',
        [('type', 'api', None), ('type', 'api-change', ('forced_api_type', True))]
    )
    def test_list_type_api_filter(
            self, resource_of_type_api, local_file_resource, admin, filter_name, filter_value, set_attrs
    ):
        content = self.get_filter_result_response(set_attrs, resource_of_type_api, admin, filter_name, filter_value)
        assert resource_of_type_api.title in content
        assert local_file_resource.title not in content

    @pytest.mark.parametrize(
        'filter_name, filter_value, set_attrs',
        [('type', 'file', None), ('type', 'file-change', ('forced_file_type', True))]
    )
    def test_list_type_file_filter(
            self, resource_of_type_api, local_file_resource, admin, filter_name, filter_value, set_attrs
    ):
        content = self.get_filter_result_response(set_attrs, local_file_resource, admin, filter_name, filter_value)
        assert resource_of_type_api.title not in content
        assert local_file_resource.title in content

    def test_list_link_status_filter(self, resource_with_failure_tasks_statuses,
                                     resource_with_success_tasks_statuses, admin):
        client = Client()
        client.force_login(admin)
        url = resource_with_failure_tasks_statuses.admin_list_url()
        first_resp = client.get(url)
        first_content = first_resp.content.decode()
        assert resource_with_failure_tasks_statuses.title in first_content
        assert resource_with_success_tasks_statuses.title in first_content
        full_url = f'{url}?link_status=FAILURE'
        resp = client.get(full_url)
        content = resp.content.decode()
        assert resource_with_failure_tasks_statuses.title in content
        assert resource_with_success_tasks_statuses.title not in content

    def test_list_link_status_na_filter(self, buzzfeed_fakenews_resource, resource, admin):
        buzzfeed_fakenews_resource.revalidate()
        resource.link_tasks.clear()
        client = Client()
        client.force_login(admin)
        url = resource.admin_list_url()
        first_resp = client.get(url)
        first_content = first_resp.content.decode()
        assert buzzfeed_fakenews_resource.title in first_content
        assert resource.title in first_content
        full_url = f'{url}?link_status=N/A'
        resp = client.get(full_url)
        content = resp.content.decode()
        assert buzzfeed_fakenews_resource.title not in content
        assert resource.title in content


class TestResourceForm(object):

    def test_change_resource(self, admin, resource):
        client = Client()
        client.force_login(admin)
        data = {
            'title': ['title changed in form'], 'description': ['<p>more than 20 characters</p>'],
            'data_date': [datetime.date(2021, 5, 4)], 'status': ['published'], 'title_en': [''], 'description_en': [''],
            'slug_en': [''], 'Resource_file_tasks-TOTAL_FORMS': ['4'], 'Resource_file_tasks-INITIAL_FORMS': ['1'],
            'dataset': [resource.dataset_id],
            'Resource_file_tasks-MIN_NUM_FORMS': ['0'], 'Resource_file_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_data_tasks-TOTAL_FORMS': ['1'], 'Resource_data_tasks-INITIAL_FORMS': ['1'],
            'Resource_data_tasks-MIN_NUM_FORMS': ['0'], 'Resource_data_tasks-MAX_NUM_FORMS': ['1000'],
            'Resource_link_tasks-TOTAL_FORMS': ['1'], 'Resource_link_tasks-INITIAL_FORMS': ['1'],
            'Resource_link_tasks-MIN_NUM_FORMS': ['0'], 'Resource_link_tasks-MAX_NUM_FORMS': ['1000'],
            '_save': ['']}
        if is_enabled('S41_resource_has_high_value_data.be'):
            data['has_high_value_data'] = False
        resp = client.post(resource.admin_change_url, data=data, follow=True)
        content = resp.content.decode()
        assert resp.resolver_match.url_name == 'resources_resource_changelist'
        assert 'title changed in form' in content

    def test_non_csv_resource_doesnt_display_csv_file_data(self, admin, resource_of_type_website):
        client = Client()
        client.force_login(admin)
        resp = client.get(resource_of_type_website.admin_change_url)
        content = resp.content.decode()
        assert 'csv_file' not in content

    def test_xls_resource_display_csv_file_data(self, admin, resource_with_xls_file):
        client = Client()
        client.force_login(admin)
        resp = client.get(resource_with_xls_file.admin_change_url)
        content = resp.content.decode()
        if is_enabled('S40_new_file_model.be'):
            assert 'csv_converted_file' in content
        else:
            assert 'csv_file' in content

    def test_forced_file_type_checkbox_visible_for_api_resource(self, admin, remote_file_resource_of_api_type):
        client = Client()
        client.force_login(admin)
        resp = client.get(remote_file_resource_of_api_type.admin_change_url)
        content = resp.content.decode()
        assert 'forced_file_type' in content

    def test_forced_file_type_checkbox_visible_for_forced_file_resource(
            self, admin, remote_file_resource_with_forced_file_type):
        client = Client()
        client.force_login(admin)
        resp = client.get(remote_file_resource_with_forced_file_type.admin_change_url)
        content = resp.content.decode()
        assert 'forced_file_type' in content

    def test_forced_file_type_checkbox_not_visible_for_forced_api_resource(self, admin, resource_of_type_api):
        resource_of_type_api.forced_api_type = True
        resource_of_type_api.save()
        client = Client()
        client.force_login(admin)
        resp = client.get(resource_of_type_api.admin_change_url)
        content = resp.content.decode()
        assert 'forced_file_type' not in content
