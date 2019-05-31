from marshmallow import pre_dump

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import \
    Relationships, ObjectAttrs, TopLevel, Relationship, Aggregation
from mcod.core.api.schemas import ExtSchema
from mcod.lib.serializers import TranslatedStr, TranslatedTagsList


class ApplicationApiRelationships(Relationships):
    datasets = fields.Nested(Relationship,
                             many=False,
                             _type='dataset',
                             url_template='{object_url}/datasets',
                             )

    @pre_dump
    def prepare_data(self, data):
        if not self.context.get('is_listing', False):
            data['datasets'] = data['datasets'].filter(status='published')
        return data


class ApplicationApiAggs(ExtSchema):
    by_modified = fields.Nested(Aggregation,
                                many=True,
                                attribute='_filter_by_format.by_modified.buckets'
                                )


class ApplicationApiAttrs(ObjectAttrs):
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    author = fields.Str(faker_type='firstname')
    url = fields.Str(faker_type='url')
    image_url = fields.Str(faker_type='image_url')
    image_thumb_url = fields.Str(faker_type='image_thumb_url')
    followed = fields.Boolean(faker_type='boolean')
    tags = TranslatedTagsList(TranslatedStr(), faker_type='tagslist')
    views_count = fields.Integer(faker_type='integer')
    modified = fields.Str(faker_type='datetime')
    created = fields.Str(faker_type='datetime')

    class Meta:
        relationships_schema = ApplicationApiRelationships
        object_type = 'application'
        url_template = '{api_url}/applications/{ident}'


class ApplicationApiResponse(TopLevel):
    class Meta:
        attrs_schema = ApplicationApiAttrs
        aggs_schema = ApplicationApiAggs


class SubmissionAttrs(ObjectAttrs):
    class Meta:
        object_type = 'application-submission'
        path = 'submissions'
        url_template = '{api_url}/applications/submissions/{ident}'


class SubmissionApiResponse(TopLevel):
    class Meta:
        attrs_schema = SubmissionAttrs
