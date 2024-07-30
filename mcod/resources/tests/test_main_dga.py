import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from unittest import mock
from unittest.mock import MagicMock, call

import pandas as pd
import pytest
from django.conf import settings
from django.db.models import QuerySet

from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.dga_utils import (
    add_style_to_main_dga_excel_file,
    check_all_resource_validations_status,
    clean_up_after_main_dga_resource_creation,
    create_main_dga_dataset,
    create_main_dga_df,
    create_main_dga_file,
    create_main_dga_resource_with_dataset,
    get_all_dga_resources,
    get_dga_resource_for_institution,
    get_main_dga_dataset,
    get_main_dga_resource,
    get_or_create_main_dga_path,
    update_or_create_aggr_dga_info_and_delete_old_main_dga,
)
from mcod.resources.exceptions import FailedValidationException, PendingValidationException
from mcod.resources.factories import DGAResourceFactory, MainDGAResourceFactory, ResourceFactory
from mcod.resources.models import AggregatedDGAInfo, Resource, ResourceFile
from mcod.resources.tasks import create_main_dga_resource_task


@pytest.mark.feat_main_dga
def test_get_main_dga_resource(dga_info: AggregatedDGAInfo):
    main_dga_resource: Optional[Resource] = get_main_dga_resource()
    assert main_dga_resource == dga_info.resource


@pytest.mark.feat_main_dga
def test_get_main_dga_dataset(dga_info: AggregatedDGAInfo):
    main_dga_dataset: Optional[Dataset] = get_main_dga_dataset()
    assert main_dga_dataset == dga_info.resource.dataset


@pytest.mark.feat_main_dga
def test_get_dga_resource_for_dga_owner(main_dga_resource: Resource):
    dga_owner: Organization = main_dga_resource.dataset.organization

    # second DGA Resource creation for Main DGA Resource Owner
    dataset: Dataset = DatasetFactory.create(organization=dga_owner)
    dga_resource: Resource = DGAResourceFactory.create(dataset=dataset)

    institution_res: Optional[Resource] = get_dga_resource_for_institution(
        organization_id=dga_owner.pk,
    )
    assert institution_res == dga_resource


@pytest.mark.feat_main_dga
def test_create_main_dga_dataset(main_dga_owner_organization: Organization):
    dataset_pk: int = create_main_dga_dataset()
    assert Dataset.objects.filter(pk=dataset_pk).exists()

    dataset: Dataset = Dataset.objects.get(pk=dataset_pk)
    assert dataset.title == settings.MAIN_DGA_DATASET_DEFAULT_TITLE
    assert dataset.notes == settings.MAIN_DGA_DATASET_DEFAULT_DESC
    assert dataset.organization == main_dga_owner_organization
    assert dataset.update_notification_recipient_email == settings.MAIN_DGA_DATASET_UPDATE_NOTIFICATION_EMAIL
    assert dataset.has_dynamic_data is False
    assert dataset.has_high_value_data is False
    assert dataset.has_research_data is False
    assert dataset.update_frequency == "daily"
    assert dataset.status == "published"
    assert list(dataset.categories.values_list("title", flat=True)) == settings.MAIN_DGA_DATASET_CATEGORIES_TITLES
    assert list(dataset.tags.values_list("name", flat=True)) == settings.MAIN_DGA_DATASET_TAGS_NAMES


@pytest.mark.feat_main_dga
def test_get_all_dga_resources(main_dga_resource: Resource):
    dga_resources: List[Resource] = DGAResourceFactory.create_batch(5)

    # Creation of Resources that should not be included
    DGAResourceFactory.create_batch(3, status="draft")
    DGAResourceFactory.create_batch(2, status="published", is_removed=True)

    all_dga_resources: QuerySet = get_all_dga_resources()

    assert len(all_dga_resources) == 5
    assert main_dga_resource not in all_dga_resources

    for resource in dga_resources:
        assert resource in all_dga_resources

    # check if Resources are sorted by Organization title
    expected_organization_titles: List[str] = sorted([resource.dataset.organization.title for resource in dga_resources])
    organization_titles: List[str] = list(all_dga_resources.values_list("dataset__organization__title", flat=True))
    assert organization_titles == expected_organization_titles


