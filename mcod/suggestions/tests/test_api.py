from time import sleep

import pytest
from falcon import HTTP_201, HTTP_405

from mcod.suggestions.models import Suggestion


@pytest.mark.django_db
def test_suggestion_create(client14):
    assert len(Suggestion.objects.all()) == 0
    resp = client14.simulate_post(
        path=f'/submissions',
        json={
            "data": {
                "type": "submission",
                "attributes": {
                    "notes": "123"
                }
            }
        }
    )

    assert resp.status == HTTP_201
    sleep(2)
    assert len(Suggestion.objects.all()) == 1
    assert Suggestion.objects.last().notes == "123"


@pytest.mark.django_db
def test_suggestion_get_is_not_allowed(client14):
    resp = client14.simulate_get(
        path=f'/submissions'
    )

    assert resp.status == HTTP_405
