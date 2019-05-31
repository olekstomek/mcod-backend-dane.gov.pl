from mcod.core.api import fields as core_fields
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs


class CreateSubmissionAttrs(ObjectAttrs):
    notes = core_fields.String(description='Notes', example='Lorem Ipsum', required=True)

    class Meta:
        strict = True
        ordered = True
        object_type = 'submission'


class CreateSubmissionRequest(TopLevel):
    class Meta:
        attrs_schema = CreateSubmissionAttrs