@pytest.mark.feat_main_dga
@pytest.mark.parametrize("is_path_exists", [True, False])
@mock.patch("mcod.resources.dga_utils.datetime")
@mock.patch("mcod.resources.dga_utils.os.makedirs")
@mock.patch("mcod.resources.dga_utils.os.path.exists")
def test_get_or_create_main_dga_path(
    mock_path_exists: MagicMock,
    mock_makedirs: MagicMock,
    mock_datetime: MagicMock,
    is_path_exists: bool,
):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20251201"
    mock_path_exists.return_value = is_path_exists

    directory: Path = Path(settings.MAIN_DGA_RESOURCE_XLSX_CREATION_ROOT)
    file_path: Path = get_or_create_main_dga_path()

    if is_path_exists:
        mock_makedirs.assert_not_called()
    else:
        mock_makedirs.assert_called_once_with(directory)

    expected_file_name = "Wykaz zasobów chronionych DGA – wykaz zbiorczy – " "Ministerstwo Cyfryzacji 20251201.xlsx"
    expected_path: Path = directory / expected_file_name
    assert file_path == expected_path


@pytest.mark.feat_main_dga
def test_create_main_dga_df(dga_resources_with_df):
    dga_resources, expected_df = dga_resources_with_df
    main_dga_df: pd.DataFrame = create_main_dga_df(dga_resources)

    # Ensure that the "Lp." column correctly contains a sequence from 1 to the
    # number of rows in expected_df.
    assert main_dga_df["Lp."].tolist() == list(range(1, len(expected_df) + 1))

    # Because DataFrames are constructed from data that may be loaded lazily,
    # the row order can differ each time the DataFrame is generated.
    # Sorting ensures that the data comparison is independent of row order,
    # focusing solely on the content accuracy and structure.
    main_dga_df = main_dga_df.drop(columns=["Lp."])
    expected_df = expected_df.drop(columns=["Lp."])

    expected_df_sorted = expected_df.sort_values(by=list(expected_df.columns)).reset_index(drop=True)
    main_dga_df_sorted = main_dga_df.sort_values(by=list(main_dga_df.columns)).reset_index(drop=True)

    assert main_dga_df_sorted.equals(expected_df_sorted)


@pytest.mark.feat_main_dga
def test_create_empty_main_dga_df():
    empty_queryset: QuerySet = Resource.objects.none()
    main_dga_df: pd.DataFrame = create_main_dga_df(empty_queryset)
    assert main_dga_df.empty


@pytest.mark.feat_main_dga
@pytest.mark.parametrize(
    ("data_status", "file_status", "link_status", "exception", "data_failure"),
    [
        ("SUCCESS", "SUCCESS", "SUCCESS", None, None),
        ("", "", "", PendingValidationException, None),
        ("SUCCESS", "", "", PendingValidationException, None),
        ("", "SUCCESS", "", PendingValidationException, None),
        ("", "", "SUCCESS", PendingValidationException, None),
        ("FAILURE", "SUCCESS", "SUCCESS", None, ["Brak wierszy z danymi"]),
        (
            "FAILURE",
            "SUCCESS",
            "",
            PendingValidationException,
            ["Brak wierszy z danymi"],
        ),
        (
            "FAILURE",
            "SUCCESS",
            "SUCCESS",
            FailedValidationException,
            ["Brak wierszy z danymi", "Another Error"],
        ),
        (
            "FAILURE",
            "SUCCESS",
            "SUCCESS",
            FailedValidationException,
            ["Unexpected Error"],
        ),
        ("FAILURE", "FAILURE", "FAILURE", FailedValidationException, None),
        ("SUCCESS", "FAILURE", "SUCCESS", FailedValidationException, None),
        ("SUCCESS", "SUCCESS", "FAILURE", FailedValidationException, None),
        ("", "FAILURE", "", FailedValidationException, None),
        ("", "", "FAILURE", FailedValidationException, None),
    ],
)
def test_check_all_resource_validations_status(
    data_status: str,
    file_status: str,
    link_status: str,
    exception: Optional[Exception],
    data_failure: Optional[List[str]],
):
    resource = MagicMock()
    resource.data_tasks_last_status = data_status
    resource.file_tasks_last_status = file_status
    resource.link_tasks_last_status = link_status

    last_task = MagicMock()
    last_task.message = data_failure
    resource.data_tasks.last = MagicMock(return_value=last_task)

    if exception:
        with pytest.raises(exception):
            check_all_resource_validations_status(resource)
    else:
        check_all_resource_validations_status(resource)
        assert True


