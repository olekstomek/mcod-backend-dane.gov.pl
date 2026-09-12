from unittest.mock import MagicMock, patch

import pytest
from celery.states import SUCCESS

from mcod.resources.factories import ApiResourceFactory, ResourceCsvFactory
from mcod.resources.models import Resource
from mcod.resources.tasks.entrypoint_res import entrypoint_process_resource_validation_task
from mcod.resources.tests.test_entrypoints_tasks._helpers import (
    assert_no_extra_celery_tasks,
    build_signature,
)


def test_resource_entrypoint_runs_celery_tasks_in_expected_order_for_file_resource():
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published", openness_score=5)
    Resource.raw.filter(pk=resource.pk).update(openness_score=1)
    task_calls = []
    # Keep the full task chain visible, including nested fan-out hidden by mocked parents.
    process_url_signature = build_signature(
        task_calls,
        "process_resource_from_url_task",
        "apply",
        MagicMock(status=SUCCESS),
    )
    process_file_signature = build_signature(
        task_calls,
        "process_resource_res_file_task",
        "apply",
        MagicMock(status=SUCCESS),
    )

    def update_resource_openness_score(resource_pk: int):
        Resource.raw.filter(pk=resource_pk).update(openness_score=7)
        task_calls.append(("update_resource_openness_score", "call", Resource.raw.get(pk=resource_pk).openness_score))

    def update_resource_verification_date(resource_pk: int):
        task_calls.append(("update_resource_verification_date", "call"))

    # `process_resource_file_data_task.apply` normally spawns
    # `increase_openness_score_task.apply_async_on_commit`, so the mock replays that nested call.
    process_file_data_signature = build_signature(task_calls, "process_resource_file_data_task", "apply")

    def process_resource_file_data_task(*args, **kwargs):
        from mcod.resources.tasks.process_resource_file_data import increase_openness_score_task

        result = process_file_data_signature.apply(*args, **kwargs)
        increase_openness_score_task.apply_async_on_commit(args=(resource.pk,))
        return result

    def increase_openness_score_task(*args, **kwargs):
        task_calls.append(("increase_openness_score_task", "apply_async_on_commit"))

    def update_with_related_task(*args, **kwargs):
        task_calls.append(("update_with_related_task", "apply_async", Resource.raw.get(pk=resource.pk).openness_score))

    def update_graph_task(*args, **kwargs):
        task_calls.append(("update_graph_task", "apply_async_on_commit", Resource.raw.get(pk=resource.pk).openness_score))

    with assert_no_extra_celery_tasks(), patch(
        "mcod.resources.tasks.entrypoint_res.process_resource_from_url_task.apply",
        side_effect=lambda *args, **kwargs: process_url_signature.apply(*args, **kwargs),
    ), patch(
        "mcod.resources.tasks.entrypoint_res.process_resource_res_file_task.apply",
        side_effect=lambda *args, **kwargs: process_file_signature.apply(*args, **kwargs),
    ), patch(
        "mcod.resources.tasks.entrypoint_res.update_resource_openness_score",
        side_effect=update_resource_openness_score,
    ), patch(
        "mcod.resources.tasks.entrypoint_res.update_resource_verification_date",
        side_effect=update_resource_verification_date,
    ), patch(
        "mcod.resources.models.process_resource_file_data_task.apply",
        side_effect=process_resource_file_data_task,
    ), patch(
        "mcod.resources.tasks.process_resource_file_data.increase_openness_score_task.apply_async_on_commit",
        side_effect=increase_openness_score_task,
    ), patch(
        "mcod.resources.models.update_with_related_task.apply_async",
        side_effect=update_with_related_task,
    ), patch(
        "mcod.resources.models.update_graph_task.apply_async_on_commit",
        side_effect=update_graph_task,
    ):
        # WHEN
        entrypoint_process_resource_validation_task(resource.pk)

    # THEN
    assert task_calls == [
        ("process_resource_from_url_task", "apply"),
        ("process_resource_res_file_task", "apply"),
        ("process_resource_file_data_task", "apply"),
        ("increase_openness_score_task", "apply_async_on_commit"),
        # openness_score is written to DB *before* the ES/RDF tasks are scheduled,
        # so the Celery workers will read the correct value from the DB.
        ("update_resource_openness_score", "call", 7),
        ("update_resource_verification_date", "call"),
        ("update_with_related_task", "apply_async", 7),
        ("update_graph_task", "apply_async_on_commit", 7),
    ]


def test_resource_entrypoint_skips_followup_when_url_validation_fails(patch_resource_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_entrypoint(url_status="FAILURE") as mocks:
        # WHEN
        entrypoint_process_resource_validation_task(resource.pk)

    # THEN
    mocks["process_file_task"].assert_not_called()
    mocks["run_file_data_validation"].assert_not_called()
    mocks["update_resource_openness_score"].assert_called_once_with(resource.pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource.pk)
    # ES/RDF is NOT triggered when URL validation fails (production returns early)
    mocks["schedule_es_and_rdf_update"].assert_not_called()


def test_resource_entrypoint_handles_missing_main_file(patch_resource_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    resource.files.all().delete()
    with patch_resource_entrypoint() as mocks:
        # WHEN
        entrypoint_process_resource_validation_task(resource.pk)

    # THEN
    mocks["process_file_task"].assert_not_called()
    # Data validation still runs even without a main file
    mocks["run_file_data_validation"].assert_called_once_with(apply_on_commit=False)


def test_resource_entrypoint_skips_file_validation_for_api_without_forced_file_type(patch_resource_entrypoint):
    # GIVEN
    resource: Resource = ApiResourceFactory.create(status="published")

    with patch_resource_entrypoint() as mocks:
        # WHEN
        entrypoint_process_resource_validation_task(resource.pk)

    # THEN
    mocks["process_file_task"].assert_not_called()
    mocks["run_file_data_validation"].assert_not_called()
    mocks["update_resource_openness_score"].assert_called_once_with(resource.pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource.pk)
    mocks["schedule_es_and_rdf_update"].assert_called_once()


def test_resource_entrypoint_skips_file_data_validation_when_file_validation_fails(patch_resource_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_entrypoint(file_status="FAILURE") as mocks:
        # WHEN
        entrypoint_process_resource_validation_task(resource.pk)

    # THEN
    mocks["run_file_data_validation"].assert_not_called()


def test_resource_entrypoint_skips_file_validation_when_resource_is_missing(patch_resource_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    resource_pk = resource.pk + 1000000
    with patch_resource_entrypoint() as mocks:
        # WHEN – production re-raises the DoesNotExist coming from Resource.raw.get
        with pytest.raises(Resource.DoesNotExist):
            entrypoint_process_resource_validation_task(resource_pk)

    # THEN
    mocks["process_file_task"].assert_not_called()
    mocks["run_file_data_validation"].assert_not_called()
    # finally block still fires
    mocks["update_resource_openness_score"].assert_called_once_with(resource_pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource_pk)
    # ES/RDF is never reached when an exception is raised
    mocks["schedule_es_and_rdf_update"].assert_not_called()
