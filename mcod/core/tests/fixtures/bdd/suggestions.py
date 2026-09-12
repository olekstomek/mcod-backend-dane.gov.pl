import pytest

from mcod.suggestions.factories import DatasetSubmission, ResourceCommentFactory


@pytest.fixture
def dataset_submission():
    return DatasetSubmission.create()


@pytest.fixture
def resource_comment():
    return ResourceCommentFactory.create()
