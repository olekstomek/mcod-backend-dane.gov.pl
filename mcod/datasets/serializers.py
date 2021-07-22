import marshmallow as ma
from django.apps import apps
from django.db.models.manager import Manager
from django.utils.translation import gettext_lazy as _
from querystring_parser import builder

from mcod import settings
from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import (
    Relationships,
    Relationship,
    ObjectAttrs,
    TopLevel,
    Aggregation,
    ExtAggregation,
    HighlightObjectMixin
)
from mcod.core.api.rdf import fields as rdf_fields
from mcod.core.api.rdf.profiles.common import HYDRAPagedCollection
from mcod.core.api.rdf.schemas import ResponseSchema as RDFResponseSchema
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer, ListWithoutNoneStrElement
from mcod.datasets.models import UPDATE_FREQUENCY
from mcod.core.api.rdf.schema_mixins import ProfilesMixin
from mcod.lib.extended_graph import ExtendedGraph
from mcod.lib.serializers import TranslatedStr, KeywordsList
from mcod.lib.serializers import TranslatedTagsList
from mcod.resources.serializers import ResourceRDFMixin
from mcod.unleash import is_enabled
from mcod.watchers.serializers import SubscriptionMixin

_UPDATE_FREQUENCY = dict(UPDATE_FREQUENCY)

Organization = apps.get_model('organizations', 'Organization')
Category = apps.get_model('categories', 'Category')
Dataset = apps.get_model('datasets', 'Dataset')


UPDATE_FREQUENCY_TO_DCAT_PREFIX = 'http://publications.europa.eu/resource/authority/frequency/'
UPDATE_FREQUENCY_TO_DCAT = {
    "notApplicable": "UNKNOWN",
    "yearly": "ANNUAL",
    "everyHalfYear": "ANNUAL_2",
    "quarterly": "QUARTERLY",
    "monthly": "MONTHLY",
    "weekly": "WEEKLY",
    "daily": "DAILY",
}


class CategoryRDFNestedSchema(ProfilesMixin, ma.Schema):
    code = ma.fields.Str()
    title_pl = ma.fields.Str(attribute='title_translated.pl')
    title_en = ma.fields.Str(attribute='title_translated.en')


class ResourceRDFNestedSchema(ResourceRDFMixin, ma.Schema):
    pass


class DatasetOrganization:
    def __init__(self, dataset):
        self.org = dataset.organization
        self.dataset = dataset

    def __getattr__(self, item):
        if item == 'dataset':
            return self.dataset
        else:
            return getattr(self.org, item)


class OrganizationRDFMixin(ProfilesMixin):
    id = ma.fields.Str(attribute='id')
    access_url = ma.fields.Str(attribute='frontend_absolute_url')
    title_pl = ma.fields.Str(attribute='title_translated.pl')
    title_en = ma.fields.Str(attribute='title_translated.en')
    email = ma.fields.Str()


class OrganizationRDFNestedSchema(OrganizationRDFMixin, ma.Schema):
    dataset_frontend_absolute_url = ma.fields.Function(lambda o: o.dataset.frontend_absolute_url)


def resources_dump(dataset, context):
    return ResourceRDFNestedSchema(many=True, context=context).dump(dataset.resources.filter(status='published'))


def organization_dump(dataset, context):
    return OrganizationRDFNestedSchema(many=False, context=context).dump(DatasetOrganization(dataset))


def categories_dump(dataset, context):
    context = {**context, 'dataset_uri': dataset.frontend_absolute_url}
    return CategoryRDFNestedSchema(many=True, context=context).dump(dataset.categories.all())


class DcatUpdateFrequencyField(fields.String):
    @fields.after_serialize
    def to_dcat(self, value=None):
        dcat_value = UPDATE_FREQUENCY_TO_DCAT.get(value)
        if dcat_value:
            dcat_value = f'{UPDATE_FREQUENCY_TO_DCAT_PREFIX}{dcat_value}'
        return dcat_value


