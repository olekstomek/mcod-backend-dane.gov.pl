from collections import OrderedDict
import environ
from django.utils.translation import gettext_lazy as _
from kombu import Queue

env = environ.Env()

ROOT_DIR = environ.Path(__file__) - 3

APPS_DIR = ROOT_DIR.path('mcod')

DATA_DIR = ROOT_DIR.path('data')

LOGS_DIR = str(ROOT_DIR.path('logs'))

DATABASE_DIR = str(ROOT_DIR.path('database'))

DEBUG = False

SECRET_KEY = 'xb2rTZ57yOY9iCdqR7W+UAWnU'

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'dal_admin_filters',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'suit',
    'django_elasticsearch_dsl',
    'ckeditor',
    'ckeditor_uploader',
    'rules.apps.AutodiscoverRulesConfig',
    'nested_admin',
    'django_celery_results',
    'localflavor',
    'django.contrib.admin',
    'constance',
    'constance.backends.database',
    'rangefilter',
    'modeltrans',
    # Our apps
    'mcod.organizations',
    'mcod.categories',
    'mcod.tags',
    'mcod.applications',
    'mcod.articles',
    'mcod.datasets',
    'mcod.resources',
    'mcod.users',
    'mcod.licenses',
    'mcod.following',
    'mcod.counters',
    'mcod.histories',
    'mcod.searchhistories',
    'mcod.core',
    'mcod.reports',
    'mcod.alerts',
    'mcod.watchers',
    'mcod.suggestions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mcod.lib.middleware.PostgresConfMiddleware',
    'mcod.lib.middleware.UserTokenMiddleware',
    'mcod.lib.middleware.ComplementUserDataMiddleware',
]

ROOT_URLCONF = 'mcod.urls'

WSGI_APPLICATION = 'mcod.wsgi.application'

ALLOWED_HOSTS = ['*']

FIXTURE_DIRS = (
    str(ROOT_DIR.path('fixtures')),
)

ADMINS = [
    ("""Rafał Korzeniewski""", 'rafal.korzeniewski@britenet.com.pl'),
    ("""Piotr Zientarski""", 'piotr.zientarski@britenet.com.pl'),
    ("""Michał Pilch""", 'michal.pilch@britenet.com.pl'),
]

ADMIN_URL = r'^$'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

PASSWORD_HASHERS = [

    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'mcod.lib.hashers.PBKDF2SHA512PasswordHasher',

]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'user_attributes': ('email', 'fullname'), 'max_similarity': 0.6}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'mcod.lib.password_validators.McodPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        'OPTIONS': {'password_list_path': str(DATA_DIR.path('common-passwords.txt.gz'))}
    },
]

AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend'
]

DATABASES = {
    'default': env.db('POSTGRES_DATABASE_URL', default='postgres://mcod:mcod@mcod-db:5432/mcod'),  # noqa: F405
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEBUG_EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_PORT', default=465)
EMAIL_USE_SSL = True if env('EMAIL_USE_SSL', default='yes') in ('yes', '1', 'true') else False
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# pwgen -ny 64
JWT_SECRET_KEY = 'aes_oo7ooSh8phiayohvah0ZieH3ailahh9ieb6ahthah=hing7AhJu7eexeiHoo'
JWT_ISS = 'Ministry of Digital Affairs'
JWT_AUD = 'dane.gov.pl'
JWT_ALGORITHMS = ['HS256', ]
JWT_VERIFY_CLAIMS = ['signature', 'exp', 'nbf', 'iat']
JWT_REQUIRED_CLAIMS = ['exp', 'iat', 'nbf']
JWT_HEADER_PREFIX = 'Bearer'
JWT_LEEWAY = 0
JWT_EXPIRATION_DELTA = 24 * 60 * 60

AUTH_USER_MODEL = 'users.User'

TIME_ZONE = 'Europe/Warsaw'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            'debug': False,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ],
            'context_processors': [
                'constance.context_processors.config',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'mcod.core.contextprocessors.settings',
                'mcod.alerts.contextprocessors.active_alerts',
            ],
        },
    },
]

