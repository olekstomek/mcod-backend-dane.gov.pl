from unittest.mock import patch

from mcod.datasets.models import Dataset
from mcod.resources.models import Resource
from mcod.submissions.models import Category, Subject
from mcod.suggestions.factories import (
    DatasetCommentFactory,
    DatasetSubmissionFactory,
    ResourceCommentFactory,
)
from mcod.suggestions.models import DatasetComment, DatasetSubmission, ResourceComment


def test_dataset_submission_creates_submission_event_on_creation_but_not_on_update() -> None:
    with patch("mcod.suggestions.models.create_submission_event") as mock_create:
        # creation - create_submission_event - called
        submission: DatasetSubmission = DatasetSubmissionFactory.create()
        mock_create.assert_called_once_with(
            reference_object=submission,
            submission_date=submission.created,
            subject=Subject.DATA,
            category=Category.SUGGEST_DATA,
        )
        mock_create.reset_mock()

        # update - create_submission_event - not called
        submission.title = "Updated title"
        submission.save()
        mock_create.assert_not_called()


def test_dataset_comment_creates_submission_event_on_creation_but_not_on_update(dataset: Dataset) -> None:
    with patch("mcod.suggestions.models.create_submission_event") as mock_create:
        # creation - create_submission_event - called
        comment: DatasetComment = DatasetCommentFactory.create(
            dataset=dataset,
            comment="Test comment",
        )
        mock_create.assert_called_once_with(
            reference_object=comment,
            submission_date=comment.created,
            subject=Subject.DATA,
            category=Category.FEEDBACK,
        )
        mock_create.reset_mock()

        # update - create_submission_event - not called
        comment.comment = "Updated comment"
        comment.save()
        mock_create.assert_not_called()


def test_resource_comment_creates_submission_event_on_creation_but_not_on_update(resource: Resource) -> None:
    with patch("mcod.suggestions.models.create_submission_event") as mock_create:
        # creation - create_submission_event - called
        comment: ResourceComment = ResourceCommentFactory.create(
            resource=resource,
            comment="Test comment",
        )
        mock_create.assert_called_once_with(
            reference_object=comment,
            submission_date=comment.created,
            subject=Subject.DATA,
            category=Category.FEEDBACK,
        )
        mock_create.reset_mock()

        # update - create_submission_event - not called
        comment.comment = "Updated comment"
        comment.save()
        mock_create.assert_not_called()
