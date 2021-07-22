import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from pydiscourse import DiscourseClient

logger = logging.getLogger('mcod')


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug('Attempting to synchronize mcod and forum users.')
        client = DiscourseClient(
            getattr(settings, 'DISCOURSE_URL', ''),
            api_username=getattr(settings, 'DISCOURSE_API_USER', ''),
            api_key=getattr(settings, 'DISCOURSE_API_KEY', ''))
        sso_secret_key = getattr(settings, 'DISCOURSE_SSO_SECRET_KEY')
        users_to_sync = get_user_model().objects.filter(
            is_active=True, state='active'
        ).filter(Q(is_superuser=True) | Q(is_agent=True) | Q(extra_agent_of__isnull=False))
        logger.debug(f'Found {users_to_sync.count()} users to synchronize')
        for user in users_to_sync:
            logger.debug(f'Synchronizing user {user.email}')
            user_details = {
                'sso_secret': sso_secret_key,
                'external_id': user.pk,
                'email': user.email,
                'username': user.email,
                'name': user.fullname if user.fullname else user.email.split('@')[0],
                'avatar_url': '',
                'avatar_force_update': False
            }
            client.sync_sso(**user_details)
        logger.debug('User synchronization completed.')