from django.template import context_processors
from django.template.response import TemplateResponse
from django.contrib.admin.sites import AdminSite

FORM_RENDERER = 'mcod.lib.forms.renderers.TemplatesRenderer'

STATIC_ROOT = str(ROOT_DIR('statics'))
STATIC_URL = '/static/'
STATICFILES_FINDERS = [
    'mcod.lib.staticfiles_finders.StaticRootFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MEDIA_ROOT = str(ROOT_DIR('media'))
IMAGES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'images'))
RESOURCES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'resources'))
REPORTS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'reports'))

MEDIA_URL = '/media/'
RESOURCES_URL = '%s%s' % (MEDIA_URL, 'resources')
IMAGES_URL = '%s%s' % (MEDIA_URL, 'images')
REPORTS_MEDIA = '%s%s' % (MEDIA_URL, 'reports')

CKEDITOR_UPLOAD_PATH = 'ckeditor/'

LOCALE_PATHS = (
    str(ROOT_DIR.path('translations', 'system')),
    str(ROOT_DIR.path('translations', 'custom')),
)

LANGUAGE_CODE = 'pl'

LANGUAGES = [
    ('pl', _('Polish')),
    ('en', _('English')),
]

MODELTRANS_AVAILABLE_LANGUAGES = ('pl', 'en')

MODELTRANS_FALLBACK = {
    'default': (LANGUAGE_CODE,),
}

REDIS_URL = env('REDIS_URL', default='redis://mcod-redis:6379')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "%s/0" % REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "%s/1" % REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }

}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

USER_STATE_CHOICES = (
    ('active', _('Active')),
    ('pending', _('Pending')),
    ('blocked', _('Blocked'))
)

USER_STATE_LIST = [choice[0] for choice in USER_STATE_CHOICES]

SUIT_CONFIG = {
    'ADMIN_NAME': _("Open Data - Administration Panel"),
    'HEADER_DATE_FORMAT': 'l, j. F Y',
    'HEADER_TIME_FORMAT': 'H:i',  # 18:42
    'SHOW_REQUIRED_ASTERISK': True,
    'CONFIRM_UNSAVED_CHANGES': True,
    'SEARCH_URL': '',
    'MENU_OPEN_FIRST_CHILD': True,  # Default True
    'MENU_EXCLUDE': ('auth.group',),
    'MENU': (
        {'label': 'Dane', 'models': [
            {'model': 'datasets.dataset', 'admin_url':"/datasets/dataset", 'app_name': 'datasets', 'label': _('Datasets'), 'icon': 'icon-database'},
            {'model': 'resources.resource', 'label': _('Resources'), 'icon': 'icon-file-cloud'},
            {'model': 'organizations.organization', 'label': _('Institutions'), 'icon': 'icon-building'},
            {'model': 'applications.application', 'permissions': 'auth.add_user', 'label': _('Applications'),
             'icon': 'icon-cupe-black'},
            {'model': 'articles.article', 'label': _('Articles'), 'permissions': 'auth.add_user', 'icon': 'icon-leaf'},
        ], 'icon': 'icon-file'},
        {'label': _('Users'), 'url': '/users/user', 'icon': 'icon-lock'},
        {
            'label': _('CSV Reports'),
            'models': [
                # FIXME label 'Users' koliduje z panelem użytkowników i w lewym menu podświetla się nie właściwa pozycja
                {'model': 'reports.userreport', 'label': _('Users reports')},
                {'model': 'reports.resourcereport', 'label': _('Resources')},
                {'model': 'reports.datasetreport', 'label': _('Datasets')},
                {'model': 'reports.organizationreport', 'label': _('Institutions')},
                {'model': 'reports.summarydailyreport', 'label': _('Daily Reports')},
            ],
            'permissions': 'auth.add_user',
            'icon': 'icon-tasks'
        },
        {
            'label': _('Alerts'),
            'url': '/alerts/alert',
            'permissions': 'auth.add_user',
            'icon': 'icon-bullhorn'
        },
        {
            'label': _('Config'),
            'url': '/constance/config',
            'permissions': 'auth.add_user',
            'icon': 'icon-cog'
        }
    ),
    'LIST_PER_PAGE': 20,
    # CUSTOM SETTINGS
    'APPS_SKIPPED_IN_DASHBOARD': [
        'alerts',
        'constance',
        'django_celery_results',
    ]
}

