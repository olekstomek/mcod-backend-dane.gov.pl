import json
import logging
import os
import re
import shutil

import unicodecsv
from io import BytesIO

import magic
from celery.signals import task_prerun, task_failure, task_success, task_postrun
from constance import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Max, Sum
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, get_language
from django_celery_results.models import TaskResult as TaskResultOrig
from elasticsearch_dsl.connections import Connections
from mimeparse import parse_mime_type
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField

from mcod.core import signals as core_signals
from mcod.core import storages
from mcod.core.api.search import signals as search_signals
from mcod.core.api.rdf import signals as rdf_signals
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel, update_watcher, TrashModelBase
from mcod.core.utils import sizeof_fmt
from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.datasets.models import Dataset
from mcod.lib.data_rules import painless_body
from mcod.resources.error_mappings import recommendations, messages
from mcod.resources.indexed_data import ShpData, TabularData
from mcod.resources.link_validation import content_type_from_file_format
from mcod.resources.manager import ResourceManager
from mcod.resources.signals import revalidate_resource, update_chart_resource
from mcod.resources.tasks import process_resource_from_url_task, process_resource_file_task, \
    process_resource_file_data_task, validate_link
from mcod.unleash import is_enabled

from mcod.watchers.tasks import update_model_watcher_task

User = get_user_model()

es_connections = Connections()
es_connections.configure(**settings.ELASTICSEARCH_DSL)

STATUS_CHOICES = [
    ('published', _('Published')),
    ('draft', _('Draft'))
]

OPENNESS_SCORE = {_type: os for _, _type, _, os in settings.SUPPORTED_CONTENT_TYPES}

signal_logger = logging.getLogger('signals')


class ResourceDataValidationError(Exception):
    pass


def supported_formats():
    data = []
    for item in settings.SUPPORTED_CONTENT_TYPES:
        data.extend(item[2])
    return sorted(list(set(data)))


def supported_formats_choices():
    return [(i, i.upper()) for i in supported_formats()]


def get_coltype(col, table_schema):
    fields = table_schema.get('fields')
    col_index = int(col.replace("col", "")) - 1
    return fields[col_index]['type']


@deconstructible
class FileValidator(object):
    error_messages = {
        'max_size': ("Ensure this file size is not greater than %(max_size)s."
                     " Your file size is %(size)s."),
        'min_size': ("Ensure this file size is not less than %(min_size)s. "
                     "Your file size is %(size)s."),
        'content_type': "Files of type %(content_type)s are not supported.",
    }

    def __call__(self, file):
        min_size = settings.RESOURCE_MIN_FILE_SIZE
        max_size = settings.RESOURCE_MAX_FILE_SIZE
        try:
            filesize = file.size
        except FileNotFoundError:
            raise ValidationError(_('File %s does not exist, please upload it again') % file.name)

        if max_size is not None and filesize > max_size:
            params = {
                'max_size': filesizeformat(max_size),
                'size': filesizeformat(filesize),
            }
            raise ValidationError(self.error_messages['max_size'],
                                  'max_size', params)

        if min_size is not None and filesize < min_size:
            params = {
                'min_size': filesizeformat(min_size),
                'size': filesizeformat(filesize)
            }
            raise ValidationError(self.error_messages['min_size'],
                                  'min_size', params)

        mime_type = magic.from_buffer(file.read(), mime=True)
        family, content_type, options = parse_mime_type(mime_type)
        file.seek(0)
        if content_type not in [ct[1] for ct in settings.SUPPORTED_CONTENT_TYPES]:
            params = {'content_type': content_type}
            raise ValidationError(self.error_messages['content_type'],
                                  'content_type', params)

    def __eq__(self, other):
        return isinstance(other, FileValidator)


RESOURCE_TYPE_WEBSITE = 'website'
RESOURCE_TYPE_API = 'api'
RESOURCE_TYPE = (
    ('file', _('File')),
    (RESOURCE_TYPE_WEBSITE, _('Web Site')),
    (RESOURCE_TYPE_API, _('API')),
)

RESOURCE_TYPE_API_CHANGE = 'api-change'
RESOURCE_TYPE_API_CHANGE_LABEL = _('API - change')


