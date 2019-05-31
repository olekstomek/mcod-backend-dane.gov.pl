import json
import logging
import os
import uuid
from collections import OrderedDict
from datetime import datetime

import magic
from celery.signals import task_prerun, task_failure, task_success, task_postrun
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult as TaskResultOrig
from elasticsearch import exceptions as es_exceptions
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, DocType
from elasticsearch_dsl import field as dsl_field
from elasticsearch_dsl.connections import Connections
from goodtables import validate as validate_table
from mimeparse import parse_mime_type
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField
from tableschema import Table

from mcod.core import signals as core_signals
from mcod.core import storages
from mcod.core.api import fields as api_fields
from mcod.core.api.search import signals as search_signals
from mcod.core.api.search.analyzers import polish_analyzer
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel, update_watcher
from mcod.core.utils import sizeof_fmt
from mcod.datasets.models import Dataset
from mcod.lib.utils import content_type_from_file_format
from mcod.resources.error_mappings import recommendations, messages
from mcod.resources.signals import revalidate_resource
from mcod.resources.tasks import process_resource_from_url_task, process_resource_file_task, \
    process_resource_file_data_task

User = get_user_model()

es_connections = Connections()
es_connections.configure(**settings.ELASTICSEARCH_DSL)

STATUS_CHOICES = [
    ('published', _('Published')),
    ('draft', _('Draft'))
]

OPENNESS_SCORE = {_type: os for _, _type, _, os in settings.SUPPORTED_CONTENT_TYPES}

signal_logger = logging.getLogger('signals')

_schema2doc_map = {
    'integer': dsl_field.Float(),
    'number': dsl_field.ScaledFloat(scaling_factor=100),
    'string': dsl_field.Text(
        analyzer=polish_analyzer,
        fields={
            'raw': dsl_field.Text(),
        }
    ),
    'any': dsl_field.Text(
        analyzer=polish_analyzer,
        fields={
            'raw': dsl_field.Text(),
        }
    ),
    'boolean': dsl_field.Boolean(),
    'date': dsl_field.Date(),
    'datetime': dsl_field.Date(),
    'time': dsl_field.Date()
}

_schema_to_api_field = {
    'integer': api_fields.Number,
    'number': api_fields.Number,
    'string': api_fields.String,
    'any': api_fields.String,
    'boolean': api_fields.Boolean,
    'date': api_fields.DateTime,
    'datetime': api_fields.DateTime,
    'time': api_fields.Time
}


class ResourceDataValidationError(Exception):
    pass


def supported_formats_choices():
    data = []
    for item in settings.SUPPORTED_CONTENT_TYPES:
        data.extend(item[2])

    return [(i, i.upper()) for i in sorted(list(set(data)))]


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


RESOURCE_TYPE = (
    ('file', _('File')),
    ('website', _('Web Site')),
    ('api', _('API')),
)


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

    @property
    def message(self):
        result = json.loads(self.result) if self.result else {}
        if isinstance(result, str):
            result = json.loads(result)
        if result.get('exc_message', "").startswith('[{'):
            return [msg or "" for msg in self.values_from_result(result, 'message')]
        else:
            return [messages.get(self._find_error_code(result), "Nierozpoznany błąd walidacji")]

    @property
    def recommendation(self):
        result = json.loads(self.result) if self.result else {}
        if isinstance(result, str):
            result = json.loads(result)
        try:
            codes = list(self.values_from_result(result, 'code'))
        except Exception:
            codes = [self._find_error_code(result)]
        return [recommendations.get(code, "Skontaktuj się z administratorem systemu.") for code in codes]

    @staticmethod  # noqa
    def _find_error_code(result):
        if 'exc_type' not in result:
            return None

        if result['exc_message'] == "The 'file' attribute has no file associated with it.":
            return 'no-file-associated'

        if result['exc_type'] == 'OperationalError':
            if result['exc_message'].startswith("could not connect to server: Connection refused") \
                    or result['exc_message'].find("remaining connection slots are reserved") > 0:
                return 'connection-error'

        if result['exc_type'] == 'Exception':
            if result['exc_message'] == 'unknown-file-format':
                return result['exc_message']

        if result['exc_type'] == 'InvalidResponseCode':
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

        if result['exc_type'] == 'ConnectionError':
            if result['exc_message'].startswith("('Connection aborted."):
                return 'connection-aborted'
            if result['exc_message'].find('Failed to establish a new connection') > -1:
                return 'failed-new-connection'

        return result['exc_type']

    class Meta:
        proxy = True


