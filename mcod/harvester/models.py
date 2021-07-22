import logging
import os
import pprint
from urllib.parse import urlencode

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files import File
from django.core.validators import validate_email
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.fields import AutoCreatedField
from model_utils.models import SoftDeletableModel, TimeStampedModel
from dateutil.relativedelta import relativedelta
from marshmallow import ValidationError as SchemaValidationError

from mcod import settings
from mcod.categories.models import Category
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import TrashModelBase
from mcod.harvester.managers import DataSourceManager
from mcod.harvester.tasks import send_import_report_mail_task
from mcod.harvester.utils import get_remote_xml_hash, make_request, retrieve_to_file, validate_xml_url
from mcod.organizations.models import Organization
from mcod.unleash import is_enabled


logger = logging.getLogger('mcod')

OLD_CATEGORY_TITLE_2_DCAT_CATEGORY_CODE = {
    'Rolnictwo': 'AGRI',
    'Biznes i Gospodarka': 'ECON',
    'Budżet i Finanse Publiczne': 'ECON',
    'Kultura': 'EDUC',
    'Nauka i Oświata': 'EDUC',
    'Sport i Turystyka': 'EDUC',
    'Środowisko': 'ENVI',
    'Administracja Publiczna': 'GOVE',
    'Zdrowie': 'HEAL',
    'Bezpieczeństwo': 'JUST',
    'Praca i Pomoc Społeczna': 'SOCI',
    'Społeczeństwo': 'SOCI',
    'Regiony i miasta': 'REGI',
}


def validate_emails_list(value):
    emails_list = [x.strip() for x in value.split(',') if x]
    if not emails_list:
        raise ValidationError(_('This field is required!'))
    for item in emails_list:
        validate_email(item)


FREQUENCY_CHOICES = (
    (1, _('every day')),
    (7, _('every week')),
    (30, _('every month')),
    (90, _('every quarter')),
)

STATUS_OK = 'ok'
STATUS_OK_PARTIAL = 'ok-partial'
STATUS_ERROR = 'error'
IMPORT_STATUS_CHOICES = (
    (STATUS_OK, 'OK'),
    (STATUS_OK_PARTIAL, _('OK - partial import')),
    (STATUS_ERROR, _('Error')),
)


