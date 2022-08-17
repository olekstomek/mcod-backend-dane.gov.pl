from django.conf import settings
from django.contrib.auth import get_user_model

from mcod.core.tasks import extended_shared_task
from mcod.discourse.client import DiscourseClient


@extended_shared_task
def user_sync_task(user_id, created=False):
    User = get_user_model()
    user = User.raw.filter(pk=user_id).first()

    client = DiscourseClient(settings.DISCOURSE_SYNC_HOST, settings.DISCOURSE_API_USER, settings.DISCOURSE_API_KEY)
    can_access_forum = all([user, user.is_active, (user.is_superuser or user.agent), not user.is_removed])

    if can_access_forum:

        username = user.email.split('@')[0]
        user_details = {
            'sso_secret': settings.DISCOURSE_SSO_SECRET,
            'external_id': user_id,
            'email': user.email,
            'username': user.email.split('@')[0],
            'name': user.fullname if user.fullname else username,
            'admin': True if user.is_superuser else False,
            'moderator': True if user.is_superuser else False
        }
        forum_user = client.sync_sso(**user_details)
        if not user.has_access_to_forum and forum_user:
            username = forum_user['username']
            response = client.create_api_key(username)
            if "key" in response:
                user.discourse_user_name = username
                user.discourse_api_key = response['key']['key']
                user.save()
                client.activate(forum_user['id'])
    else:
        forum_user = client.by_external_id(user_id)
        _user_id = forum_user['id']
        client.log_out(_user_id)
        client.deactivate(_user_id)

    return {'result': 'ok'}


@extended_shared_task
def user_logout_task(user_id):
    client = DiscourseClient(settings.DISCOURSE_SYNC_HOST, settings.DISCOURSE_API_USER, settings.DISCOURSE_API_KEY)
    forum_user = client.by_external_id(user_id)
    client.log_out(forum_user['id'])

    return {'result': 'ok'}
