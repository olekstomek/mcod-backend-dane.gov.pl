import csv
import datetime
import json
import os
from pathlib import Path
from time import sleep
from typing import Dict, List
from unittest import mock

import pandas as pd
import pytest
import pytz
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.test import override_settings

from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.reports.models import SummaryDailyReport
from mcod.reports.tasks import create_daily_resources_report, generate_csv
from mcod.users.models import User as User_model

User = get_user_model()
Report = apps.get_model("reports", "Report")
TaskResult = apps.get_model("django_celery_results", "TaskResult")


@pytest.fixture
def admin_with_id_1(admin: User_model) -> User_model:
    admin.id = 1
    admin.email = "testadmin@test.example.com"
    admin.save()
    return admin


class TestTasks:
    def test_generate_csv(self, active_user_with_last_login: User, admin: User):
        request_date = datetime.datetime(2018, 12, 4)
        eager = generate_csv.s(
            [active_user_with_last_login.id, admin.id],
            User._meta.label,
            active_user_with_last_login.id,
            request_date.strftime("%Y%m%d%H%M%S.%s"),
        ).apply_async(countdown=1)

        sleep(1)
        assert eager

        result_task = TaskResult.objects.get(task_id=eager)
        result_dict = json.loads(result_task.result)

        assert result_dict["model"] == "users.User"
        assert "date" in result_dict
        assert result_dict["user_email"] == active_user_with_last_login.email
        assert result_dict["csv_file"].startswith("/media/reports/users/")
        assert result_dict["csv_file"].endswith(request_date.strftime("%Y%m%d%H%M%S.%s") + ".csv")

        r = Report.objects.get(task=result_task)

        assert r.task == result_task
        assert r.task.status == "SUCCESS"
        assert r.file == result_dict["csv_file"]
        assert r.ordered_by == active_user_with_last_login
        assert r.model == "users.User"
        file_path = os.path.join(settings.TEST_ROOT, result_dict["csv_file"].strip("/"))
        with open(file_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

        local_tz = pytz.timezone(settings.TIME_ZONE)
        localized_active_user_last_login = active_user_with_last_login.last_login.astimezone(local_tz)
        expected_active_user_last_login = localized_active_user_last_login.strftime("%Y-%m-%dT%H:%M:%S+02:00\n")
        for line in lines:
            split_line = line.split(";")
            assert len(split_line) == 17
            if split_line[1] == active_user_with_last_login.email:
                assert split_line[16] == expected_active_user_last_login

    def test_invalid_user_ordering_report(self, active_user):
        request_date = datetime.datetime.now()
        eager = generate_csv.delay(
            [
                active_user.id,
            ],
            User._meta.label,
            active_user.id + 100,
            request_date.strftime("%Y%m%d%H%M%S.%s"),
        )

        assert eager
        result_task = TaskResult.objects.get(task_id=eager)
        r = Report.objects.get(task=result_task)
        assert r.task == result_task
        assert r.task.status == "FAILURE"

    def test_columns_in_user_csv_report(self, tmp_path: str, active_user):
        """Check if required columns are present in csv metadata report."""

        columns_required = [
            "id",
            "Email",
            "Imię i nazwisko",
            "telefon służbowy",
            "Edytor",
            "Urzędnik",
            "Administrator",
            "Administrator AOD",
            "Administrator LOD",
            "Pełnomocnik",
            "Dodatkowy pełnomocnik",
            "Stan",
            "Instytucja1",
            "Instytucja2",
            "Powiązanie z WK",
            "Sposób ostatniego logowania",
            "Data ostatniego logowania",
        ]

        with override_settings(REPORTS_MEDIA_ROOT=tmp_path):
            file_name_postfix = "csv_test"
            user_ids = [user.pk for user in User.objects.all()]
            generate_csv(user_ids, "users.User", active_user.pk, file_name_postfix)
            filename = "users_" + file_name_postfix + ".csv"
            file = Path(tmp_path) / "users" / filename
            dataframe_report = pd.read_csv(file, sep=";")

            for column in columns_required:
                assert column in dataframe_report

    def test_wrong_model_report(self, active_user):
        request_date = datetime.datetime.now()
        eager = generate_csv.delay(
            [active_user.id],
            "users.WrongModel",
            active_user.id,
            request_date.strftime("%Y%m%d%H%M%S.%s"),
        )

        assert eager
        result_task = TaskResult.objects.get(task_id=eager)
        r = Report.objects.get(task=result_task)
        assert r.task == result_task
        assert r.task.status == "FAILURE"

    @pytest.mark.usefixtures("resource")
    def test_create_daily_resources_report(self, admin_with_id_1):
        request_date = datetime.datetime.now().strftime("%Y_%m_%d_%H")
        create_daily_resources_report()
        r = SummaryDailyReport.objects.last()

        assert r
        assert r.file.startswith("media/reports/daily/Zbiorczy_raport_dzienny_")
        assert r.file.endswith(".csv")
        assert request_date in r.file

    def test_counters_in_daily_report(self, admin_with_id_1, resource_with_counters):
        create_daily_resources_report()
        r = SummaryDailyReport.objects.last()
        file_path = f"{settings.TEST_ROOT}/{r.file}"
        with open(file_path, "r") as report_file:
            reader = csv.reader(report_file, delimiter=",")
            headers: List[str] = next(reader)
            resource_data: List[str] = next(reader)
            resource_data_with_headers: Dict[str, str] = {header: value for header, value in zip(headers, resource_data)}
        views_count = ResourceViewCounter.objects.filter(resource_id=resource_with_counters.pk).aggregate(views_sum=Sum("count"))[
            "views_sum"
        ]
        downloads_count = ResourceDownloadCounter.objects.filter(resource_id=resource_with_counters.pk).aggregate(
            downloads_sum=Sum("count")
        )["downloads_sum"]

        assert int(resource_data_with_headers["Liczba wyswietlen"]) == views_count
        assert int(resource_data_with_headers["Liczba pobran"]) == downloads_count

    @pytest.mark.usefixtures("resource")
    @mock.patch("mcod.reports.tasks.datetime")
    def test_daily_resources_report_includes_all_required_metadata_fields(self, mock_datetime, tmp_path, admin_with_id_1):
        """
        Test whether the daily resources report correctly includes all
        necessary metadata fields.
        """
        mock_datetime.datetime.now.return_value.strftime.return_value = "2020_02_05_2310"
        with override_settings(REPORTS_MEDIA_ROOT=tmp_path):
            create_daily_resources_report()
            report_file = Path(tmp_path, "daily", "Zbiorczy_raport_dzienny_2020_02_05_2310.csv")
            dataframe_report = pd.read_csv(report_file, sep=",")
            # DGA
            assert "Zasob zawiera wykaz chronionych danych" in dataframe_report
            # Resource metadata
            assert "Zasob posiada dane wysokiej wartosci" in dataframe_report
            assert "Zasob posiada dane wysokiej wartosci z wykazu KE" in dataframe_report
            assert "Zasob posiada dane dynamiczne" in dataframe_report
            assert "Zasob posiada dane badawcze" in dataframe_report
            # Dataset metadata
            assert "Zbior danych posiada dane wysokiej wartosci" in dataframe_report
            assert "Zbior danych posiada dane wysokiej wartosci z wykazu KE" in dataframe_report
            assert "Zbior danych posiada dane dynamiczne" in dataframe_report
            assert "Zbior danych posiada dane badawcze" in dataframe_report
