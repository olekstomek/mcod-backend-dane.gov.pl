from pytest_bdd import given
from pytest_bdd import parsers

from mcod.alerts.factories import AlertFactory


@given(parsers.parse('alert'))
def alert():
    return AlertFactory.create()