class TaskResult(TaskResultOrig):
    @staticmethod
    def values_from_result(result, key):
        exc_message = result["exc_message"]

        for s in exc_message.lstrip('[{0').rstrip('}]').split('}, {'):
            pos = s.find(f"'{key}'")
            if pos < 0:
                raise KeyError()
            start = pos + len(key) + 4
            end = start
            escape = False
            while end < len(s):
                end += 1
                if escape:
                    escape = False
                    continue
                if s[end] == '\\':
                    escape = True
                    continue
                if s[end] == s[start]:
                    yield s[start + 1:end]
                    break

    @staticmethod
    def find_es_parse_errors(text):
        pattern = re.compile(r"failed to parse field (\[[\w.]+\]) of type (\[[\w_]+\])")
        errors = pattern.findall(text)
        replacements = {
            '[scaled_float]': '[Liczba zmiennoprzecinkowa]',
            '[long]': '[Liczba całkowita]'
        }
        error = tuple()
        if errors:
            error = errors[0]
            if error[1] in replacements:
                error = (error[0], replacements[error[1]])
        return error

    @property
    def message(self):
        result = json.loads(self.result) if self.result else {}
        if isinstance(result, str):
            result = json.loads(result)
        exc_message = result.get('exc_message', "")
        error = self.find_es_parse_errors(exc_message)
        error_code = self._find_error_code(result)
        if exc_message.startswith('[{'):
            return [msg or "" for msg in self.values_from_result(result, 'message')]
        elif error_code == 'es-index-error' and error:
            return [messages.get(error_code).format(*error)]
        if error_code in ['InvalidContentType', 'UnsupportedContentType']:
            exc_message = exc_message.split(':')[-1] if ':' in exc_message else exc_message
        return [messages.get(error_code, "Nierozpoznany błąd walidacji").format(exc_message)]

    @property
    def recommendation(self):
        result = json.loads(self.result) if self.result else {}

        if isinstance(result, str):
            result = json.loads(result)
        exc_message = result.get('exc_message', "")
        error = self.find_es_parse_errors(exc_message)

        try:
            codes = list(self.values_from_result(result, 'code'))
        except Exception:
            codes = [self._find_error_code(result)]

        if error:
            return [recommendations.get(code).format(error[0]) for code in codes if recommendations.get(code)]

        return [recommendations.get(code, "Skontaktuj się z administratorem systemu.") for code in codes]

    @staticmethod
    def _find_error_code(result):  # noqa:C901
        if 'exc_type' not in result:
            return None

        if result['exc_message'] == "The 'file' attribute has no file associated with it.":
            return 'no-file-associated'

        if result['exc_type'] == 'OperationalError':
            if result['exc_message'].startswith("could not connect to server: Connection refused") \
                    or result['exc_message'].find("remaining connection slots are reserved") > 0:
                return 'connection-error'

        elif result['exc_type'] == 'Exception':
            if result['exc_message'] == 'unknown-file-format':
                return result['exc_message']

        elif result['exc_type'] == 'InvalidResponseCode':
            if result['exc_message'] == 'Resource location has been moved!':
                return 'location-moved'
            if result['exc_message'].startswith('Invalid response code:'):
                if result['exc_message'].endswith("400"):
                    return '400-bad-request'
                if result['exc_message'].endswith("403"):
                    return '403-forbidden'
                if result['exc_message'].endswith("404"):
                    return '404-not-found'
                if result['exc_message'].endswith("503"):
                    return '503-service-unavailable'

        elif result['exc_type'] == 'ConnectionError':
            if result['exc_message'].startswith("('Connection aborted."):
                return 'connection-aborted'
            if result['exc_message'].find('Failed to establish a new connection') > -1:
                return 'failed-new-connection'

        elif result['exc_type'] == "BulkIndexError":
            if result['exc_message'].find('must be between -180.0 and 180.0') > -1:
                return 'longitude-error'
            if result['exc_message'].find('must be between -90.0 and 90.0') > -1:
                return 'latitude-error'
            if (result['exc_message'].find("document(s) failed to index") > -1 and result['exc_message'].find(
                    'mapper_parsing_exception') > -1):
                return 'es-index-error'
        return result['exc_type']

    class Meta:
        proxy = True


