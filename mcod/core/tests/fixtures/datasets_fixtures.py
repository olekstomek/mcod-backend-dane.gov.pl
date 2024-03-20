from typing import Callable, Type

import pytest

from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.datasets.factories import DatasetFactory
from mcod.organizations.documents import Dataset
from mcod.resources.factories import ResourceFactory


@pytest.fixture
def dataset_with_resources_factory() -> Type[Callable]:
    """Dataset and resources factory fixture."""

    def create_ds(**kwargs):
        dataset = DatasetFactory.create(**kwargs)
        ResourceFactory.create_batch(2, dataset=dataset)
        run_on_commit_events()
        return dataset

    return create_ds


@pytest.fixture
def dataset_with_resources(dataset_with_resources_factory, tmp_path, mocker) -> Dataset:
    """Create dataset with resources."""
    return dataset_with_resources_factory(mocker=mocker, tmp_path=tmp_path)
