import string
from collections import OrderedDict
from datetime import date

import environ
from celery.schedules import crontab
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from kombu import Queue
from wagtail.embeds.oembed_providers import all_providers
from bokeh.util.paths import bokehjsdir

env = environ.Env()
ROOT_DIR = environ.Path(__file__) - 3
try:
    env.read_env(ROOT_DIR.file('.env'))
except FileNotFoundError:
    pass

APPS_DIR = ROOT_DIR.path('mcod')

DATA_DIR = ROOT_DIR.path('data')

SCHEMAS_DIR = DATA_DIR.path('schemas')

HARVESTER_DATA_DIR = DATA_DIR.path('harvester')

SHACL_SHAPES_DIR = DATA_DIR.path('shacl')

SPEC_DIR = DATA_DIR.path('spec')

LOGS_DIR = str(ROOT_DIR.path('logs'))

DATABASE_DIR = str(ROOT_DIR.path('database'))

COMPONENT = env('COMPONENT', default='admin')

ENVIRONMENT = env('ENVIRONMENT', default='prod')

NOTEBOOKS_DIR = env('NOTEBOOKS_DIR', default=str(ROOT_DIR.path('notebooks/notebooks')))

NOTEBOOK_ARGUMENTS = [
    '--config', 'mcod/settings/jupyter_config.py'
]

DEBUG = env('DEBUG', default='no') in ('yes', 1, 'true') or env('TEST_DEBUG', default='no') in ('yes', 1, 'true')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='xb2rTZ57yOY9iCdqR7W+UAWnU')

NEWSLETTER_REMOVE_INACTIVE_TIMEOUT = 60 * 60 * 24  # after 24h.

INSTALLED_APPS = [
    'mcod.hacks',
    'wagtail.contrib.redirects',
    'wagtail.contrib.modeladmin',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail.core',
    'wagtail.api.v2',
    'hypereditor',

    'modelcluster',
    'taggit',
    'rest_framework',

    'dal',
    'dal_select2',
    'dal_admin_filters',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'admin_confirm',
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
    'celery_progress',
    'django_extensions',
    'channels',
    'notifications',
    'django_admin_multiple_choice_list_filter',
    # 'bokeh.server.django',
    'auditlog',

    # Our apps
    'mcod.core',
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
    'mcod.reports',
    'mcod.alerts',
    'mcod.watchers',
    'mcod.suggestions',
    'mcod.newsletter',
    'mcod.harvester',
    'mcod.cms',
    'mcod.laboratory',
    'mcod.academy',
    'mcod.pn_apps',
    'mcod.schedules',
    'mcod.guides',
    'mcod.special_signs',
    'mcod.discourse',
    'mcod.regions',
    'mcod.showcases',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',
    'mcod.cms.middleware.SiteMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mcod.lib.middleware.PostgresConfMiddleware',
    'mcod.lib.middleware.APIAuthTokenMiddleware',
    'mcod.lib.middleware.ComplementUserDataMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
]

ROOT_URLCONF = 'mcod.urls'

PN_APPS_URLCONF = 'mcod.pn_apps.urls'

WSGI_APPLICATION = 'mcod.wsgi.application'
ASGI_APPLICATION = 'mcod.routing.application'

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS',
                         default=['dane.gov.pl', 'admin.dane.gov.pl',
                                  'cms.dane.gov.pl', 'api.dane.gov.pl'])

FIXTURE_DIRS = (
    str(ROOT_DIR.path('fixtures')),
)

ADMINS = [tuple(x.split(':')) for x in env.list('DJANGO_ADMINS', default=['admin:admin@example.com'])]

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

if env('ENABLE_VAULT_HELPERS', default='yes') in ['yes', '1', 'true']:
    import vaulthelpers

    INSTALLED_APPS += [
        'vaulthelpers',
    ]

    DATABASES = {
        'default': vaulthelpers.database.get_config({
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 3600
        }),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', default='mcod'),
            'USER': env('POSTGRES_USER', default='mcod'),
            'PASSWORD': env('POSTGRES_PASSWORD', default='mcod'),
            'HOST': env('POSTGRES_HOST', default='mcod-db'),
            'PORT': env('POSTGRES_PORT', default='5432'),
            'ATOMIC_REQUESTS': True
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEBUG_EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env('EMAIL_USE_SSL', default='yes') in ('yes', '1', 'true')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DATA_UPLOAD_MAX_NUMBER_FIELDS = env('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=10000)

XML_VERSION_SINGLE_CATEGORY = '1.0-rc1'
XML_VERSION_MULTIPLE_CATEGORIES = '1.1'
HARVESTER_XML_VERSION_TO_SCHEMA_PATH = {
    '1.0-rc1': HARVESTER_DATA_DIR.path('xml_import_otwarte_dane_1_0_rc1.xsd').root,
    '1.1': HARVESTER_DATA_DIR.path('xml_import_otwarte_dane_1_1.xsd').root,
    '1.2': HARVESTER_DATA_DIR.path('xml_import_otwarte_dane_1_2.xsd').root,
    '1.3': HARVESTER_DATA_DIR.path('xml_import_otwarte_dane_1_3.xsd').root,
    '1.4': HARVESTER_DATA_DIR.path('xml_import_otwarte_dane_1_4.xsd').root,
}

HARVESTER_IMPORTERS = {
    'ckan': {
        'API_URL_PARAMS': {
            # 'limit': 100,
        },
        'MEDIA_URL_TEMPLATE': '{}/uploads/group/{}',
        'SCHEMA': 'mcod.harvester.serializers.DatasetSchema',
    },
    'xml': {
        'IMPORT_FUNC': 'mcod.harvester.utils.fetch_xml_data',
        'SCHEMA': 'mcod.harvester.serializers.XMLDatasetSchema',
        'ONE_DATASOURCE_PER_ORGANIZATION': False,
    },
    'dcat': {
        'IMPORT_FUNC': 'mcod.harvester.utils.fetch_dcat_data',
        'SCHEMA': 'mcod.harvester.serializers.DatasetDCATSchema',
    }
}

HTTP_REQUEST_DEFAULT_HEADERS = {
    'User-Agent': 'Otwarte Dane',
}

HTTP_REQUEST_DEFAULT_PARAMS = {
    'stream': True,
    'allow_redirects': True,
    'verify': False,
    'timeout': 180,
    'headers': HTTP_REQUEST_DEFAULT_HEADERS,
}

# pwgen -ny 64
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default='aes_oo7ooSh8phiayohvah0ZieH3ailahh9ieb6ahthah=hing7AhJu7eexeiHoo')
JWT_ISS = 'Chancellery of the Prime Minister'
JWT_AUD = 'dane.gov.pl'
JWT_ALGORITHMS = ['HS256', ]
JWT_VERIFY_CLAIMS = ['signature', 'exp', 'nbf', 'iat']
JWT_REQUIRED_CLAIMS = ['exp', 'iat', 'nbf']
JWT_HEADER_PREFIX = 'Bearer'
JWT_LEEWAY = 0

AUTH_USER_MODEL = 'users.User'

TIME_ZONE = 'Europe/Warsaw'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

TEMPLATE_DIRS = [
    str(APPS_DIR.path('templates')),
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'OPTIONS': {
            'debug': DEBUG,
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

FORM_RENDERER = 'mcod.lib.forms.renderers.TemplatesRenderer'

STATIC_ROOT = str(ROOT_DIR('statics'))
STATIC_URL = '/static/'
STATICFILES_FINDERS = [
    'mcod.lib.staticfiles_finders.StaticRootFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder'
]

STATICFILES_DIRS = [
    bokehjsdir()
]

MEDIA_ROOT = str(ROOT_DIR('media'))
ACADEMY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'academy'))
IMAGES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'images'))
MEETINGS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'meetings'))
NEWSLETTER_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'newsletter'))
RESOURCES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'resources'))
DATASETS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'datasets'))
REPORTS_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'reports'))
SHOWCASES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'showcases'))
LABORATORY_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'lab_reports'))
RESOURCES_FILES_TO_REMOVE_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'to_be_removed', 'resources'))
DCAT_VOCABULARIES_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'dcat', 'vocabularies'))
METADATA_MEDIA_ROOT = str(ROOT_DIR.path(MEDIA_ROOT, 'datasets', 'catalog'))