class DataSource(SoftDeletableModel, TimeStampedModel):
    """Model of data source."""
    INSTITUTION_TYPE_CHOICES = Organization.INSTITUTION_TYPE_CHOICES
    if is_enabled('S23_harvester_dcat_endpoint.be'):
        SOURCE_TYPE_CHOICES = (
            ('ckan', 'CKAN'),
            ('xml', 'XML'),
            ('dcat', 'DCAT-AP')
        )
    else:
        SOURCE_TYPE_CHOICES = (
            ('ckan', 'CKAN'),
            ('xml', 'XML'),
        )
    STATUS_CHOICES = (
        ('active', _('active')),
        ('inactive', _('inactive')),
    )
    name = models.CharField(max_length=255, verbose_name=_('name'))
    description = models.TextField(verbose_name=_('description'))
    frequency_in_days = models.PositiveIntegerField(choices=FREQUENCY_CHOICES, default=7, verbose_name=_('frequency'))
    status = models.CharField(max_length=8, verbose_name=_('status'), choices=STATUS_CHOICES)
    license_condition_db_or_copyrighted = models.TextField(
        blank=True, verbose_name=_('data use rules'))
    institution_type = models.CharField(
        max_length=7, blank=True, choices=INSTITUTION_TYPE_CHOICES, default=INSTITUTION_TYPE_CHOICES[2][0],
        verbose_name=_('Default type for newly created institutions'))
    source_type = models.CharField(
        max_length=10, choices=SOURCE_TYPE_CHOICES, verbose_name=_('source type'))
    emails = models.TextField(verbose_name=_('e-mail'), validators=[validate_emails_list])
    last_activation_date = models.DateTimeField(verbose_name=_('last activation date'), null=True, blank=True)
    category = models.ForeignKey(
        'categories.Category', on_delete=models.CASCADE, related_name='category_datasources',
        verbose_name=_('category'), blank=True, null=True, limit_choices_to=Q(code=''))

    categories = models.ManyToManyField('categories.Category',
                                        db_table='data_source_category',
                                        verbose_name=_('Categories'),
                                        related_name='data_sources',
                                        related_query_name="data_source",
                                        blank=True,
                                        limit_choices_to=~Q(code=''))

    created = AutoCreatedField(_('creation date'))
    created_by = models.ForeignKey(
        'users.User', on_delete=models.DO_NOTHING, related_name='created_datasources', verbose_name=_('created by'))
    modified_by = models.ForeignKey(
        'users.User', models.DO_NOTHING, null=True, blank=True, verbose_name=_('modified by'),
        related_name='modified_datasources',
    )
    last_import_status = models.CharField(
        max_length=50, verbose_name=_('last import status'), choices=IMPORT_STATUS_CHOICES, blank=True)
    last_import_timestamp = models.DateTimeField(verbose_name=_('last import timestamp'), null=True, blank=True)

    # CKAN related fields.
    portal_url = models.URLField(verbose_name=_('portal url'), blank=True)
    api_url = models.URLField(verbose_name=_('api url'), blank=True)

    # XML related fields.
    xml_url = models.URLField(verbose_name=_('XML url'), blank=True)
    source_hash = models.CharField(max_length=32, verbose_name=_('source hash'), blank=True)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='organization_datasources',
        verbose_name=_('Institution'), null=True, blank=True
    )

    sparql_query = models.TextField(blank=True, null=True, verbose_name=_('Sparql query'))

    tracker = FieldTracker()
    raw = models.Manager()
    objects = DataSourceManager()
    deleted = DeletedManager()

    class Meta:
        verbose_name = _('data source')
        verbose_name_plural = _('data sources')

    def __str__(self):
        return self.name

    @property
    def categories_list_as_html(self):
        categories = self.categories.all()
        return mark_safe('<br>'.join(category.title for category in categories)) if categories else '-'

    @cached_property
    def category_model(self):
        return apps.get_model('categories.Category')

    @cached_property
    def dataset_model(self):
        return apps.get_model('datasets.Dataset')

    @cached_property
    def organization_model(self):
        return apps.get_model('organizations.Organization')

    @cached_property
    def resource_model(self):
        return apps.get_model('resources.Resource')

    @cached_property
    def tag_model(self):
        return apps.get_model('tags.Tag')

    @cached_property
    def user_model(self):
        return apps.get_model('users.User')

    @cached_property
    def import_settings(self):
        try:
            return settings.HARVESTER_IMPORTERS[self.source_type]
        except KeyError:
            raise ImproperlyConfigured(f'settings.HARVESTER_SETTINGS should contain {self.source_type} key!')

    @cached_property
    def import_user(self):
        import_user_email = 'automatic_import@mc.gov.pl'
        return self.user_model.objects.filter(email=import_user_email).first() or self.user_model.objects._create_user(
            email=import_user_email)

    @cached_property
    def import_func_kwargs(self):
        if self.is_xml:
            return {'url': self.xml_url}
        elif self.is_dcat:
            return {'api_url': self.api_url, 'query': self.sparql_query}
        params = self.import_settings.get('API_URL_PARAMS')
        return {'url': f'{self.api_url}?{urlencode(params)}' if params else self.api_url}

    @cached_property
    def url(self):
        if self.is_xml:
            return self.xml_url
        elif self.is_ckan:
            return self.portal_url
        elif self.is_dcat:
            return self.api_url

    @property
    def emails_list(self):
        return list(set(filter(None, [x.strip() for x in self.emails.split(',')])))

    @property
    def is_ckan(self):
        return self.source_type == 'ckan'

    @property
    def is_xml(self):
        return self.source_type == 'xml'

    @property
    def is_dcat(self):
        return self.source_type == 'dcat'

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def next_import_date(self):
        if self.last_import_timestamp:
            return (self.last_import_timestamp + relativedelta(
                days=self.frequency_in_days)).replace(hour=3, minute=0, second=0, microsecond=0)

    @property
    def title(self):
        return self.name

    @property
    def update_frequency(self):
        return next(freq[1] for freq in FREQUENCY_CHOICES if freq[0] == self.frequency_in_days)

    def _validate_ckan_type(self):
        errors = {}
        required_msg = _('This field is required.')
        if not is_enabled('S19_DCAT_categories.be'):
            if not self.category:
                errors.update({'category': required_msg})
        if not self.portal_url:
            errors.update({'portal_url': required_msg})
        if not self.api_url:
            errors.update({'api_url': required_msg})
        if self.api_url:
            msg = _('Inaccessible API!')
            try:
                response = make_request(self.api_url)
                if not response.ok or 'application/json' not in response.headers.get('Content-Type', ''):
                    errors.update({'api_url': msg})
            except Exception as exc:
                logger.debug(exc)
                errors.update({'api_url': msg})
        if errors:
            raise ValidationError(errors)

    def _validate_xml_type(self):
        required_msg = _('This field is required.')
        if not self.organization:
            raise ValidationError({'organization': required_msg})
        if self.import_settings.get('ONE_DATASOURCE_PER_ORGANIZATION', False):
            organization_datasources = DataSource.objects.filter(organization=self.organization)
            if self.id:
                organization_datasources = organization_datasources.exclude(id=self.id)
            if organization_datasources.exists():
                raise ValidationError({'organization': _('Data source for this institution already exists!')})
        if not self.xml_url:
            raise ValidationError({'xml_url': required_msg})

    def _validate_dcat_type(self):
        required_msg = _('This field is required.')
        if not self.organization:
            raise ValidationError({'organization': required_msg})

    def validate_xml_url(self):
        xml_hash_url, xml_hash = get_remote_xml_hash(self.xml_url)
        if not xml_hash:
            msg = _('Remote hash not found in %(url)s location!') % {'url': xml_hash_url}
            raise ValidationError(msg)
        if xml_hash == self.source_hash:
            raise ValidationError(
                f'Download of xml stopped! Remote hash ({xml_hash}) is the same as local ({self.source_hash}).')
        try:
            filename, source_hash = validate_xml_url(self.xml_url)
        except Exception as exc:
            raise ValidationError(exc)
        if source_hash:
            self.source_hash = source_hash

    def clean(self):
        if self.is_ckan:
            self._validate_ckan_type()
        elif self.is_xml:
            self._validate_xml_type()
        elif self.is_dcat:
            self._validate_dcat_type()

    def import_needed(self):
        if not self.last_import_timestamp:
            return True
        return self.next_import_date <= timezone.now()

    def get_api_image_url(self, image_url):
        return f'{self.api_url}/uploads/group/{image_url}'

    def delete_stale_datasets(self, data):
        ext_idents = [x[0] for x in data]
        ext_idents.append('')
        objs = self.dataset_model.objects.filter(source=self).exclude(ext_ident__in=ext_idents)
        count = objs.count()
        for obj in objs:
            obj.delete()
        return count

    def delete_stale_resources(self, data):
        count = 0
        for item in data:
            ext_idents = [x for x in item[1]]
            ext_idents.append('')
            objs = self.resource_model.objects.filter(
                dataset__source=self, dataset__ext_ident=item[0]).exclude(ext_ident__in=ext_idents)
            count += objs.count()
            for obj in objs:
                obj.delete()
        return count

    def update_from_items(self, data):
        ds_imported = 0
        ds_created = 0
        ds_updated = 0
        r_imported = 0
        r_created = 0
        r_updated = 0
        for item in data:
            category = self._get_dataset_category(item)
            categories = self._get_dataset_categories(category, item)

            license = self._get_license(item)
            license_condition_db_or_copyrighted = self._get_license_condition_db_or_copyrighted(item)
            license_chosen = self._get_license_chosen(item)

            organization = self._get_organization(item)
            if is_enabled('S18_new_tags.be'):
                tags = self._prepare_tags(item)
            else:
                tags = self._get_tags(item)
            resources_data = item.pop('resources')
            item.update({
                'category': category,
                'source': self,
                'organization': organization,
                'license': license,
                'license_condition_db_or_copyrighted': license_condition_db_or_copyrighted,
                'license_chosen': license_chosen,
            })
            dataset, created = self._update_or_create_dataset(item)
            ds_imported += 1
            if dataset:
                if created:
                    ds_created += 1
                else:
                    ds_updated += 1

                dataset.tags.set(tags)
                dataset.categories.set(categories)

                for rd in resources_data:
                    resource, created = self._update_or_create_resource(dataset, rd)
                    r_imported += 1
                    if resource:
                        if created:
                            r_created += 1
                        else:
                            r_updated += 1
        return ds_imported, ds_created, ds_updated, r_imported, r_created, r_updated

    def _update_or_create_dataset(self, data):
        data.update({'created_by': self.import_user, 'status': data.get('status', 'published')})
        modified = data.pop('modified', None)
        modified = modified or data.get('created')
        int_ident = data.pop('int_ident', None)

        if int_ident:
            created = False
            obj = self.dataset_model.raw.filter(id=int_ident, organization=data['organization']).first()
            if obj:
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.save()
        else:
            obj, created = self.dataset_model.raw.update_or_create(
                ext_ident=data['ext_ident'], source=data['source'], defaults=data)
        if obj and modified:  # TODO: find a better way to save modification date with value from data.
            self.dataset_model.raw.filter(id=obj.id).update(modified=modified)
        return obj, created

    def _get_dataset_category(self, data):
        if self.is_ckan:
            return self.category
        elif self.is_xml and self.xsd_schema_version < settings.XML_VERSION_MULTIPLE_CATEGORIES:
            category_ids_list = data.pop('categories', None)
            if category_ids_list:
                category_model = apps.get_model('categories.Category')
                return category_model.objects.filter(id__in=category_ids_list[:1]).first()

    def _get_dataset_categories(self, category, data):
        if self.is_ckan:
            return self.categories.all()
        elif self.is_xml:
            if self.xsd_schema_version < settings.XML_VERSION_MULTIPLE_CATEGORIES:
                old_category = category
                new_category = None
                if old_category:
                    code = OLD_CATEGORY_TITLE_2_DCAT_CATEGORY_CODE.get(old_category.title_pl)
                    new_category = Category.objects.filter(code=code).first()
                if new_category:
                    return [new_category]
            else:
                return self._get_dcat_categories(data)
        elif self.is_dcat:
            return self._get_dcat_categories(data)
        return []

    def _get_dcat_categories(self, data):
        category_codes_list = data.pop('categories', None)
        if category_codes_list:
            return Category.objects.filter(code__in=category_codes_list)

    def _get_license(self, data):
        if self.is_xml:
            name = data.pop('license', None)
            if name:
                license_model = apps.get_model('licenses.License')
                return license_model.objects.filter(name=name).first()

    def _get_license_condition_db_or_copyrighted(self, data):
        if self.is_ckan:
            return self.license_condition_db_or_copyrighted
        elif self.is_xml:
            return data.get('license_condition_db_or_copyrighted')

    def _get_license_chosen(self, data):
        if self.is_ckan:
            dataset_model = apps.get_model('datasets.Dataset')
            license_name_to_code = dict((row[1], row[0]) for row in dataset_model.LICENSES)
            license_name = settings.CKAN_LICENSES_WHITELIST.get(data.pop('license_id', None))
            license_code = license_name_to_code.get(license_name)
            return license_code
        elif self.is_xml:
            return data.get('license_chosen')
        elif self.is_dcat:
            dataset_model = apps.get_model('datasets.Dataset')
            license_name_to_code = dict((row[1], row[0]) for row in dataset_model.LICENSES)
            license_code = license_name_to_code.get(data.get('license_chosen'))
            return license_code

    @staticmethod
    def _get_file_from_url(url):
        try:
            filename, headers = retrieve_to_file(url)
            return File(open(filename, 'rb'))
        except Exception as exc:
            logger.debug(exc)

    def _get_organization(self, data):
        if self.is_xml or self.is_dcat:
            return self.organization
        elif self.is_ckan:
            data = data.pop('organization', None)
            if data:
                obj = self.organization_model.raw.filter(title=data['title']).first()
                if obj:
                    return obj
                image_name = data.pop('image_name')
                obj = self.organization_model.raw.create(
                    created_by=self.import_user, institution_type=self.institution_type, **data)
                if image_name:
                    if image_name.startswith('http'):  # sometimes it's' full path to image (with domain name).
                        image_url = image_name
                        image_name = os.path.basename(image_url)
                    else:
                        media_url_template = self.import_settings.get('MEDIA_URL_TEMPLATE')
                        image_url = media_url_template.format(self.portal_url, image_name)
                    image = self._get_file_from_url(image_url)
                    if image:
                        obj.image.save(image_name, image)
                return obj

    def _update_or_create_resource(self, dataset, data):
        if dataset.status == self.dataset_model.STATUS.draft:  # TODO: move to SIGNAL_MAP in Dataset?
            data['status'] = self.resource_model.STATUS.draft
        data['created_by'] = self.import_user
        if 'format' in data:
            data['format'] = data.get('format') or None
        modified = data.pop('modified', None)
        modified = modified or data.get('created')
        int_ident = data.pop('int_ident', None)
        if int_ident:
            created = False
            obj = self.resource_model.raw.filter(dataset=dataset, id=int_ident).first()
            if obj:
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.save()
        else:
            obj, created = self.resource_model.raw.update_or_create(
                dataset=dataset, ext_ident=data['ext_ident'], defaults=data)
        if obj and modified:  # TODO: find a better way to save modification date with value from data.
            self.resource_model.raw.filter(id=obj.id).update(modified=modified)
        return obj, created

    def _import_from(self, path):
        parts = path.split('.')
        module = '.'.join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m

    def _get_ext_idents(self, data):
        dataset_ext_ident = data['ext_ident']
        resources_ext_idents = [x['ext_ident'] for x in data['resources']]
        return dataset_ext_ident, resources_ext_idents

    def _get_tag_query_params(self, data):
        lang = data.pop('lang', None)
        query_params = {'name': data.get('name')}
        if lang in ['en', 'pl']:
            name = data.pop('name', '')
            data[f'name_{lang}'] = name
            query_params = {f'name_{lang}': name}
        return query_params

    def _get_tags(self, data):
        data = data.pop('tags', [])
        tag_ids = []
        for item in data:
            defaults = {'created_by': self.import_user}
            query_params = self._get_tag_query_params(item)
            obj, _ = self.tag_model.objects.get_or_create(language='', defaults=defaults, **query_params)
            tag_ids.append(obj.id)
        return self.tag_model.objects.filter(id__in=tag_ids)

    def _prepare_tags(self, data):
        tags_data = data.pop('tags', [])
        tags_ids = []
        for tag_data in tags_data:
            name = tag_data.get('name')
            if not name:
                continue
            language = tag_data.pop('lang', 'pl')
            defaults = {'created_by': self.import_user}
            tag, _ = self.tag_model.objects.get_or_create(name=name, language=language, defaults=defaults)
            tags_ids.append(tag.id)
        return self.tag_model.objects.filter(id__in=tags_ids)

    def _validate_cc_licenses(self, items, error_desc):
        ds_rejected = 0
        if self.is_ckan and is_enabled('S21_licenses.be'):
            rejected_items = []
            accepted_items = []
            for item in items:
                if item.get('license_id') in settings.CKAN_LICENSES_WHITELIST:
                    accepted_items.append(item)
                else:
                    rejected_items.append(item)

            items = accepted_items
            if rejected_items:
                ds_rejected = len(rejected_items)
                error_desc = str(error_desc)
                if error_desc:
                    error_desc += '<br>'
                error_desc += 'Wartość w polu license_id spoza słownika CC'

                item_error_descs = []
                for item in rejected_items:
                    item_error_descs.append(f"<p><strong>id zbioru danych:</strong> {item.get('ext_ident')}</p>"
                                            f"<p><strong>license_id:</strong> {item.get('license_id')}</p>")

                inner_error_desc = '<br>'.join(item_error_descs)
                error_desc += f'<div class="expandable">{inner_error_desc}</div>'
        return items, ds_rejected, error_desc

    def import_data(self):
        if not self.is_active:
            logger.debug(f'Cannot import data. Data source \"{self}\" is not active!')
            return
        data = None
        error_desc = ''
        start = timezone.now()
        import_func_path = self.import_settings.get('IMPORT_FUNC', 'mcod.harvester.utils.fetch_data')
        import_func = self._import_from(import_func_path)
        schema_path = self.import_settings.get('SCHEMA')
        schema_class = self._import_from(schema_path)
        try:
            data = import_func(**self.import_func_kwargs)
        except Exception as exc:
            error_desc = exc
        try:
            schema = schema_class(many=True)
            schema.context['organization'] = self.organization
            items = schema.load(data) if data else []
        except SchemaValidationError as err:
            items = []
            error_desc = err.messages
            if isinstance(error_desc, dict):
                error_desc = pprint.pformat(error_desc)

        items, ds_rejected, error_desc = self._validate_cc_licenses(items, error_desc)

        dsi = DataSourceImport.objects.create(
            datasource=self,
            start=start,
            error_desc=error_desc,
            datasets_rejected_count=ds_rejected,
        )
        self.last_import_timestamp = dsi.start
        self.save()
        self.xsd_schema_version = getattr(data, 'xsd_schema_version', None)

        imported_ext_idents = [self._get_ext_idents(item) for item in items]

        ds_imported, ds_created, ds_updated, r_imported, r_created, r_updated = self.update_from_items(items)

        r_deleted = 0
        ds_deleted = 0
        if not dsi.is_failed:
            r_deleted = self.delete_stale_resources(imported_ext_idents)
            ds_deleted = self.delete_stale_datasets(imported_ext_idents)
        dsi.datasets_count = ds_imported
        dsi.datasets_created_count = ds_created
        dsi.datasets_updated_count = ds_updated
        dsi.datasets_deleted_count = ds_deleted
        dsi.datasets_rejected_count = ds_rejected
        dsi.resources_count = r_imported
        dsi.resources_created_count = r_created
        dsi.resources_updated_count = r_updated
        dsi.resources_deleted_count = r_deleted
        dsi.end = timezone.now()
        dsi.save()
        self.last_import_status = dsi.status
        self.save()
        if self.emails_list and is_enabled('harvester_mails.be'):
            send_import_report_mail_task.s(dsi.id).apply_async()


