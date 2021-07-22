from django.utils.translation import gettext_lazy as _
from marshmallow import pre_dump, post_dump

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import \
    Relationships, ObjectAttrs, TopLevel, Relationship, Aggregation, HighlightObjectMixin
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer
from mcod.lib.serializers import TranslatedStr
from mcod.watchers.serializers import SubscriptionMixin


class InstitutionApiRelationships(Relationships):
    datasets = fields.Nested(Relationship,
                             many=False, default=[],
                             _type='dataset',
                             url_template='{object_url}/datasets',
                             )
    subscription = fields.Nested(Relationship, many=False, _type='subscription',
                                 url_template='{api_url}/auth/subscriptions/{ident}')

    @pre_dump
    def prepare_data(self, data, **kwargs):
        if not self.context.get('is_listing', False):
            data['datasets'] = data['datasets'].filter(status='published')
        return data


class InstitutionApiAggs(ExtSchema):
    by_created = fields.Nested(Aggregation,
                               many=True,
                               attribute='_filter_by_created.by_created.buckets',
                               )
    by_modified = fields.Nested(Aggregation,
                                many=True,
                                attribute='_filter_by_modified.by_modified.buckets',
                                )
    by_city = fields.Nested(Aggregation,
                            many=True,
                            attribute='_filter_by_city.by_city.buckets'
                            )
    by_institution_type = fields.Nested(Aggregation,
                                        many=True,
                                        attribute='_filter_by_institution_type.by_institution_type.buckets'
                                        )


class DataSourceAttr(ExtSchema):
    title = fields.Str()
    url = fields.URL()
    source_type = fields.Str()


class InstitutionApiAttrs(ObjectAttrs, HighlightObjectMixin):
    abbreviation = fields.Str()
    city = fields.Str()
    created = fields.Str()
    datasets_count = fields.Int(attribute='published_datasets_count')
    email = fields.Str()
    epuap = fields.Str()
    fax = fields.Str()
    flat_number = fields.Str()
    followed = fields.Boolean()
    image_url = fields.Str()
    institution_type = fields.Str()
    modified = fields.Str()
    description = TranslatedStr()
    postal_code = fields.Str()
    regon = fields.Str()
    resources_count = fields.Int(attribute='published_resources_count')
    slug = TranslatedStr()
    sources = fields.Nested(DataSourceAttr, many=True)
    street = fields.Str()
    street_number = fields.Str()
    street_type = fields.Str()
    tel = fields.Str()
    title = TranslatedStr()
    website = fields.Str()

    class Meta:
        relationships_schema = InstitutionApiRelationships
        object_type = 'institution'
        url_template = '{api_url}/institutions/{ident}'
        model = 'organizations.Organization'

    @post_dump(pass_many=False)
    def prepare_notes(self, data, **kwargs):
        data["notes"] = data.get("description")
        return data


class InstitutionApiResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = InstitutionApiAttrs
        aggs_schema = InstitutionApiAggs


class InstitutionCSVSchema(CSVSerializer):
    id = fields.Integer(data_key=_('ID'), required=True)
    title = fields.Str(data_key=_("Title"), default='')
    institution_type = fields.Str(data_key=_("Institution type"), default='')
    datasets_count = fields.Int(data_key=_("The number of datasets"), default=None)

    class Meta:
        ordered = True
        model = 'organizations.Organization'
