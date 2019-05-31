from django.utils.translation import gettext_lazy as _
from marshmallow import pre_dump

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import \
    Relationships, ObjectAttrs, TopLevel, Relationship, Aggregation
from mcod.core.api.schemas import ExtSchema
from mcod.core.serializers import CSVSerializer
from mcod.lib.serializers import TranslatedStr


class InstitutionApiRelationships(Relationships):
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


class InstitutionApiAggs(ExtSchema):
    by_city = fields.Nested(Aggregation,
                            many=True,
                            attribute='_filter_by_format.by_city.buckets'
                            )
    by_instytution_type = fields.Nested(Aggregation,
                                        many=True,
                                        attribute='_filter_by_type.by_instytution_type.buckets'
                                        )


class InstitutionApiAttrs(ObjectAttrs):
    slug = TranslatedStr()
    title = TranslatedStr()
    description = TranslatedStr()
    image_url = fields.Str()
    postal_code = fields.Str()
    city = fields.Str()
    street_type = fields.Str()
    street = fields.Str()
    street_number = fields.Str()
    flat_number = fields.Str()
    email = fields.Str()
    epuap = fields.Str()
    fax = fields.Str(attribute='fax_display')
    tel = fields.Str(attribute='phone_display')
    regon = fields.Str()
    website = fields.Str()
    institution_type = fields.Str()
    followed = fields.Boolean()
    modified = fields.Str()
    created = fields.Str()

    class Meta:
        relationships_schema = InstitutionApiRelationships
        object_type = 'institution'
        url_template = '{api_url}/institutions/{ident}'


class InstitutionApiResponse(TopLevel):
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