class TabularData(object):
    def __init__(self, resource):
        self.resource = resource
        idx_prefix = getattr(settings, 'ELASTICSEARCH_INDEX_PREFIX', None)
        self.idx_name = 'resource-{}'.format(self.resource.id)
        if idx_prefix:
            self.idx_name = '{}-{}'.format(idx_prefix, self.idx_name)
        self._table_cache = None
        self._schema_cache = None
        self._idx_cache = None
        self._headers_map_cache = None
        self._doc_cache = None

    @property
    def available(self):
        if not self.idx.exists():
            return False

        task = self.resource.data_tasks.last()
        status = task.status if task else 'NOT_AVAILABLE'
        return True if status == 'SUCCESS' else False

    @property
    def doc(self):
        if not self._doc_cache:
            _fields, _map = {}, {}
            for idx, _f in enumerate(self.schema['fields']):
                alias_name = _f['name']
                field_name = 'col{}'.format(idx + 1)
                _field = _schema2doc_map[_f['type']]
                _map[field_name] = alias_name
                _fields[field_name] = _field

            _fields['resource'] = dsl_field.Nested(
                properties={
                    'id': dsl_field.Integer(),
                    'title': dsl_field.Text(
                        analyzer=polish_analyzer,
                        fields={'raw': dsl_field.Keyword()})
                }
            )

            _fields['updated_at'] = dsl_field.Date()
            _fields['row_no'] = dsl_field.Long()

            doc = type(self.idx_name, (DocType,), _fields)
            doc._doc_type.index = self.idx_name
            doc._doc_type.mapping._meta['_meta'] = {'headers': _map}
            doc._doc_type.mapping._meta['_meta']
            self._doc_cache = doc
        return self._doc_cache

    def get_api_fields(self):
        _fields = {}
        for _f in self.schema['fields']:
            field_name = self.headers_map[_f['name']]
            field_cls = _schema_to_api_field[_f['type']]
            _fields[field_name] = field_cls(description="Value of *{}* column".format(_f['name']))

        return _fields

    @staticmethod
    def _row_2_dict(row):
        return {
            'col{}'.format(idx + 1): value for idx, value in enumerate(row)
        }

    @staticmethod
    def _get_row_id(row):
        if isinstance(row, dict):
            row = row.values()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, '+|+'.join(str(i)[:10000] for i in row)))

    def get_schema(self, use_aliases=True):
        _schema = self.schema
        if use_aliases:
            _schema = dict(_schema)
            headers = self.headers_map
            _fields = [
                {
                    'name': headers[item['name']],
                    'type': item['type'],
                    'format': item['format']
                } for item in _schema['fields']
            ]
            _schema['fields'] = _fields

        return _schema

    @property
    def schema(self, use_headers=True):
        if not self.resource.file:
            raise ValidationError(_('File does not exist'))

        if self.resource.format not in ('csv', 'tsv', 'xls', 'xlsx', 'ods'):
            raise ValidationError(_('Invalid file type'))

        if not self._schema_cache:
            _schema = self.resource.tabular_data_schema or None
            if not _schema:
                _table = Table(self.resource.file.path,
                               ignore_blank_headers=True,
                               format=self.resource.format,
                               encoding=self.resource.file_encoding or 'utf-8')
                _schema = _table.infer(limit=5000)
            self._schema_cache = _schema

        return self._schema_cache

    def validate(self):
        report = validate_table(self.resource.file.path,
                                skip_checks=('blank-row', 'blank-header', 'duplicate-row'),
                                error_limit=10,
                                infer_schema=True,
                                format=self.resource.format,
                                preset='table',
                                encoding=self.resource.file_encoding,
                                )
        if not report['valid']:
            raise ResourceDataValidationError(report['tables'][0]['errors'])

        return report

    @property
    def idx(self):
        if not self._idx_cache:
            self._idx_cache = Index(self.idx_name)
        return self._idx_cache

    @property
    def headers_map(self):
        if not self._headers_map_cache:
            try:
                headers = self.idx.get_mapping()[self.idx_name]['mappings']['doc']['_meta']['headers']
            except (es_exceptions.NotFoundError, KeyError):
                headers = self.doc._doc_type.mapping._meta['_meta']['headers']
            headers = {item: key for key, item in headers.items()}
            self._headers_map_cache = OrderedDict(
                sorted(headers.items(), key=lambda x: int(x[1].strip('col'))))
        return self._headers_map_cache

    @property
    def headers(self):
        return [header[0] for header in self.headers_map]

    @property
    def qs(self):
        return self.doc.search()

    def iter(self, qs=None, from_=0, size=25, as_list=False):
        _search = qs or self.qs
        _search = _search.extra(from_=from_, size=size)
        results = _search.execute()
        for result in results.hits:
            yield [result[field] for field in list(result)] if as_list else result

    @property
    def table(self):
        if not self._table_cache:
            schema = self.schema or None
            self._table_cache = Table(self.resource.file.path,
                                      ignore_blank_headers=True,
                                      schema=schema,
                                      format=self.resource.format,
                                      encoding=self.resource.file_encoding or 'utf-8')
        return self._table_cache

    def _docs_iter(self, doc):
        for row_no, row in enumerate(self.table.iter(keyed=True)):
            if not row:
                continue

            if isinstance(row, (list, tuple)):
                row = self._row_2_dict(row)
            r = {self.headers_map.get(field_name, field_name): item for field_name, item in row.items()}
            row_id = self._get_row_id(r)
            r['updated_at'] = datetime.now()
            r['row_no'] = row_no + 1
            r['resource'] = {
                'id': self.resource.id,
                'title': self.resource.title
            }
            d = doc(**r)
            d.meta.id = row_id
            yield d

    def index(self, force=False, chunk_size=500):
        doc = self.doc
        if force:
            self.idx.delete(ignore_unavailable=True)

        self.idx.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)
        self.idx.mapping(doc._doc_type.mapping)
        if not self.idx.exists():
            self.idx.create()

        es = es_connections.get_connection()
        success, failed = bulk(es,
                               (d.to_dict(True) for d in self._docs_iter(doc)),
                               index=self.idx_name,
                               doc_type=doc._doc_type.name,
                               chunk_size=chunk_size,
                               stats_only=True
                               )

        if success:
            self.idx.flush()

        return success, failed


