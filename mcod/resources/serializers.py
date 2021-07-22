import json

import marshmallow as ma
from django.utils.translation import gettext_lazy as _, get_language
from django.utils.html import strip_tags

from mcod.core.api import fields, schemas
from mcod.core.api.jsonapi.serializers import (
    Relationships,
    Relationship,
    Object,
    ObjectAttrs,
    TopLevel,
    TopLevelMeta,
    ObjectAttrsMeta,
    Aggregation,
    HighlightObjectMixin
)
from mcod.core.api.rdf.schemas import ResponseSchema as RDFResponseSchema
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer, ListWithoutNoneStrElement
from mcod.core.utils import sizeof_fmt
from mcod.lib.extended_graph import ExtendedGraph
from mcod.lib.serializers import TranslatedStr
from mcod.core.api.rdf.schema_mixins import ProfilesMixin
from mcod.resources.models import Resource
from mcod.watchers.serializers import SubscriptionMixin
from mcod.unleash import is_enabled


class ResourceApiRelationships(Relationships):
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

    tabular_data = fields.Nested(
        Relationship,
        many=False,
        _type='tabular_data',
        url_template='{api_url}/resources/{ident}/data'
    )

    geo_data = fields.Nested(
        Relationship,
        many=False,
        _type='geo_data',
        url_template='{api_url}/resources/{ident}/geo'
    )

    chart = fields.Nested(
        Relationship,
        many=False,
        _type='chart',
        attribute="chartable",
        url_template='{api_url}/resources/{ident}/chart'
    )


class SpecialSignSchema(ExtSchema):
    symbol = fields.Str()
    name = TranslatedStr()
    description = TranslatedStr()


class ResourceApiAttrs(ObjectAttrs, HighlightObjectMixin):
    title = TranslatedStr()
    description = TranslatedStr()
    category = fields.Str()
    format = fields.Str()
    media_type = fields.Str(attribute='type')  # https://jsonapi.org/format/#document-resource-object-fields
    visualization_types = ListWithoutNoneStrElement(fields.Str())
    downloads_count =\
        fields.Function(
            lambda obj: obj.computed_downloads_count if is_enabled('S16_new_date_counters.be') and
            hasattr(obj, 'computed_downloads_count') else obj.downloads_count)
    openness_score = fields.Integer()
    views_count =\
        fields.Function(
            lambda obj: obj.computed_views_count if is_enabled('S16_new_date_counters.be') and
            hasattr(obj, 'computed_views_count') else obj.views_count)
    modified = fields.DateTime()
    created = fields.DateTime()
    verified = fields.DateTime()
    data_date = fields.Date()
    file_url = fields.Str()
    file_size = fields.Integer()
    csv_file_url = fields.Str()
    csv_file_size = fields.Integer()
    download_url = fields.Str()
    csv_download_url = fields.Str()
    link = fields.Str()
    if is_enabled('S16_special_signs.be'):
        data_special_signs = fields.Nested(SpecialSignSchema, data_key='special_signs', many=True)
    if is_enabled('S24_named_charts.be'):
        is_chart_creation_blocked = fields.Bool()

    class Meta:
        relationships_schema = ResourceApiRelationships
        object_type = 'resource'
        api_path = 'resources'
        url_template = '{api_url}/resources/{ident}'
        model = 'resources.Resource'


class ResourceApiAggregations(ExtSchema):
    by_created = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_created.by_created.buckets',
    )
    by_modified = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_modified.by_modified.buckets',
    )
    by_verified = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_verified.by_verified.buckets',
    )
    by_format = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_format.by_format.buckets'
    )
    by_type = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_type.by_type.buckets'
    )
    by_openness_score = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_openness_score.by_openness_score.buckets'
    )
    by_visualization_type = fields.Nested(
        Aggregation,
        many=True,
        attribute='_filter_by_visualization_type.by_visualization_type.buckets'
    )


class ResourceApiResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = ResourceApiAttrs
        aggs_schema = ResourceApiAggregations


class ResourceRDFMixin(ProfilesMixin):
    dataset_frontend_absolute_url = ma.fields.Function(lambda r: r.dataset.frontend_absolute_url)
    id = ma.fields.Str(attribute='id')
    dataset_id = ma.fields.Str(attribute='dataset_id')
    title_pl = ma.fields.Str(attribute='title_translated.pl')
    title_en = ma.fields.Str(attribute='title_translated.en')
    description_pl = ma.fields.Str(attribute='description_translated.pl')
    description_en = ma.fields.Str(attribute='description_translated.en')
    status = ma.fields.Str()
    created = ma.fields.DateTime()
    modified = ma.fields.DateTime()
    access_url = ma.fields.Str(attribute='frontend_absolute_url')
    download_url = ma.fields.Str()
    format = ma.fields.Str()
    file_mimetype = ma.fields.Str()
    file_size = ma.fields.Int()
    if is_enabled('S21_licenses.be'):
        license = ma.fields.Function(lambda r: r.dataset.license_link)
    else:
        license = ma.fields.Function(lambda r: r.dataset.license.name if r.dataset.license else "unknown")


