import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _, override
from django.utils.timezone import is_naive, make_aware
from marshmallow import Schema as BaseSchema, EXCLUDE, pre_load, post_load, validate
from marshmallow import ValidationError, validates_schema
from marshmallow.fields import Bool, Date, DateTime, Int, List, Nested, Str, URL, UUID, Method

from mcod.core.api.rdf.profiles.dcat_ap import DCATDatasetDeserializer
from mcod.datasets.models import Dataset
from mcod.resources.models import Resource, supported_formats_choices
from mcod.resources.archives import ARCHIVE_EXTENSIONS
from mcod.unleash import is_enabled


SUPPORTED_RESOURCE_FORMATS = [i[0] for i in supported_formats_choices()]
SUPPORTED_RESOURCE_FORMATS.extend(ARCHIVE_EXTENSIONS)
SUPPORTED_RESOURCE_FORMATS.append('api')


class Schema(BaseSchema):

    @post_load
    def modify_data(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                data[key] = make_aware(value, is_dst=False) if is_naive(value) else value
        return data


class ExtraSchema(Schema):
    key = Str()
    value = Str()


class CategorySchema(Schema):
    description = Str()
    display_name = Str()
    uuid = UUID()
    image_url = URL(data_key='image_display_url')
    name = Str()
    title = Str()

    class Meta:
        fields = ('title', 'description', 'uuid', 'image_url')
        unknown = EXCLUDE


class OrganizationSchema(Schema):
    created = DateTime()
    description = Str()
    uuid = Str(data_key='id')
    image_name = Str(data_key='image_url')
    slug = Str(data_key='name')
    title = Str()

    class Meta:
        fields = ('created', 'description', 'uuid', 'image_name', 'slug', 'title')
        unknown = EXCLUDE


class RelationshipObjectSchema(Schema):
    id = Str()


class RelationshipSubjectSchema(Schema):
    id = Str()


class ResourceMixin:

    @validates_schema
    def validate_link(self, data, **kwargs):
        value = data.get('link')
        if value and "://" in value and is_enabled('S37_validate_resource_link_scheme_harvester.be'):
            scheme = value.split("://")[0].lower()
            if scheme != 'https':
                raise ValidationError(_('Required scheme is https://'), field_name='link')


class ResourceSchema(ResourceMixin, Schema):
    mimetype = Str(allow_none=True)
    cache_last_updated = Str(allow_none=True)
    cache_url = Str(allow_none=True)
    created = DateTime()
    description = Str()
    hash = Str()
    ext_ident = Str(data_key='id', validate=validate.Length(max=36))
    modified = DateTime(data_key='last_modified', allow_none=True)
    mimetype_inner = Str(allow_none=True)
    title = Str(data_key='name')
    format = Str()
    link = URL(data_key='url')
    datastore_active = Bool()
    package_id = UUID()
    position = Int()
    resource_type = Str(allow_none=True)
    revision_id = UUID()
    size = Str(allow_none=True)
    state = Str()
    url_type = Str(allow_none=True)

    class Meta:
        fields = ('created', 'modified', 'ext_ident', 'title', 'description', 'link', 'format')
        unknown = EXCLUDE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Does it makes sense to validate format here? Disabled for now.
        self.format_validation = False

    @validates_schema
    def validate_format(self, data, **kwargs):
        value = data.get('format')
        if self.format_validation and value and value not in SUPPORTED_RESOURCE_FORMATS:
            error = _('Unsupported format: %(format)s.') % {'format': value}
            raise ValidationError(error, field_name='format')

    @pre_load
    def prepare_data(self, data, **kwargs):
        if 'format' in data:
            value = data['format'].lower()
            if value not in SUPPORTED_RESOURCE_FORMATS:
                value = ''
            data['format'] = value
        return data


class TagSchema(Schema):
    uuid = UUID(data_key='id')
    name = Str()
    status = Str(
        data_key='state', validate=validate.OneOf(choices=['active']))

    class Meta:
        fields = ('name', 'uuid')
        unknown = EXCLUDE


class XMLTagSchema(Schema):
    name = Str(data_key='$')
    lang = Str(data_key='@lang', validate=validate.OneOf(choices=['en', 'pl']))

    class Meta:
        fields = ('name', 'lang')
        unknown = EXCLUDE


class TagDCATSchema(Schema):
    name = Str()
    lang = Str(validate=validate.OneOf(choices=['en', 'pl']))

    class Meta:
        fields = ('name', 'lang')
        unknown = EXCLUDE
        ordered = True


class DatasetSchema(Schema):
    author = Str()
    author_email = Str()
    creator_user_id = UUID()
    extras = Nested(ExtraSchema, many=True)
    groups = Nested(CategorySchema, many=True)
    license_id = Str()
    license_title = Str()
    license_url = URL()
    maintainer = Str()
    maintainer_email = Str()
    created = DateTime(data_key='metadata_created')
    modified = DateTime(data_key='metadata_modified', allow_none=True)
    slug = Str(data_key='name')
    notes = Str()
    num_resources = Int()
    num_tags = Int()
    ext_ident = Str(data_key='id', validate=validate.Length(max=36))
    isopen = Bool()
    organization = Nested(OrganizationSchema, many=False)
    owner_org = UUID()
    private = Bool()
    relationships_as_object = Nested(RelationshipObjectSchema, many=True)
    relationships_as_subject = Nested(RelationshipSubjectSchema, many=True)
    resources = Nested(ResourceSchema, many=True)
    revision_id = UUID()
    status = Str(data_key='state')
    tags = Nested(TagSchema, many=True)
    title = Str()
    type = Str()
    url = Str()
    version = Str()

    class Meta:
        exclude = [
            'author', 'author_email', 'creator_user_id', 'extras', 'groups', 'license_title', 'license_url',
            'maintainer', 'maintainer_email', 'num_resources', 'num_tags', 'isopen', 'owner_org', 'private',
            'relationships_as_object', 'relationships_as_subject', 'revision_id', 'type', 'status',
            'url', 'version']
        ordered = True
        unknown = EXCLUDE


class XMLResourceSchema(ResourceMixin, Schema):
    ext_ident = Str(data_key='extIdent', validate=validate.Length(max=36), required=True)
    int_ident = Int(data_key='intIdent')
    status = Str(data_key='@status', validate=validate.OneOf(choices=['draft', 'published']))
    link = URL(data_key='url')
    title_pl = Str()
    title_en = Str()
    description_pl = Str()
    description_en = Str()
    availability = Str(validate=validate.OneOf(choices=['local', 'remote']))
    data_date = Date(data_key='dataDate')
    created = DateTime(data_key='created', allow_none=True)
    modified = DateTime(data_key='lastUpdateDate', allow_none=True)
    special_signs = List(Str())

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_load
    def prepare_data(self, data, **kwargs):
        if 'title' in data and isinstance(data.get('title'), dict):
            data['title_en'] = data['title'].get('english', '')
            data['title_pl'] = data['title'].get('polish', '')
        if 'description' in data and isinstance(data.get('description'), dict):
            data['description_en'] = data['description'].get('english', '')
            data['description_pl'] = data['description'].get('polish', '')
        data['availability'] = data.get('availability', 'local')
        special_signs = data.pop('specialSigns', {})
        if 'specialSign' in special_signs:
            data['special_signs'] = special_signs['specialSign']
        return data

    @validates_schema
    def validate_int_ident(self, data, **kwargs):
        int_ident = data.get('int_ident')
        dataset_int_ident = self.context.get('dataset_int_ident')
        organization = self.context['organization']
        if int_ident and not dataset_int_ident:
            raise ValidationError(_('intIdent value for related dataset is also required!'), field_name='int_ident')
        if int_ident and dataset_int_ident and organization and not Resource.raw.filter(
                id=int_ident, dataset_id=dataset_int_ident, dataset__organization=organization).exists():
            msg = _('Resource with id: %(r_id)s, dataset\'s id: %(d_id)s and institution "%(ins)s" was not found.') % {
                'r_id': int_ident, 'd_id': dataset_int_ident, "ins": organization.title}
            raise ValidationError(msg, field_name='int_ident')


class XMLDatasetSchema(Schema):
    ext_ident = Str(data_key='extIdent', validate=validate.Length(max=36), required=True)
    int_ident = Int(data_key='intIdent')
    status = Str(data_key='@status', validate=validate.OneOf(choices=['draft', 'published']))
    title_pl = Str()
    title_en = Str()
    notes_pl = Str()
    notes_en = Str()
    url = URL(allow_none=True)
    update_frequency = Str(data_key='updateFrequency')
    license = Str()
    license_chosen = Int(allow_none=True)
    license_condition_db_or_copyrighted = Str(allow_none=True)
    license_condition_modification = Bool(allow_none=True)
    license_condition_personal_data = Str(allow_none=True)
    license_condition_responsibilities = Str(allow_none=True)
    license_condition_source = Bool(allow_none=True)
    created = DateTime(data_key='created', allow_none=True)
    modified = DateTime(data_key='lastUpdateDate', allow_none=True)
    categories = List(Str())
    resources = Nested(XMLResourceSchema, many=True)
    tags = Nested(XMLTagSchema, many=True)

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_load
    def prepare_data(self, data, **kwargs):
        if 'title' in data and isinstance(data.get('title'), dict):
            data['title_en'] = data['title'].get('english', '')
            data['title_pl'] = data['title'].get('polish', '')
        if 'conditions' in data:
            data['license_condition_source'] = data['conditions'].get('source', False)
            data['license_condition_modification'] = data['conditions'].get('modification', False)
            data['license_condition_responsibilities'] = data['conditions'].get('responsibilities')
            data['license_condition_db_or_copyrighted'] = data['conditions'].get('dbOrCopyrighted')
            license_text_to_num = dict((row[1], row[0]) for row in Dataset.LICENSES)
            license_chosen_text = data['conditions'].get('dbOrCopyrightedLicenseChosen')
            data['license_chosen'] = license_text_to_num.get(license_chosen_text)
            data['license_condition_personal_data'] = data['conditions'].get('personalData')
        if 'description' in data and isinstance(data.get('description'), dict):
            data['notes_en'] = data['description'].get('english', '')
            data['notes_pl'] = data['description'].get('polish', '')
        if 'tags' in data:
            data['tags'] = data['tags'].get('tag', [])
        if 'categories' in data:
            if 'category' in data['categories']:  # XSD SCHEMA >= 1.1
                data['categories'] = data['categories']['category']
            else:
                data['categories'] = [str(row) for row in data['categories']]
        if 'resources' in data:
            data['resources'] = data['resources'].get('resource', [])
        int_ident = data.get('intIdent')
        if int_ident:
            self.context['dataset_int_ident'] = int_ident
        return data

    @validates_schema
    def validate_int_ident(self, data, **kwargs):
        int_ident = data.get('int_ident')
        organization = self.context['organization']
        if int_ident and organization and not Dataset.raw.filter(id=int_ident, organization=organization).exists():
            msg = _('Dataset with id: %(d_id)s and institution: "%(ins)s" was not found.') % {
                'd_id': int_ident, 'ins': organization.title}
            raise ValidationError(msg, field_name='int_ident')

    @validates_schema
    def validate_license_condition_personal_data(self, data, **kwargs):
        field_name = 'license_condition_personal_data'
        if data.get(field_name):
            raise ValidationError(
                message=_('Chosen conditions for re-use mean that they contain personal data. '
                          'Please contact the administrator at kontakt@dane.gov.pl.'),
                field_name=field_name,
            )

    @validates_schema
    def validate_license_condition_db_or_copyrighted(self, data, **kwargs):
        field_name = 'license_condition_db_or_copyrighted'
        if data.get(field_name) and not data.get('license_chosen'):
            raise ValidationError(
                message=_("Field 'dbOrCopyrightedLicenseChosen' is required if field 'dbOrCopyrighted' is provided."),
                field_name=field_name,
            )

    @validates_schema
    def validate_license_chosen(self, data, **kwargs):
        field_name = 'license_chosen'
        if data.get(field_name) and not data.get('license_condition_db_or_copyrighted'):
            raise ValidationError(
                message=_("Field 'dbOrCopyrighted' is required if field 'dbOrCopyrightedLicenseChosen' is provided."),
                field_name=field_name,
            )


class ResourceDCATSchema(ResourceMixin, Schema):
    ext_ident = Str(validate=validate.Length(max=36))
    title_pl = Str()
    title_en = Str(allow_none=True)
    description_pl = Str(allow_none=True)
    description_en = Str(allow_none=True)
    created = DateTime(allow_none=True)
    modified = DateTime(allow_none=True)
    link = URL()
    format = Str()
    file_mimetype = Str(allow_none=True)

    @pre_load(pass_many=True)
    def prepare_multi_data(self, data, **kwargs):
        for res in data:
            if res.get('modified') and not res.get('created'):
                res['created'] = res['modified']
            if not res.get('title_pl') and res.get('title_en'):
                res['title_pl'] = res['title_en']
        return data

    @post_load(pass_many=True)
    def postprocess_data(self, data, **kwargs):
        for res in data:
            if res['created'] is None:
                res.pop('created')
            if res['modified'] is None:
                res.pop('modified')
        return data

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DatasetDCATSchema(Schema):
    ext_ident = Str(validate=validate.Length(max=36))
    title_pl = Str()
    title_en = Str(allow_none=True)
    notes_pl = Str(data_key='description_pl', allow_none=True)
    notes_en = Str(data_key='description_en', allow_none=True)
    created = DateTime(allow_none=True)
    modified = DateTime(allow_none=True)
    tags = Nested(TagDCATSchema, many=True)
    resources = Nested(ResourceDCATSchema, many=True)
    categories = List(Str())
    update_frequency = Str(allow_none=True)
    license_chosen = Str(allow_none=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load(pass_many=True)
    def prepare_multi_data(self, triple_store_dct, **kwargs):
        triple_store = triple_store_dct
        dataset_deserializer = DCATDatasetDeserializer(many=True)
        from_triples_data = dataset_deserializer.from_triples(triple_store)
        for dataset in from_triples_data:
            if not dataset.get('title_pl') and dataset.get('title_en'):
                dataset['title_pl'] = dataset['title_en']
            if dataset.get('modified') and not dataset.get('created'):
                dataset['created'] = dataset['modified']
            dataset['license_chosen'] = dataset['resources'][0]['license']
        return from_triples_data

    @post_load(pass_many=True)
    def postprocess_data(self, data, **kwargs):
        for dataset in data:
            if dataset['created'] is None:
                dataset.pop('created')
            if dataset['modified'] is None:
                dataset.pop('modified')
        return data


class DataSourceSerializer(Schema):
    source_type = Str()
    url = URL()
    title = Str()
    last_import_timestamp = DateTime()
    update_frequency = Method('get_update_frequency')

    def get_update_frequency(self, obj):
        translations = {}
        for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
            with override(lang):
                translations[lang] = str(obj.get_frequency_in_days_display())
        return translations