class Resource(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_updated
        ),
        'published': (
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_published
        ),
        'restored': (
            revalidate_resource,
            search_signals.update_document_with_related,
            core_signals.notify_restored
        ),
    }
    file = models.FileField(verbose_name=_("File"), storage=storages.get_storage('resources'),
                            upload_to='%Y%m%d',
                            max_length=2000, blank=True, null=True)
    packed_file = models.FileField(verbose_name=_("Packed file"), storage=storages.get_storage('resources'),
                                   upload_to='%Y%m%d',
                                   max_length=2000, blank=True, null=True)
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

    old_file = models.FileField(verbose_name=_("File"), storage=storages.get_storage('resources'), upload_to='',
                                max_length=2000, blank=True, null=True)
    old_resource_type = models.TextField(verbose_name=_("Data type"), null=True)
    old_format = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Format"))
    old_customfields = JSONField(blank=True, null=True, verbose_name=_("Customfields"))
    old_link = models.URLField(verbose_name=_('Resource Link'), max_length=2000, blank=True, null=True)
    downloads_count = models.PositiveIntegerField(default=0)

    show_tabular_view = models.BooleanField(verbose_name=_('Tabular view'), default=True)
    tabular_data_schema = JSONField(null=True, blank=True)
    data_date = models.DateField(null=True, verbose_name=_("Data date"))

    verified = models.DateTimeField(blank=True, default=now, verbose_name=_("Update date"))

    def __str__(self):
        return self.title

    @property
    def media_type(self):
        return self.type or ''

    @property
    def category(self):
        return self.dataset.category if self.dataset else ''

    @property
    def link_is_valid(self):
        task = self.link_tasks.last()
        return task.status if task else 'NOT_AVAILABLE'

    @property
    def file_is_valid(self):
        task = self.file_tasks.last()
        return task.status if task else 'NOT_AVAILABLE'

    @property
    def data_is_valid(self):
        task = self.data_tasks.last()
        return task.status if task else 'NOT_AVAILABLE'

    @property
    def file_url(self):
        if self.file:
            _file_url = self.file.url if not self.packed_file else self.packed_file.url
            return '%s%s' % (settings.API_URL, _file_url)
        return ''

    @property
    def file_size(self):
        return self.file.size if self.file else None

    @property
    def download_url(self):
        if self.file:
            return '{}/resources/{}/file'.format(settings.API_URL, self.ident)
        return ''

    @property
    def is_indexable(self):
        if self.type == 'file' and not self.file_is_valid:
            return False

        if self.type in ('api', 'website') and not self.link_is_valid:
            return False

        return True

    @property
    def tabular_data(self):
        if not self._tabular_data:
            if self.format in ('csv', 'tsv', 'xls', 'xlsx', 'ods') and self.file:
                self._tabular_data = TabularData(self)
        return self._tabular_data

    def index_tabular_data(self, force=False):
        self.tabular_data.validate()
        return self.tabular_data.index(force=force)

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
        if not self.link or self.link.startswith(settings.BASE_URL):
            process_resource_file_task.s(self.id, **kwargs).apply_async(countdown=2)
        else:
            process_resource_from_url_task.s(self.id, **kwargs).apply_async(countdown=2)

    @classmethod
    def accusative_case(cls):
        return _("acc: Resource")

    @property
    def _openness_score(self):
        if not self.format:
            return 0
        _, content = content_type_from_file_format(self.format.lower())
        return OPENNESS_SCORE.get(content, 0)

    @property
    def file_size_human_readable(self):
        file_size = self.file_size or 0
        return sizeof_fmt(file_size)

    @property
    def title_truncated(self):
        title = (self.title[:100] + '..') if len(self.title) > 100 else self.title
        return title

    _tabular_data = None

    i18n = TranslationField(fields=("title", "description"))
    tracker = FieldTracker()
    slugify_field = 'title'

    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()

    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
        db_table = 'resource'
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


