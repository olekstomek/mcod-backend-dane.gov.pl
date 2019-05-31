import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField

from mcod.core.api.search import signals as search_signals
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel
from mcod.tags.signals import update_related_datasets, update_related_articles, update_related_applications

User = get_user_model()

STATUS_CHOICES = [
    ('published', _('Published')),
    ('draft', _('Draft')),
]

signal_logger = logging.getLogger('signals')


class Tag(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (update_related_datasets,
                    update_related_articles,
                    update_related_applications
                    ),
        'published': (update_related_datasets,
                      update_related_articles,
                      update_related_applications
                      ),
        'restored': (update_related_datasets,
                     update_related_articles,
                     update_related_applications
                     ),
        'removed': (update_related_datasets,
                    update_related_articles,
                    update_related_applications
                    ),
    }

    name = models.CharField(unique=True, max_length=100, verbose_name=_("name"))

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='tags_created'
    )
    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='tags_modified'
    )

    def __str__(self):
        return self.name

    @classmethod
    def accusative_case(cls):
        return _("acc: Tag")

    i18n = TranslationField(fields=("name",), required_languages=("pl",))
    tracker = FieldTracker()
    slugify_field = 'name'

    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        db_table = 'tag'
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(update_related_datasets, sender=Tag)
def update_tag_in_datasets(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Updating related datasets',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'update_related_datasets'
        },
        exc_info=1
    )
    for dataset in instance.datasets.all():
        search_signals.update_document.send(dataset._meta.model, dataset)


@receiver(update_related_articles, sender=Tag)
def update_tag_in_articles(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Updating related articles',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'update_related_articles'
        },
        exc_info=1
    )
    for app in instance.applications.all():
        search_signals.update_document.send(app._meta.model, app)


@receiver(update_related_applications, sender=Tag)
def update_tag_in_applications(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Updating related applications',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'update_related_applications'
        },
        exc_info=1
    )
    for article in instance.articles.all():
        search_signals.update_document.send(article._meta.model, article)
