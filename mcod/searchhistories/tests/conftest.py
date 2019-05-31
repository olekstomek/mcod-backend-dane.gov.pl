import pytest
from mcod.core.tests import factories
from mcod.core.tests.conftest import *  # noqa


@pytest.fixture
def hundred_of_search_histories():
    searchhistories = []
    for i in range(20):
        user = factories.UserFactory()
        for i in range(5):
            sh = factories.SearchHistoryFactory.build(user=user)
            sh.save()
            searchhistories.append(sh)
    return searchhistories


@pytest.fixture
def searchhistory_for_admin(admin_user):
    searchhistories = []
    for i in range(5):
        sh = factories.SearchHistoryFactory.build(user=admin_user)
        sh.save()
        searchhistories.append(sh)
    return searchhistories
