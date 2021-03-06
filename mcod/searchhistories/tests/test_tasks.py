import pytest

from mcod.searchhistories.tasks import save_searchhistories_task
from mcod.searchhistories.models import SearchHistory
from django_redis import get_redis_connection


@pytest.mark.django_db
class TestSearchhistoryTool:

    def test_save_searchhistories_task(self, editor_user):
        redis_con = get_redis_connection("default")
        redis_con.delete("search_history_user_None")
        keys = [k.decode() for k in redis_con.keys()]
        key = f"search_history_user_{editor_user.id}"
        assert key not in keys

        redis_con.lpush(key, "http://test.dane.gov.pl/datasets?q=test")
        redis_con.lpush(key, "http://test.dane.gov.pl/datasets?q=test2")

        keys = [k.decode() for k in redis_con.keys()]
        assert key in keys
        assert SearchHistory.objects.all().count() == 0

        save_searchhistories_task()
        assert SearchHistory.objects.all().count() == 2

    def test_save_searchhistories_task_for_not_existing_user(self, editor_user):
        redis_con = get_redis_connection("default")

        keys = [k.decode() for k in redis_con.keys()]
        key = f"search_history_user_{editor_user.id + 1000}"
        assert key not in keys
        redis_con.lpush(key, "http://test.dane.gov.pl/datasets?q=test")
        redis_con.lpush(key, "http://test.dane.gov.pl/datasets?q=test2")

        keys = [k.decode() for k in redis_con.keys()]
        assert key in keys
        assert SearchHistory.objects.all().count() == 0

        save_searchhistories_task()
        assert SearchHistory.objects.all().count() == 0

        keys = [k.decode() for k in redis_con.keys()]
        assert key not in keys

    def test_save_searchhistories_task_for_search_with_empty_q(self, editor_user):
        redis_con = get_redis_connection("default")

        keys = [k.decode() for k in redis_con.keys()]
        key = f"search_history_user_{editor_user.id}"

        assert key not in keys
        redis_con.lpush(key, "http://test.dane.gov.pl/datasets")
        redis_con.lpush(key, "http://test.dane.gov.pl/applications")

        keys = [k.decode() for k in redis_con.keys()]
        assert key in keys
        assert SearchHistory.objects.all().count() == 0

        save_searchhistories_task()
        assert SearchHistory.objects.all().count() == 0

        keys = [k.decode() for k in redis_con.keys()]
        assert key not in keys