MEDIA_URL = '/media/'
ACADEMY_URL = '%s%s' % (MEDIA_URL, 'academy')
MEETINGS_URL = '%s%s' % (MEDIA_URL, 'meetings')
NEWSLETTER_URL = '%s%s' % (MEDIA_URL, 'newsletter')
RESOURCES_URL = '%s%s' % (MEDIA_URL, 'resources')
DATASETS_URL = '%s%s' % (MEDIA_URL, 'datasets')
SHOWCASES_URL = '%s%s' % (MEDIA_URL, 'showcases')
IMAGES_URL = '%s%s' % (MEDIA_URL, 'images')
REPORTS_MEDIA = '%s%s' % (MEDIA_URL, 'reports')
LABORATORY_URL = '%s%s' % (MEDIA_URL, 'lab_reports')
DCAT_VOCABULARIES_URL = '%s%s' % (MEDIA_URL, 'dcat/vocabularies')

CKEDITOR_UPLOAD_PATH = 'ckeditor/'

LOCALE_PATHS = [
    str(ROOT_DIR.path('translations', 'system')),
    str(ROOT_DIR.path('translations', 'custom')),
    str(ROOT_DIR.path('translations', 'cms')),
]

# if COMPONENT == 'cms':
#     LOCALE_PATHS.append(
#         str(ROOT_DIR.path('translations', 'cms')),
#     )

LANGUAGE_CODE = 'pl'

LANGUAGE_COOKIE_NAME = "mcod_language"

LANGUAGES = [
    ('pl', _('Polish')),
    ('en', _('English')),
]

LANG_TO_LOCALE = {
    'pl': 'pl_PL.UTF-8',
    'en': 'en_GB.UTF-8'
}

LANGUAGE_CODES = [lang[0] for lang in LANGUAGES]

MODELTRANS_AVAILABLE_LANGUAGES = ('pl', 'en')

MODELTRANS_FALLBACK = {
    'default': (LANGUAGE_CODE,),
}

USE_RDF_DB = env('USE_RDF_DB', default='no') in ('yes', '1', 'true')
FUSEKI_URL = env('FUSEKI_URL', default='http://mcod-rdfdb:3030')
FUSEKI_DATASET = env('FUSEKI_DATASET_1', default='ds')
SPARQL_QUERY_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"
SPARQL_UPDATE_ENDPOINT = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
SPARQL_USER = env('SPARQL_USER', default='admin')
SPARQL_PASSWORD = env('ADMIN_PASSWORD', default='Britenet.1')
SPARQL_CACHE_TIMEOUT = env('SPARQL_CACHE_TIMEOUT', default=60)  # in secs.
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
    },
    # https://docs.wagtail.io/en/stable/advanced_topics/performance.html#caching-image-renditions
    'renditions': {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "%s/2" % REDIS_URL,
        'TIMEOUT': 600,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

CMS_API_CACHE_TIMEOUT = env('CMS_API_CACHE_TIMEOUT', default=3600)  # 1 hour.

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_PREFIX = env('SESSION_COOKIE_PREFIX', default=None)
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN', default='dane.gov.pl')
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', default='yes') in ('yes', '1', 'true')
SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE', default=14400)  # 4h
SESSION_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_PATH = '/'

SESSION_COOKIE_NAME = "sessionid"
if SESSION_COOKIE_PREFIX:
    SESSION_COOKIE_NAME = SESSION_COOKIE_PREFIX + '_' + SESSION_COOKIE_NAME

API_TOKEN_COOKIE_NAME = "apiauthtoken"
if SESSION_COOKIE_PREFIX:
    API_TOKEN_COOKIE_NAME = SESSION_COOKIE_PREFIX + '_' + API_TOKEN_COOKIE_NAME

JWT_EXPIRATION_DELTA = SESSION_COOKIE_AGE + 2

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
    'MENU': [
        {
            'label': 'Dane',
            'models': [
                {
                    'model': 'datasets.dataset',
                    'admin_url': "/datasets/dataset",
                    'app_name': 'datasets',
                    'label': _('Datasets'),
                    'icon': 'icon-database'
                }, {
                    'model': 'resources.resource',
                    'label': _('Resources'),
                    'icon': 'icon-file-cloud'
                }, {
                    'model': 'organizations.organization',
                    'label': _('Institutions'),
                    'icon': 'icon-building'
                }, {
                    'model': 'applications.application',
                    'permissions': 'auth.add_user',
                    'label': _('Applications'),
                    'icon': 'icon-cupe-black'
                }, {
                    'model': 'showcases.showcase',
                    'permissions': 'auth.add_user',
                    'label': _('PoCoTo'),
                    'icon': 'icon-cupe-black'
                }, {
                    'model': 'articles.article',
                    'label': _('Articles'),
                    'permissions': 'auth.add_user',
                    'icon': 'icon-leaf'
                }, {
                    'model': 'suggestions.AcceptedDatasetSubmission',
                    'label': _('Data suggestions'),
                    'permissions': 'auth.add_user',
                },
            ],
            'icon': 'icon-file'
        },
        {
            'label': _('Users'),
            'url': '/users/user',
            'icon': 'icon-lock',
            'orig_url': '/users/user',
        },
        {
            'label': _('CSV Reports'),
            'app': 'reports',
            'models': [
                # FIXME label 'Users' koliduje z panelem użytkowników i w lewym menu podświetla się nie właściwa pozycja
                {'model': 'reports.userreport', 'label': _('Users reports')},
                {'model': 'reports.resourcereport', 'label': _('Resources')},
                {'model': 'reports.datasetreport', 'label': _('Datasets')},
                {'model': 'reports.organizationreport', 'label': _('Institutions')},
                {'model': 'reports.monitoringreport', 'label': _('Monitoring')},
                {'model': 'reports.summarydailyreport', 'label': _('Daily Reports')},
            ],
            'permissions': 'auth.add_user',
            'icon': 'icon-tasks'
        },
        {
            'label': _('Alerts'),
            'url': '/alerts/alert',
            'permissions': 'auth.add_user',
            'icon': 'icon-bullhorn',
            'orig_url': '/alerts/alert'
        },
        {
            'label': _('Newsletter'),
            'url': '/newsletter/newsletter/',
            'permissions': 'auth.add_user',
            'icon': 'icon-envelope',
            'orig_url': '/newsletter/newsletter/'
        },
        {
            'label': _('Data Sources'),
            'url': '/harvester/datasource/',
            'permissions': 'auth.add_user',
            'icon': 'icon-bullhorn',
            'orig_url': '/harvester/datasource/'
        },
        {
            'label': pgettext_lazy('Dashboard', 'Dashboard'),
            'url': '',
            'permissions': 'is_logged_academy_or_labs_admin',
            'icon': 'icon-list-alt',
            'models': [
                {
                    'label': _('Open Data Lab'),
                    'model': 'laboratory.labevent',
                    'admin_url': 'laboratory/labevent',
                    'app_name': 'laboratory',
                    'permissions': ('laboratory.view_labevent', 'laboratory.view_labreport'),
                },
                {
                    'label': _('Open Data Academy'),
                    'url': '/academy/course',
                    'permissions': ('academy.view_course',),
                },
                {
                    'model': 'users.meeting',
                    'permissions': ('auth.add_user',),
                },
            ]
        },
        {
            'label': _('Portal guide'),
            'url': '/guides/guide',
            'permissions': 'auth.add_user',
            'icon': 'icon-bullhorn',
            'orig_url': '/guides/guide'
        },
        {
            'label': _('Monitoring'),
            'permissions': 'auth.add_user',
            'models': [
                {
                    'model': 'applications.applicationproposal',
                    'permissions': 'auth.add_user',
                    'url': '/applications/applicationproposal/?decision=not_taken',
                },
                {
                    'model': 'showcases.showcaseproposal',
                    'permissions': 'auth.add_user',
                    'label': 'Propozycje PoCoTo',
                    'url': '/showcases/showcaseproposal/?decision=not_taken',
                },
                {
                    'label': _('Data suggestions'),
                    'model': 'suggestions.datasetsubmission',
                    'url': '/suggestions/datasetsubmission/?decision=not_taken',
                },
                {
                    'model': 'suggestions.datasetcomment',
                    'permissions': 'auth.add_user',
                    'url': '/suggestions/datasetcomment/?decision=not_taken',
                },
                {
                    'model': 'suggestions.resourcecomment',
                    'permissions': 'auth.add_user',
                    'url': '/suggestions/resourcecomment/?decision=not_taken',
                },
            ]
        },
        {
            'label': _('Configuration'),
            'url': '/constance/config',
            'permissions': 'auth.add_user',
            'icon': 'icon-cog',
            'orig_url': '/constance/config',
        },
    ],
    'LIST_PER_PAGE': 20,
    # CUSTOM SETTINGS
    'APPS_SKIPPED_IN_DASHBOARD': [
        'alerts',
        'constance',
        'django_celery_results',
    ]
}

