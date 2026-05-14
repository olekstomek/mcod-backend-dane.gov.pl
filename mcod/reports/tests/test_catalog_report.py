import csv
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import factory
import pytest
from django.test import override_settings
from django.utils import translation
from django.utils.translation import gettext as _
from pytest_mock import MockerFixture

from mcod.categories.factories import CategoryFactory
from mcod.datasets.documents import DataSource
from mcod.datasets.factories import DatasetFactory, SupplementFactory
from mcod.datasets.models import UPDATE_FREQUENCY
from mcod.datasets.tasks import create_xml_metadata_files
from mcod.organizations.factories import OrganizationFactory
from mcod.regions.factories import RegionFactory
from mcod.regions.models import Region
from mcod.reports.catalog import generate_catalog_csv_report
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource
from mcod.special_signs.factories import SpecialSignFactory
from mcod.tags.factories import EnglishTagFactory, PolishTagFactory
from mcod.tags.models import Tag


def assert_csv_exact_match(actual_rows, expected_rows, label="Report"):
    """
    Compares two CSV reports row by row.
    Fails fast with a detailed error message on the first mismatched row.
    Assumes index 0 contains headers.
    """
    # 1. Quick length check using assert
    assert len(actual_rows) == len(expected_rows), (
        f"[{label}] Row count mismatch! " f"Expected: {len(expected_rows)}, Actual: {len(actual_rows)}."
    )

    if not actual_rows:
        return  # Both lists are empty, test passes

    # Safe header extraction for error descriptions
    headers = expected_rows[0]

    # 2. Iterate row by row
    for row_idx, (act_row, exp_row) in enumerate(zip(actual_rows, expected_rows)):
        if act_row != exp_row:
            # 3. Extract only the differing columns
            diffs = []
            max_cols = max(len(act_row), len(exp_row))

            for col_idx in range(max_cols):
                # Fallback for missing columns if rows have different lengths
                act_val = act_row[col_idx] if col_idx < len(act_row) else "<MISSING_COLUMN>"
                exp_val = exp_row[col_idx] if col_idx < len(exp_row) else "<MISSING_COLUMN>"

                if act_val != exp_val:
                    # Get column name (or fallback if something is severely broken)
                    col_name = headers[col_idx] if col_idx < len(headers) else f"Column_Index_{col_idx}"

                    diffs.append(f"  -> [{col_name}]:\n" f"       expected: '{exp_val}'\n" f"       actual:   '{act_val}'")

            # 4. Format the final error message
            error_msg = (
                f"\n\n[{label}] MISMATCH DETECTED at row {row_idx} (where 0 is headers).\n"
                f"Cell differences:\n" + "\n".join(diffs)
            )

            # 5. Native assert with the built message
            assert act_row == exp_row, error_msg


