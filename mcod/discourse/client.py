from pydiscourse import DiscourseClient as BaseDiscourseClient
from mcod import settings


class DiscourseClient(BaseDiscourseClient):
    def list_api_keys(self):
        return self._get('/admin/api/keys')

    def create_api_key(self, username, scopes=None):
        kwargs = {
            'key': {
                'username': username,
                'description': f'Access key for user {username}'
            },
        }
        return self._post("/admin/api/keys", json=True, ** kwargs)

    def revoke_api_key(self, keyid):
        return self._post("/admin/api/keys/{0}/revoke".format(keyid))

    def undo_revoke_api_key(self, keyid):
        return self._post("/admin/api/keys/{0}/undo-revoke".format(keyid))

    def delete_api_key(self, keyid):
        return self._delete("/admin/api/keys/{0}".format(keyid))


def get_client():
    return DiscourseClient(
        settings.DISCOURSE_HOST, api_username=settings.DISCOURSE_API_USER, api_key=settings.DISCOURSE_API_KEY)
