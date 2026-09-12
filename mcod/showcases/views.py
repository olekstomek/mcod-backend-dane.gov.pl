from functools import partial
from typing import Optional

import falcon
from django.apps import apps
from elasticsearch_dsl import Q

from mcod.core.api.handlers import CreateOneHdlr, RetrieveOneHdlr, SearchHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.datasets.deserializers import DatasetApiSearchRequest
from mcod.datasets.documents import DatasetDocument
from mcod.datasets.serializers import DatasetApiResponse
from mcod.showcases.deserializers import (
    CreateShowcaseProposalRequest,
    ShowcaseApiRequest,
    ShowcasesApiRequest,
)
from mcod.showcases.documents import ShowcaseDocument
from mcod.showcases.models import Showcase, ShowcaseProposal
from mcod.showcases.serializers import ShowcaseApiResponse, ShowcaseProposalApiResponse
from mcod.showcases.tasks import send_showcase_proposal_mail_task
from mcod.submissions.models import Category, Subject
from mcod.submissions.service import create_submission_event


class ShowcasesSearchHdlr(SearchHdlr):
    deserializer_schema = ShowcasesApiRequest
    serializer_schema = partial(ShowcaseApiResponse, many=True)
    search_document = ShowcaseDocument()

    def _queryset_extra(self, queryset, id=None, **kwargs):
        if id:
            queryset = queryset.query("nested", path="datasets", query=Q("term", **{"datasets.id": id}))
        return queryset.filter("term", status=Showcase.STATUS.published)


class ShowcasesApiView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/showcases/showcases_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(ShowcasesSearchHdlr):
        pass


class DatasetShowcasesApiView(JsonAPIView):

    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/datasets/dataset_showcases_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(ShowcasesSearchHdlr):
        pass


class ShowcaseApiView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/showcases/showcase_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = ShowcaseApiRequest
        database_model = apps.get_model("showcases.Showcase")
        serializer_schema = ShowcaseApiResponse

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, "_cached_instance", None)
            if not instance:
                model = self.database_model
                try:
                    user = getattr(self.request, "user", None)
                    data = {"id": id, "status": "published"}
                    if user and user.is_superuser:
                        data = {"id": id, "status__in": ["draft", "published"]}
                    self._cached_instance = model.objects.get(**data)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance


class ShowcaseDatasetsView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/showcases/showcase_datasets_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = DatasetApiSearchRequest
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetDocument()
        include_default = ["institution"]

        def _queryset_extra(self, queryset, id=None, **kwargs):
            queryset = queryset.query("nested", path="showcases", query=Q("term", **{"showcases.id": id})) if id else queryset
            return queryset.filter("term", status="published")


class ShowcaseProposalView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = apps.get_model("showcases.ShowcaseProposal")
        deserializer_schema = CreateShowcaseProposalRequest
        serializer_schema = ShowcaseProposalApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            _data = cleaned["data"]["attributes"]
            applicant_full_name = _data.pop("applicant_full_name", None)
            _data.pop("is_personal_data_processing_accepted", None)
            _data.pop("is_terms_of_service_accepted", None)
            return self._create_showcase_proposal(_data, applicant_full_name)

        def _create_showcase_proposal(self, data: dict, applicant_full_name: Optional[str]) -> ShowcaseProposal:
            """Create a showcase proposal, register a submission event, and schedule the notification email."""
            obj = ShowcaseProposal.create(data)
            event = create_submission_event(
                reference_object=obj,
                submission_date=obj.created,
                subject=Subject.DATA,
                category=Category.SUGGEST_REUSE,
            )
            event_id = event.id if event else None
            send_showcase_proposal_mail_task.apply_async_on_commit(args=(obj.id, event_id, applicant_full_name))
            return obj
