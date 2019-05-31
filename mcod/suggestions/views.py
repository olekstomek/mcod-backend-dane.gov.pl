# Create your views here.
from collections import namedtuple
from functools import partial
from uuid import uuid4

from django.apps import apps

from mcod.core.api.handlers import CreateOneHdlr
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.suggestions.deserializers import CreateSubmissionRequest
from mcod.suggestions.serializers import SubmissionApiResponse
from mcod.suggestions.tasks import create_data_suggestion


class SubmissionView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = partial(CreateSubmissionRequest)
        database_model = apps.get_model('suggestions', 'Suggestion')
        serializer_schema = partial(SubmissionApiResponse, many=False)

        def _get_data(self, cleaned, *args, **kwargs):
            _data = cleaned['data']['attributes']
            create_data_suggestion.s(_data).apply_async(countdown=1)
            fields, values = [], []
            for field, val in _data.items():
                fields.append(field)
                values.append(val)
            fields.append('id')
            values.append(str(uuid4()))
            result = namedtuple('Submission', fields)(*values)
            return result
