from unittest.mock import MagicMock, patch

import pytest
from celery.states import SUCCESS

import mcod
from mcod.resources.factories import (
    ResourceCsvFactory,
    ResourceJsonFactory,
    ResourceTxtFactory,
    ResourceXlsxFactory,
)
from mcod.resources.models import Resource
from mcod.resources.tasks.entrypoint_res_file import (
    entrypoint_process_resource_file_validation_task,
)
from mcod.resources.tests.test_entrypoints_tasks._helpers import (
    assert_no_extra_celery_tasks,
    build_signature,
    build_status_signature,
)


def test_resource_file_entrypoint_runs_celery_tasks_in_expected_order():
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published", openness_score=5)
    Resource.raw.filter(pk=resource.pk).update(openness_score=1)
    task_calls = []
    # Keep the full task chain visible, including nested fan-out hidden by mocked parents.
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
        "mcod.resources.tasks.entrypoint_res_file.process_resource_res_file_task.apply",
        side_effect=lambda *args, **kwargs: process_file_signature.apply(*args, **kwargs),
    ), patch(
        "mcod.resources.tasks.entrypoint_res_file.update_resource_openness_score",
        side_effect=update_resource_openness_score,
    ), patch(
        "mcod.resources.tasks.entrypoint_res_file.update_resource_verification_date",
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
        entrypoint_process_resource_file_validation_task(
            resource.files.first().pk,
            update_link=False,
        )

    # THEN
    assert task_calls == [
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


@pytest.mark.parametrize(
    "resource_factory, data_validation_expected",
    [
        (ResourceCsvFactory, True),
        (ResourceXlsxFactory, True),
        (ResourceTxtFactory, False),
        (ResourceJsonFactory, False),
    ],
)
def test_resource_file_data_validation_task_call_only_for_processable_resources(resource_factory, data_validation_expected: bool):
    # GIVEN
    resource: Resource = resource_factory.create()
    mock_sig = MagicMock()
    file_signature = build_status_signature(SUCCESS)
    with patch(
        "mcod.resources.tasks.entrypoint_res_file.process_resource_res_file_task.s",
        return_value=file_signature,
    ), patch.object(mcod.resources.models.process_resource_file_data_task, "apply", return_value=mock_sig) as mock_apply, patch(
        "mcod.resources.tasks.entrypoint_res_file.update_resource_openness_score"
    ), patch(
        "mcod.resources.tasks.entrypoint_res_file.update_resource_verification_date"
    ), patch(
        "mcod.resources.models.Resource.update_es_and_rdf_db"
    ):
        # WHEN
        entrypoint_process_resource_file_validation_task(resource.files.first().id)

        # THEN
        if data_validation_expected:
            args, kwargs = mock_apply.call_args
            assert resource.is_data_processable
            assert args == ()
            assert kwargs == {"args": (resource.id,)}
            assert mock_apply.call_count == 1
        else:
            assert not resource.is_data_processable
            assert mock_apply.call_count == 0


def test_resource_file_entrypoint_skips_followup_when_file_validation_fails(patch_resource_file_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_file_entrypoint(file_status="FAILURE") as mocks:
        # WHEN
        entrypoint_process_resource_file_validation_task(resource.files.first().pk)

    # THEN
    mocks["run_file_data_validation"].assert_not_called()
    mocks["update_resource_openness_score"].assert_called_once_with(resource.pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource.pk)
    # ES/RDF is NOT triggered when file validation fails (production returns early)
    mocks["schedule_es_and_rdf_update"].assert_not_called()


def test_resource_file_entrypoint_creates_success_link_task_result_when_update_link_enabled(patch_resource_file_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_file_entrypoint() as mocks:  # noqa: F841
        # WHEN
        entrypoint_process_resource_file_validation_task(resource.files.first().pk, update_link=True)

    # THEN – verify a link task was actually persisted in the DB
    resource.refresh_from_db()
    assert resource.link_tasks.count() == 1
    assert resource.link_tasks_last_status == SUCCESS


def test_resource_file_entrypoint_skips_success_link_task_result_when_update_link_disabled(patch_resource_file_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_file_entrypoint() as mocks:
        # WHEN
        entrypoint_process_resource_file_validation_task(resource.files.first().pk, update_link=False)

    # THEN
    mocks["run_file_data_validation"].assert_called_once()
    mocks["update_resource_openness_score"].assert_called_once_with(resource.pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource.pk)
    mocks["schedule_es_and_rdf_update"].assert_called_once()
    # No link task should have been created
    resource.refresh_from_db()
    assert resource.link_tasks.count() == 0


def test_resource_file_entrypoint_creates_success_task_result_in_database(patch_resource_file_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_file_entrypoint():
        # WHEN – link task creation is always inline (real DB) in production
        entrypoint_process_resource_file_validation_task(resource.files.first().pk, update_link=True)

    # THEN
    resource.refresh_from_db()
    latest_link_task = resource.link_tasks.latest("id")
    assert latest_link_task.status == SUCCESS
    assert resource.link_tasks_last_status == SUCCESS


def test_resource_file_entrypoint_reraises_when_success_link_task_result_creation_raises(patch_resource_file_entrypoint):
    # GIVEN
    resource: Resource = ResourceCsvFactory.create(status="published")
    with patch_resource_file_entrypoint() as mocks, patch(
        "mcod.resources.tasks.entrypoint_res_file.prepare_url_task_result_for_resource",
        side_effect=RuntimeError("boom"),
    ):
        # WHEN – production re-raises the exception after logging
        with pytest.raises(RuntimeError):
            entrypoint_process_resource_file_validation_task(resource.files.first().pk, update_link=True)

    # THEN
    mocks["update_resource_openness_score"].assert_called_once_with(resource.pk)
    mocks["update_resource_verification_date"].assert_called_once_with(resource.pk)
    # ES/RDF is never reached when an exception propagates
    mocks["schedule_es_and_rdf_update"].assert_not_called()