class ResourceRDFResponseSchema(ResourceRDFMixin, RDFResponseSchema):

    @ma.pre_dump(pass_many=True)
    def prepare_data(self, data, many, **kwargs):
        # If many, serialize data as catalog - from Elasticsearch
        return data.data if hasattr(data, 'data') else data

    @ma.post_dump(pass_many=False)
    def prepare_graph_triples(self, data, **kwargs):
        distribution = self.get_rdf_class_for_model(model=Resource)()
        return distribution.to_triples(data, self.include_nested_triples)

    @ma.post_dump(pass_many=True)
    def prepare_graph(self, data, many, **kwargs):
        graph = ExtendedGraph(ordered=True)
        self.add_bindings(graph=graph)

        for triple in data:
            graph.add(triple)
        return graph

    class Meta:
        ordered = True
        model = 'resources.Resource'


class TableApiRelationships(Relationships):
    resource = fields.Nested(Relationship,
                             many=False,
                             _type='resource',
                             url_template='{api_url}/resources/{ident}'
                             )


class TableApiAttrsMeta(ObjectAttrsMeta):
    updated_at = fields.DateTime()
    row_no = fields.Integer()


class TableApiAttrs(ObjectAttrs):
    class Meta:
        object_type = 'row'
        url_template = '{api_url}/resources/{data.resource.id}/data/{ident}'
        relationships_schema = TableApiRelationships
        meta_schema = TableApiAttrsMeta


class MetricAggregation(ExtSchema):
    column = fields.String()
    value = fields.Number()


class TableAggregations(ExtSchema):
    sum = fields.Nested(MetricAggregation, many=True)
    avg = fields.Nested(MetricAggregation, many=True)


class TableApiMeta(TopLevelMeta):
    data_schema = fields.Raw()
    headers_map = fields.Raw()
    aggregations = fields.Nested(TableAggregations)


class TableApiResponse(TopLevel):
    class Meta:
        attrs_schema = TableApiAttrs
        meta_schema = TableApiMeta


class GeoApiRelationships(Relationships):
    resource = fields.Nested(Relationship,
                             many=False,
                             _type='resource',
                             url_template='{api_url}/resources/{ident}'
                             )


class GeoApiAttrsMeta(ObjectAttrsMeta):
    updated_at = fields.DateTime()
    row_no = fields.Integer()


class Geometry(ma.Schema):
    type = fields.String(required=True)
    coordinates = fields.Raw(required=True)


class GeoFeatureRecord(ma.Schema):
    pass


class GeoShapeObject(schemas.ExtSchema):
    shape = fields.Nested(Geometry)
    record = fields.Nested(GeoFeatureRecord, many=False)
    label = fields.String()


class GeoApiAttrs(ObjectAttrs, GeoShapeObject):
    class Meta:
        object_type = 'geoshape'
        url_template = '{api_url}/resources/{data.resource.id}/geo/{ident}'
        relationships_schema = GeoApiRelationships
        meta_schema = GeoApiAttrsMeta


class GeoTileAggregation(schemas.ExtSchema):
    tile_name = fields.String()
    doc_count = fields.Integer()
    shapes = fields.Nested(GeoShapeObject, many=True)
    centroid = fields.List(fields.Float)


class GeoBounds(schemas.ExtSchema):
    top_left = fields.List(fields.Float)
    bottom_right = fields.List(fields.Float)


class GeoAggregations(ma.Schema):
    tiles = fields.Nested(GeoTileAggregation, many=True)
    bounds = fields.Nested(GeoBounds)


class GeoApiMeta(TopLevelMeta):
    data_schema = fields.Raw()
    headers_map = fields.Raw()
    aggregations = fields.Nested(GeoAggregations)


class GeoApiResponse(TopLevel):
    @ma.pre_dump
    def prepare_top_level(self, c, **kwargs):
        try:
            super().prepare_top_level(c, **kwargs)
        except ZeroDivisionError:
            pass
        return c

    class Meta:
        attrs_schema = GeoApiAttrs
        meta_schema = GeoApiMeta


class CommentApiRelationships(Relationships):
    resource = fields.Nested(Relationship, many=False, _type='resource', url_template='{api_url}/resources/{ident}')


