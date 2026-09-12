from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import pytest
from celery.states import SUCCESS

from mcod.resources.tests.test_entrypoints_tasks._helpers import build_status_signature


@pytest.fixture
def patch_resource_entrypoint():
    @contextmanager
    def _patch(
        url_status=SUCCESS,
        file_status=None,
        patch_file_validation=True,
        patch_file_data_validation=True,
        patch_es_rdf_update=True,
    ):
        with ExitStack() as stack:
            mocks = {}
            mocks["url_signature"] = build_status_signature(url_status)
            stack.enter_context(
                patch(
                    "mcod.resources.tasks.entrypoint_res.process_resource_from_url_task.apply",
                    side_effect=lambda *args, **kwargs: mocks["url_signature"].apply(*args, **kwargs),
                )
            )
            if patch_file_validation:
                if file_status is None:
                    mocks["process_file_task"] = stack.enter_context(
                        patch("mcod.resources.tasks.entrypoint_res.process_resource_res_file_task.apply")
                    )
                else:
                    file_signature = build_status_signature(file_status)
                    mocks["process_file_task"] = stack.enter_context(
                        patch(
                            "mcod.resources.tasks.entrypoint_res.process_resource_res_file_task.apply",
                            side_effect=lambda *args, **kwargs: file_signature.apply(*args, **kwargs),
                        )
                    )
            if patch_file_data_validation:
                mocks["run_file_data_validation"] = stack.enter_context(
                    patch("mcod.resources.models.Resource.revalidate_tabular_data")
                )
            if patch_es_rdf_update:
                mocks["schedule_es_and_rdf_update"] = stack.enter_context(
                    patch("mcod.resources.models.Resource.update_es_and_rdf_db")
                )
            mocks["update_resource_openness_score"] = stack.enter_context(
                patch("mcod.resources.tasks.entrypoint_res.update_resource_openness_score")
            )
            mocks["update_resource_verification_date"] = stack.enter_context(
                patch("mcod.resources.tasks.entrypoint_res.update_resource_verification_date")
            )
            yield mocks

    return _patch


@pytest.fixture
def patch_resource_file_entrypoint():
    @contextmanager
    def _patch(
        file_status=SUCCESS,
        patch_file_data_validation=True,
        patch_es_rdf_update=True,
    ):
        with ExitStack() as stack:
            mocks = {}
            mocks["file_signature"] = build_status_signature(file_status)
            stack.enter_context(
                patch(
                    "mcod.resources.tasks.entrypoint_res_file.process_resource_res_file_task.apply",
                    side_effect=lambda *args, **kwargs: mocks["file_signature"].apply(*args, **kwargs),
                )
            )
            if patch_file_data_validation:
                mocks["run_file_data_validation"] = stack.enter_context(
                    patch("mcod.resources.models.Resource.revalidate_tabular_data")
                )
            if patch_es_rdf_update:
                mocks["schedule_es_and_rdf_update"] = stack.enter_context(
                    patch("mcod.resources.models.Resource.update_es_and_rdf_db")
                )
            mocks["update_resource_openness_score"] = stack.enter_context(
                patch("mcod.resources.tasks.entrypoint_res_file.update_resource_openness_score")
            )
            mocks["update_resource_verification_date"] = stack.enter_context(
                patch("mcod.resources.tasks.entrypoint_res_file.update_resource_verification_date")
            )
            yield mocks

    return _patch
