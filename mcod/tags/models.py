import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from modeltrans.fields import TranslationField

from mcod import settings
from mcod.core.api.search import signals as search_signals
from mcod.core.api.rdf import signals as rdf_signals
from mcod.core.db.models import BaseExtendedModel
from mcod.tags.signals import update_related_datasets, update_related_articles, update_related_applications


User = get_user_model()

STATUS_CHOICES = [
    ('published', _('Published')),
    ('draft', _('Draft')),
]

signal_logger = logging.getLogger('signals')


class Tag(BaseExtendedModel):
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
    name = models.CharField(max_length=100, verbose_name=_("name"))
    language = models.CharField(
        max_length=2, choices=settings.LANGUAGES, default=settings.LANGUAGES[0][0], verbose_name=_("language"), db_index=True)

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
        en_name = getattr(self, 'name_en', '') or ''
        return self.name or en_name

    @classmethod
    def accusative_case(cls):
        return _("acc: Tag")

    i18n = TranslationField(fields=("name",), required_languages=("pl",))
    tracker = FieldTracker()
    slugify_field = 'name'

    objects = models.Manager()

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        db_table = 'tag'
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]
        unique_together = ('name', 'language')

    @property
    def translations_dict(self):
        return {lang: getattr(self, f'name_{lang}', '') or '' for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES}

    @property
    def to_dict(self):
        return {
            'name': self.name,
            'language': self.language,
        }

    @property
    def language_readonly(self):
        return self.language


@receiver(update_related_datasets, sender=Tag)
def update_tag_in_datasets(sender, instance, *args, **kwargs):
    signal_logger.debug(
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
        rdf_signals.update_graph.send(dataset._meta.model, dataset)


@receiver(update_related_articles, sender=Tag)
def update_tag_in_articles(sender, instance, *args, **kwargs):
    signal_logger.debug(
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
    signal_logger.debug(
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
