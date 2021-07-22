# import pytest
# from django.test import Client
# from django.urls import reverse
# from falcon import HTTP_OK
#
# from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper
# from mcod.datasets.models import Dataset, UPDATE_FREQUENCY
#
#
#
# class TestDatasetsView(ElasticCleanHelper):
#     def test_update_frequency_translations(self, client, institution):
#         # MCOD-1031
#         for uf_code, readable in UPDATE_FREQUENCY:
#             ds = Dataset(
#                 slug=f"test-{uf_code}-dataset",
#                 title=f"{readable} test name",
#                 organization=institution,
#                 update_frequency=uf_code
#             )
#             ds.save()
#
#             resp = client.simulate_get(f'/datasets/{ds.id}')
#             assert HTTP_OK == resp.status
#             body = resp.json
#             assert readable == body['data']['attributes']['update_frequency']
#
#
#
# def test_dataset_autocomplete_view(admin, datasets):
#     client = Client()
#     client.force_login(admin)
#
#     response = client.get(reverse("dataset-autocomplete"))
#
#     assert len(response.json()['results']) == 3
#
#
#
# def test_dataset_autocomplete_view_for_editor_without_organization(active_editor_without_org, datasets):
#     client = Client()
#     assert not active_editor_without_org.organizations.all()
#     client.force_login(active_editor_without_org)
#
#     response = client.get(reverse("dataset-autocomplete"))
#
#     assert len(response.json()['results']) == 0
#
#
# #
# # def test_dataset_autocomplete_view_editor_with_organization(active_editor):
# #     client = Client()
# #     client.force_login(active_editor)
# #
# #     response = client.get(reverse("dataset-autocomplete"))
# #
# #     assert len(response.json()['results']) == 2
