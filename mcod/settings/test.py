import os
from mcod.settings.base import *  # noqa: F403, F405

ROOT_DIR = environ.Path(__file__) - 3  # noqa: F405
DEBUG = True

TEMPLATES[0]['OPTIONS']['debug'] = DEBUG  # noqa: F405

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'  # change this to a proper location

BASE_URL = 'http://test.mcod'
API_URL = 'http://api.test.mcod'
ADMIN_URL = 'http://admin.test.mcod'
APM_URL = 'https://apm.test.mcod'


ELASTICSEARCH_INDEX_NAMES = {
    "articles": "test-articles",
    "applications": "test-applications",
    "datasets": "test-datasets",
    "institutions": "test-institutions",
    "resources": "test-resources",
    "histories": "test-histories",
    "searchhistories": "test-searchhistories",
}

TEST_DATA_PATH = str(ROOT_DIR('data/test'))
TEST_ROOT = str(ROOT_DIR('test'))

MEDIA_ROOT = os.path.join(TEST_ROOT, 'media')
IMAGES_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'images')
RESOURCES_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'resources')
REPORTS_MEDIA_ROOT = os.path.join(MEDIA_ROOT,'reports')

ELASTICSEARCH_INDEX_PREFIX = 'test'

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}

ELASTICSEARCH_HISTORIES_IDX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}

MEDIA_URL = '/media/'
RESOURCES_URL = '%s%s' % (MEDIA_URL, 'resources')
IMAGES_URL = '%s%s' % (MEDIA_URL, 'images')
REPORTS_MEDIA = '%s%s' % (MEDIA_URL, 'reports')

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_DEFAULT_QUEUE = 'mcod'
CELERY_TASK_QUEUES = {
    Queue('test'),
}

CELERY_TASK_ROUTES = {}
SESSION_ENV_PREFIX = "test_"

LOGGING['loggers']['django.db.backends']['level'] = 'ERROR'
LOGGING['loggers']['django.db.backends']['handlers'] = ['console']
LOGGING['loggers']['django.request']['level'] = 'ERROR'
LOGGING['loggers']['django.request']['handlers'] = ['console']
LOGGING['loggers']['django.server']['level'] = 'ERROR'
LOGGING['loggers']['django.server']['handlers'] = ['console']
LOGGING['loggers']['signals']['handlers'] = ['console']
LOGGING['loggers']['celery.app.trace']['handlers'] = ['console']
LOGGING['loggers']['mcod']['handlers'] = ['console']
LOGGING['loggers']['resource_file_processing']['handlers'] = ['console']