class ResourceTrash(Resource):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


@receiver(pre_save, sender=Resource)
def preprocess_resource(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Updating openness score',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'pre_save'
        },
        exc_info=1
    )
    instance.openness_score = instance._openness_score


@receiver(post_save, sender=Resource)
def update_dataset_verified(sender, instance, *args, **kwargs):
    max_verified = instance.dataset.resources.filter(status=Dataset.STATUS.published).only("verified").aggregate(
        Max('verified')).get('verified__max')
    if max_verified:
        Dataset.objects.filter(pk=instance.dataset.id).update(verified=max_verified)  # we don't want signals here
    else:
        Dataset.objects.filter(pk=instance.dataset.id).update(verified=instance.dataset.created)


@receiver(revalidate_resource, sender=Resource)
def process_resource(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Processing resource',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'pre_save'
        },
        exc_info=1
    )

    if instance.tracker.has_changed('link'):
        process_resource_from_url_task.s(instance.id).apply_async(countdown=2)
    elif instance.tracker.has_changed('file'):
        process_resource_file_task.s(instance.id).apply_async(countdown=2)


core_signals.notify_published.connect(update_watcher, sender=Resource)
core_signals.notify_restored.connect(update_watcher, sender=Resource)
core_signals.notify_updated.connect(update_watcher, sender=Resource)
core_signals.notify_removed.connect(update_watcher, sender=Resource)

core_signals.notify_published.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_restored.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_updated.connect(update_watcher, sender=ResourceTrash)
core_signals.notify_removed.connect(update_watcher, sender=ResourceTrash)


@task_prerun.connect(sender=process_resource_from_url_task)
def append_link_task(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()
        resource.link_tasks.add(result_task)
    except Exception:
        pass


@task_prerun.connect(sender=process_resource_file_task)
def append_file_task(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()
        resource.file_tasks.add(result_task)
    except Exception:
        pass


@task_prerun.connect(sender=process_resource_file_data_task)
def append_data_task(sender, task_id, task, signal, **kwargs):
    try:
        resource_id = int(kwargs['args'][0])
        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()
        resource.data_tasks.add(result_task)
    except Exception:
        pass


def update_verified(task_id, **kwargs):
    resource_id = int(kwargs['args'][0])
    resource = Resource.objects.get(pk=resource_id)
    result_task = TaskResult.objects.get_task(task_id)
    if resource.verified < result_task.date_done:
        # we don't want signals here - just updates:
        Resource.objects.filter(pk=resource_id).update(verified=result_task.date_done)
        if resource.status == Dataset.STATUS.published and resource.dataset.status == Dataset.STATUS.published:
            Dataset.objects.filter(pk=resource.dataset.id).update(verified=result_task.date_done)


@task_postrun.connect(sender=process_resource_from_url_task)
def handle_set_verified_after_link_task(sender, task_id, task, signal, **kwargs):
    try:
        update_verified(task_id, **kwargs)
    except Exception:
        pass


@task_postrun.connect(sender=process_resource_file_task)
def handle_set_verified_after_file_task(sender, task_id, task, signal, **kwargs):
    try:
        update_verified(task_id, **kwargs)
    except Exception:
        pass


@task_postrun.connect(sender=process_resource_file_data_task)
def handle_set_verified_after_data_task(sender, task_id, task, signal, **kwargs):
    try:
        update_verified(task_id, **kwargs)
    except Exception:
        pass


@task_success.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_success(sender, result, **kwargs):
    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=process_resource_from_url_task)
def process_resource_from_url_task_failure(sender, task_id, exception, args, traceback, einfo, signal, **kwargs):
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
    update_verified(task_id, **kwargs)


@task_success.connect(sender=process_resource_file_task)
def save_result_on_verify_resource_file_task_success(sender, result, *args, **kwargs):
    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=process_resource_file_task)
def save_result_on_verify_resource_file_task_failure(sender, task_id, exception, args, traceback, einfo, signal,
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
    update_verified(task_id, **kwargs)


@task_success.connect(sender=process_resource_file_data_task)
def save_result_on_process_resource_file_data_task_task_success(sender, result, *args, **kwargs):
    if sender.request.is_eager:
        result_task = TaskResult.objects.get_task(sender.request.id)
        result_task.result = json.dumps(result)
        result_task.status = 'SUCCESS'
        result_task.save()


@task_failure.connect(sender=process_resource_file_data_task)
def save_result_on_process_resource_file_data_task_task_failure(sender, task_id, exception, args, traceback, einfo,
                                                                signal,
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
    update_verified(task_id, **kwargs)
