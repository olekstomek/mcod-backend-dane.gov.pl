import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from mcod.discourse.client import DiscourseClient

logger = logging.getLogger('mcod')


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug('Attempting to synchronize mcod and forum users.')
        client = DiscourseClient(settings.DISCOURSE_SYNC_HOST, settings.DISCOURSE_API_USER, settings.DISCOURSE_API_KEY)
        sso_secret = settings.DISCOURSE_SSO_SECRET
        users_to_sync = get_user_model().objects.filter(
            is_active=True, state='active'
        ).filter(Q(is_superuser=True) | Q(is_agent=True) | Q(extra_agent_of__isnull=False))
        logger.debug(f'Found {users_to_sync.count()} users to synchronize')
        for user in users_to_sync:
            logger.debug(f'Synchronized user {user.email}, api_key {user.discourse_api_key}')
            username = user.email.split('@')[0]
            user_details = {
                'sso_secret': sso_secret,
                'external_id': user.pk,
                'email': user.email,
                'username': username,
                'name': user.fullname if user.fullname else username,
                'admin': True if user.is_superuser else False,
                'moderator': True if user.is_superuser else False
            }
            response = client.sync_sso(**user_details)
            if response:
                username = response['username']
                response = client.create_api_key(username)
                if "key" in response:
                    user.discourse_user_name = username
                    user.discourse_api_key = response['key']['key']
                    user.save()
            else:
                logger.debug(f'Skipping {user.email}, no response from discourse.')
        logger.debug('User synchronization completed.')