SPECIAL_CHARS = ' !"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'

CKEDITOR_CONFIGS = {
    'default': {
        # 'toolbar': 'Basic',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter',
             'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Attachments', ],
            ['RemoveFormat', 'Source']
        ],
        'height': 300,
        'width': '100%',
    },
    'alert_description': {
        'toolbar': "Custom",
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
        ],
        'height': 300,
        'width': '100%',
    }
}

CKEDITOR_ALLOW_NONIMAGE_FILES = True

TOKEN_EXPIRATION_TIME = 24  # In hours

PER_PAGE_LIMIT = 200
PER_PAGE_DEFAULT = 20


ELASTICSEARCH_HOSTS = env('ELASTICSEARCH_HOSTS', default='mcod-elasticsearch-1:9200')

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ELASTICSEARCH_HOSTS.split(','),
        'http_auth': "user:changeme",
        'timeout': 100
    },
}

ELASTICSEARCH_INDEX_NAMES = OrderedDict({
    "articles": "articles",
    "applications": "applications",
    "institutions": "institutions",
    "datasets": "datasets",
    "resources": "resources",
    "searchhistories": "searchhistories",
    "histories": "histories",
})

ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'mcod.core.api.search.signals.AsyncSignalProcessor'

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 1
}

ELASTICSEARCH_HISTORIES_IDX_SETTINGS = {
    'number_of_shards': 3,
    'number_of_replicas': 1
}

ELASTICSEARCH_INDEX_PREFIX = ''

CELERY_BROKER_URL = 'amqp://%s' % str(env('RABBITMQ_HOST', default='mcod-rabbitmq:5672'))

CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_ALWAYS_EAGER = False

CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_TASK_QUEUES = {
    Queue('default'),
    Queue('resources'),
    Queue('indexing'),
    Queue('periodic'),
    Queue('notifications'),
    Queue('search_history'),
}

CELERY_TASK_ROUTES = {
    'mcod.core.api.search.tasks.update_document_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.update_with_related_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_document_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_with_related_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_related_documents_task': {'queue': 'indexing'},
    'mcod.resources.tasks.process_resource_from_url_task': {'queue': 'resources'},
    'mcod.resources.tasks.process_resource_file_task': {'queue': 'resources'},
    'mcod.resources.tasks.process_resource_file_data_task': {'queue': 'resources'},
    'mcod.counters.tasks.save_counters': {'queue': 'periodic'},
    'mcod.histories.tasks.index_history': {'queue': 'periodic'},
    'mcod.datasets.tasks.send_dataset_comment': {'queue': 'notifications'},
    'mcod.searchhistories.tasks.create_search_history': {'queue': 'search_history'},
}

RESOURCE_MIN_FILE_SIZE = 1024
RESOURCE_MAX_FILE_SIZE = 1024 * 1024 * 512  # 512MB

FIXTURE_DIRS = [
    str(ROOT_DIR('fixtures')),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'elasticapm': {
            'level': 'WARNING',
            'class': 'mcod.apm.handlers.LoggingHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'logstash-admin': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': 'mcod-logstash',
            'port': 5959,
            'version': 1,
            'message_type': 'admin',
            'fqdn': False,
        },
        'logstash-signals': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': 'mcod-logstash',
            'port': 5959,
            'version': 1,
            'message_type': 'signals',
            'fqdn': False,
        },
        'logstash-tasks': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': 'mcod-logstash',
            'port': 5959,
            'version': 1,
            'message_type': 'tasks',
            'fqdn': False,
        },
        # Check if these are required
        'mail-admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['mail-admins','logstash-admin'],
            'propagate': False,
        },
        'django.templates': {
            'handlers': ['logstash-admin',],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail-admins', 'logstash-admin'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['mail-admins', 'logstash-admin'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'signals': {
            'handlers': ['console', 'logstash-signals'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery.app.trace': {
            'handlers': ['console', 'logstash-tasks'],
            'level': 'DEBUG',
            'propagate': True
        },
        'mcod': {
            'handlers': ['console',],
            'level': 'DEBUG',
            'propagate': False,
        },
        'resource_file_processing': {
            'handlers': ['console',],
            'level': 'DEBUG',
            'propagate': False,
        },
        'elasticapm.errors': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
}