class DatasetRDFResponseSchema(ProfilesMixin, RDFResponseSchema):
    identifier = ma.fields.Function(lambda ds: ds.frontend_absolute_url)
    id = ma.fields.Str()
    frontend_absolute_url = ma.fields.Str()
    title_pl = ma.fields.Str(attribute='title_translated.pl')
    title_en = ma.fields.Str(attribute='title_translated.en')
    notes_pl = ma.fields.Str(attribute='notes_translated.pl')
    notes_en = ma.fields.Str(attribute='notes_translated.en')
    status = ma.fields.Str()
    created = ma.fields.DateTime()
    modified = ma.fields.DateTime()
    landing_page = fields.Function(lambda ds: ds.frontend_absolute_url)
    version = ma.fields.Str()
    tags = rdf_fields.Tags(ma.fields.Str())
    resources = ma.fields.Function(resources_dump)
    organization = ma.fields.Function(organization_dump)
    categories = ma.fields.Function(categories_dump)
    update_frequency = DcatUpdateFrequencyField()
    license = ma.fields.Function(lambda ds: ds.license_link)

    @staticmethod
    def _from_path(es_resp, path):
        try:
            obj = es_resp
            for step in path.split('.'):
                obj = getattr(obj, step)
            return obj
        except AttributeError:
            return None

    @ma.pre_dump(pass_many=True)
    def extract_pagination(self, data, many, **kwargs):
        request = self.context['request'] if 'request' in self.context else None
        cleaned_data = dict(getattr(request.context, 'cleaned_data', {})) if request else {}

        def _get_page_link(page_number):
            cleaned_data['page'] = page_number
            return '{}{}?{}'.format(settings.API_URL, request.path, builder.build(cleaned_data))

        if self.many:
            page, per_page = cleaned_data.get('page', 1), cleaned_data.get('per_page', 20)
            self.context['count'] = self._from_path(data, 'hits.total')
            self.context['per_page'] = per_page

            items_count = self._from_path(data, 'hits.total')
            if page > 1:
                self.context['first_page'] = _get_page_link(1)
                self.context['prev_page'] = _get_page_link(page - 1)
            if items_count:
                max_count = min(items_count, 10000)
                off = 1 if max_count % per_page else 0
                last_page = max_count // per_page + off
                if last_page > 1:
                    self.context['last_page'] = _get_page_link(last_page)
                if page * per_page < max_count:
                    self.context['next_page'] = _get_page_link(page + 1)

        return data

    @ma.pre_dump(pass_many=True)
    def prepare_datasets(self, data, many, **kwargs):
        self.context['dataset_refs'] = []
        if self.many:
            self.context['catalog_modified'] = self._from_path(data, 'aggregations.catalog_modified.value_as_string')
            dataset_ids = [x.id for x in data]
            data = Dataset.objects.filter(pk__in=dataset_ids)
        return data

    @ma.post_dump(pass_many=False)
    def prepare_graph_triples(self, data, **kwargs):
        self.context['dataset_refs'].append(data['frontend_absolute_url'])
        dataset = self.get_rdf_class_for_model(model=Dataset)()
        return dataset.to_triples(data, self.include_nested_triples)

    @ma.post_dump(pass_many=True)
    def prepare_graph(self, data, many, **kwargs):
        graph = ExtendedGraph(ordered=True)
        self.add_bindings(graph=graph)

        # Jeżeli many == True, to serializujemy katalog.
        if many:
            triples = []
            # Dla katalogu, w data, mamy listę list, trzeba to spłaszczyć.
            for _triples in data:
                triples.extend(_triples)

            self.add_pagination_bindings(graph=graph)
            paged_collection = HYDRAPagedCollection()
            triples.extend(paged_collection.to_triples(self.context))
            catalog = self.get_rdf_class_for_catalog()()
            triples.extend(catalog.to_triples(self.context))
        else:
            triples = data
        for triple in triples:
            graph.add(triple)
        return graph

    class Meta:
        model = 'datasets.Dataset'


class DatasetCategoryAttr(ExtSchema):
    id = fields.Str()
    title = TranslatedStr()
    code = fields.Str()

    @ma.pre_dump(pass_many=True)
    def prepare_data(self, data, many, **kwargs):
        if isinstance(data, Manager):
            data = data.all()
        return data


class SourceSchema(ExtSchema):
    title = fields.Str()
    type = fields.Str(attribute='source_type')
    url = fields.URL()
    update_frequency = TranslatedStr()
    last_import_timestamp = fields.DateTime()


class TransUpdateFreqField(fields.String):
    @fields.after_serialize
    def translate(self, value=None):
        if value:
            value = str(_(_UPDATE_FREQUENCY[value]))
        return value


class InstitutionAggregation(ExtAggregation):
    class Meta:
        model = 'organizations.Organization'
        title_field = 'title_i18n'


class CategoryAggregation(ExtAggregation):
    class Meta:
        model = 'categories.Category'
        title_field = 'title_i18n'


class DatasetApiAggregations(ExtSchema):
    by_created = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_created.by_created.buckets'
    )
    by_modified = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_modified.by_modified.buckets'
    )
    by_verified = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_verified.by_verified.buckets'
    )
    by_format = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_format.by_format.buckets'
    )
    by_institution = fields.Nested(
        InstitutionAggregation,
        many=True,
        attribute='_filter_by_institution.by_institution.inner.buckets'
    )
    by_types = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_types.by_types.buckets'
    )
    by_visualization_types = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_visualization_types.by_visualization_types.buckets'
    )
    by_category = fields.Nested(
        CategoryAggregation,
        many=True,
        attribute='_filter_by_category.by_category.inner.buckets'
    )
    by_categories = fields.Nested(
        CategoryAggregation,
        many=True,
        attribute='_filter_by_categories.by_categories.inner.buckets'
    )
    by_openness_score = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_openness_score.by_openness_score.buckets'
    )
    by_tag = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_tag.by_tag.inner.buckets'
    )
    by_keyword = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_keyword.by_keyword.inner.inner.buckets'
    )


