from django.apps import apps
from django.utils.translation import get_language
from marshmallow import missing

from mcod import settings
from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import (
    Aggregation,
    HighlightObjectMixin,
    ObjectAttrs,
    Relationships,
    Relationship,
    TopLevel,
    TopLevelMeta
)
from mcod.core.api.rdf.schemas import ResponseSchema as RDFResponseSchema
from mcod.core.api.schemas import ExtSchema
from mcod.datasets.serializers import (
    BoolDataAggregation,
    CategoryAggregation,
    InstitutionAggregation,
    SourceSchema,
    LicenseAggregation,
    UpdateFrequencyAggregation,
)
from mcod.lib.serializers import TranslatedStr, KeywordsList
from mcod.organizations.serializers import DataSourceAttr
from mcod.regions.serializers import RegionSchema
from mcod.resources.serializers import GeoTileAggregation
from mcod.showcases.serializers import (
    ShowcaseCategoryAggregation,
    ShowcasePlatformAggregation,
    ShowcaseTypeAggregation,
)
from mcod.watchers.serializers import SubscriptionMixin
from mcod.unleash import is_enabled


class CommonObjectRelationships(Relationships):
    dataset = fields.Nested(
        Relationship,
        many=False,
        _type='dataset',
        path='datasets',
        url_template='{api_url}/datasets/{ident}'
    )
    institution = fields.Nested(
        Relationship,
        many=False,
        _type='institution',
        attribute="institution",
        url_template='{api_url}/institutions/{ident}'
    )
    subscription = fields.Nested(
        Relationship,
        many=False,
        _type='subscription',
        url_template='{api_url}/auth/subscriptions/{ident}'
    )


class Category(ExtSchema):
    id = fields.String()
    name = TranslatedStr()
    title = TranslatedStr()
    description = TranslatedStr()
    image_url = fields.String()
    code = fields.String()


class CommonObjectApiAttrs(ObjectAttrs, HighlightObjectMixin):
    model = fields.Str()

    # common
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    keywords = KeywordsList(TranslatedStr(), faker_type='tagslist')
    modified = fields.DateTime()
    created = fields.DateTime()
    verified = fields.DateTime()
    categories = fields.Nested(Category, many=True)
    category = fields.Nested(Category)
    if is_enabled('S43_dynamic_data.be'):
        has_dynamic_data = fields.Boolean()
    if is_enabled('S35_high_value_data.be'):
        has_high_value_data = fields.Boolean()

    # datasets
    source = fields.Nested(SourceSchema)

    # resources
    data_date = fields.Date()
    visualization_types = fields.List(fields.Str())

    # applications, showcases
    author = fields.Str()
    illustrative_graphics_alt = TranslatedStr()
    illustrative_graphics_url = fields.Str()
    image_alt = TranslatedStr()
    image_thumb_url = fields.Str()
    if is_enabled('S39_showcases.be'):
        showcase_category = fields.Str()
        showcase_category_name = fields.Method('get_showcase_category_name')
        showcase_types = fields.List(fields.Str())
        showcase_platforms = fields.List(fields.Str())

    # institutions
    abbreviation = fields.Str()
    institution_type = fields.Str()
    datasets_count = fields.Int(attribute='published_datasets_count')
    resources_count = fields.Int(attribute='published_resources_count')
    fax = fields.Str()
    tel = fields.Str()
    sources = fields.Nested(DataSourceAttr, many=True)

    # cms pages
    html_url = fields.Str()

    if is_enabled('S39_filter_by_geodata.be'):
        # regions
        region_id = fields.Int()
        hierarchy_label = TranslatedStr()
        bbox = fields.List(fields.List(fields.Float), attribute='bbox.coordinates')
        regions = fields.Nested(RegionSchema, many=True)

    def get_showcase_category_name(self, obj):
        val = getattr(obj, 'showcase_category', None)
        if val:
            model = apps.get_model('showcases.Showcase')
            return str(model.CATEGORY_NAMES[val])
        return missing

    @staticmethod
    def self_api_url(data):
        try:
            api_url = getattr(settings, 'API_URL', 'https://api.dane.gov.pl')
            model = data.model
            obj_id = data.id
            slug = data['slug'][get_language()]
            full_url = f'{api_url}/{model}s/{obj_id},{slug}'
        except AttributeError:
            full_url = None
        return full_url

    class Meta:
        relationships_schema = CommonObjectRelationships
        object_type = 'common'
        api_path = 'search'