@pytest.mark.feat_main_dga
def test_create_main_dga_resource_with_dataset(
    main_dga_owner_organization: Organization,
):
    file_path: str = f"{os.path.join(settings.TEST_SAMPLES_PATH, 'example_main_dga_file.xlsx')}"
    resource_pk, dataset_pk = create_main_dga_resource_with_dataset(file_path)

    assert resource_pk
    assert dataset_pk

    resource = Resource.objects.get(pk=resource_pk)
    dataset = Dataset.objects.get(pk=dataset_pk)

    assert resource.title == settings.MAIN_DGA_RESOURCE_DEFAULT_TITLE
    assert resource.description == settings.MAIN_DGA_RESOURCE_DEFAULT_DESC
    assert resource.dataset == dataset
    assert resource.dataset.institution == main_dga_owner_organization
    assert resource.has_dynamic_data is False
    assert resource.has_high_value_data is False
    assert resource.has_research_data is False
    assert resource.contains_protected_data is True
    assert resource.status == "published"

    resource_files = ResourceFile.objects.filter(resource=resource)

    assert resource_files.count() == 1
    assert resource_files.first().is_main is True


@pytest.mark.feat_main_dga
def test_update_aggr_dga_info(dga_info: AggregatedDGAInfo, main_dga_dataset: Dataset):
    """
    Tests update_or_create_aggr_dga_info_and_delete_old_main_dga method
    when main DGA Resource already exists.
    """
    old_resource: Resource = dga_info.resource
    views_count: int = old_resource.dataset.computed_views_count
    downloads_count: int = old_resource.dataset.computed_downloads_count

    new_resource: Resource = MainDGAResourceFactory.create(dataset=main_dga_dataset)

    update_or_create_aggr_dga_info_and_delete_old_main_dga(new_resource)

    old_resource.refresh_from_db()
    assert old_resource.is_removed is True

    dga_info.refresh_from_db()
    assert dga_info.main_dga_resource == new_resource
    assert new_resource.dataset.computed_views_count == views_count
    assert new_resource.dataset.downloads_count == downloads_count


@pytest.mark.feat_main_dga
def test_create_aggr_dga_info(main_dga_dataset: Dataset):
    """
    Tests update_or_create_aggr_dga_info_and_delete_old_main_dga method
    when main DGA Resource does not exist.
    """
    resource: Resource = MainDGAResourceFactory.create(dataset=main_dga_dataset)
    update_or_create_aggr_dga_info_and_delete_old_main_dga(resource)

    dga_info: AggregatedDGAInfo = AggregatedDGAInfo.objects.last()
    assert dga_info
    assert dga_info.main_dga_resource == resource


@pytest.mark.feat_main_dga
@pytest.mark.parametrize(
    ("resource_id", "dataset_id", "exc_occurred"),
    [
        (123, 456, False),
        (123, 456, True),
        (123, None, False),
        (123, None, True),
        (None, None, True),
        (None, None, False),
    ],
)
@mock.patch("mcod.resources.dga_utils.sentry_sdk.api.capture_exception")
@mock.patch("mcod.resources.dga_utils.os.remove")
@mock.patch("mcod.resources.dga_utils.key_generator_for_create_main_dga_resource")
@mock.patch("mcod.resources.dga_utils.key_generator_for_create_main_xlsx_file")
@mock.patch("mcod.resources.dga_utils.caches")
def test_clean_up_after_main_dga_resource_creation(
    mock_caches: MagicMock,
    mock_xlsx_key: MagicMock,
    mock_objects_key: MagicMock,
    mock_os_remove: MagicMock,
    mock_sentry: MagicMock,
    resource_id: Optional[int],
    dataset_id: Optional[int],
    exc_occurred: bool,
):
    # Set return values to cache key generators
    mock_xlsx_key.return_value = "xlsx_key"
    mock_objects_key.return_value = "objects_key"

    # Create objects
    dataset: Optional[Dataset] = DatasetFactory.create(pk=dataset_id) if dataset_id else None

    if dataset and resource_id:
        ResourceFactory.create(pk=resource_id, dataset=dataset)
    else:
        ResourceFactory.create(pk=resource_id)

    # Set mock cache side effect
    def get_mock_cache_side_effect(key, default=None):
        values = {
            "objects_key": (resource_id, dataset_id),
            "xlsx_key": "/path/to/temporary/file.xlsx",
        }
        return values.get(key, default)

    mock_cache: MagicMock = MagicMock()
    mock_cache.get.side_effect = get_mock_cache_side_effect
    mock_caches.__getitem__.return_value = mock_cache

    # Test function call
    clean_up_after_main_dga_resource_creation(exc_occurred)
    if exc_occurred:
        assert Resource.raw.filter(pk=resource_id).exists() is False
        assert Dataset.raw.filter(pk=dataset_id).exists() is False
    else:
        assert bool(resource_id) is Resource.raw.filter(pk=resource_id).exists()
        assert bool(dataset_id) is Dataset.raw.filter(pk=dataset_id).exists()

    mock_os_remove.assert_called_once_with("/path/to/temporary/file.xlsx")
    mock_cache.delete.assert_has_calls([call("objects_key"), call("xlsx_key")])


