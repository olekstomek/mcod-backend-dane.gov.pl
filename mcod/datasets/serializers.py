from django.apps import apps
from django.utils.translation import gettext_lazy as _
from marshmallow import pre_dump

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import \
    Relationships, Relationship, ObjectAttrs, TopLevel, Aggregation
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer
from mcod.datasets.models import UPDATE_FREQUENCY
from mcod.lib.serializers import TranslatedStr
from mcod.lib.serializers import TranslatedTagsList

_UPDATE_FREQUENCY = dict(UPDATE_FREQUENCY)

Organization = apps.get_model('organizations', 'Organization')
Category = apps.get_model('categories', 'Category')


class DatasetCategoryAttr(ExtSchema):
    id = fields.Str()
    title = TranslatedStr()


class TransUpdateFreqField(fields.String):
    @fields.after_serialize
    def translate(self, value=None):
        if value:
            value = _(_UPDATE_FREQUENCY[value])
        return value


class DatasetsByInstitutionAgg(Aggregation):
    @pre_dump(pass_many=True)
    def prepare_data(self, data, many):
        if many:
            ids = [d.key for d in data]
            qs = Organization.objects.filter(pk__in=ids).values('id', 'title')
            _data = {i['id']: i['title'] for i in qs}
            for item in data:
                item['title'] = _data.get(item.key) or str(item.key).upper()
            return data


class DatasetByCategoryAgg(Aggregation):
    @pre_dump(pass_many=True)
    def prepare_data(self, data, many):
        if many:
            ids = [d.key for d in data]
            qs = Category.objects.filter(pk__in=ids).values('id', 'title')
            _data = {i['id']: i['title'] for i in qs}
            for item in data:
                item['title'] = _data.get(item.key) or str(item.key).upper()
            return data


class DatasetApiAggregations(ExtSchema):
    by_format = fields.Nested(Aggregation,
                              many=True,
                              attribute='_filter_by_format.by_format.buckets'
                              )
    by_institution = fields.Nested(DatasetsByInstitutionAgg,
                                   many=True,
                                   attribute='_filter_by_institution.by_institution.inner.buckets'
                                   )
    by_type = fields.Nested(Aggregation,
                            many=True,
                            attribute='_filter_by_type.by_type.buckets'
                            )
    by_category = fields.Nested(DatasetByCategoryAgg,
                                many=True,
                                attribute='_filter_by_category.by_category.inner.buckets'
                                )
    by_openness_score = fields.Nested(Aggregation,
                                      many=True,
                                      attribute='_filter_by_openness_score.by_openness_score.buckets'
                                      )
    by_tag = fields.Nested(Aggregation,
                           many=True,
                           attribute='_filter_by_tag.by_tag.buckets'
                           )


class DatasetApiRelationships(Relationships):
    institution = fields.Nested(Relationship, many=False,
                                _type='institution',
                                path='institutions',
                                url_template='{api_url}/institutions/{ident}',
                                )
    resources = fields.Nested(Relationship,
                              many=False,
                              _type='resource',
                              url_template='{object_url}/resources',
                              )

    @pre_dump
    def prepare_data(self, data):
        if not self.context.get('is_listing', False):
            data['resources'] = data['resources'].filter(status='published')
        return data


class DatasetApiAttrs(ObjectAttrs):
    title = TranslatedStr()
    slug = TranslatedStr()
    notes = TranslatedStr()
    category = fields.Nested(DatasetCategoryAttr, many=False)
    formats = fields.List(fields.String)
    tags = TranslatedTagsList(TranslatedStr(), attr='tags_list')
    openness_scores = fields.List(fields.Int())
    license_condition_db_or_copyrighted = fields.String()
    license_condition_modification = fields.Boolean()
    license_condition_original = fields.Boolean()
    license_condition_responsibilities = fields.String()
    license_condition_source = fields.Boolean()
    license_condition_timestamp = fields.Boolean()
    license_name = fields.String()
    license_description = fields.String()
    update_frequency = TransUpdateFreqField()
    views_count = fields.Integer()
    url = fields.String()
    followed = fields.Boolean()
    modified = fields.DateTime()
    resource_modified = fields.DateTime()
    created = fields.DateTime()
    verified = fields.DateTime()

    class Meta:
        relationships_schema = DatasetApiRelationships
        object_type = 'dataset'
        url_template = '{api_url}/datasets/{ident}'


class DatasetApiResponse(TopLevel):
    class Meta:
        attrs_schema = DatasetApiAttrs
        aggs_schema = DatasetApiAggregations


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
