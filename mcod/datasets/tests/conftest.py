import csv
import os

import pytest
from pytest_factoryboy import register
from mcod.core.tests.conftest import *  # noqa
from mcod import settings
from mcod.core.tests import factories

register(factories.OrganizationFactory)
register(factories.EditorFactory)
register(factories.DatasetFactory)


@pytest.fixture
def state_variants():
    f = open(os.path.join(settings.TEST_DATA_PATH, 'state_variants.csv'), 'rt')
    data = [r for r in csv.reader(f)]
    headers = data[0]
    result = []
    for row in data[1:]:
        result.append({
            headers[idx]: item for idx, item in enumerate(row)
        })

    return result