class DatasetApiRelationships(Relationships):
    institution = fields.Nested(
        Relationship, many=False,
        _type='institution',
        path='institutions',
        url_template='{api_url}/institutions/{ident}'
    )
    resources = fields.Nested(
        Relationship,
        many=False, default=[],
        _type='resource',
        url_template='{object_url}/resources'
    )
    subscription = fields.Nested(
        Relationship,
        many=False,
        _type='subscription',
        url_template='{api_url}/auth/subscriptions/{ident}'
    )

    @ma.pre_dump
    def prepare_data(self, data, **kwargs):
        object_url = data.pop('object_url', None)
        if object_url:
            self._fields['resources'].schema.context.update(object_url=object_url)
        if not self.context.get('is_listing', False) and 'resources' in data:
            data['resources'] = data['resources'].filter(status='published')
        return data


class DatasetApiAttrs(ObjectAttrs, HighlightObjectMixin):
    title = TranslatedStr()
    slug = TranslatedStr()
    notes = TranslatedStr()
    categories = fields.Nested(DatasetCategoryAttr, many=True)
    category = fields.Nested(DatasetCategoryAttr, many=False)
    formats = fields.List(fields.String())
    types = fields.List(fields.String())
    tags = TranslatedTagsList(TranslatedStr())
    keywords = KeywordsList(TranslatedStr())
    openness_scores = fields.List(fields.Int())
    license_chosen = fields.Integer()
    license_condition_db_or_copyrighted = fields.String()
    license_condition_personal_data = fields.String()
    license_condition_modification = fields.Boolean()
    license_condition_original = fields.Boolean()
    license_condition_responsibilities = fields.String()
    license_condition_source = fields.Boolean()
    license_condition_timestamp = fields.Boolean()
    license_name = fields.String()
    license_description = fields.String()
    update_frequency = TransUpdateFreqField()
    views_count =\
        fields.Function(
            lambda obj: obj.computed_views_count if is_enabled('S16_new_date_counters.be') and
            hasattr(obj, 'computed_views_count') else obj.views_count)
    downloads_count =\
        fields.Function(
            lambda obj: obj.computed_downloads_count if is_enabled('S16_new_date_counters.be') and
            hasattr(obj, 'computed_downloads_count') else obj.downloads_count)
    url = fields.String()
    followed = fields.Boolean()
    modified = fields.DateTime()
    resource_modified = fields.DateTime()
    created = fields.DateTime()
    verified = fields.DateTime()
    visualization_types = ListWithoutNoneStrElement(fields.Str())
    source = fields.Nested(SourceSchema)
    image_url = fields.Str()
    image_alt = TranslatedStr()

    class Meta:
        relationships_schema = DatasetApiRelationships
        object_type = 'dataset'
        url_template = '{api_url}/datasets/{ident}'
        model = 'datasets.Dataset'


class DatasetApiResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = DatasetApiAttrs
        aggs_schema = DatasetApiAggregations


# class SearchResultAttrs(ObjectAttrs):
#     title = TranslatedStr()
#     notes = TranslatedStr()
#
#     class Meta:
#         ordered = True


# class ApplicationSearchResultAttrs(SearchResultAttrs):
#     notes = TranslatedStr()
#     author = fields.Str()
#     verified = fields.DateTime(attribute='modified')
#     tags = TranslatedTagsList(TranslatedStr())


# class ArticleSearchResultAttrs(SearchResultAttrs):
#     notes = TranslatedStr()
#     verified = fields.DateTime(attribute='modified')
#     tags = TranslatedTagsList(TranslatedStr())


# class DatasetSearchResultAttrs(SearchResultAttrs):
#     verified = fields.DateTime()
#     source_title = fields.Str()
#     source_url = fields.URL()
#     source_type = fields.Str()
#     tags = TranslatedTagsList(TranslatedStr())
#     keywords = KeywordsList(TranslatedStr())


# class InstitutionSearchResultAttrs(SearchResultAttrs):
#     verified = fields.DateTime(attribute='modified')


# class ResourceSearchResultAttrs(SearchResultAttrs):
#     notes = TranslatedStr(attribute='description')
#     verified = fields.DateTime()


