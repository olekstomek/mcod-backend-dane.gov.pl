from datetime import date
from functools import partial
from typing import Optional

import falcon
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mcod.core.api.handlers import CreateOneHdlr, RemoveOneHdlr
from mcod.core.api.hooks import login_optional, login_required
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.submissions.models import Category, Subject, SubmissionEvent
from mcod.submissions.service import create_submission_event
from mcod.suggestions.deserializers import (
    AcceptedSubmissionCommentApiRequest,
    CreateDatasetSubmissionRequest,
    CreateFeedbackRequest,
)
from mcod.suggestions.handlers import (
    AcceptedSubmissionRetrieveOneHdlr,
    AcceptedSubmissionSearchHdlr,
)
from mcod.suggestions.models import AcceptedDatasetSubmission, DatasetSubmission
from mcod.suggestions.serializers import (
    AcceptedSubmissionApiResponse,
    AcceptedSubmissionCommentApiResponse,
    PublicSubmissionApiResponse,
    SubmissionApiResponse,
)
from mcod.suggestions.tasks import (
    send_accepted_submission_comment,
    send_dataset_suggestion_mail_task,
)

User = get_user_model()


class AcceptedSubmissionListView(JsonAPIView):
    @falcon.before(login_required, roles=["editor", "admin", "agent"])
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @versioned
    def on_get_public_submission(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GETPublic, *args, **kwargs)

    class GET(AcceptedSubmissionSearchHdlr):
        pass

    class GETPublic(AcceptedSubmissionSearchHdlr):
        serializer_schema = partial(PublicSubmissionApiResponse, many=True)

        def _queryset_extra(self, queryset, *args, **kwargs):
            return queryset.filter("term", is_published_for_all=True)


class AcceptedSubmissionDetailView(JsonAPIView):
    @falcon.before(login_required, roles=["editor", "admin", "agent"])
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @versioned
    def on_get_public_submission(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GETPublic, *args, **kwargs)

    class GET(AcceptedSubmissionRetrieveOneHdlr):
        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, "_cached_instance", None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status__in=model.PUBLISHED_STATUSES)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

    class GETPublic(AcceptedSubmissionRetrieveOneHdlr):
        serializer_schema = partial(PublicSubmissionApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, "_cached_instance", None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status=model.STATUS.published, is_published_for_all=True)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance


class SubmissionView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = CreateDatasetSubmissionRequest
        database_model = apps.get_model("suggestions", "DatasetSubmission")
        serializer_schema = partial(SubmissionApiResponse, many=False)

        def _get_data(self, cleaned, *args, **kwargs):
            _data = cleaned["data"]["attributes"]
            _data["submission_date"] = date.today().strftime("%Y-%m-%d")
            if self.request.user and self.request.user.is_authenticated:
                _data["submitted_by"] = self.request.user

            applicant_full_name = _data.pop("applicant_full_name", None)
            applicant_email = _data.pop("applicant_email", None)
            return self._create_dataset_submission(_data, applicant_full_name, applicant_email)

        def _create_dataset_submission(self, data: dict, applicant_full_name: Optional[str], applicant_email: Optional[str]):
            """Create a dataset submission, register a submission event, and schedule the notification email."""
            submission = DatasetSubmission(**data)
            submission.save()
            event: Optional[SubmissionEvent] = create_submission_event(
                reference_object=submission,
                submission_date=submission.created,
                subject=Subject.DATA,
                category=Category.SUGGEST_DATA,
            )
            event_id: Optional[int] = event.id if event else None
            send_dataset_suggestion_mail_task.apply_async_on_commit(
                args=(submission.id, event_id, applicant_full_name, applicant_email)
            )
            return submission


class FeedbackDatasetSubmission(JsonAPIView):
    @falcon.before(login_required, roles=["editor", "admin", "agent"])
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        return self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = apps.get_model("suggestions", "SubmissionFeedback")
        submission_model = apps.get_model("suggestions", "AcceptedDatasetSubmission")
        deserializer_schema = CreateFeedbackRequest
        serializer_schema = partial(AcceptedSubmissionApiResponse, many=False)

        def clean(self, *args, **kwargs):
            cleaned = super().clean(*args, **kwargs)
            if cleaned["data"]["attributes"]["opinion"] not in ("plus", "minus"):
                raise falcon.HTTPBadRequest(description=_("Valid values are 'plus' and 'minus'"))
            return cleaned

        def _get_data(self, cleaned, id, *args, **kwargs):
            data = cleaned["data"]["attributes"]
            submission: Optional[AcceptedDatasetSubmission] = self.submission_model.objects.filter(pk=id).first()
            if not submission:
                raise falcon.HTTPNotFound
            if submission.status != "published":
                raise falcon.HTTPConflict(description="Not published Submission")
            if not submission.is_active:
                raise falcon.HTTPConflict(description="Not active Submission")

            obj = self.database_model.objects.update_or_create(user=self.request.user, submission=submission, defaults=data)[0]
            self.response.context.data = obj

    @falcon.before(login_required, roles=["editor", "admin", "agent"])
    @versioned
    def on_delete(self, request, response, *args, **kwargs):
        return self.handle_delete(request, response, self.DELETE, *args, **kwargs)

    class DELETE(RemoveOneHdlr):
        database_model = apps.get_model("suggestions", "SubmissionFeedback")

        def clean(self, id, *args, **kwargs):
            try:
                return self.database_model.objects.get(submission__id=id, user=self.request.user)
            except self.database_model.DoesNotExist:
                raise falcon.HTTPNotFound


class AcceptedDatasetSubmissionCommentView(JsonAPIView):

    @falcon.before(login_optional)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        return self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = apps.get_model("suggestions", "AcceptedDatasetSubmission")
        deserializer_schema = partial(AcceptedSubmissionCommentApiRequest, many=False)
        serializer_schema = partial(AcceptedSubmissionCommentApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, "_cached_instance", None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status=model.STATUS.published, is_published_for_all=True)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

        def clean(self, id, *args, **kwargs):
            cleaned = super().clean(id, *args, **kwargs)
            self._get_instance(id, *args, **kwargs)
            return cleaned

        def _get_data(self, cleaned, id, *args, **kwargs):
            instance = self._get_instance(id, *args, **kwargs)
            send_accepted_submission_comment.s(
                instance.id,
                cleaned["data"]["attributes"]["comment"],
            ).apply_async()
            setattr(instance, "is_comment_email_sent", True)
            return instance