@pytest.mark.feat_main_dga
def test_add_style_to_main_dga_excel_file_smoke():
    source_file_path = Path(settings.TEST_SAMPLES_PATH, "example_main_dga_file.xlsx")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Given
        temp_file_path = Path(temp_dir, "file_name.xlsx")
        shutil.copy(source_file_path, temp_file_path)
        original_mtime: float = os.path.getmtime(temp_file_path)
        # When
        add_style_to_main_dga_excel_file(temp_file_path, "Arkusz 1")
        # Then
        assert original_mtime != os.path.getmtime(temp_file_path)


@pytest.mark.feat_main_dga
@mock.patch("mcod.resources.dga_utils.get_or_create_main_dga_path")
@mock.patch("mcod.resources.dga_utils.get_all_dga_resources")
@mock.patch("mcod.resources.dga_utils.create_main_dga_df")
@mock.patch("mcod.resources.dga_utils.save_df_to_xlsx")
@mock.patch("mcod.resources.dga_utils.add_style_to_main_dga_excel_file")
def test_create_main_dga_file(
    mock_add_style_to_main_dga_excel_file: MagicMock,
    mock_save_df_to_xlsx: MagicMock,
    mock_create_main_dga_df: MagicMock,
    mock_get_all_dga_resources: MagicMock,
    mock_get_or_create_main_dga_path: MagicMock,
):
    # Set mocks
    mock_get_or_create_main_dga_path.return_value = Path("path", "to", "dga_file.xlsx")

    mock_df = MagicMock()
    mock_create_main_dga_df.return_value = mock_df

    mock_dga_resources = MagicMock()
    mock_get_all_dga_resources.return_value = mock_dga_resources

    # Test function call
    result = create_main_dga_file()

    # Check functions calls with appropriate arguments
    mock_get_or_create_main_dga_path.assert_called_once()
    mock_get_all_dga_resources.assert_called_once()
    mock_create_main_dga_df.assert_called_once_with(mock_dga_resources)
    mock_save_df_to_xlsx.assert_called_once_with(
        df=mock_df,
        file_path=Path("path", "to", "dga_file.xlsx"),
        sheet_name=settings.MAIN_DGA_XLSX_WORKSHEET_NAME,
    )
    mock_add_style_to_main_dga_excel_file.assert_called_once_with(
        file_path=Path("path", "to", "dga_file.xlsx"),
        sheet_name=settings.MAIN_DGA_XLSX_WORKSHEET_NAME,
    )

    # Check result
    assert result == Path("path", "to", "dga_file.xlsx")


