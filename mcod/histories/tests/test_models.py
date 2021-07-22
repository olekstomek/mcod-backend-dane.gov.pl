# import pytest
# from mcod.histories.models import History
#
#
#
# class TestApplicationModel(object):
#     def test_read_history_for_application(self, valid_application):
#         assert History.get_object_history(valid_application).count() == 1
#         valid_application.save()
#         assert History.get_object_history(valid_application).count() == 2