SPECIAL_CHARS = ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

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
    },
    'data_source_description': {
        'toolbar': "Custom",
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
        ],
        'height': 100,
        'width': '100%',
    },
    'licenses': {
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter',
             'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Attachments', ],
            ['RemoveFormat', 'Source']
        ],
        'height': 150,
        'width': '100%',
    },
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

ELASTICSEARCH_COMMON_ALIAS_NAME = "common_alias"

ELASTICSEARCH_INDEX_NAMES = OrderedDict({
    "articles": "articles",
    "applications": "applications",
    "courses": "courses",
    "institutions": "institutions",
    "datasets": "datasets",
    "resources": "resources",
    "regions": "regions",
    "searchhistories": "searchhistories",
    "histories": "histories",
    "logentries": "logentries",
    "lab_events": "lab_events",
    "accepted_dataset_submissions": "accepted_dataset_submissions",
    "meetings": "meetings",
    "knowledge_base_pages": "knowledge_base_pages",
    "showcases": "showcases",
})

ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'mcod.core.api.search.signals.AsyncSignalProcessor'

ELASTICSEARCH_DSL_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 1
}

ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 1,
    'max_result_window': 25000
}

ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS = {
    ELASTICSEARCH_COMMON_ALIAS_NAME: {},
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
    Queue('harvester'),
    Queue('resources'),
    Queue('indexing'),
    Queue('indexing_data'),
    Queue('periodic'),
    Queue('newsletter'),
    Queue('notifications'),
    Queue('search_history'),
    Queue('watchers'),
    Queue('history'),
}

CELERY_TASK_ROUTES = {
    'mcod.core.api.search.tasks.update_document_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.update_with_related_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_document_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_with_related_task': {'queue': 'indexing'},
    'mcod.core.api.search.tasks.delete_related_documents_task': {'queue': 'indexing'},
    'mcod.resources.tasks.process_resource_data_indexing_task': {'queue': 'indexing_data'},
    'mcod.resources.tasks.check_link_protocol': {'queue': 'periodic'},
    'mcod.resources.tasks.process_resource_from_url_task': {'queue': 'resources'},
    'mcod.resources.tasks.process_resource_file_task': {'queue': 'resources'},
    'mcod.resources.tasks.process_resource_res_file_task': {'queue': 'resources'},
    'mcod.resources.tasks.process_resource_file_data_task': {'queue': 'resources'},
    'mcod.resources.tasks.remove_orphaned_files_task': {'queue': 'resources'},
    'mcod.resources.tasks.update_resource_has_table_has_map_task': {'queue': 'resources'},
    'mcod.resources.tasks.update_resource_openness_score_task': {'queue': 'resources'},
    'mcod.resources.tasks.update_resource_validation_results_task': {'queue': 'resources'},
    'mcod.resources.tasks.send_resource_comment': {'queue': 'notifications'},
    'mcod.counters.tasks.save_counters': {'queue': 'periodic'},
    'mcod.harvester.tasks.harvester_supervisor': {'queue': 'harvester'},
    'mcod.harvester.tasks.import_data_task': {'queue': 'harvester'},
    'mcod.harvester.tasks.validate_xml_url_task': {'queue': 'harvester'},
    'mcod.histories.tasks.index_history': {'queue': 'periodic'},
    'mcod.histories.tasks.save_history_as_log_entry': {'queue': 'history'},
    'mcod.datasets.tasks.send_dataset_comment': {'queue': 'notifications'},
    'mcod.newsletter.tasks.remove_inactive_subscription': {'queue': 'newsletter'},
    'mcod.newsletter.tasks.send_newsletter': {'queue': 'newsletter'},
    'mcod.newsletter.tasks.send_newsletter_mail': {'queue': 'newsletter'},
    'mcod.newsletter.tasks.send_subscription_confirm_mail': {'queue': 'newsletter'},

    'mcod.reports.tasks.create_resources_report_task': {'queue': 'periodic'},

    'mcod.schedules.tasks.send_admin_notification_task': {'queue': 'notifications'},
    'mcod.schedules.tasks.send_schedule_notifications_task': {'queue': 'notifications'},
    'mcod.schedules.tasks.update_notifications_task': {'queue': 'notifications'},

    'mcod.searchhistories.tasks.create_search_history': {'queue': 'search_history'},

    'mcod.suggestions.tasks.create_accepted_dataset_suggestion_task': {'queue': 'notifications'},
    'mcod.suggestions.tasks.create_data_suggestion': {'queue': 'notifications'},
    'mcod.suggestions.tasks.create_dataset_suggestion': {'queue': 'notifications'},
    'mcod.suggestions.tasks.deactivate_accepted_dataset_submissions': {'queue': 'notifications'},
    'mcod.suggestions.tasks.send_dataset_suggestion_mail_task': {'queue': 'notifications'},
    'mcod.suggestions.tasks.send_data_suggestion': {'queue': 'notifications'},

    'mcod.watchers.tasks.update_model_watcher_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.remove_user_notifications_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.update_notifications_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.model_watcher_updated_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.update_query_watchers_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.query_watcher_updated_task': {'queue': 'watchers'},
    'mcod.watchers.tasks.send_report_from_subscriptions': {'queue': 'watchers'},
}