@pytest.mark.feat_main_dga
class TestMainDGAResourceCreationTask:
    """
    Test Class for create_main_dga_resource_task possible scenarios.
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """
        Mock functions used in the creation of Main DGA resource task.
        """
        self.resource_mock = MagicMock()
        self.resource_objects_get_mock = MagicMock()
        self.resource_mock.objects = MagicMock(get=self.resource_objects_get_mock)
        with mock.patch(
            "mcod.resources.tasks.apps.get_model", return_value=self.resource_mock
        ) as self.mock_get_model, mock.patch("mcod.resources.tasks.create_main_dga_file") as self.mock_create_file, mock.patch(
            "mcod.resources.tasks.create_main_dga_resource_with_dataset"
        ) as self.mock_create_resource, mock.patch(
            "mcod.resources.tasks.check_all_resource_validations_status"
        ) as self.mock_check_status, mock.patch(
            "mcod.resources.tasks.update_or_create_aggr_dga_info_and_delete_old_main_dga"
        ) as self.mock_update_aggr_dga_info, mock.patch(
            "mcod.resources.tasks.clean_up_after_main_dga_resource_creation"
        ) as self.mock_clean_up:  # noqa: E501
            yield

    def test_main_dga_resource_creation_task(self):
        # Set up mocks
        self.mock_create_file.return_value = "/path/to/dga_file.xlsx"
        self.mock_create_resource.return_value = (10, 2)

        # Test function call
        create_main_dga_resource_task()

        # Assertions
        self.mock_create_file.assert_called_once()
        self.mock_create_resource.assert_called_once_with(file_path="/path/to/dga_file.xlsx")
        self.resource_objects_get_mock.assert_called_once_with(pk=10)
        self.mock_check_status.assert_called_once_with(self.resource_objects_get_mock.return_value)
        self.mock_update_aggr_dga_info.assert_called_once_with(self.resource_objects_get_mock.return_value)
        self.mock_clean_up.assert_called_once_with(exception_occurred=False)

    def test_main_dga_file_creation_exception(self):
        # Exception raised in Step 1: xlsx file creation
        self.mock_create_file.side_effect = Exception()

        # Test function call
        with pytest.raises(Exception):
            create_main_dga_resource_task()

        # Assertions
        self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    def test_main_dga_resource_creation_exception(self):
        # Set up mocks
        self.mock_create_file.return_value = "/path/to/dga_file.xlsx"

        # Exception raised in Step 2: Main DGA Resource creation
        self.mock_create_resource.side_effect = Exception()

        # Test function call
        with pytest.raises(Exception):
            create_main_dga_resource_task()

        # Assertions
        self.mock_create_file.assert_called_once()
        self.mock_create_resource.assert_called_once_with(file_path="/path/to/dga_file.xlsx")
        self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    @pytest.mark.parametrize(
        "exception",
        [
            Exception,
            PendingValidationException,
            FailedValidationException,
        ],
    )
    def test_validations_exception(self, exception: Exception):
        # Set up mocks
        self.mock_create_file.return_value = "/path/to/dga_file.xlsx"
        self.mock_create_resource.return_value = (10, 2)

        # Exception raised in Step 3: Check resource validations
        self.mock_check_status.side_effect = exception

        # Test function call
        with pytest.raises(exception):
            create_main_dga_resource_task()

        # Assertions
        self.mock_create_file.assert_called_once()
        self.mock_create_resource.assert_called_once_with(file_path="/path/to/dga_file.xlsx")
        self.resource_objects_get_mock.assert_called_once_with(pk=10)
        self.mock_check_status.assert_called_once_with(self.resource_objects_get_mock.return_value)
        if exception is PendingValidationException:
            self.mock_clean_up.assert_not_called()
        else:
            self.mock_clean_up.assert_called_once_with(exception_occurred=True)

    def test_update_aggr_dga_info_exception(self):
        # Set up mocks
        self.mock_create_file.return_value = "/path/to/dga_file.xlsx"
        self.mock_create_resource.return_value = (10, 2)

        # Exception raised in Step 4: Update Aggregated DGA Info
        self.mock_update_aggr_dga_info.side_effect = Exception()

        # Test function call
        with pytest.raises(Exception):
            create_main_dga_resource_task()

        # Assertions
        self.mock_create_file.assert_called_once()
        self.mock_create_resource.assert_called_once_with(file_path="/path/to/dga_file.xlsx")
        self.resource_objects_get_mock.assert_called_once_with(pk=10)
        self.mock_check_status.assert_called_once_with(self.resource_objects_get_mock.return_value)
        self.mock_update_aggr_dga_info.assert_called_once_with(self.resource_objects_get_mock.return_value)
        self.mock_clean_up.assert_called_once_with(exception_occurred=True)