class Resource(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (
            rdf_signals.update_graph,
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_updated
        ),
        'published': (
            rdf_signals.create_graph_with_related_update,
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_published
        ),
        'restored': (
            rdf_signals.create_graph_with_related_update,
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_restored
        ),
        'removed': (
            rdf_signals.delete_graph_with_related_update,
            search_signals.remove_document_with_related,
            core_signals.notify_removed
        )
    }
    ext_ident = models.CharField(
        max_length=36, blank=True, editable=False, verbose_name=_('external identifier'),
        help_text=_('external identifier of resource taken during import process (optional)'))
    availability = models.CharField(
        max_length=6, blank=True, null=True, editable=False, verbose_name=_('availability'))
    file = models.FileField(verbose_name=_("File"), storage=storages.get_storage('resources'),
                            upload_to='%Y%m%d',
                            max_length=2000, blank=True, null=True)
    packed_file = models.FileField(verbose_name=_("Packed file"), storage=storages.get_storage('resources'),
                                   upload_to='%Y%m%d',
                                   max_length=2000, blank=True, null=True)
    csv_file = models.FileField(verbose_name=_("File as CSV"), storage=storages.get_storage('resources'),
                                upload_to='%Y%m%d',
                                max_length=2000, blank=True, null=True)
    file_mimetype = models.TextField(blank=True, null=True, editable=False, verbose_name=_("File mimetype"))
    file_info = models.TextField(blank=True, null=True, editable=False, verbose_name=_("File info"))
    file_encoding = models.CharField(max_length=150, null=True, blank=True, editable=False,
                                     verbose_name=_("File encoding"))
    link = models.URLField(verbose_name=_('Resource Link'), max_length=2000, blank=True, null=True)
    title = models.CharField(max_length=500, verbose_name=_("title"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    position = models.IntegerField(default=1, verbose_name=_("Position"))
    dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE, related_name='resources',
                                verbose_name=_('Dataset'))

    format = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Format"),
                              choices=supported_formats_choices())
    type = models.CharField(max_length=10, choices=RESOURCE_TYPE, default='file', editable=False,
                            verbose_name=_("Type"))
    forced_api_type = models.BooleanField(verbose_name=_("Mark resource as API"), default=False)
    openness_score = models.IntegerField(default=0, verbose_name=_("Openness score"),
                                         validators=[MinValueValidator(0), MaxValueValidator(5)])

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='resources_created'
    )
    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='resources_modified'
    )
    link_tasks = models.ManyToManyField('TaskResult', verbose_name=_('Download Tasks'),
                                        blank=True,
                                        related_name='link_task_resources',
                                        )
    file_tasks = models.ManyToManyField('TaskResult', verbose_name=_('Download Tasks'),
                                        blank=True,
                                        related_name='file_task_resources')
    data_tasks = models.ManyToManyField('TaskResult', verbose_name=_('Download Tasks'),
                                        blank=True,
                                        related_name='data_task_resources')

    link_tasks_last_status = models.CharField(verbose_name=_('link tasks last status'), max_length=7, blank=True)
    file_tasks_last_status = models.CharField(verbose_name=_('file tasks last status'), max_length=7, blank=True)
    data_tasks_last_status = models.CharField(verbose_name=_('data tasks last status'), max_length=7, blank=True)
    old_file = models.FileField(verbose_name=_("File"), storage=storages.get_storage('resources'), upload_to='',
                                max_length=2000, blank=True, null=True)
    old_resource_type = models.TextField(verbose_name=_("Data type"), null=True)
    old_format = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Format"))
    old_customfields = JSONField(blank=True, null=True, verbose_name=_("Customfields"))
    old_link = models.URLField(verbose_name=_('Resource Link'), max_length=2000, blank=True, null=True)
    downloads_count = models.PositiveIntegerField(default=0)

    show_tabular_view = models.BooleanField(verbose_name=_('Tabular view'), default=True)
    has_chart = models.BooleanField(verbose_name=_('has chart?'), default=False)
    has_map = models.BooleanField(verbose_name=_('has map?'), default=False)
    has_table = models.BooleanField(verbose_name=_('has table?'), default=False)
    is_chart_creation_blocked = models.BooleanField(verbose_name=_('is chart creation blocked?'), default=False)
    tabular_data_schema = JSONField(null=True, blank=True)
    data_date = models.DateField(null=True, verbose_name=_("Data date"))

    verified = models.DateTimeField(blank=True, default=now, verbose_name=_("Update date"))
    from_resource = models.ForeignKey("self", blank=True, null=True, on_delete=models.DO_NOTHING)
    special_signs = models.ManyToManyField(
        'special_signs.SpecialSign', verbose_name=_('special signs'), blank=True,
        related_name='special_signs_resources')

    def __str__(self):
        return self.title

    @property
    def type_as_str(self):
        if self.type == RESOURCE_TYPE_API and self.forced_api_type:
            return RESOURCE_TYPE_API_CHANGE_LABEL
        return self.get_type_display()
    type_as_str.fget.short_description = _("Type")

    @property
    def media_type(self):
        return self.type or ''

    @property
    def data_rules(self):
        return self.tabular_data_schema

    @property
    def is_data_processable(self):
        return self.format in ('csv', 'tsv', 'xls', 'xlsx', 'ods', 'shp') and self.file

    @property
    def is_linked(self):
        if self.is_imported:
            return self.availability == 'remote'
        return bool(self.link and not self.link.startswith(settings.API_URL))

    @property
    def is_imported(self):
        return self.dataset.is_imported

    @property
    def is_imported_from_ckan(self):
        return self.dataset.is_imported_from_ckan

    @property
    def is_imported_from_xml(self):
        return self.dataset.is_imported_from_xml

    @property
    def maps_and_plots(self):
        return self.tabular_data_schema

    @property
    def category(self):
        return self.dataset.category if self.dataset else ''

    @property
    def comment_editors(self):
        emails = []
        if self.dataset.source:
            emails.extend(self.dataset.source.emails_list)
        else:
            if self.modified_by:
                emails.append(self.modified_by.email)
            else:
                emails.extend(user.email for user in self.dataset.organization.users.all())
        return emails

    @property
    def comment_mail_recipients(self):
        return [config.CONTACT_MAIL, ] + self.comment_editors

    @property
    def csv_file_url(self):
        return '%s%s' % (settings.API_URL, self.csv_file.url) if self.csv_file else None

    @property
    def csv_file_size(self):
        try:
            return self.csv_file.size if self.csv_file else None
        except FileNotFoundError:
            return None

    @property
    def dataset_title_pl(self):
        return self.dataset.title_pl

    @property
    def dataset_title_en(self):
        return self.dataset.title_en

    @property
    def dataset_slug_pl(self):
        return self.dataset.slug_pl

    @property
    def dataset_slug_en(self):
        return self.dataset.slug_en

    @property
    def link_is_valid(self):
        return self.link_tasks_last_status == 'SUCCESS'

    @property
    def file_is_valid(self):
        return self.file_tasks_last_status == 'SUCCESS'

    @property
    def data_is_valid(self):
        return self.data_tasks_last_status == 'SUCCESS'

    @property
    def file_url(self):
        if self.is_imported and self.availability != 'local':
            return self.link
        if self.file:
            _file_url = self.file.url if not self.packed_file else self.packed_file.url
            return '%s%s' % (settings.API_URL, _file_url)
        return ''

    @property
    def file_basename(self):
        return os.path.basename(self.file.name) if self.file else None

    @property
    def file_size(self):
        if self.file:
            try:
                return self.file.size
            except FileNotFoundError:
                return None

    @property
    def frontend_url(self):
        return f'/dataset/{self.dataset.id}/resource/{self.id}'

    @property
    def frontend_absolute_url(self):
        return self._get_absolute_url(self.frontend_url)

    @property
    def formats(self):
        if self.format:
            return '{}{}'.format(self.get_format_display(), ', CSV' if self.csv_file else '')

    @property
    def download_url(self):
        if self.file or self.is_imported:
            return '{}/resources/{}/file'.format(settings.API_URL, self.ident)
        return ''

    @property
    def csv_download_url(self):
        return '{}/resources/{}/csv'.format(settings.API_URL, self.ident) if self.csv_file else None

    @property
    def is_indexable(self):
        if self.type == 'file' and not self.file_is_valid:
            return False

        if self.type in ('api', 'website') and not self.link_is_valid:
            return False

        return True

    @property
    def data(self):
        if not self._data:
            if self.file:
                if self.has_tabular_format():
                    self._data = TabularData(self)
                if self.format == 'shp':
                    self._data = ShpData(self)

        return self._data

    @property
    def data_meta(self):
        if self.data and self.data.available:
            return dict(
                headers_map=self.data.headers_map,
                data_schema=self.data.data_schema,
            )
        return {}

    @property
    def geo_data(self):
        if self.data and self.data.available and self.data.has_geo_data:
            return self.data
        return None

    @property
    def tabular_data(self):
        if self.data and self.data.available and self.show_tabular_view:
            return self.data
        return None

    def increase_openness_score(self):
        csv_file = None
        if self.format in ['xls', 'xlsx'] and not self.is_linked and self.has_data and self.data.table:
            csv_filename = os.path.splitext(self.file_basename)[0]
            headers = self.data.table.schema.field_names
            f = BytesIO()
            csv_out = unicodecsv.writer(f, encoding='utf-8')
            csv_out.writerow(headers)
            for row in self.data.table.iter(cast=False):
                csv_out.writerow(row)
            f.seek(0)
            csv_file = self.save_file(f, f'{csv_filename}.csv')
        self.csv_file = csv_file
        self.save()

    def save_file(self, content, filename):
        dt = self.created.date() if self.created else now().date()
        subdir = dt.isoformat().replace("-", "")
        dest_dir = os.path.join(self.file.storage.location, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content.read())
        return '%s/%s' % (subdir, filename)

    def revalidate(self, **kwargs):
        if not self.link or self.link.startswith(settings.API_URL):
            process_resource_file_task.s(self.id, **kwargs).apply_async(countdown=2)
        else:
            process_resource_from_url_task.s(self.id, **kwargs).apply_async(
                countdown=2)

    @classmethod
    def accusative_case(cls):
        return _("acc: Resource")

    @classmethod
    def get_resources_files(cls):
        resources_files = [x.file.path for x in cls.raw.exclude(file=None).exclude(file='')]
        resources_files.extend(
            [x.packed_file.path for x in cls.raw.exclude(packed_file=None).exclude(packed_file='')])
        resources_files.extend(
            [x.csv_file.path for x in cls.raw.exclude(csv_file=None).exclude(csv_file='')])
        return resources_files

    @classmethod
    def get_all_files(cls, path=settings.RESOURCES_MEDIA_ROOT):
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    yield entry.path
                else:
                    yield from cls.get_all_files(entry.path)
            except OSError as error:
                print('Error calling is_file():', error)
                continue

    @classmethod
    def remove_orphaned_file(cls, file_path, removed_files_root=settings.RESOURCES_FILES_TO_REMOVE_ROOT):
        file_dirname = os.path.basename(os.path.dirname(file_path))
        file_name = os.path.basename(file_path)

        removed_files_dir = os.path.join(removed_files_root, file_dirname)
        if not os.path.exists(removed_files_dir):
            os.makedirs(removed_files_dir)

        removed_file_path = os.path.join(removed_files_dir, file_name)
        return shutil.move(file_path, removed_file_path)

    @classmethod
    def sizeof_fmt(cls, file_size):
        return sizeof_fmt(file_size)

    def get_chart(self, user=None):
        result = None
        if user:
            qs = self.charts.filter(is_removed=False, created_by=user)
            result = qs.filter(is_default=False).last() or qs.filter(is_default=True).last()
        return result or self.charts.filter(is_removed=False, is_default=True).last()

    def get_chart_for_update(self, user, is_default):
        qs = self.charts.filter(is_removed=False, is_default=is_default)
        return qs.filter(created_by=user).last() or (qs.last() if is_default else None)

    def get_openness_score(self, format_=None):
        format_ = format_ or self.format
        if self.csv_file:
            format_ = 'csv'
        if format_ is None:
            return 0
        _, content = content_type_from_file_format(format_.lower())
        return OPENNESS_SCORE.get(content, 0)

    @property
    def file_size_human_readable(self):
        return self.sizeof_fmt(self.file_size or 0)

    @property
    def title_truncated(self):
        title = (self.title[:100] + '..') if len(self.title) > 100 else self.title
        return title

    @property
    def has_data(self):
        try:
            next(self.data.iter(size=1))
            return True
        except Exception:
            return False

    @property
    def visualization_types(self):
        result = []
        if self.is_linked:
            return result
        if self.has_chart:
            result.append('chart')
        if self.has_map:
            result.append('map')
        if self.has_table:
            result.append('table')
        return result

    def verify_rules(self, rules):

        if self.data:
            es_index = self.data.idx_name
            es = es_connections.get_connection()
            validation_results = {}
            for rule in rules.items():
                col, val = rule
                col_type = get_coltype(col, self.tabular_data_schema)
                mappings = self.data.idx.get_field_mapping(fields=f'{col}.*')[self.data.idx._name]['mappings']
                mappings = mappings['doc'].keys() if 'doc' in mappings else []
                col = f'{col}.val' if f'{col}.val' in mappings else col
                if col_type in ["string", "any"]:
                    col += ".keyword"
                try:
                    results = es.search(index=es_index, body=painless_body(col, val), params={"size": 5})
                except Exception:
                    results = {}
                validation_results[rule[0]] = results
            return validation_results

    _data = None

    i18n = TranslationField(fields=("title", "description"))
    tracker = FieldTracker()
    slugify_field = 'title'

    raw = models.Manager()
    objects = ResourceManager()
    deleted = DeletedManager()

    @property
    def chartable(self):
        if self.data and self.data.available and self.data.is_chartable:
            return self
        return None

    @property
    def institution(self):
        return self.dataset.organization

    @property
    def types(self):
        return [self.type, ]

    @property
    def map_preview(self):
        return f"{settings.BASE_URL}/{get_language()}/dataset/{self.dataset.id}/resource/{self.id}/preview/map"

    @property
    def chart_preview(self):
        return f"{settings.BASE_URL}/{get_language()}/dataset/{self.dataset.id}/resource/{self.id}/preview/chart"

    def has_tabular_format(self, extra_formats=tuple()):
        base_formats = ['csv', 'tsv', 'xls', 'xlsx', 'ods']
        base_formats += extra_formats
        return self.format in base_formats

    @property
    def computed_downloads_count(self):
        return ResourceDownloadCounter.objects.filter(
            resource_id=self.pk).aggregate(count_sum=Sum('count'))['count_sum'] or 0

    @property
    def computed_views_count(self):
        return ResourceViewCounter.objects.filter(
            resource_id=self.pk).aggregate(count_sum=Sum('count'))['count_sum'] or 0

    @cached_property
    def data_special_signs(self):
        return self.special_signs.order_by('name')

    @cached_property
    def special_signs_symbols_list(self):
        return list(self.special_signs.values_list('symbol', flat=True))

    def to_rdf_graph(self):
        _schema = self.get_rdf_serializer_schema()
        from collections import namedtuple
        ResourceRDF = namedtuple('ResourceRDF', ['data'])
        obj = ResourceRDF(self)
        return _schema(many=False).dump(obj)

    def as_sparql_create_query(self):
        g = self.to_rdf_graph()
        data = ''.join([f'{s.n3()} {p.n3()} {o.n3()} . ' for s, p, o in g.triples((None, None, None))])
        namespaces_dict = {prefix: ns for prefix, ns in g.namespaces()}
        return 'INSERT DATA { %(data)s }' % {'data': data}, namespaces_dict

    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
        db_table = 'resource'
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