# CELERY_TIMEZONE = 'Europe/Warsaw'

CELERY_BEAT_SCHEDULE = {
    'every-2-minute': {
        'task': 'mcod.counters.tasks.save_counters',
        'schedule': 120,
    },
    'every-3-minutes': {
        'task': 'mcod.histories.tasks.index_history',
        'schedule': 180,
    },
    'every-5-minutes': {
        'task': 'mcod.searchhistories.tasks.save_searchhistories_task',
        'schedule': 300,
    },
    'update-query-watchers': {
        'task': 'mcod.watchers.tasks.update_query_watchers_task',
        'schedule': crontab(minute=0, hour=22)
    },
    'send-subscriptions-report': {
        'task': 'mcod.watchers.tasks.send_report_from_subscriptions',
        'schedule': crontab(minute=0, hour=5)
    },
    'send-schedule-notifications': {
        'task': 'mcod.schedules.tasks.send_schedule_notifications_task',
        'schedule': crontab(minute=0, hour=2),
    },
    'send-newsletter': {
        'task': 'mcod.newsletter.tasks.send_newsletter',
        'schedule': crontab(minute=0, hour=8)
    },
    'deactivate-accepted-dataset-submissions': {
        'task': 'mcod.suggestions.tasks.deactivate_accepted_dataset_submissions',
        'schedule': crontab(minute=0, hour=5)
    }
}
if env('ENABLE_MONTHLY_REPORTS', default='no') in ['yes', '1', 'true']:
    CELERY_BEAT_SCHEDULE.update({
        'monthly_broken_links_report': {
            'task': 'mcod.reports.tasks.validate_resources_links',
            'schedule': crontab(minute=30, hour=3, day_of_month=1)
        },
        'monthly_nodata_datasets_report': {
            'task': 'mcod.reports.tasks.create_no_resource_dataset_report',
            'schedule': crontab(minute=0, hour=3, day_of_month=1)
        }
    })

if ENVIRONMENT in ['dev', 'int']:
    CELERY_BEAT_SCHEDULE.update({
        'hourly': {
            'task': 'mcod.reports.tasks.create_daily_resources_report',
            'schedule': 3600
        }
    })
else:
    CELERY_BEAT_SCHEDULE.update({
        'every-day-morning': {
            'task': 'mcod.reports.tasks.create_daily_resources_report',
            'schedule': crontab(minute=0, hour=2)
        },
    })

CELERY_SINGLETON_BACKEND_URL = REDIS_URL

RESOURCE_MIN_FILE_SIZE = 1024
RESOURCE_MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1024 MB

FIXTURE_DIRS = [
    str(ROOT_DIR('fixtures')),
]

