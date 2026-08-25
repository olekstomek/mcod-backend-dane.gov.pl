from enum import Enum
from typing import List, Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


# TODO (django-upgrade): Replace with models.TextChoices after upgrading Django to 3.0+
class Subject(str, Enum):
    DATA = "DATA"
    PORTAL = "PORTAL"
    DATA_PROTECTION = "DATA_PROTECTION"
    LEGAL = "LEGAL"
    OTHER = "OTHER"


_SUBJECT_CHOICES = (
    (Subject.DATA, "Dane"),
    (Subject.PORTAL, "Portal dane.gov.pl"),
    (Subject.DATA_PROTECTION, "Ochrona danych osobowych w portalu"),
    (Subject.LEGAL, "Regulacje prawne dotyczące otwartości danych"),
    (Subject.OTHER, "Inne"),
)


class Category(str, Enum):
    SHARING = "SHARING"
    SUGGEST_DATA = "SUGGEST_DATA"
    SUGGEST_REUSE = "SUGGEST_REUSE"
    FEEDBACK = "FEEDBACK"
    STANDARDS = "STANDARDS"
    HVD = "HVD"
    DGA = "DGA"
    FEATURES = "FEATURES"
    PROFILES = "PROFILES"
    PERMISSIONS = "PERMISSIONS"
    BUGS = "BUGS"
    OTHER = "OTHER"


_CATEGORY_CHOICES = (
    (Category.SHARING, "Udostępnianie danych w portalu"),
    (Category.SUGGEST_DATA, "Zaproponuj dane do udostępnienia w portalu"),
    (Category.SUGGEST_REUSE, "Zaproponuj przykład ponownego wykorzystania danych"),
    (Category.FEEDBACK, "Zgłoś uwagi do danych udostępnionych w portalu"),
    (Category.STANDARDS, "Standardy otwartości danych"),
    (Category.HVD, "Dane o wysokiej wartości (HVD)"),
    (Category.DGA, "Chronione dane (DGA)"),
    (Category.FEATURES, "Funkcjonalności portalu"),
    (Category.PROFILES, "Zakładanie profili dostawców"),
    (Category.PERMISSIONS, "Nadawanie uprawnień"),
    (Category.BUGS, "Błędy w działaniu portalu"),
    (Category.OTHER, "Inne"),
)


SUBJECT_CATEGORY_DEPENDENCIES = {
    Subject.DATA: [
        Category.SHARING,
        Category.SUGGEST_DATA,
        Category.SUGGEST_REUSE,
        Category.FEEDBACK,
        Category.STANDARDS,
        Category.HVD,
        Category.DGA,
        Category.OTHER,
    ],
    Subject.PORTAL: [
        Category.FEATURES,
        Category.PROFILES,
        Category.PERMISSIONS,
        Category.BUGS,
        Category.OTHER,
    ],
    Subject.DATA_PROTECTION: [],
    Subject.LEGAL: [],
    Subject.OTHER: [],
}


class SubmissionEvent(models.Model):
    subject = models.CharField(
        max_length=32,
        choices=_SUBJECT_CHOICES,
        blank=False,
        verbose_name=_("Submission subject"),
    )
    category = models.CharField(
        max_length=32,
        choices=_CATEGORY_CHOICES,
        blank=True,
        verbose_name=_("Submission category"),
    )
    submission_date = models.DateTimeField(
        verbose_name=_("Submission date"),
    )
    reference_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Reference content type"),
        related_name="+",
    )
    reference_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Reference object id"),
    )
    reference_object = GenericForeignKey("reference_content_type", "reference_object_id")

    class Meta:
        verbose_name = _("Submission Event")
        verbose_name_plural = _("Submission Events")
        indexes = [
            models.Index(fields=["reference_content_type", "reference_object_id"], name="subm_evt_ref_ct_oid_idx"),
        ]

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()

        try:
            subject = Subject(self.subject)
        except ValueError:
            raise ValidationError({"subject": "Invalid subject."})

        category: Optional[Category] = None
        if self.category:
            try:
                category = Category(self.category)
            except ValueError:
                raise ValidationError({"category": "Invalid category."})

        valid_categories: List[Category] = SUBJECT_CATEGORY_DEPENDENCIES.get(subject, [])
        if not valid_categories:
            if category is not None:
                raise ValidationError({"category": "Invalid category selected for this subject."})
        elif category not in valid_categories:
            raise ValidationError({"category": "Invalid category selected for this subject."})
