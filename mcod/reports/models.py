from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from model_utils.models import TimeStampedModel

User = get_user_model()


class Report(TimeStampedModel):
    ordered_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Ordered by"),
        related_name='reports_ordered'
    )
    task = models.ForeignKey(
        TaskResult,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Task"),
        related_name='report'
    )
    model = models.CharField(null=True, max_length=80)
    file = models.CharField(null=True, max_length=512, verbose_name=_('File path'))

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")


class UserReport(Report):
    class Meta:
        proxy = True
        verbose_name = _("User report")
        verbose_name_plural = _("User reports")


class ResourceReport(Report):
    class Meta:
        proxy = True
        verbose_name = _("Reource report")
        verbose_name_plural = _("Resource reports")


class DatasetReport(Report):
    class Meta:
        proxy = True
        verbose_name = _("Dataset report")
        verbose_name_plural = _("Dataset reports")


class OrganizationReport(Report):
    class Meta:
        proxy = True
        verbose_name = _("Institution report")
        verbose_name_plural = _("Institution reports")


class SummaryDailyReport(TimeStampedModel):
    file = models.CharField(null=True, max_length=512, verbose_name=_('File path'))
    ordered_by = models.ForeignKey(
        User,
        models.SET_NULL,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Ordered by"),
        related_name='reports_ordered_by'
    )

    status = models.CharField(max_length=20, default="SUCCESS")

    class Meta:
        verbose_name = _("Summary daily report")
        verbose_name_plural = _("Summary daily reports")