class Chart(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (update_chart_resource,),
        'published': (update_chart_resource,),
        'restored': (update_chart_resource,),
        'removed': (update_chart_resource,),
    }
    # https://docs.djangoproject.com/en/2.2/topics/db/models/#field-name-hiding-is-not-permitted
    # Czemu te pola nie mogły istnieć w tym modelu?
    slug = None
    uuid = None
    views_count = None

    resource = models.ForeignKey(Resource, on_delete=models.DO_NOTHING, related_name="charts")
    chart = JSONField()
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='chart_created'
    )
    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='chart_modified'
    )

    tracker = FieldTracker()

    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()

    class Meta:
        db_table = "resource_chart"

    @property
    def signals_map(self):
        return getattr(self, 'SIGNALS_MAP', {})

    @property
    def is_private(self):
        return not self.is_default

    @property
    def organization(self):
        return self.resource.dataset.organization

    @classmethod
    def get_charts(cls, resource_id, user=None):
        default_charts = cls.objects.filter(resource_id=resource_id, is_default=True).order_by('-id')[:1]
        if user:
            user_charts = cls.objects.filter(
                resource_id=resource_id, is_default=False, created_by=user).order_by('-id')[:1]
            return default_charts.union(user_charts)
        return default_charts

    @classmethod
    def save_chart(cls, user, instance, data):
        data.setdefault('is_default', False)
        if instance:
            instance.chart = data.get('chart')
            if not instance.modified_by or instance.modified_by != user:
                instance.modified_by = user
            instance.save()
        else:
            instance = cls.objects.create(created_by=user, **data)
        return instance

    @classmethod
    def without_i18_fields(cls):
        """Hack which prevents from creation of translated fields (inherited from ExtendedModel)."""
        return True

    def get_unique_slug(self):
        return f"chart-{self.id}"


