# import pytest
#
# from mcod.counters.lib import Counter
# from mcod.lib.tests.conftest import *  # noqa
# from mcod.lib.tests.helpers.elasticsearch import ElasticCleanHelper
#
#
#
# class TestCounters(ElasticCleanHelper):
#     def test_application_save_counters(self, client, applications_list, mocker):
#         app1, app2, _, app3 = applications_list
#
#         modified_before = [app.modified for app in (app1, app2, app3)]
#
#         counter = Counter()
#         counter._clear_counters()
#
#         def refresh():
#             # FIXME bulk na ES nie znajduje dokumentów.
#             #   końcówka applications wszystko zwraca więc są zaindeksowane
#             #   może być używany inny obiekt connections? albo coś jeszcze potrzebne do testów?
#             counter.save_counters()
#
#             for app in (app1, app2, app3):
#                 app.refresh_from_db()
#
#         client.simulate_get(f"/applications")
#         client.simulate_get(f"/applications/{app1.id}")
#         client.simulate_get(f"/applications/{app1.id}/datasets")
#         client.simulate_get(f"/applications/{app1.id}/history")
#
#         client.simulate_get(f"/applications/{app2.id}")
#
#         client.simulate_get(f"/applications/{app3.id}")
#         client.simulate_get(f"/applications/{app3.id}/datasets")
#
#         #mocker.patch('mcod.counters.lib._client', return_value=_client)
#         counter.save_counters()
#
#         #refresh()
#
#         for app in (app1, app2, app3):
#             app.refresh_from_db()
#
#         assert app1.views_count == 1
#         assert app2.views_count == 1
#         assert app3.views_count == 1
#
#         for i in range(4):
#             client.simulate_get(f"/applications/{app1.id}")
#
#         for i in range(2):
#             client.simulate_get(f"/applications/{app2.id}")
#
#         for i in range(7):
#             client.simulate_get(f"/applications/{app3.id}")
#
#         refresh()
#         assert app1.views_count == 5
#         assert app2.views_count == 3
#         assert app3.views_count == 8
#
#         app_list = client.simulate_get(f"/applications").json['data']
#         es_values = {app['id']: app['attributes']['views_count'] for app in app_list}
#
#         for i, app in enumerate((app1, app2, app3)):
#             assert app.modified == modified_before[i]
#             assert app.views_count == es_values[app.id]