class SearchCounterAggregation(ExtSchema):
    datasets = fields.Integer()
    resources = fields.Integer()
    showcases = fields.Integer()
    applications = fields.Integer()
    institutions = fields.Integer()
    articles = fields.Integer()
    knowledge_base = fields.Integer()


class SearchDateRangeAggregation(ExtSchema):
    max_date = fields.Date()
    min_date = fields.Date()


class CommonObjectApiAggregations(ExtSchema):
    counters = fields.Nested(SearchCounterAggregation)

    by_format = fields.Nested(Aggregation,
                              many=True,
                              attribute='_filter_by_format.by_format.buckets')
    by_institution = fields.Nested(InstitutionAggregation,
                                   many=True,
                                   attribute='_filter_by_institution.by_institution.inner.buckets')
    by_types = fields.Nested(Aggregation,
                             many=True,
                             attribute='_filter_by_types.by_types.buckets')
    by_visualization_types = fields.Nested(Aggregation,
                                           many=True,
                                           attribute='_filter_by_visualization_types.by_visualization_types.buckets')
    by_category = fields.Nested(CategoryAggregation,
                                many=True,
                                attribute='_filter_by_category.by_category.inner.buckets')
    by_categories = fields.Nested(CategoryAggregation,
                                  many=True,
                                  attribute='_filter_by_categories.by_categories.inner.buckets')
    by_openness_score = fields.Nested(Aggregation,
                                      many=True,
                                      attribute='_filter_by_openness_score.by_openness_score.buckets')

    by_institution_type = fields.Nested(Aggregation,
                                        many=True,
                                        attribute='_filter_by_institution_type.by_institution_type.buckets')
    search_date_range = fields.Nested(SearchDateRangeAggregation)
    by_license_code = fields.Nested(LicenseAggregation,
                                    many=True,
                                    attribute='_filter_by_license_code.by_license_code.buckets')
    by_update_frequency = fields.Nested(UpdateFrequencyAggregation,
                                        many=True,
                                        attribute='_filter_by_update_frequency.by_update_frequency.buckets')

    by_has_dynamic_data = fields.Nested(
        BoolDataAggregation,
        many=True,
        attribute='_filter_by_has_dynamic_data.by_has_dynamic_data.buckets')
    by_has_high_value_data = fields.Nested(
        BoolDataAggregation,
        many=True,
        attribute='_filter_by_has_high_value_data.by_has_high_value_data.buckets')
    by_showcase_category = fields.Nested(
        ShowcaseCategoryAggregation,
        many=True,
        attribute='_filter_by_showcase_category.by_showcase_category.buckets')
    by_showcase_types = fields.Nested(
        ShowcaseTypeAggregation,
        many=True,
        attribute='_filter_by_showcase_types.by_showcase_types.buckets')
    by_showcase_platforms = fields.Nested(
        ShowcasePlatformAggregation,
        many=True,
        attribute='_filter_by_showcase_platforms.by_showcase_platforms.buckets')
    by_tiles = fields.Nested(GeoTileAggregation, many=True)


class CommonObjectApiMetaSchema(TopLevelMeta):
    aggregations = fields.Nested(CommonObjectApiAggregations)


class SparqlNamespaceApiAttrs(ObjectAttrs):
    prefix = fields.Str()
    url = fields.Str()

    class Meta:
        object_type = 'namespace'
        ordered = True

    @staticmethod
    def self_api_url(data):
        return None


class SparqlNamespaceApiResponse(TopLevel):
    class Meta:
        attrs_schema = SparqlNamespaceApiAttrs


class SparqlAttrs(ObjectAttrs):
    pass


class SparqlResponseSchema(RDFResponseSchema):
    pass


class SparqlApiAttrs(ObjectAttrs):
    result = fields.Str()
    has_previous = fields.Bool()
    has_next = fields.Bool()
    content_type = fields.Str()
    download_url = fields.Url()

    class Meta:
        object_type = 'sparql'
        ordered = True


class SparqlApiResponse(TopLevel):
    class Meta:
        attrs_schema = SparqlApiAttrs


class CommonObjectResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = CommonObjectApiAttrs
        meta_schema = CommonObjectApiMetaSchema