class ResourceTrash(Resource, metaclass=TrashModelBase):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


@receiver(pre_delete, sender=Chart)
def update_modified_by(sender, instance, *args, **kwargs):
    if 'modified_by' in kwargs and isinstance(kwargs['modified_by'], User):
        instance.modified_by = kwargs.pop('modified_by')


@receiver(update_chart_resource, sender=Chart)
def update_chart_resource_handler(sender, instance, *args, **kwargs):
    Resource.objects.filter(id=instance.resource_id).update(
        has_chart=instance.resource.charts.filter(is_removed=False, is_default=True).exists())

    signal_logger.debug(
        'Reindex resource after chart updated',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'update_chart_resource'
        },
        exc_info=1
    )
    search_signals.update_document_with_related.send(instance.resource._meta.model, instance.resource)


@receiver(pre_save, sender=Resource)
def preprocess_resource(sender, instance, *args, **kwargs):
    signal_logger.debug(
        'Updating openness score',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'pre_save'
        },
        exc_info=1
    )
    if instance.is_imported and instance.created:
        creation_date = instance.created.date()
        if not instance.data_date or instance.data_date < creation_date:
            instance.data_date = creation_date
    instance.openness_score = instance.get_openness_score()
    instance.has_chart = instance.charts.filter(is_removed=False, is_default=True).exists()
    if is_enabled('S22_forced_api_type.be') and instance.id and instance.tracker.has_changed('forced_api_type'):
        if instance.forced_api_type and instance.type == RESOURCE_TYPE_WEBSITE:
            instance.type = RESOURCE_TYPE_API
        elif not instance.forced_api_type and instance.type == RESOURCE_TYPE_API:
            instance.type = RESOURCE_TYPE_WEBSITE


