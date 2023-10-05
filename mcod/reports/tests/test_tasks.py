import csv
import datetime
import json
import os
from time import sleep

import pytz
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum

from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.reports.models import SummaryDailyReport
from mcod.reports.tasks import create_daily_resources_report, generate_csv

User = get_user_model()
Report = apps.get_model("reports", "Report")
TaskResult = apps.get_model("django_celery_results", "TaskResult")


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
        assert result_dict["csv_file"].endswith(
            request_date.strftime("%Y%m%d%H%M%S.%s") + ".csv"
        )

        r = Report.objects.get(task=result_task)

        assert r.task == result_task
        assert r.task.status == "SUCCESS"
        assert r.file == result_dict["csv_file"]
        assert r.ordered_by == active_user_with_last_login
        assert r.model == "users.User"
        file_path = os.path.join(
            settings.TEST_ROOT, result_dict["csv_file"].strip("/")
        )
        with open(file_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

        local_tz = pytz.timezone(settings.TIME_ZONE)
        localized_active_user_last_login = (
            active_user_with_last_login.last_login.astimezone(local_tz)
        )
        expected_active_user_last_login = (
            localized_active_user_last_login.strftime(
                "%Y-%m-%dT%H:%M:%S+02:00\n"
            )
        )
        for line in lines:
            split_line = line.split(";")
            assert len(split_line) == 15
            if split_line[1] == active_user_with_last_login.email:
                assert split_line[14] == expected_active_user_last_login

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

    def test_create_daily_resources_report(self, admin, resource):
        admin.id = 1
        admin.email = "testadmin@test.xx"
        admin.save()

        request_date = datetime.datetime.now().strftime("%Y_%m_%d_%H")
        create_daily_resources_report()
        r = SummaryDailyReport.objects.last()

        assert r
        assert r.file.startswith("media/reports/daily/Zbiorczy_raport_dzienny_")
        assert r.file.endswith(".csv")
        assert request_date in r.file

    def test_counters_in_daily_report(self, admin, resource_with_counters):
        admin.id = 1
        admin.email = "testadmin@test.xx"
        admin.save()
        create_daily_resources_report()
        r = SummaryDailyReport.objects.last()
        file_path = f"{settings.TEST_ROOT}/{r.file}"
        with open(file_path, "r") as report_file:
            reader = csv.reader(report_file, delimiter=",")
            next(reader)
            resource_data = next(reader)
        views_count = ResourceViewCounter.objects.filter(
            resource_id=resource_with_counters.pk
        ).aggregate(views_sum=Sum("count"))["views_sum"]
        downloads_count = ResourceDownloadCounter.objects.filter(
            resource_id=resource_with_counters.pk
        ).aggregate(downloads_sum=Sum("count"))["downloads_sum"]
        assert int(resource_data[13]) == views_count
        assert int(resource_data[14]) == downloads_count