class CommentAttrs(ObjectAttrs):
    comment = fields.Str(required=True, example='Looks unpretty')

    class Meta:
        object_type = 'comment'
        url_template = '{api_url}/resources/{data.resource.id}/comments/{ident}'
        relationships_schema = CommentApiRelationships


class CommentApiResponse(TopLevel):
    class Meta:
        attrs_schema = CommentAttrs
        max_items_num = 20000


class ResourceCSVSchema(CSVSerializer):
    id = fields.Integer(data_key=_('id'), required=True)
    uuid = fields.Str(data_key=_("uuid"), default='')
    title = fields.Str(data_key=_("title"), default='')
    description = fields.Str(data_key=_("description"), default='')
    link = fields.Str(data_key=_("link"), default='')
    link_is_valid = fields.Str(data_key=_('link_tasks_last_status'), default='')
    file_is_valid = fields.Str(data_key=_('file_tasks_last_status'), default='')
    data_is_valid = fields.Str(data_key=_('data_tasks_last_status'), default='')
    format = fields.Str(data_key=_("format"), default='')
    dataset = fields.Str(attribute='dataset.title', data_key=_("dataset"), default='')
    status = fields.Str(data_key=_("status"), default='')
    created_by = fields.Int(attribute='created_by.id', data_key=_("created_by"), default=None)
    created = fields.DateTime(data_key=_("created"), default=None)
    modified_by = fields.Int(attribute='modified_by.id', data_key=_("modified_by"), default=None)
    modified = fields.DateTime(data_key=_("modified"), default=None)
    resource_type = fields.Str(attribute='type', data_key=_("type"), default='')
    openness_score = fields.Int(data_key=_("openness_score"), default=None)
    views_count = fields.Function(
        lambda obj: obj.computed_views_count if is_enabled('S16_new_date_counters.be') and
        hasattr(obj, 'computed_views_count') else obj.views_count, data_key=_("views_count"), default=None)
    downloads_count = fields.Function(
        lambda obj: obj.computed_downloads_count if is_enabled('S16_new_date_counters.be') and
        hasattr(obj, 'computed_downloads_count') else obj.downloads_count, data_key=_("downloads_count"), default=None)

    class Meta:
        ordered = True
        model = 'resources.Resource'


class ChartApiRelationships(Relationships):
    resource = fields.Nested(Relationship, many=False, _type='resource', url_template='{api_url}/resources/{ident}')


class ChartApiAttrs(ObjectAttrs):
    chart = fields.Raw()
    is_default = fields.Boolean()

    def get_chart(self, obj):
        return json.dumps(obj.chart)

    class Meta:
        relationships_schema = ChartApiRelationships
        object_type = 'chart'
        api_path = 'chart'
        url_template = '{api_url}/charts/{ident}'
        model = 'resources.Chart'


class ChartApiData(Object):

    @ma.pre_dump(pass_many=False)
    def prepare_data(self, data, **kwargs):
        if not data:
            return
        return super().prepare_data(data, **kwargs)


class ChartApiResponse(TopLevel):
    class Meta:
        data_schema = ChartApiData
        attrs_schema = ChartApiAttrs

    @ma.pre_dump
    def prepare_top_level(self, c, **kwargs):
        if self.context['is_listing']:
            c.data = c.data if hasattr(c, 'data') else []
        return super().prepare_top_level(c, **kwargs)


