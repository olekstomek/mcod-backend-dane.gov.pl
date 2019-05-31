from django.utils.translation import gettext_lazy as _

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import \
    Relationships, Relationship, ObjectAttrs, TopLevel, TopLevelMeta, ObjectAttrsMeta, Aggregation
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer
from mcod.lib.serializers import TranslatedStr


class ResourceApiRelationships(Relationships):
    dataset = fields.Nested(Relationship, many=False, _type='dataset', path='datasets')


class ResourceApiAttrs(ObjectAttrs):
    title = TranslatedStr()
    description = TranslatedStr()
    category = fields.Str()
    format = fields.Str()
    media_type = fields.Str()
    downloads_count = fields.Integer()
    openness_score = fields.Integer()
    views_count = fields.Integer()
    modified = fields.DateTime()
    created = fields.DateTime()
    verified = fields.DateTime()
    data_date = fields.Date()
    file_url = fields.Str()
    download_url = fields.Str()
    link = fields.Str()
    file_size = fields.Integer()

    class Meta:
        relationships_schema = ResourceApiRelationships
        object_type = 'resource'
        api_path = 'resources'
        url_template = '{api_url}/resources/{ident}'


class ResourceApiAggregations(ExtSchema):
    by_format = fields.Nested(Aggregation,
                              many=True,
                              attribute='_filter_by_format.by_format.buckets'
                              )
    by_type = fields.Nested(Aggregation,
                            many=True,
                            attribute='_filter_by_type.by_type.buckets'
                            )
    by_openness_score = fields.Nested(Aggregation,
                                      many=True,
                                      attribute='_filter_by_openness_score.by_openness_score.buckets'
                                      )


class ResourceApiResponse(TopLevel):
    class Meta:
        attrs_schema = ResourceApiAttrs
        aggs_schema = ResourceApiAggregations


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


class TableApiMeta(TopLevelMeta):
    data_schema = fields.Raw()
    headers_map = fields.Raw()


class TableApiResponse(TopLevel):
    class Meta:
        attrs_schema = TableApiAttrs
        meta_schema = TableApiMeta


# class ResourceAggregations(schemas.ExtSchema):
#     format = fields.Nested(jss.SearchAggregation, attribute='_filter_format.format.buckets', name='format', many=True)
#     type = fields.Nested(jss.SearchAggregation, attribute='_filter_type.type.buckets', name='type', many=True)
#     openness_score = fields.Nested(jss.SearchAggregation, attribute='_filter_openness_score.openness_score.buckets',
#                                    many=True, name='openness_score')
#
#     class Meta:
#         nullable = True

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
    link_is_valid = fields.Str(data_key=_("link_is_valid"), default='')
    file_is_valid = fields.Str(data_key=_("file_is_valid"), default='')
    data_is_valid = fields.Str(data_key=_("data_is_valid"), default='')
    format = fields.Str(data_key=_("format"), default='')
    dataset = fields.Str(attribute='dataset.title', data_key=_("dataset"), default='')
    status = fields.Str(data_key=_("status"), default='')
    created_by = fields.Int(attribute='created_by.id', data_key=_("created_by"), default=None)
    created = fields.DateTime(data_key=_("created"), default=None)
    modified_by = fields.Int(attribute='modified_by.id', data_key=_("modified_by"), default=None)
    modified = fields.DateTime(data_key=_("modified"), default=None)
    resource_type = fields.Str(attribute='type', data_key=_("type"), default='')
    openness_score = fields.Int(data_key=_("openness_score"), default=None)
    views_count = fields.Int(data_key=_("views_count"), default=None)
    downloads_count = fields.Int(data_key=_("downloads_count"), default=None)

    class Meta:
        ordered = True
        model = 'resources.Resource'
