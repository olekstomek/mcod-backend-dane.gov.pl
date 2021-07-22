from pytest_bdd import given, parsers
from mcod.histories.factories import HistoryFactory


@given(parsers.parse('{num:d} histories'))
def num_of_histories(num):
    return HistoryFactory.create_batch(num)
