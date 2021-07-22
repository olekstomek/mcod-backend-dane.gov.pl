from marshmallow import pre_dump
from django.utils.translation import gettext_lazy as _

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import (
    Relationships,
    ObjectAttrs,
    TopLevel,
    Relationship,
    Aggregation,
    HighlightObjectMixin
)
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer
from mcod.lib.serializers import TranslatedStr, TranslatedTagsList, KeywordsList
from mcod.watchers.serializers import SubscriptionMixin


class ExternalDataset(ExtSchema):
    title = fields.String()
    url = fields.String()


class ApplicationApiRelationships(Relationships):
    datasets = fields.Nested(Relationship,
                             many=False, default=[],
                             _type='dataset',
                             url_template='{object_url}/datasets',
                             )
    subscription = fields.Nested(Relationship, many=False, _type='subscription',
                                 url_template='{api_url}/auth/subscriptions/{ident}')

    @pre_dump
    def prepare_datasets(self, data, **kwargs):
        if not self.context.get('is_listing', False) and 'datasets' in data:
            data['datasets'] = data['datasets'].filter(status='published')
        return data


class ApplicationApiAggs(ExtSchema):
    by_created = fields.Nested(Aggregation,
                               many=True,
                               attribute='_filter_by_created.by_created.buckets'
                               )
    by_modified = fields.Nested(Aggregation,
                                many=True,
                                attribute='_filter_by_modified.by_modified.buckets'
                                )
    by_tag = fields.Nested(Aggregation,
                           many=True,
                           attribute='_filter_by_tag.by_tag.inner.buckets'
                           )
    by_keyword = fields.Nested(Aggregation,
                               many=True,
                               attribute='_filter_by_keyword.by_keyword.inner.inner.buckets'
                               )


class ApplicationApiAttrs(ObjectAttrs, HighlightObjectMixin):
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    author = fields.Str(faker_type='firstname')
    url = fields.Str(faker_type='url')
    image_url = fields.Str(faker_type='image_url')
    image_thumb_url = fields.Str(faker_type='image_thumb_url')
    image_alt = TranslatedStr()
    illustrative_graphics_url = fields.Str()
    illustrative_graphics_alt = TranslatedStr()
    followed = fields.Boolean(faker_type='boolean')
    tags = TranslatedTagsList(TranslatedStr(), faker_type='tagslist')
    keywords = KeywordsList(TranslatedStr(), faker_type='tagslist')
    views_count = fields.Integer(faker_type='integer')
    modified = fields.Str(faker_type='datetime')
    created = fields.Str(faker_type='datetime')
    has_image_thumb = fields.Bool()
    main_page_position = fields.Int()
    external_datasets = fields.Nested(ExternalDataset, many=True)

    class Meta:
        relationships_schema = ApplicationApiRelationships
        object_type = 'application'
        url_template = '{api_url}/applications/{ident}'
        model = 'applications.Application'


class ApplicationApiResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = ApplicationApiAttrs
        aggs_schema = ApplicationApiAggs


class ApplicationProposalCSVSerializer(CSVSerializer):
    id = fields.Int(data_key='id', required=True, example=77)
    title = fields.Str(data_key=_('Application name'), example='Nazwa aplikacji')
    notes = fields.Str(data_key=_('Notes'), default='', example='opis...')
    url = fields.Str(data_key=_('App URL'), default='', example='http://example.com')
    author = fields.Str(data_key=_('Author'), default='', example='Jan Kowalski')
    applicant_email = fields.Email(
        data_key=_('applicant email'), default='', required=False, example='user@example.com')
    keywords = fields.Str(data_key=_('keywords'), attribute='keywords_as_str', default='', example='tag1,tag2,tag3')
    report_date = fields.Date(data_key=_('report date'))
    decision_date = fields.Date(data_key=_('decision date'), default=None)
    comment = fields.Str(data_key=_('comment'), example='komentarz...', default='')
    datasets = fields.Method('get_datasets', data_key=_('datasets'), example='998,999', default='')
    external_datasets = fields.Raw(data_key=_('external datasets'), example='[]')
    application = fields.Int(data_key=_('Application'), attribute='application.id', default=None)

    class Meta:
        ordered = True
        model = 'applications.ApplicationProposal'

    def get_datasets(self, obj):
        return ','.join(str(x.id) for x in obj.datasets.order_by('id'))


class SubmissionAttrs(ObjectAttrs):
    title = fields.Str()
    url = fields.URL()
    applicant_email = fields.Email()

    class Meta:
        object_type = 'application-submission'
        path = 'submissions'
        url_template = '{api_url}/applications/submissions/{ident}'


class SubmissionApiResponse(TopLevel):
    class Meta:
        attrs_schema = SubmissionAttrs