LOGSTASH_HOST = env('LOGSTASH_HOST', default='mcod-logstash')
STATS_LOG_LEVEL = env('STATS_LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'stats': {
            'format': '%(asctime)s;%(name)s;%(levelname)s;%(message)s'
        },
        'signals-console-formatter': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s\n'
                      '[%(signal)s] sender:%(sender)s, instance:%(instance)s, id:%(instance_id)s'
        },
    },
    'handlers': {
        'signals-console-handler': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'signals-console-formatter',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'logstash-admin': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': LOGSTASH_HOST,
            'port': 5959,
            'version': 1,
            'message_type': f'admin-{ENVIRONMENT}' if ENVIRONMENT else 'admin',
            'fqdn': False,
            'tags': [f'admin-{ENVIRONMENT}'] if ENVIRONMENT else None,
        },
        'logstash-signals': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': LOGSTASH_HOST,
            'port': 5959,
            'version': 1,
            'message_type': f'signals-{ENVIRONMENT}' if ENVIRONMENT else 'signals',
            'fqdn': False,
            'tags': [f'signals-{ENVIRONMENT}'] if ENVIRONMENT else None,
        },
        'logstash-tasks': {
            'level': 'DEBUG',
            'class': 'logstash.UDPLogstashHandler',
            'host': LOGSTASH_HOST,
            'port': 5959,
            'version': 1,
            'message_type': F'tasks-{ENVIRONMENT}' if ENVIRONMENT else 'tasks',
            'fqdn': False,
            'tags': [f'tasks-{ENVIRONMENT}'] if ENVIRONMENT else None,
        },
        'stats-log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{LOGS_DIR}/stats.log',
            'formatter': 'stats'
        },
        'kibana-statistics': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{LOGS_DIR}/kibana_statistics.log',
            'formatter': 'console'
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
            'handlers': ['mail-admins', 'logstash-admin'],
            'propagate': False,
        },
        'django.templates': {
            'handlers': ['logstash-admin', ],
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
            'handlers': ['signals-console-handler', 'logstash-signals'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery.app.trace': {
            'handlers': ['console', 'logstash-tasks'],
            'level': 'DEBUG',
            'propagate': True
        },
        'mcod': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'kibana-statistics': {
            'handlers': ['kibana-statistics', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'resource_file_processing': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'stats-queries': {
            'handlers': ['stats-log', ],
            'level': 'DEBUG',
            'propagate': True
        },
        'stats-profile': {
            'handlers': ['stats-log', ],
            'level': STATS_LOG_LEVEL,
            'propagate': True
        }
    },
}

CELERYD_HIJACK_ROOT_LOGGER = False

APM_SERVER_URL = env('APM_SERVER_URL', default=None)

# Disable APM for ASGI (ws component)
APM_SERVICES = ['api', 'admin', 'cms', 'celery']

if APM_SERVER_URL and COMPONENT in APM_SERVICES:
    INSTALLED_APPS += [
        'elasticapm.contrib.django',
    ]

    ELASTIC_APM = {
        'DEBUG': True,
        'SERVICE_NAME': f'{ENVIRONMENT}-{COMPONENT}',
        'SERVER_URL': APM_SERVER_URL,
        'CAPTURE_BODY': 'errors',
        'FILTER_EXCEPTION_TYPES': [
            'falcon.errors.HTTPNotFound',
            'falcon.errors.HTTPMethodNotAllowed',
            'falcon.errors.HTTPUnauthorized',
            'falcon.errors.HTTPBadRequest',
            'falcon.errors.HTTPUnprocessableEntity',
            'falcon.errors.HTTPForbidden'
        ],
        'DJANGO_TRANSACTION_NAME_FROM_ROUTE': True
    }

    LOGGING['handlers']['elasticapm'] = {
        'level': 'WARNING',
        'class': 'elasticapm.contrib.django.handlers.LoggingHandler',
    }

    LOGGING['loggers']['elasticapm.errors'] = {
        'handlers': ['console', ],
        'level': 'DEBUG',
        'propagate': False,
    }

    TEMPLATES[0]['OPTIONS']['context_processors'] += [
        'mcod.core.contextprocessors.apm',
        'elasticapm.contrib.django.context_processors.rum_tracing',
    ]

SUPPORTED_CONTENT_TYPES = [
    # (family, type, extensions, default openness score, other possible openness scores)
    ('application', 'csv', ('csv',), 3, {4, 5}),
    ('application', 'epub+zip', ('epub',), 1),
    ('application', 'excel', ('xls',), 2),
    ('application', 'geo+json', ('geojson',), 3, {4, 5}),
    ('application', 'gml+xml', ('xml',), 3, {4, 5}),
    ('application', 'gpx+xml', ('gpx',), 3, {4, 5}),
    ('application', 'json', ('json',), 3, {4, 5}),
    ('application', 'mspowerpoint', ('ppt', 'pot', 'ppa', 'pps', 'pwz'), 1),
    ('application', 'msword', ('doc', 'docx', 'dot', 'wiz'), 1),
    ('application', 'pdf', ('pdf',), 1),
    ('application', 'postscript', ('pdf', 'ps'), 1),
    ('application', 'powerpoint', ('ppt', 'pot', 'ppa', 'pps', 'pwz'), 1),
    ('application', 'rtf', ('rtf',), 1),
    ('application', 'shapefile', ('shp',), 3, {4, 5}),
    ('application', 'vnd.api+json', ('json',), 3, {4, 5}),
    ('application', 'vnd.geo+json', ('geojson',), 3, {4, 5}),
    ('application', 'vnd.google-earth.kml+xml', ('kml',), 3, {4, 5}),
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
    ('application', 'x-csv', ('csv',), 3, {4, 5}),
    ('application', 'x-excel', ('xls', 'xlsx', 'xlb'), 2),
    ('application', 'x-rtf', ('rtf',), 1),
    ('application', 'xhtml+xml', ('html', 'htm'), 3),
    ('application', 'xml', ('xml',), 3, {4, 5}),
    ('application', 'x-tex', ('tex',), 3),
    ('application', 'x-texinfo', ('texi', 'texinfo',), 3),
    ('application', 'x-dbf', ('dbf',), 3),
    ('application', 'x-grib', ('grib', 'grib2',), 2),
    ('application', 'netcdf', ('nc',), 2),
    ('image', 'bmp', ('bmp',), 1),
    ('image', 'gif', ('gif',), 2),
    ('image', 'jpeg', ('jpeg', 'jpg', 'jpe'), 1),
    ('image', 'png', ('png',), 1),
    ('image', 'svg+xml', ('svg',), 3),
    ('image', 'tiff', ('tiff', 'tif'), 1),
    ('image', 'tiff;application=geotiff', ('geotiff',), 3),
    ('image', 'webp', ('webp',), 2),
    ('image', 'x-tiff', ('tiff',), 1),
    ('image', 'x-ms-bmp', ('bmp',), 1),
    ('image', 'x-portable-pixmap', ('ppm',), 2),
    ('image', 'x-xbitmap', ('xbm',), 2),
    ('text', 'csv', ('csv',), 3, {4, 5}),
    ('text', 'html', ('html', 'htm'), 3),
    ('text', 'xhtml+xml', ('html', 'htm'), 3),
    ('text', 'plain', ('txt', 'rd', 'md', 'bat'), 1),
    ('text', 'richtext', ('rtf',), 1),
    ('text', 'tab-separated-values', ('tsv',), 3),
    ('text', 'xml', ('xml', 'wsdl', 'xpdl', 'xsl'), 3, {4, 5}),
    # RDF
    ('application', 'ld+json', ('jsonld', 'json-ld'), 4, {5}),
    ('application', 'rdf+xml', ('rdf',), 4, {5}),
    ('text', 'n3', ('n3',), 4, {5}),
    ('text', 'turtle', ('ttl', 'turtle'), 4, {5}),
    ('application', 'nt-triples', ('nt', 'nt11', 'ntriples'), 4, {5}),
    ('application', 'n-quads', ('nq', 'nquads',), 4, {5}),
    ('application', 'trix', ('trix',), 4, {5}),
    ('application', 'trig', ('trig',), 4, {5}),
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 1073741824  # 1Gb
FILE_UPLOAD_PERMISSIONS = 0o644

IMAGE_UPLOAD_MAX_SIZE = 10 * 1024 ** 2
THUMB_SIZE = (200, 1024)

COUNTED_VIEWS = ['applications', 'articles', 'resources']
SEARCH_PATH = '/search'

JSONAPI_SCHEMA_PATH = str(DATA_DIR.path('jsonapi.config.json'))
JSONSTAT_SCHEMA_PATH = str(DATA_DIR.path('json_stat_schema_2_0.json'))
JSONSTAT_V1_ALLOWED = env('JSONSTAT_V1_ALLOWED', default='yes') in ('yes', '1', 'true')
GPX_11_SCHEMA_PATH = str(DATA_DIR.path('gpx_xsd_1_1.xsd'))
GPX_10_SCHEMA_PATH = str(DATA_DIR.path('gpx_xsd_1_0.xsd'))

DATE_BASE_FORMATS = ['yyyy-MM-dd', 'yyyy-MM-dd HH:mm', 'yyyy-MM-dd HH:mm:ss', 'yyyy-MM-dd HH:mm:ss.SSSSSS',
                     "yyyy-MM-dd'T'HH:mm:ss.SSSSSS", 'yyyy.MM.dd', 'yyyy.MM.dd HH:mm', 'yyyy.MM.dd HH:mm:ss',
                     'yyyy.MM.dd HH:mm:ss.SSSSSS', "yyyy.MM.dd'T'HH:mm:ss.SSSSSS", 'yyyy/MM/dd', 'yyyy/MM/dd HH:mm',
                     'yyyy/MM/dd HH:mm:ss', 'yyyy/MM/dd HH:mm:ss.SSSSSS', "yyyy/MM/dd'T'HH:mm:ss.SSSSSS", 'dd-MM-yyyy',
                     'dd-MM-yyyy HH:mm', 'dd-MM-yyyy HH:mm:ss', 'dd-MM-yyyy HH:mm:ss.SSSSSS',
                     "dd-MM-yyyy'T'HH:mm:ss.SSSSSS", 'dd.MM.yyyy', 'dd.MM.yyyy HH:mm', 'dd.MM.yyyy HH:mm:ss',
                     'dd.MM.yyyy HH:mm:ss.SSSSSS', "dd.MM.yyyy'T'HH:mm:ss.SSSSSS", 'dd/MM/yyyy', 'dd/MM/yyyy HH:mm',
                     'dd/MM/yyyy HH:mm:ss', 'dd/MM/yyyy HH:mm:ss.SSSSSS', "dd/MM/yyyy'T'HH:mm:ss.SSSSSS",
                     "yyyy-MM-dd'T'HH:mm:ss", "yyyy.MM.dd'T'HH:mm:ss", "yyyy/MM/dd'T'HH:mm:ss", "dd-MM-yyyy'T'HH:mm:ss",
                     "dd.MM.yyyy'T'HH:mm:ss", "dd/MM/yyyy'T'HH:mm:ss", "yyyy-MM-dd'T'HH:mm", "yyyy.MM.dd'T'HH:mm",
                     "yyyy/MM/dd'T'HH:mm", "dd-MM-yyyy'T'HH:mm", "dd.MM.yyyy'T'HH:mm", "dd/MM/yyyy'T'HH:mm"]

TIME_BASE_FORMATS = ['HH:mm', 'HH:mm:ss', 'HH:mm:ss.SSSSSS']

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_PREFIX = 'constance:mcod:'
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'

CONSTANCE_CONFIG = {
    'NO_REPLY_EMAIL': ('no-reply@dane.gov.pl', '', str),
    'CONTACT_MAIL': ('kontakt@dane.gov.pl', '', str),
    'SUGGESTIONS_EMAIL': ("uwagi@dane.gov.pl", '', str),
    'ACCOUNTS_EMAIL': ("konta@dane.gov.pl", '', str),
    'FOLLOWINGS_EMAIL': ("obserwowane@dane.gov.pl", '', str),
    'NEWSLETTER_EMAIL': ('newsletter@dane.gov.pl', '', str),
    'TESTER_EMAIL': ('no-reply@dane.gov.pl', '', str),
    'MANUAL_URL': ('https://dane.gov.pl/article/1226', '', str),
    'DATE_FORMATS': ("||".join(DATE_BASE_FORMATS), "", str),
    'TIME_FORMATS': ("||".join(TIME_BASE_FORMATS), "", str),
    'CATALOG__TITLE_PL': ('Portal z danymi publicznymi', '', str),
    'CATALOG__TITLE_EN': ("Poland's Open Data Portal", '', str),
    'CATALOG__DESCRIPTION_PL': ('Dane o szczególnym znaczeniu dla rozwoju innowacyjności w państwie i rozwoju społeczeństwa informacyjnego w jednym miejscu', '', str),  # noqa: E501
    'CATALOG__DESCRIPTION_EN': ('Data of particular importance for the development of innovation in the country and the development of the information society gathered in one location', '', str),  # noqa: E501
    'CATALOG__ISSUED': (date(2014, 4, 30), "", date),
    'CATALOG__PUBLISHER__NAME_PL': ('KPRM', '', str),
    'CATALOG__PUBLISHER__NAME_EN': ('KPRM', '', str),
    'CATALOG__PUBLISHER__EMAIL': ('kontakt@dane.gov.pl', '', str),
    'CATALOG__PUBLISHER__HOMEPAGE': ('https://dane.gov.pl', '', str),
    'DATASET__CONTACT_POINT__FN': ('KPRM', '', str),
    'DATASET__CONTACT_POINT__HAS_EMAIL': ('mailto:kontakt@dane.gov.pl', '', str),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict((
    ('URLs', ('MANUAL_URL',)),
    ('Mails', (
        'NO_REPLY_EMAIL', 'CONTACT_MAIL', 'SUGGESTIONS_EMAIL', 'ACCOUNTS_EMAIL', 'FOLLOWINGS_EMAIL',
        'NEWSLETTER_EMAIL')),
    ('Development', ('TESTER_EMAIL',)),
    ('Dates', ('DATE_FORMATS', 'TIME_FORMATS')),
    ('RDF', (
        'CATALOG__TITLE_PL', 'CATALOG__TITLE_EN', 'CATALOG__DESCRIPTION_PL', 'CATALOG__DESCRIPTION_EN',
        'CATALOG__ISSUED', 'CATALOG__PUBLISHER__NAME_PL', 'CATALOG__PUBLISHER__NAME_EN',
        'CATALOG__PUBLISHER__EMAIL', 'CATALOG__PUBLISHER__HOMEPAGE',
        'DATASET__CONTACT_POINT__FN', 'DATASET__CONTACT_POINT__HAS_EMAIL',
    )
    ),
))

SHOW_GENERATE_RAPORT_BUTTOON = env('SHOW_GENERATE_RAPORT_BUTTOON', default='yes') in ['yes', '1', 'true']

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

BASE_URL = env('BASE_URL', default='https://www.dane.gov.pl')
API_URL = env('API_URL', default='https://api.dane.gov.pl')
ADMIN_URL = env('ADMIN_URL', default='https://admin.dane.gov.pl')
CMS_URL = env('CMS_URL', default='https://cms.dane.gov.pl')
TOURPICKER_URL = f'{BASE_URL}?tourPicker=1'
API_URL_INTERNAL = env('API_URL_INTERNAL', default='http://mcod-api:8000')

PASSWORD_RESET_PATH = '/user/reset-password/%s/'
EMAIL_VALIDATION_PATH = '/user/verify-email/%s/'

VERIFICATION_RULES = (
    ("numeric", _("Numeric"),
     "Wymaga się stosowania kropki dziesiętnej (a nie przecinka) w zapisie ułamków dziesiętnych, bez żadnych "
     "dodatkowych separatorów (np. oddzielających tysiące); dopuszczalny jest tzw. zapis naukowy"),
    ("regon", "REGON", "Wymagany format: ciąg 9  lub 14 cyfr, bez spacji lub łączników"),
    ("nip", "NIP", "Wymagany format: ciąg 10 cyfr, bez spacji lub łączników"),
    ("krs", "KRS", "Wymagany format: ciąg 10 cyfr, bez spacji lub łączników"),
    ("uaddress", _("Universal address"), """
    Wymagany format: ciąg kodów oddzielonych separatorem &quot;|&quot; lub &quot;;&quot;:
- kodu pocztowego (tzw. PNA) bez myślnika (5 cyfr)
- identyfikatora terytorialnego TERC (7 lub 6 cyfr)
- identyfikatora miejscowości podstawowej SIMC (7 cyfr)
- identyfikatora miejscowości SIMC (7 cyfr)
- identyfikatora katalogu ulic ULIC (5 cyfr)
- współrzędnych geodezyjnych x (w metrach)
- współrzędnych geodezyjnych y (w metrach)
- numeru budynku
Przykłady:
00184|146501|0918123|0918123|04337|489147.9218|636045.6562|5A|
40035;2469011;0937474;0937474;16466;265394;501512;6;

    """),
    ("pna", _("PNA code"), "Wymagany format: xx-xxx"),
    ("address_feature", _("Address feature"),
     "Wymagane wartości: ul. (ulica), al. (aleja), pl. (plac), skwer, bulw. (bulwar), rondo, park, rynek, szosa, "
     "droga, os. (osiedle), ogród, wyspa, wyb. (wybrzeże), inne"),
    ("phone", _("Phone number"),
     "W polskiej strefie numeracyjnej zaleca się zapisywanie numeru telefonu jako ciągu 9 cyfr, bez wyróżniania "
     "tzw. numeru kierunkowego miejscowości. Dopuszczalne jest stosowanie prefiksu międzynarodowego poprzedzonego "
     "znakiem plus „+” – struktura xxxxxxxxx/ lub +48xxxxxxxxx. Nie stosuje się spacji, nawiasów i łączników ani "
     "podobnych znaków pełniących role separatorów."),
    ("bool", _("Field of logical values"), "Wymagane wartości: True, False"),
    #     ("date", _("Date"), """Wymagany format zapisu dat:
    # a) yyyy-mm-dd;
    # """),
    #     ("time", _("Time"), """Wymagany format zapisu czasu:
    # a) hh:mm:ss
    # b) hh:mm
    # """),
    #     ("datetime", _("DateTime"), """
    # Wymagane formaty łącznego zapisu dat i czasu:
    # a) yyyy-mm-ddThh:mm
    # b) yyyy-mm-ddThh:mm:ss
    # c) yyyy-mm-dd hh:mm (spacja między datą a czasem)
    # d) yyyy-mm-dd hh:mm:ss (spacja między datą a czasem)
    # """),
)

DATA_TYPES = (
    ("integer", _("Integer"), ""),
    ("number", _("Float"), ""),
    ("string", _("String"), ""),
    ("boolean", _("Logic value (True/False)"), ""),
    ("date", _("Date"), ""),
    ("time", _("Time"), ""),
    ("datetime", _("DateTime"), ""),
    ("any", _("Any type"), "")
)

RESOURCE_VALIDATION_TOOL_ENABLED = True

ENABLE_SUBSCRIPTIONS_EMAIL_REPORTS = True

# WAGTAIL CONFIG
WAGTAIL_SITE_NAME = 'Otwarte Dane'

UNLEASH_URL = 'https://flags.dane.gov.pl/api'

GEO_TYPES = {
    "": [
        ("label", _("Label"), _("Describes the presented data. Required item.")),
    ],
    "geographical coordinates": [
        ("l", _("Longitude"),
         "Dla zestawu danych mapowych “współrzędne geograficzne” należy obowiązkowo wybrać trzy elementy z listy: "
         "„długość geograficzna”, „szerokość geograficzna” oraz „etykieta” (opis punktu, który ma się pojawić na "
         "mapie). Współrzędne geograficzne są przetwarzane zgodnie z układem współrzędnych WGS84. Kolumny zawierające "
         "współrzędne geograficzne muszą być typu numerycznego"),
        ("b", _("Latitude"),
         "Dla zestawu danych mapowych “współrzędne geograficzne” należy obowiązkowo wybrać trzy elementy z listy: "
         "„długość geograficzna”, „szerokość geograficzna” oraz „etykieta” (opis punktu, który ma się pojawić na "
         "mapie). Współrzędne geograficzne są przetwarzane zgodnie z układem współrzędnych WGS84. Kolumny zawierające "
         "współrzędne geograficzne muszą być typu numerycznego"),
    ],
    'universal address': [
        ("uaddress", _("Universal address"),
         "Dla zestawu danych mapowych “adres uniwersalny“ należy obowiązkowo wybrać dwa elementy z listy: "
         "„adres uniwersalny” oraz “etykieta” (opis punktu, który ma się pojawić na mapie)."),
    ],
    "address": [

        ("place", _("Place"),
         "Dla zestawu danych mapowych “adres” należy obowiązkowo wybrać trzy elementy z listy: „miejscowość”, "
         "„kod pocztowy” oraz „etykieta” (opis punktu, który ma się pojawić na mapie). Elementy ulica i numer "
         "domu są opcjonalne."),
        ("street", _("Street"),
         "Dla zestawu danych mapowych “adres” należy obowiązkowo wybrać trzy elementy z listy: „miejscowość”, "
         "„kod pocztowy” oraz „etykieta” (opis punktu, który ma się pojawić na mapie). Elementy ulica i numer "
         "domu są opcjonalne."),
        ("house_number", _("House number"),
         "Dla zestawu danych mapowych “adres” należy obowiązkowo wybrać trzy elementy z listy: „miejscowość”, "
         "„kod pocztowy” oraz „etykieta” (opis punktu, który ma się pojawić na mapie). Elementy ulica i numer "
         "domu są opcjonalne."),
        ("postal_code", _("Postal code"),
         "Dla zestawu danych mapowych “adres” należy obowiązkowo wybrać trzy elementy z listy: „miejscowość”, "
         "„kod pocztowy” oraz „etykieta” (opis punktu, który ma się pojawić na mapie). Elementy ulica i numer "
         "domu są opcjonalne."),
    ]
}

CMS_RICH_TEXT_FIELD_FEATURES = [
    'bold',
    'italic',
    'h2',
    'h3',
    'h4',
    'titled_link',
    'ol',
    'ul',
    'superscript',
    'subscript',
    'strikethrough'
    'document-link',
    'lang-pl',
    'lang-en',
]

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
        'OPTIONS': {
            'features': ['bold', 'italic', 'h2', 'h3', 'h4', 'ol', 'ul', 'hr',
                         'image', 'embed', 'titled_link', 'document-link', 'lang-en', 'lang-pl']
        }
    },
}

GEOCODER_URL = env('GEOCODER_URL', default='http://geocoder.mcod.local')
GEOCODER_USER = env('GEOCODER_USER', default='geouser')
GEOCODER_PASS = env('GEOCODER_PASS', default='1234')
PLACEHOLDER_URL = env('PLACEHOLDER_URL', default='http://placeholder.mcod.local')

MAX_TAG_LENGTH = 100

WAGTAILDOCS_DOCUMENT_MODEL = 'cms.CustomDocument'
WAGTAILIMAGES_IMAGE_MODEL = 'cms.CustomImage'
WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK = True

EXPORT_FORMAT_TO_MIMETYPE = {
    'csv': 'text/csv',
    'xlsx': 'application/vnd.ms-excel',
    'xml': 'application/xml',
}

RDF_FORMAT_TO_MIMETYPE = {
    'json-ld': 'application/ld+json',
    'jsonld': 'application/ld+json',
    'xml': 'application/rdf+xml',
    'rdf': 'application/rdf+xml',
    'n3': 'text/n3',
    'ttl': 'text/turtle',
    'turtle': 'text/turtle',
    'nt': 'application/n-triples',
    'nt11': 'application/n-triples',
    'ntriples': 'application/n-triples',
    'nq': 'application/n-quads',
    'nquads': 'application/n-quads',
    'trix': 'application/trix',
    'trig': 'application/trig',
}

RDF_MIMETYPES = list(set(RDF_FORMAT_TO_MIMETYPE.values()))

JSONAPI_FORMAT_TO_MIMETYPE = {
    'ja': 'application/vnd.api+json; ext=bulk',
    'json': 'application/vnd.api+json; ext=bulk',
    'jsonapi': 'application/vnd.api+json; ext=bulk',
    'json-api': 'application/vnd.api+json; ext=bulk',
}

JSONAPI_MIMETYPES = [
    'application/vnd.api+json; ext=bulk',
    'application/vnd.api+json'
]

dailymotion = {
    "endpoint": "http://www.dailymotion.com/api/oembed/",
    "urls": [
        r'^http(?:s)?://[-\w]+\.dailymotion\.com/.+$'
    ],
}

youtube = {
    "endpoint": "https://www.youtube.com/oembed",
    "urls": [
        r'^https?://(?:[-\w]+\.)?youtube\.com/watch.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/v/.+$',
        r'^https?://youtu\.be/.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/user/.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/[^#?/]+#[^#?/]+/.+$',
        r'^https?://m\.youtube\.com/index.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/profile.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/view_play_list.+$',
        r'^https?://(?:[-\w]+\.)?youtube\.com/playlist.+$',
    ],
}

WAGTAILEMBEDS_FINDERS = [
    {
        'class': 'wagtail.embeds.finders.oembed',
        'providers': [dailymotion, youtube] + all_providers,
    }
]

HYPER_EDITOR = {
    'IMAGE_API_URL': '%s/hypereditor/chooser-api/images/' % CMS_URL
}

HYPER_EDITOR_EXCLUDE_BLOCKS = ['contentbox', 'tab', 'slider']

# CSRF config:
ENABLE_CSRF = True
CSRF_SECRET_LENGTH = 32
CSRF_TOKEN_LENGTH = 2 * CSRF_SECRET_LENGTH
CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits
API_CSRF_COOKIE_NAME = 'mcod_csrf_token'
API_CSRF_HEADER_NAME = 'X-MCOD-CSRF-TOKEN'
API_CSRF_TRUSTED_ORIGINS = [
    'dane.gov.pl',
]
API_CSRF_COOKIE_DOMAINS = env('API_CSRF_COOKIE_DOMAINS', default=SESSION_COOKIE_DOMAIN).split(',')

# ELASTICSEARCH SYNONYMS
ES_EN_SYN_FILTER_KWARGS = {
    "type": "synonym",
    "lenient": True,
    "format": "wordnet",
    "synonyms_path": "synonyms/en_wn_s.pl"

}

ES_PL_SYN_FILTER_KWARGS = {
    "type": "synonym",
    "lenient": True,
    "format": "solr",
    "synonyms_path": "synonyms/pl_synonyms.txt"
}
DEACTIVATE_ACCEPTED_DATASET_SUBMISSIONS_PUBLISHED_DAYS_AGO = 90
DESCRIPTION_FIELD_MAX_LENGTH = 10000
DESCRIPTION_FIELD_MIN_LENGTH = 20

SHACL_SHAPES = {
    # 'count': SHACL_SHAPES_DIR.join('dcat-ap.shapes.ttl').root,
    # 'vocab': SHACL_SHAPES_DIR.join('dcat-ap-mdr-vocabularies.shapes.ttl').root,
    # 'classes': SHACL_SHAPES_DIR.join('dcat-ap-mandatory-classes.shapes.ttl').root,
    'shapes': SHACL_SHAPES_DIR.path('dcat-ap_2.0.1_shacl_shapes.ttl').root,
    'mdr-vocabularies': SHACL_SHAPES_DIR.path('dcat-ap_2.0.1_shacl_mdr-vocabularies.shape.ttl').root,
    'deprecateduris': SHACL_SHAPES_DIR.path('dcat-ap_2.0.1_shacl_deprecateduris.ttl').root,
}

NOTIFICATIONS_NOTIFICATION_MODEL = 'schedules.Notification'

SHACL_UNSUPPORTED_MIMETYPES = ['application/n-quads', 'application/trix']

STATS_THEME_COOKIE_NAME = 'mcod_stats_theme'

FALCON_CACHING_ENABLED = env('FALCON_CACHING_ENABLED', default='yes') in ('yes', 1, 'true')
FALCON_LIMITER_ENABLED = env('FALCON_LIMITER_ENABLED', default='yes') in ('yes', 1, 'true')
# https://falcon-limiter.readthedocs.io/en/latest/#rate-limit-string-notation
FALCON_LIMITER_DEFAULT_LIMITS = env('FALCON_LIMITER_DEFAULT_LIMITS', default='5 per minute,2 per second')
FALCON_LIMITER_SPARQL_LIMITS = env('FALCON_LIMITER_SPARQL_LIMITS', default='20 per minute,1 per second')

DISCOURSE_HOST = env('DISCOURSE_HOST', default='http://forum.mcod.local')
DISCOURSE_SYNC_HOST = env('DISCOURSE_SYNC_HOST', default='http://forum.mcod.local')
DISCOURSE_API_USER = env('DISCOURSE_API_USER', default='system')
DISCOURSE_API_KEY = env('DISCOURSE_API_KEY', default='')
DISCOURSE_SSO_SECRET = env('DISCOURSE_SSO_SECRET', default='')
DISCOURSE_SSO_REDIRECT = env('DISCOURSE_SSO_REDIRECT', default=f'{DISCOURSE_HOST}/session/sso_login')

LICENSES_LINKS = {
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-NC 4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA 4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-ND 4.0": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-NC-ND 4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
}
CKAN_LICENSES_WHITELIST = {
    "cc-zero": "CC0 1.0",
    "cc-by": "CC BY 4.0",
    "cc-by-sa": "CC BY-SA 4.0",
    "cc-nc": "CC BY-NC 4.0",
}

CSV_CATALOG_BATCH_SIZE = env('CSV_CATALOG_BATCH_SIZE', default=20000)

DISCOURSE_FORUM_ENABLED = env('DISCOURSE_FORUM_ENABLED', default=True)

SPARQL_ENDPOINTS = {
    'kronika': {'endpoint': env('KRONIKA_SPARQL_URL', default='http://kronika.mcod.local'),
                'headers': {'host': 'public-api.k8s'},
                'returnFormat': 'json'}
}
METABASE_URL = env('METABASE_URL', default='http://metabase.mcod.local')
KIBANA_URL = env('KIBANA_URL', default='http://kibana.mcod.local')
ZABBIX_API = {
    'user': env('ZABBIX_API_USER', default='user'),
    'password': env('ZABBIX_API_PASSWORD', default=''),
    'url': env('ZABBIX_API_URL', default='http://zabbix.mcod.local')
}

DEFAULT_REGION_ID = 85633723

DATASET_ARCHIVE_FILES_TASK_DELAY = env('DATASET_ARCHIVE_FILES_TASK_DELAY', default=180)

ALLOWED_MINIMUM_SPACE = 1024*1024*1024*env('ALLOWED_MINIMUM_FREE_GB', default=20)