class TestMetadataFileCreation:
    """
    Tests metadata file creation functionalities.

    Contains test methods for validating the creation of various types of metadata files
    and their proper handling under different conditions.

    The class includes tests for:
    - Creating XML and CSV metadata files.
    - Validating metadata file creation with previous file deletion.
    """

    @pytest.mark.parametrize(
        "extension, task",
        [
            ("xml", create_xml_metadata_files),
            ("csv", generate_catalog_csv_report),
        ],
    )
    @pytest.mark.usefixtures("tmp_path", "mocker")
    def test_create_metadata_files(self, tmp_path: str, mocker: "MockerFixture", extension, task):
        """
        Tests the creation of XML metadata files.

        Validates the creation of XML metadata files by executing a specified task and
        verifying the existence of a file in 'tmp_path' with a specific naming format.

        Args:
        - tmp_path (str): Temporary directory provided for testing.
        - mocker (MockerFixture): Pytest mocker fixture for mocking objects.
        - extension (str): Expected extension of the metadata file.
        - task (callable): The task generating the metadata file.
        """
        with override_settings(METADATA_MEDIA_ROOT=tmp_path):
            # Create a mock for datetime.
            # Ensure that test will not fail due to datetime.today().date()
            new_today = self.mock_date(year=2023, month=12, day=24, mocker=mocker)

            task()
            file = Path(f"{tmp_path}") / f"pl/katalog_{new_today}.{extension}"
            assert file.is_file()

    @staticmethod
    def mock_date(mocker: "MockerFixture", year: int, month: int, day: int) -> date:
        """
        Mocks the current date with a specified year, month, and day.
        Returns:
        - new_today (datetime.date): The newly created date object with specified values.
        """
        new_today = date(year=year, month=month, day=day)
        datetime_mock = mocker.Mock()
        datetime_mock.today.return_value.date.return_value = new_today
        mocker.patch("mcod.datasets.tasks.datetime", datetime_mock)
        mocker.patch("mcod.reports.catalog.generator.datetime", datetime_mock)

        return new_today

    @pytest.mark.parametrize(
        "extension, task",
        [
            ("xml", create_xml_metadata_files),
            ("csv", generate_catalog_csv_report),
        ],
    )
    @pytest.mark.usefixtures("tmp_path", "mocker")
    def test_create_metadata_files_with_deletion_previous(self, tmp_path, mocker, task, extension):
        """
        Tests metadata file creation with previous file deletion.

        Validates the creation of metadata files while simulating file deletion
        and recreation. It ensures the proper creation and deletion of files
        based on the specified conditions.
        """
        with override_settings(METADATA_MEDIA_ROOT=tmp_path):
            new_today = self.mock_date(year=2023, month=12, day=24, mocker=mocker)
            task()
            file = Path(f"{tmp_path}") / f"pl/katalog_{new_today}.{extension}"

            new_today2 = self.mock_date(year=2023, month=12, day=25, mocker=mocker)
            task()
            file2 = Path(f"{tmp_path}") / f"pl/katalog_{new_today2}.{extension}"

            assert not file.is_file()
            assert file2.is_file()

    @staticmethod
    def _get_expected_report_headers(lang: str) -> List[str]:
        with translation.override(lang):
            headers = [
                _("Dataset URL"),
                _("Title"),
                _("Notes"),
                _("Tag"),
                _("Category"),
                _("Update frequency"),
                _("Dataset created"),
                _("Dataset verified"),
                _("Dataset views count"),
                _("Dataset downloads count"),
                _("Number of data"),
                _("Terms of use"),
                _("License"),
                _("source"),
                _("Dataset has high value data"),
                _("Dataset has high value data from the EC list"),
                _("Dataset has dynamic data"),
                _("Dataset has research data"),
                _("Dataset regions"),
                _("Dataset supplements (name, language, url, file size)"),
                _("Organization URL"),
                _("Institution type"),
                _("Name"),
                _("Abbreviation"),
                _("Id Institution"),
                _("REGON"),
                _("EPUAP"),
                _("Address for electronic delivery"),
                _("Website"),
                _("Organization created"),
                _("Organization modified"),
                _("Number of datasets"),
                _("Number of organization resources"),
                _("Postal code"),
                _("City"),
                _("Street type"),
                _("Street"),
                _("Street number"),
                _("Flat number"),
                _("Email"),
                _("Phone"),
                _("Resource URL"),
                _("Resource title"),
                _("Resource description"),
                _("Resource created"),
                _("Data date"),
                _("Openness score"),
                _("Type"),
                _("File format"),
                _("File size"),
                _("Resource views count"),
                _("Resource downloads count"),
                _("Table"),
                _("Map"),
                _("Chart"),
                _("Resource has high value data"),
                _("Resource has high value data from the EC list"),
                _("Resource has dynamic data"),
                _("Resource has research data"),
                _("Contains protected data list"),
                _("Resource regions"),
                _("Download URL"),
                _("special signs"),
                _("Resource supplements (name, language, url, file size)"),
            ]

            return [str(header) for header in headers]

    @staticmethod
    def _get_expected_csv_report_row_for_resource(resource: Resource, lang: str) -> List[str]:
        dataset = resource.dataset
        organization = resource.institution

        def get_nullable_bool_text(value: Optional[bool]) -> str:
            if value is None:
                return _("not specified")
            return _("YES") if value else _("NO")

        def get_source_text(source: Optional[DataSource]) -> str:
            if source is None:
                return ""
            title = f'{_("name")}: {source.title or ""}'
            url = f'{_("url")}: {source.url or ""}'
            last_import = (
                f'{_("last import timestamp")}: '
                f'{source.last_import_timestamp.isoformat() if source.last_import_timestamp else ""}'
            )
            frequency = f'{_("Update frequency")}: {source.update_frequency or ""}'
            return ", ".join([title, url, last_import, frequency])

        with translation.override(lang):
            row = [
                dataset.frontend_absolute_url,
                getattr(dataset, f"title_{lang}") or dataset.title,
                getattr(dataset, f"notes_{lang}") or dataset.notes,
                ", ".join(tag.name for tag in dataset.tags.filter(language=lang).order_by("name")),
                ", ".join(title for cat in dataset.categories.order_by("pk").all() if (title := getattr(cat, f"title_{lang}"))),
                dict(UPDATE_FREQUENCY).get(dataset.update_frequency, ""),
                dataset.created.isoformat(),
                dataset.verified.isoformat() if dataset.verified else "",
                dataset.computed_views_count,
                dataset.computed_downloads_count,
                dataset.resources.all().count(),
                dataset.formatted_condition_descriptions,
                dataset.license_name or "",
                get_source_text(dataset.source),
                get_nullable_bool_text(dataset.has_high_value_data),
                get_nullable_bool_text(dataset.has_high_value_data_from_ec_list),
                get_nullable_bool_text(dataset.has_dynamic_data),
                get_nullable_bool_text(dataset.has_research_data),
                dataset.regions_str,
                dataset.supplements_str,
                organization.frontend_absolute_url,
                organization.get_institution_type_display(),
                getattr(organization, f"title_{lang}") or organization.title,
                organization.abbreviation,
                organization.pk,
                organization.regon or "",
                organization.epuap or "",
                organization.electronic_delivery_address or "",
                organization.website or "",
                organization.created.isoformat(),
                organization.modified.isoformat(),
                organization.datasets_count,
                organization.published_resources_count,
                organization.postal_code or "",
                organization.city or "",
                organization.street_type or "",
                organization.street or "",
                organization.street_number or "",
                organization.flat_number or "",
                organization.email or "",
                organization.tel or "",
                resource.frontend_absolute_url,
                getattr(resource, f"title_{lang}") or resource.title,
                getattr(resource, f"description_{lang}") or resource.description,
                resource.created.isoformat(),
                resource.data_date,
                resource.openness_score,
                resource.get_type_display(),
                resource.format or "",
                resource.file_size_human_readable_or_empty_str,
                resource.computed_views_count,
                resource.computed_downloads_count,
                get_nullable_bool_text(resource.has_table),
                get_nullable_bool_text(resource.has_chart),
                get_nullable_bool_text(resource.has_map),
                get_nullable_bool_text(resource.has_high_value_data),
                get_nullable_bool_text(resource.has_high_value_data_from_ec_list),
                get_nullable_bool_text(resource.has_dynamic_data),
                get_nullable_bool_text(resource.has_research_data),
                get_nullable_bool_text(resource.contains_protected_data),
                resource.all_regions_str,
                resource.download_url,
                ", ".join(
                    f"{_('name')}: {getattr(sign, f'name_{lang}') or ''}, "
                    f"{_('symbol')}: \"{sign.symbol or ''}\", "
                    f"{_('description')}: {getattr(sign, f'description_{lang}') or ''}"
                    for sign in resource.special_signs.order_by("id")
                ),
                resource.supplements_str,
            ]

            return [str(val) for val in row]

    def test_generate_catalog_csv_report(
        self,
        mocker: "MockerFixture",
        tmp_path: str,
        django_assert_max_num_queries,
    ):

        pl_tags: List[Tag] = PolishTagFactory.create_batch(5)
        en_tags: List[Tag] = EnglishTagFactory.create_batch(5)

        organization_1 = OrganizationFactory.create()
        dataset_1 = DatasetFactory.create(organization=organization_1, id=1)
        dataset_1.tags.add(*pl_tags, *en_tags)
        resources_1 = ResourceFactory.create_batch(2, dataset=dataset_1)

        organization_2 = OrganizationFactory.create()
        dataset_2 = DatasetFactory.create(organization=organization_2, id=2)
        dataset_1.tags.add(pl_tags[0], *en_tags[3:])
        resources_2 = ResourceFactory.create_batch(3, dataset=dataset_2)

        resources_1 = [*resources_1, *ResourceFactory.create_batch(2, dataset=dataset_1)]

        dataset_supplement_1 = SupplementFactory.create(
            name="Supplement 1",
            name_en="English Supplement 1",
            dataset=dataset_1,
            file=factory.django.FileField(
                from_func=lambda: BytesIO(b"Some text 1"),
                filename="simple1.csv",
            ),
        )
        dataset_supplement_2 = SupplementFactory.create(
            name="Supplement 2",  # no english version
            dataset=dataset_2,
            file=factory.django.FileField(
                from_func=lambda: BytesIO(b"Some text 2"),
                filename="simple2.csv",
            ),
        )
        dataset_1.supplements.add(dataset_supplement_1)
        dataset_2.supplements.add(dataset_supplement_2)

        category1 = CategoryFactory.create(
            title="Test Category 1",
            title_en="English Test Category 1",
        )
        category2 = CategoryFactory.create(
            title="Test Category 2",
            title_en="English Test Category 2",
        )
        category3 = CategoryFactory.create(
            title="Test Category 3",  # no english version
        )
        dataset_1.categories.add(category1, category2, category3)
        dataset_2.categories.add(category1, category3)

        region: Region = RegionFactory.create(
            name="Łódź",
            name_en="Lodz",
            hierarchy_label="miasto",
            hierarchy_label_en="city",
        )
        resources_1[0].regions.add(region)

        sign_x = SpecialSignFactory.create(
            symbol="X",
            name="Znak specialny X",
            name_en="Special Sign X",
            description="Opis dla X",
            description_en="X description",
        )
        sign_y = SpecialSignFactory.create(
            symbol="Y",
            name="Znak specialny Y",
            description="Opis dla Y",
        )
        resources_1[0].special_signs.add(sign_x, sign_y)
        resources_2[0].special_signs.add(sign_x)

        ResourceFactory.create_batch(2, is_removed=True)
        ResourceFactory.create_batch(2, status="draft")

        assert Resource.objects.published().count() == 7
        assert Resource.objects.count() == 9
        assert Resource.raw.count() == 11

        for resource in [*resources_1, *resources_2]:
            resource.refresh_from_db()

        expected_pl_report_rows = [
            self._get_expected_report_headers("pl"),
            *[self._get_expected_csv_report_row_for_resource(res, lang="pl") for res in resources_1],
            *[self._get_expected_csv_report_row_for_resource(res, lang="pl") for res in resources_2],
        ]

        expected_en_report_rows = [
            self._get_expected_report_headers("en"),
            *[self._get_expected_csv_report_row_for_resource(res, lang="en") for res in resources_1],
            *[self._get_expected_csv_report_row_for_resource(res, lang="en") for res in resources_2],
        ]

        with override_settings(METADATA_MEDIA_ROOT=tmp_path):
            new_today = self.mock_date(year=2023, month=10, day=10, mocker=mocker)
            with django_assert_max_num_queries(23):
                generate_catalog_csv_report()
            pl_file = Path(tmp_path) / "pl" / f"katalog_{new_today}.csv"
            en_file = Path(tmp_path) / "en" / f"katalog_{new_today}.csv"

            assert pl_file.exists(), "Polish csv catalog report was not created."
            assert en_file.exists(), "English csv catalog report was not created."

            with open(pl_file, newline="", encoding="utf-8") as f:
                pl_file_content = list(csv.reader(f, delimiter=";"))

            with open(en_file, newline="", encoding="utf-8") as f:
                en_file_content = list(csv.reader(f, delimiter=";"))

            assert_csv_exact_match(pl_file_content, expected_pl_report_rows, "PL REPORT")
            assert_csv_exact_match(en_file_content, expected_en_report_rows, "EN REPORT")
