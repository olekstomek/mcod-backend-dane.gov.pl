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

API_URL_INTERNAL = 'http://localhost'

ELASTICSEARCH_INDEX_PREFIX = 'test'

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}

ELASTICSEARCH_HISTORIES_IDX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0
}

LANGUAGE_CODE = 'pl'


def get_es_index_names():
    import uuid
    index_prefix = str(uuid.uuid4())
    return {
        "common": "test-common-{}".format(index_prefix),
        "articles": "test-articles-{}".format(index_prefix),
        "applications": "test-applications-{}".format(index_prefix),
        "courses": "test-courses-{}".format(index_prefix),
        "datasets": "test-datasets-{}".format(index_prefix),
        "lab_events": "test-lab_events-{}".format(index_prefix),
        "institutions": "test-institutions-{}".format(index_prefix),
        "resources": "test-resources-{}".format(index_prefix),
        "histories": "test-histories-{}".format(index_prefix),
        "searchhistories": "test-searchhistories-{}".format(index_prefix),
        "accepted_dataset_submissions": "test-accepted_dataset_submissions-{}".format(index_prefix),
        "meetings": "test-meetings-{}".format(index_prefix),
        "knowledge_base_pages": "test-knowledge_base_pages-{}".format(index_prefix),
    }


ELASTICSEARCH_INDEX_NAMES = get_es_index_names()


def get_email_file_path():
    import uuid
    return '/tmp/app-messages-%s' % str(uuid.uuid4())


EMAIL_FILE_PATH = get_email_file_path()

# DATA_DIR = ROOT_DIR.path('data')
# TEST_SAMPLES_PATH = os.path.join(str(DATA_DIR), 'test_samples')


TEST_SAMPLES_PATH = str(ROOT_DIR('data/test_samples'))
TEST_ROOT = str(ROOT_DIR('test'))

MEDIA_ROOT = str(os.path.join(TEST_ROOT, 'media'))
IMAGES_MEDIA_ROOT = str(os.path.join(MEDIA_ROOT, 'images'))
MEETINGS_MEDIA_ROOT = str(os.path.join(MEDIA_ROOT, 'meetings'))
NEWSLETTER_MEDIA_ROOT = str(os.path.join(MEDIA_ROOT, 'newsletter'))
RESOURCES_MEDIA_ROOT = str(os.path.join(MEDIA_ROOT, 'resources'))
RESOURCES_FILES_TO_REMOVE_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'to_be_removed', 'resources'))
REPORTS_MEDIA_ROOT = str(os.path.join(MEDIA_ROOT, 'reports'))
DCAT_VOCABULARIES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'resources'))
METADATA_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'datasets', 'catalog'))

CACHES.update({'test': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#     },
#     "sessions": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#     },
#     "constance": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "%s/1" % REDIS_URL,
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

# CONSTANCE_DATABASE_CACHE_BACKEND = 'constance'

MEDIA_URL = '/media/'
RESOURCES_URL = '%s%s' % (MEDIA_URL, 'resources')
MEETINGS_URL = '%s%s' % (MEDIA_URL, 'meetings')
NEWSLETTER_URL = '%s%s' % (MEDIA_URL, 'newsletter')
IMAGES_URL = '%s%s' % (MEDIA_URL, 'images')
REPORTS_MEDIA = '%s%s' % (MEDIA_URL, 'reports')

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_DEFAULT_QUEUE = 'mcod'
CELERY_TASK_QUEUES = {
    Queue('test'),
}

CELERY_TASK_ROUTES = {}

SESSION_COOKIE_NAME = 'test_sessionid'
SESSION_COOKIE_DOMAIN = 'test.mcod'
SESSION_COOKIE_SECURE = False
API_TOKEN_COOKIE_NAME = 'test_apiauthtoken'


LOGGING['loggers']['django.db.backends']['level'] = 'INFO'
LOGGING['loggers']['django.db.backends']['handlers'] = ['console']
LOGGING['loggers']['django.request']['level'] = 'INFO'
LOGGING['loggers']['django.request']['handlers'] = ['console']
LOGGING['loggers']['django.server']['level'] = 'INFO'
LOGGING['loggers']['django.server']['handlers'] = ['console']
LOGGING['loggers']['signals']['level'] = 'INFO'
LOGGING['loggers']['signals']['handlers'] = ['console']
LOGGING['loggers']['celery.app.trace']['level'] = 'WARNING'
LOGGING['loggers']['celery.app.trace']['handlers'] = ['console']
LOGGING['loggers']['mcod']['handlers'] = ['console']
LOGGING['loggers']['resource_file_processing']['handlers'] = ['console']

CONSOLE_LOG_ERRORS = True

SUIT_CONFIG['LIST_PER_PAGE'] = 100

# Makes tests faster (https://brobin.me/blog/2016/08/7-ways-to-speed-up-your-django-test-suite/)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CELERY_BEAT_SCHEDULE['send-newsletter'] = {
    'task': 'mcod.newsletter.tasks.send_newsletter',
    # 'schedule': crontab(minute=0, hour=3)
    'schedule': 120,
}

COMPONENT = env('COMPONENT', default='admin')
ENVIRONMENT = 'test'
ENABLE_CSRF = False
API_CSRF_COOKIE_DOMAINS = [
    'test.local',
    'localhost',
    'dane.gov.pl'
]

ES_EN_SYN_FILTER_KWARGS = {
    "type": "synonym",
    "lenient": True,
    "synonyms": ["foo, bar => baz"]
}

ES_PL_SYN_FILTER_KWARGS = {
    "type": "synonym",
    "lenient": True,
    "synonyms": ["sierściuch, kot"]
}
FALCON_LIMITER_ENABLED = False

DISCOURSE_FORUM_ENABLED = False
