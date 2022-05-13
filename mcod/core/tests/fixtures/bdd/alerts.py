from pytest_bdd import given, parsers

from mcod.alerts.factories import AlertFactory


@given(parsers.parse('alert'))
def alert():
    return AlertFactory.create()
