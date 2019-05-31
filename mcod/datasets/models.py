import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField

from mcod.core import signals as core_signals
from mcod.core.api.search import signals as search_signals
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel, update_watcher
from mcod.datasets.signals import remove_related_resources

# from mcod.datasets.serializers import DatasetApiAttrs, DatasetCSVSchema
signal_logger = logging.getLogger('signals')

User = get_user_model()

UPDATE_FREQUENCY = (
    ("notApplicable", _("Not applicable")),
    ("yearly", _("yearly")),
    ("everyHalfYear", _("every half year")),
    ("quarterly", _("quarterly")),
    ("monthly", _("monthly")),
    ("weekly", _("weekly")),
    ("daily", _("daily")),
)

TYPE = (
    ('application', _('application')),
    ('dataset', _('dataset')),
    ('article', _('article'))
)


class Dataset(ExtendedModel):
    SIGNALS_MAP = {
        'removed': (
            remove_related_resources,
            search_signals.remove_document_with_related,
            core_signals.notify_removed),
    }
    title = models.CharField(max_length=300, null=True, verbose_name=_("Title"))
    version = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Version"))
    url = models.CharField(max_length=1000, blank=True, null=True, verbose_name=_("Url"))
    notes = models.TextField(verbose_name=_("Notes"), null=True, blank=False)

    license_old_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("License ID"))
    license = models.ForeignKey('licenses.License', on_delete=models.DO_NOTHING, blank=True, null=True,
                                verbose_name=_("License ID"))

    license_condition_db_or_copyrighted = models.CharField(max_length=300, blank=True, null=True)
    license_condition_modification = models.NullBooleanField(null=True, blank=True, default=None)
    license_condition_original = models.NullBooleanField(null=True, blank=True, default=None)
    license_condition_responsibilities = models.TextField(blank=True, null=True)
    license_condition_source = models.NullBooleanField(null=True, blank=True, default=None)
    license_condition_timestamp = models.NullBooleanField(null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='datasets',
                                     verbose_name=_('Institution'))
    customfields = JSONField(blank=True, null=True, verbose_name=_("Customfields"))
    update_frequency = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Update frequency"))
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, blank=True, null=True,
                                 verbose_name=_('Category'))
    tags = models.ManyToManyField('tags.Tag',
                                  db_table='dataset_tag',
                                  blank=False,
                                  verbose_name=_("Tag"),
                                  related_name='datasets',
                                  related_query_name="dataset")

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='datasets_created'
    )
    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='datasets_modified'

    )

    verified = models.DateTimeField(blank=True, default=now, verbose_name=_("Update date"))

    def __str__(self):
        return self.title

    @property
    def institution(self):
        return self.organization

    @property
    def downloads_count(self):
        return sum(res.downloads_count for res in self.resources.all())

    @property
    def formats(self):
        return list(set(res.format for res in self.resources.all() if res.format is not None))

    @property
    def openness_scores(self):
        return list(set(res.openness_score for res in self.resources.all()))

    @property
    def tags_list(self):
        return [tag.name_translated for tag in self.tags.all()]

    @property
    def license_name(self):
        return self.license.name if self.license and self.license.name else ''

    @property
    def license_description(self):
        return self.license.title if self.license and self.license.title else ''

    @property
    def last_modified_resource(self):
        return self.resources.all().aggregate(Max('modified'))['modified__max']

    last_modified_resource.fget.short_description = _("modified")

    @property
    def is_license_set(self):
        return any([
            self.license,
            self.license_condition_db_or_copyrighted,
            self.license_condition_modification,
            self.license_condition_original,
            self.license_condition_responsibilities
        ])

    @property
    def followers_count(self):
        return self.users_following.count()

    @classmethod
    def accusative_case(cls):
        return _("acc: Dataset")

    i18n = TranslationField(fields=("title", "notes"))
    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()
    tracker = FieldTracker()
    slugify_field = 'title'
    last_modified_resource.fget.short_description = _("modified")

    class Meta:
        verbose_name = _("Dataset")
        verbose_name_plural = _("Datasets")
        db_table = 'dataset'
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(pre_save, sender=Dataset)
def handle_dataset_pre_save(sender, instance, *args, **kwargs):
    if not instance.id:
        instance.verified = instance.created


@receiver(post_save, sender=Dataset)
def handle_dataset_without_resources(sender, instance, *args, **kwargs):
    if not instance.resources.all():
        Dataset.objects.filter(pk=instance.id).update(verified=instance.created)


@receiver(remove_related_resources, sender=Dataset)
def remove_resources_after_dataset_removed(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Remove related resources',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'remove_related_resources'
        },
        exc_info=1
    )
    if instance.is_removed:
        for resource in instance.resources.all():
            resource.delete()

    elif instance.status == sender.STATUS.draft:
        for resource in instance.resources.all():
            resource.status = resource.STATUS.draft
            resource.save()


class DatasetTrash(Dataset):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


core_signals.notify_published.connect(update_watcher, sender=Dataset)
core_signals.notify_restored.connect(update_watcher, sender=Dataset)
core_signals.notify_updated.connect(update_watcher, sender=Dataset)
core_signals.notify_removed.connect(update_watcher, sender=Dataset)

core_signals.notify_published.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_restored.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_updated.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_removed.connect(update_watcher, sender=DatasetTrash)