# class DocumentTypeAggregation(Aggregation):
#     application = fields.Int(attribute='application.doc_count')
#     dataset = fields.Int(attribute='dataset.doc_count')
#     institution = fields.Int(attribute='institution.doc_count')
#     news = fields.Int(attribute='news.doc_count')
#     knowledge_base = fields.Int(attribute='knowledge_base.doc_count')
#     resource = fields.Int(attribute='resource.doc_count')
#
#     @ma.pre_dump(pass_many=True)
#     def prepare_data(self, data, many):
#         if many:
#             keys = [x['key'] for x in data]
#             for key in ['application', 'article', 'dataset', 'institution', 'knowledge_base', 'news', 'resource']:
#                 if key not in keys:
#                     data.append({'key': key, 'doc_count': 0})
#             for item in data:
#                 item['title'] = key.upper()
#         return data


# class SearchApiAggregations(ExtSchema):
#     type = fields.Nested(DocumentTypeAggregation, attribute='documents_by_type.buckets', many=False)
#
#     class Meta:
#         ordered = True
#
#     @ma.pre_dump
#     def prepare_data(self, data):
#         documents_by_type = getattr(data, 'documents_by_type', None)
#         if not documents_by_type:
#             return {'documents_by_type': {
#                 'buckets': {
#                     'application': {'doc_count': 0},
#                     'dataset': {'doc_count': 0},
#                     'institution': {'doc_count': 0},
#                     'knowledge_base': {'doc_count': 0},
#                     'news': {'doc_count': 0},
#                     'resource': {'doc_count': 0},
#                 }}}
#         return data


# class SearchApiResult(Object):
#     class Meta:
#         attrs_schema = SearchResultAttrs
#
#     @ma.pre_dump(pass_many=False)
#     def prepare_data(self, doc):
#         data = super().prepare_data(doc)
#         data['_type'] = doc.search_type
#         lang = get_language()
#         if lang in ['en', 'pl']:
#             ident = '{},{}'.format(doc.id, getattr(doc.slug, lang, doc.slug))
#         else:
#             ident = doc.id
#         data['links']['self'] = f'{self.api_url}/{doc.meta.index}/{ident}'
#         return data


# class ApplicationSearchApiResult(SearchApiResult):
#     class Meta:
#         attrs_schema = ApplicationSearchResultAttrs


# class ArticleSearchApiResult(SearchApiResult):
#     class Meta:
#         attrs_schema = ArticleSearchResultAttrs


# class InstitutionSearchApiResult(SearchApiResult):
#     class Meta:
#         attrs_schema = InstitutionSearchResultAttrs


# class DatasetSearchApiResult(SearchApiResult):
#     class Meta:
#         attrs_schema = DatasetSearchResultAttrs


# class ResourceSearchApiResult(SearchApiResult):
#     class Meta:
#         attrs_schema = ResourceSearchResultAttrs


# DATA_SCHEMAS = {  # TODO it is misleading since isn't used anywhere
#     'application': ApplicationSearchApiResult,
#     'article': ArticleSearchApiResult,
#     'institution': InstitutionSearchApiResult,
#     'dataset': DatasetSearchApiResult,
#     'resource': ResourceSearchApiResult,
# }


class CommentApiRelationships(Relationships):
    dataset = fields.Nested(Relationship, many=False, _type='dataset', url_template='{api_url}/datasets/{ident}')


class CommentAttrs(ObjectAttrs):
    comment = fields.Str(required=True, example='Looks unpretty')

    class Meta:
        object_type = 'comment'
        path = 'datasets'
        url_template = '{api_url}/datasets/{data.dataset.id}/comments/{ident}'
        relationships_schema = CommentApiRelationships


class CommentApiResponse(TopLevel):
    class Meta:
        attrs_schema = CommentAttrs


class DatasetCSVSchema(CSVSerializer):
    id = fields.Integer(data_key=_('id'), required=True)
    uuid = fields.Str(data_key=_("uuid"), default='')
    title = fields.Str(data_key=_("title"), default='')
    notes = fields.Str(data_key=_("notes"), default='')
    url = fields.Str(data_key=_("url"), default='')
    update_frequency = fields.Str(data_key=_("Update frequency"), default='')
    institution = fields.Str(data_key=_("Institution"), attribute='organization.id', default='')
    category = fields.Str(data_key=_("Category"), default='')
    status = fields.Str(data_key=_("Status"), default='')
    is_licence_set = fields.Boolean(data_key=_("Conditions for re-use"), default=None)
    created_by = fields.Int(attribute='created_by.id', data_key=_("created_by"), default=None)
    created = fields.DateTime(data_key=_("created"), default=None)
    modified_by = fields.Int(attribute='modified_by.id', data_key=_("modified_by"), default=None)
    modified = fields.DateTime(data_key=_("modified"), default=None)
    followers_count = fields.Str(data_key=_("The number of followers"), default=None)

    class Meta:
        ordered = True
        model = 'datasets.Dataset'
