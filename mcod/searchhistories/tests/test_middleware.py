import pytest
from falcon import HTTP_OK
from django_redis import get_redis_connection


@pytest.mark.django_db
def test_searchhistories_middleware_set_up_key_in_redis(client, editor_user):
    redis_con = get_redis_connection("default")
    keys = [k.decode() for k in redis_con.keys()]

    key = f"search_history_user_{editor_user.id}"
    assert key not in keys
    resp = client.simulate_post(path='/auth/login', json={
        'email': editor_user.email,
        'password': 'Britenet.1'
    })

    token = resp.json['data']['attributes']['token']

    assert resp.status == HTTP_OK
    resp = client.simulate_get(
        "/datasets",
        query_string="q=testmiddleware",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert HTTP_OK == resp.status

    keys = [k.decode() for k in redis_con.keys()]
    assert key in keys
    redis_con.delete(key)  # clean for future tests


@pytest.mark.django_db
def test_searchhistories_middleware_simply_get_on_page_shouldnt_increas_list(client, editor_user):
    redis_con = get_redis_connection("default")
    keys = [k.decode() for k in redis_con.keys()]

    key = f"search_history_user_{editor_user.id}"
    assert key not in keys
    resp = client.simulate_post(path='/auth/login', json={
        'email': editor_user.email,
        'password': 'Britenet.1'
    })

    token = resp.json['data']['attributes']['token']

    assert resp.status == HTTP_OK
    resp = client.simulate_get(
        "/datasets",
        query_string="page=1&per_page=5&q=&sort=-modified",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert HTTP_OK == resp.status

    resp = client.simulate_get(
        "/applications",
        query_string="page=1&per_page=5&q=&sort=-created",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert HTTP_OK == resp.status

    resp = client.simulate_get(
        "/articles",
        query_string="page=1&per_page=5&q=&sort=-created",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert HTTP_OK == resp.status

    keys = [k.decode() for k in redis_con.keys()]
    assert key not in keys


@pytest.mark.django_db
def test_searchhistories_middleware_search_for_institutions_is_not_saved(client, editor_user):
    redis_con = get_redis_connection("default")
    keys = [k.decode() for k in redis_con.keys()]

    key = f"search_history_user_{editor_user.id}"
    assert key not in keys
    resp = client.simulate_post(path='/auth/login', json={
        'email': editor_user.email,
        'password': 'Britenet.1'
    })

    token = resp.json['data']['attributes']['token']

    assert resp.status == HTTP_OK
    resp = client.simulate_get(
        "/institutions",
        query_string="q=testmiddleware",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert HTTP_OK == resp.status

    keys = [k.decode() for k in redis_con.keys()]
    assert key not in keys