CELERYD_HIJACK_ROOT_LOGGER = False

ARCHIVE_CONTENT_TYPES = [
    ('application', 'gzip', ('gz',), 1),
    ('application', 'x-gzip', ('gz',), 1),
    ('application', 'vnd.rar', ('rar',), 1),
    ('application', 'rar', ('rar',), 1),
    ('application', 'x-rar', ('rar',), 1),
    ('application', 'x-rar-compressed', ('rar',), 1),
    ('application', 'x-7z-compressed', ('7zip',), 1),
    ('application', 'x-bzip', ('bz',), 1),
    ('application', 'bzip2', ('bz2',), 1),
    ('application', 'x-bzip2', ('bz2',), 1),
    ('application', 'x-tar', ('tar',), 1),
    ('application', 'x-zip-compressed', ('zip',), 1),
    ('application', 'zip', ('zip',), 1),
]

SUPPORTED_CONTENT_TYPES = [
    # (family, type, extensions, openness score)
    ('application', 'csv', ('csv',), 3),
    ('application', 'epub+zip', ('epub',), 1),
    ('application', 'excel', ('xls',), 2),
    ('application', 'gml+xml', ('xml',), 3),
    ('application', 'json', ('json',), 3),
    ('application', 'mspowerpoint', ('ppt', 'pot', 'ppa', 'pps', 'pwz'), 1),
    ('application', 'msword', ('doc', 'docx', 'dot', 'wiz'), 1),
    ('application', 'pdf', ('pdf',), 1),
    ('application', 'postscript', ('pdf', 'ps'), 1),
    ('application', 'powerpoint', ('ppt', 'pot', 'ppa', 'pps', 'pwz'), 1),
    ('application', 'rtf', ('rtf',), 1),
    ('application', 'shapefile', ('shp',), 2),
    ('application', 'vnd.api+json', ('json',), 3),  # 4?
    ('application', 'vnd.ms-excel', ('xls', 'xlsx', 'xlb'), 2),
    ('application', 'vnd.ms-excel.12', ('xls', 'xlsx', 'xlb'), 2),
    ('application', 'vnd.ms-excel.sheet.macroEnabled.12', ('xls', 'xlsx', 'xlb'), 2),
    ('application', 'vnd.ms-powerpoint', ('ppt', 'pot', 'ppa', 'pps', 'pwz'), 1),
    ('application', 'vnd.ms-word', ('doc', 'docx', 'dot', 'wiz'), 1),
    ('application', 'vnd.oasis.opendocument.chart', ('odc',), 1),
    ('application', 'vnd.oasis.opendocument.formula', ('odf',), 3),
    ('application', 'vnd.oasis.opendocument.graphics', ('odg',), 3),
    ('application', 'vnd.oasis.opendocument.image', ('odi',), 2),
    ('application', 'vnd.oasis.opendocument.presentation', ('odp',), 1),
    ('application', 'vnd.oasis.opendocument.spreadsheet', ('ods',), 3),
    ('application', 'vnd.oasis.opendocument.text', ('odt',), 1),
    ('application', 'vnd.openxmlformats-officedocument.presentationml.presentation', ('pptx',), 1),
    ('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet', ('xlsx',), 2),
    ('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document', ('docx',), 1),
    ('application', 'vnd.visio', ('vsd',), 1),
    ('application', 'x-abiword', ('abw',), 1),
    ('application', 'x-csv', ('csv',), 3),
    ('application', 'x-excel', ('xls', 'xlsx', 'xlb'), 2),
    ('application', 'x-rtf', ('rtf',), 1),
    ('application', 'xhtml+xml', ('html', 'htm'), 3),
    ('application', 'xml', ('xml',), 3),
    ('application', 'x-tex', ('tex',), 3),
    ('application', 'x-texinfo', ('texi', 'texinfo',), 3),
    ('application', 'x-dbf', ('dbf',), 1),
    ('image', 'bmp', ('bmp',), 2),
    ('image', 'gif', ('gif',), 2),
    ('image', 'jpeg', ('jpeg', 'jpg', 'jpe'), 3),
    ('image', 'png', ('png',), 3),
    ('image', 'svg+xml', ('svg',), 3),
    ('image', 'tiff', ('tiff',), 2),
    ('image', 'webp', ('webp',), 2),
    ('image', 'x-tiff', ('tiff',), 2),
    ('image', 'x-ms-bmp', ('bmp',), 2),
    ('image', 'x-portable-pixmap', ('ppm',), 2),
    ('image', 'x-xbitmap', ('xbm',), 2),
    ('text', 'csv', ('csv',), 3),
    ('text', 'html', ('html', 'htm'), 3),
    ('text', 'xhtml+xml', ('html', 'htm'), 3),
    ('text', 'plain', ('txt', 'rd', 'md', 'csv', 'tsv', 'bat'), 3),
    ('text', 'richtext', ('rtf',), 1),
    ('text', 'tab-separated-values', ('tsv',), 3),
    ('text', 'xml', ('xml', 'wsdl', 'xpdl', 'xsl'), 3),
    ('text', 'rdf', ('rdf', 'n3', 'nt', 'trix', 'rdfa', 'xml'), 4)
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 500000000
FILE_UPLOAD_PERMISSIONS = 0o644

IMAGE_UPLOAD_MAX_SIZE = 10 * 1024 ** 2
THUMB_SIZE = (200, 1024)

COUNTED_VIEWS = ['applications', 'datasets', 'articles', 'resources']
SEARCH_HISTORY_PATHS = ["/datasets", "/articles", "/applications"]

# That list (and few tests) depends on frontend querys
SEARCH_HISTORY_BLACKLISTED_QUERIES = [
    'page=1&per_page=5&q=&sort=-modified',
    'page=1&per_page=5&q=&sort=-created',
    'per_page=1&facet=categories,institutions,formats,openness_scores'
]

JSONAPI_SCHEMA_PATH = str(DATA_DIR.path('jsonapi.config.json'))

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_PREFIX = 'constance:mcod:'
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'
CONSTANCE_CONFIG = {
    'NO_REPLY_EMAIL': ('no-reply@dane.gov.pl', '', str),
    'CONTACT_MAIL': ('kontakt@dane.gov.pl', '', str),
    'SUGGESTIONS_EMAIL': ("uwagi@dane.gov.pl", '', str),
    'ACCOUNTS_EMAIL': ("konta@dane.gov.pl", '', str),
    'FOLLOWINGS_EMAIL': ("obserwowane@dane.gov.pl", '', str),
    'TESTER_EMAIL': ('no-reply@dane.gov.pl', '', str),
    'MANUAL_URL': ('', '', str),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict((
    ('URLs', ('MANUAL_URL',)),
    ('Mails', ('NO_REPLY_EMAIL', 'CONTACT_MAIL', 'SUGGESTIONS_EMAIL', 'ACCOUNTS_EMAIL', 'FOLLOWINGS_EMAIL')),
    ('Development', ('TESTER_EMAIL',))
))

SHOW_GENERATE_RAPORT_BUTTOON = False

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

BASE_URL = 'https://www.dane.gov.pl'
API_URL = 'https://api.dane.gov.pl'
ADMIN_URL = 'https://admin.dane.gov.pl'
APM_URL = 'https://apm.dane.gov.pl'


PASSWORD_RESET_PATH = '/user/reset-password/%s/'
EMAIL_VALIDATION_PATH = '/user/verify-email/%s/'