@receiver(post_save, sender=Resource)
def update_dataset_verified(sender, instance, *args, **kwargs):
    max_created = instance.dataset.resources.filter(status=Dataset.STATUS.published).only("created").aggregate(
        Max('created')).get('created__max')
    if max_created:
        Dataset.objects.filter(pk=instance.dataset.id).update(verified=max_created)  # we don't want signals here
    else:
        Dataset.objects.filter(pk=instance.dataset.id).update(verified=instance.dataset.created)


@receiver(revalidate_resource, sender=Resource)
def process_resource(sender, instance, *args, **kwargs):
    signal_logger.debug(
        'Processing resource',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'pre_save'
        },
        exc_info=1
    )

    if any([instance.tracker.has_changed('link'), instance.tracker.has_changed('availability')]):
        process_resource_from_url_task.s(instance.id).apply_async(countdown=2)
    elif instance.tracker.has_changed('file') or instance.state_restored:
        process_resource_file_task.s(instance.id).apply_async(countdown=2)


def update_dataset_watcher(sender, instance, *args, state=None, **kwargs):
    state = 'm2m_{}'.format(state)

    signal_logger.debug(
        '{} {}'.format(sender._meta.object_name, state),
        extra={
            'sender': '{}.{}'.format(sender._meta.app_label, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.app_label, instance._meta.object_name),
            'instance_id': instance.id,
            'state': state,
            'signal': 'notify_{}'.format(state)
        },
        exc_info=1
    )
    update_model_watcher_task.s(
        instance.dataset._meta.app_label,
        instance.dataset._meta.object_name,
        instance.id,
        obj_state=state
    ).apply_async(
        countdown=1
    )


