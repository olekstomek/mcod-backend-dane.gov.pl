from mcod.core.api.jsonapi.serializers import ObjectAttrs, TopLevel


class SubmissionAttrs(ObjectAttrs):
    class Meta:
        object_type = 'submission'
        path = 'submissions'
        url_template = '{api_url}/submissions/{ident}'


class SubmissionApiResponse(TopLevel):
    class Meta:
        attrs_schema = SubmissionAttrs