class DatasetResourcesCSVSerializer(CSVSerializer):
    dataset_url = fields.Url(attribute='dataset.frontend_absolute_url', data_key=_('Dataset URL'))
    dataset_title = fields.Str(attribute='dataset.title', data_key=_('Title'))
    dataset_description = fields.Function(lambda obj: strip_tags(obj.dataset.notes) if obj.dataset.notes else '',
                                          data_key=_('Notes'))
    dataset_keywords = fields.Function(lambda obj: obj.dataset.tags_as_str(get_language()), data_key=_('Tag'))
    dataset_categories = fields.Str(attribute='dataset.categories_list_str', data_key=_('Category'))
    dataset_update_frequency = fields.Str(attribute='dataset.update_frequency', data_key=_('Update frequency'))
    dataset_created = fields.DateTime(attribute='dataset.created', data_key=_('Dataset created'), format='iso8601')
    dataset_verified = fields.DateTime(attribute='dataset.verified', data_key=_('Dataset verified'), format='iso8601')
    dataset_views_count = fields.Function(
        lambda obj: obj.dataset.computed_views_count if
        is_enabled('S16_new_date_counters.be') and hasattr(obj.dataset, 'computed_views_count') else
        obj.dataset.views_count, data_key=_("Dataset views count"), default=None)
    dataset_downloads_count = fields.Function(
        lambda obj: obj.dataset.computed_downloads_count if
        is_enabled('S16_new_date_counters.be') and hasattr(obj.dataset, 'computed_downloads_count') else
        obj.dataset.downloads_count,
        data_key=_('Dataset downloads count'), default=None)
    dataset_resources_count = fields.Int(attribute='resources_count', data_key=_('Number of data'))
    dataset_conditions = fields.Method('get_dataset_conditions', data_key=_('Terms of use'))
    dataset_license = fields.Str(attribute='dataset.license_name', data_key=_('License'))
    organization_url = fields.Url(attribute='dataset.organization.frontend_absolute_url',
                                  data_key=_('Organization URL'))
    organization_type = fields.Function(lambda obj: obj.dataset.organization.get_institution_type_display(),
                                        data_key=_('Institution type'))
    organization_title = fields.Str(attribute='dataset.organization.title', data_key=_('Name'))
    organization_abbr_title = fields.Str(attribute='dataset.organization.abbreviation',
                                         data_key=_('Abbreviation'), default='')
    organization_epuap = fields.Str(attribute='dataset.organization.epuap', data_key=_('EPUAP'), default='')
    organization_website = fields.Url(attribute='dataset.organization.website', data_key=_('Website'))
    organization_created = fields.DateTime(attribute='dataset.organization.created',
                                           data_key=_('Organization created'), format='iso8601')
    organization_modified = fields.DateTime(attribute='dataset.organization.modified',
                                            data_key=_('Organization modified'), format='iso8601')
    organization_datasets_count = fields.Int(attribute='datasets_count',
                                             data_key=_('Number of datasets'))
    organization_postal_code = fields.Str(attribute='dataset.organization.postal_code', data_key=_('Postal code'))
    organization_city = fields.Str(attribute='dataset.organization.city', data_key=_('City'))
    organization_street_type = fields.Str(attribute='dataset.organization.street_type', data_key=_('Street type'))
    organization_street = fields.Str(attribute='dataset.organization.street', data_key=_('Street'))
    organization_street_number = fields.Str(attribute='dataset.organization.street_number', data_key=_('Street number'))
    organization_flat_number = fields.Str(attribute='dataset.organization.flat_number', data_key=_('Flat number'))
    organization_email = fields.Email(attribute='dataset.organization.email', data_key=_('Email'))
    organization_phone_number = fields.Str(attribute='dataset.organization.tel', data_key=_('Phone'))
    frontend_absolute_url = fields.Url(data_key=_('Resource URL'))
    title = fields.Str(data_key=_('Resource title'), default='')
    description = fields.Function(lambda obj: strip_tags(obj.description) if obj.description else '',
                                  data_key=_('Resource description'))
    created = fields.DateTime(data_key=_('Resource created'), format='iso8601')
    data_date = fields.Date(data_key=_('Data date'))
    openness_score = fields.Int(data_key=_('Openness score'))
    resource_type = fields.Function(lambda obj: obj.get_type_display(), data_key=_('Type'))
    format = fields.Str(data_key=_('File format'), default='')
    file_size = fields.Function(lambda obj: sizeof_fmt(obj.file_size) if obj.file_size else '', data_key=_('File size'))
    views_count = fields.Function(
        lambda obj: obj.computed_views_count if
        is_enabled('S16_new_date_counters.be') and hasattr(obj, 'computed_views_count') else
        obj.views_count, data_key=_("Resource views count"), default='')
    downloads_count = fields.Function(
        lambda obj: obj.computed_downloads_count if
        is_enabled('S16_new_date_counters.be') and hasattr(obj, 'computed_downloads_count') else
        obj.downloads_count, data_key=_("Resource downloads count"), default='')
    has_table = fields.Function(lambda obj: _('YES') if obj.has_table else _('NO'), data_key=_('Table'))
    has_chart = fields.Function(lambda obj: _('YES') if obj.has_chart else _('NO'), data_key=_('Map'))
    has_map = fields.Function(lambda obj: _('YES') if obj.has_map else _('NO'), data_key=_('Chart'))

    def get_dataset_conditions(self, obj):
        dataset = obj.dataset
        conditions = _('This dataset is public information, it can be reused under the following conditions: ')
        terms = [str(dataset._meta.get_field('license_condition_modification').verbose_name) if
                 dataset.license_condition_modification else '',
                 str(dataset._meta.get_field('license_condition_source').verbose_name) if
                 dataset.license_condition_source else '',
                 dataset.license_condition_db_or_copyrighted, dataset.license_condition_personal_data]
        return conditions + '\n'.join([term for term in terms if term])

    class Meta:
        ordered = True
