from urllib.parse import urlparse, parse_qs
from django_redis import get_redis_connection
from mcod.searchhistories.models import SearchHistory
from mcod.users.models import User


class SearchHistoryTool:
    def __init__(self):
        self.con = get_redis_connection()

    def save_histories(self):
        key_pattern = "search_history_user_*"
        keys = self.con.keys(key_pattern)
        for k in keys:
            user_id = int(k.decode().split("_")[-1])
            while True:
                url = self.con.lpop(k)
                if url:
                    url = url.decode()
                    o = urlparse(url)
                    query_sentence = parse_qs(o.query).get("q")
                    if query_sentence:
                        if isinstance(query_sentence, list):
                            query_sentence = query_sentence[0]
                    else:
                        query_sentence = "*"

                    if User.objects.filter(pk=user_id).exists():  # TODO - jakby to zrobić bez tego?
                        SearchHistory.objects.create(
                            url=url,
                            query_sentence=query_sentence,
                            user_id=user_id
                        )
                else:
                    break