class DataSourceTrash(DataSource, metaclass=TrashModelBase):
    class Meta:
        proxy = True
        verbose_name = _("Trash (Data Sources)")
        verbose_name_plural = _("Trash (Data Sources)")


class DataSourceImport(TimeStampedModel):
    """Model of data source import."""
    datasource = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name='imports', verbose_name=_('data source'))
    start = models.DateTimeField(verbose_name=_('start'))
    end = models.DateTimeField(verbose_name=_('end'), null=True, blank=True)
    status = models.CharField(max_length=50, verbose_name=_('status'), choices=IMPORT_STATUS_CHOICES, blank=True)
    error_desc = models.TextField(verbose_name=_('error description'), blank=True)
    datasets_rejected_count = models.PositiveIntegerField(
        verbose_name=_('number of rejected datasets'), null=True, blank=True)
    datasets_count = models.PositiveIntegerField(
        verbose_name=_('number of imported datasets'), null=True, blank=True)
    datasets_created_count = models.PositiveIntegerField(
        verbose_name=_('number of created datasets'), null=True, blank=True)
    datasets_updated_count = models.PositiveIntegerField(
        verbose_name=_('number of updated datasets'), null=True, blank=True)
    datasets_deleted_count = models.PositiveIntegerField(
        verbose_name=_('number of deleted datasets'), null=True, blank=True)
    resources_count = models.PositiveIntegerField(
        verbose_name=_('number of imported resources'), null=True, blank=True)
    resources_created_count = models.PositiveIntegerField(
        verbose_name=_('number of created resources'), null=True, blank=True)
    resources_updated_count = models.PositiveIntegerField(
        verbose_name=_('number of updated resources'), null=True, blank=True)
    resources_deleted_count = models.PositiveIntegerField(
        verbose_name=_('number of deleted resources'), null=True, blank=True)
    is_report_email_sent = models.BooleanField(verbose_name=_('Is report email sent?'), default=False)

    class Meta:
        verbose_name = _('data source import')
        verbose_name_plural = _('data source imports')

    def __str__(self):
        return '{} - start {}'.format(self.datasource.name, self.start_local_txt)

    @property
    def start_local(self):
        return timezone.localtime(self.start)

    @property
    def start_local_txt(self):
        return self.start_local.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def end_local(self):
        return timezone.localtime(self.end)

    @property
    def is_failed(self):
        return self.status == STATUS_ERROR

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.status = STATUS_OK
        if self.error_desc:
            self.status = STATUS_OK_PARTIAL if self.datasets_rejected_count else STATUS_ERROR
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