def resource_special_signs_changed(sender, instance, *args, **kwargs):
    process_resource_file_data_task.s(instance.id).apply_async()


core_signals.notify_published.connect(update_watcher, sender=Resource)
core_signals.notify_restored.connect(update_watcher, sender=Resource)
core_signals.notify_updated.connect(update_watcher, sender=Resource)
core_signals.notify_removed.connect(update_watcher, sender=Resource)
core_signals.notify_restored.connect(update_dataset_watcher, sender=Resource)
core_signals.notify_updated.connect(update_dataset_watcher, sender=Resource)
core_signals.notify_removed.connect(update_dataset_watcher, sender=Resource)

core_signals.notify_published.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_restored.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_updated.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_removed.connect(update_watcher, sender=ResourceTrash)

core_signals.notify_m2m_added.connect(resource_special_signs_changed, sender=Resource.special_signs.through)
core_signals.notify_m2m_removed.connect(resource_special_signs_changed, sender=Resource.special_signs.through)
core_signals.notify_m2m_cleaned.connect(resource_special_signs_changed, sender=Resource.special_signs.through)


@task_prerun.connect(sender=validate_link)
@task_prerun.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_prerun_handler(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()
        resource.link_tasks.add(result_task)
    except Exception:
        pass


@task_prerun.connect(sender=process_resource_file_task)
def process_resource_file_task_prerun_handler(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()
        resource.file_tasks.add(result_task)
    except Exception:
        pass


@task_prerun.connect(sender=process_resource_file_data_task)
def process_resource_file_data_task_prerun_handler(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        if resource.is_data_processable:
            result_task = TaskResult.objects.get_task(task_id)
            result_task.save()
            resource.data_tasks.add(result_task)
    except Exception:
        pass


def update_resource(task_id, **kwargs):  # noqa: C901
    update_data_tasks_last_status = kwargs.get('update_data_tasks_last_status', False)
    update_file_tasks_last_status = kwargs.get('update_file_tasks_last_status', False)
    update_link_tasks_last_status = kwargs.get('update_link_tasks_last_status', False)
    update_has_map = kwargs.get('update_has_map', False)
    update_has_table = kwargs.get('update_has_table', False)
    update_verification_date = kwargs.get('kwargs', {}).get("update_verification_date", True)
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.raw.get(pk=resource_id)
        task_result = TaskResult.objects.get_task(task_id)
        data = {}
        if update_data_tasks_last_status:
            data['data_tasks_last_status'] = task_result.status
        if update_file_tasks_last_status:
            data['file_tasks_last_status'] = task_result.status
        if update_link_tasks_last_status:
            data['link_tasks_last_status'] = task_result.status
        if update_verification_date and resource.verified < task_result.date_done:
            data['verified'] = task_result.date_done
        if update_has_map or update_has_table:
            try:
                retval = json.loads(kwargs['retval']) if isinstance(kwargs['retval'], str) else {}
            except json.JSONDecodeError:
                retval = {}
            indexed = retval.get('indexed')
            if update_has_map:
                data['has_map'] = bool(resource.data and resource.data.has_geo_data and indexed)
            if update_has_table:
                data['has_table'] = bool(resource.has_tabular_format(['shp']) and indexed)
        if data:
            Resource.raw.filter(pk=resource_id).update(**data)  # we don't want signals here - just updates.
    except Exception:
        pass


@task_postrun.connect(sender=validate_link)
@task_postrun.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_postrun_handler(sender, task_id, task, signal, **kwargs):
    update_resource(task_id, update_link_tasks_last_status=True, **kwargs)


@task_postrun.connect(sender=process_resource_file_task)
def process_resource_file_task_postrun_handler(sender, task_id, task, signal, **kwargs):
    update_resource(task_id, update_file_tasks_last_status=True, **kwargs)


@task_postrun.connect(sender=process_resource_file_data_task)
def process_resource_file_data_task_postrun_handler(sender, task_id, task, signal, **kwargs):
    update_resource(task_id, update_data_tasks_last_status=True, update_has_map=True, update_has_table=True, **kwargs)


@task_success.connect(sender=validate_link)
@task_success.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_success_handler(sender, result, **kwargs):
    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=validate_link)
@task_failure.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_failure_handler(sender, task_id, exception, args, traceback, einfo, signal,
                                                   **kwargs):
    resource_id = int(args[0])
    resource = Resource.objects.get(pk=resource_id)
    result = {
        'exc_type': exception.__class__.__name__,
        'exc_message': str(exception),
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type
    }

    result_task = TaskResult.objects.get_task(task_id)
    if sender.request.is_eager:
        result_task.status = 'FAILURE'
    result_task.result = json.dumps(result)
    result_task.save()
    update_resource(task_id, **kwargs)


@task_success.connect(sender=process_resource_file_task)
def process_resource_file_task_success_handler(sender, result, *args, **kwargs):
    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=process_resource_file_task)
def process_resource_file_task_failure_handler(sender, task_id, exception, args, traceback, einfo, signal, **kwargs):
    resource_id = int(args[0])
    resource = Resource.objects.get(pk=resource_id)
    result = {
        'exc_type': exception.__class__.__name__,
        'exc_message': str(exception),
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type
    }

    result_task = TaskResult.objects.get_task(task_id)
    if sender.request.is_eager:
        result_task.status = 'FAILURE'
    result_task.result = json.dumps(result)
    result_task.save()
    update_resource(task_id, **kwargs)


@task_success.connect(sender=process_resource_file_data_task)
def process_resource_file_data_task_success_handler(sender, result, *args, **kwargs):
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        data = {}
    indexed = data.get('indexed')
    resource_id = data.get('resource_id')
    if indexed and resource_id:
        resource = Resource.raw.filter(id=resource_id).first()
        if resource:
            resource.increase_openness_score()

    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=process_resource_file_data_task)
def process_resource_file_data_task_failure_handler(sender, task_id, exception, args, traceback, einfo, signal,
                                                    **kwargs):
    resource_id = int(args[0])
    resource = Resource.objects.get(pk=resource_id)
    result = {
        'exc_type': exception.__class__.__name__,
        'exc_message': str(exception),
        'uuid': str(resource.uuid),
        'link': resource.link,
        'format': resource.format,
        'type': resource.type,
    }

    result_task = TaskResult.objects.get_task(task_id)
    if sender.request.is_eager:
        result_task.status = 'FAILURE'
    result_task.result = json.dumps(result)
    result_task.save()
    update_resource(task_id, **kwargs)
