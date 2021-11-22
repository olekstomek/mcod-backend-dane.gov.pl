import itertools
import logging

from constance import config
from django.utils.functional import cached_property
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Sum, Q
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, get_language
from model_utils import FieldTracker
from django.utils.safestring import mark_safe
from modeltrans.fields import TranslationField

from mcod import settings

from mcod.datasets.managers import DatasetManager
from mcod.watchers.tasks import update_model_watcher_task
from mcod.core import signals as core_signals
from mcod.core.api.search import signals as search_signals
from mcod.core.api.rdf import signals as rdf_signals
from mcod.core.db.managers import TrashManager
from mcod.core.db.models import ExtendedModel, update_watcher, TrashModelBase
from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.datasets.signals import remove_related_resources
from mcod.core.storages import get_storage
from mcod.regions.models import Region
from mcod.unleash import is_enabled


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
UPDATE_FREQUENCY_NOTIFICATION_RANGES = {
    'yearly': (1, 365),
    'everyHalfYear': (1, 182),
    'quarterly': (1, 90),
    'monthly': (1, 30),
    'weekly': (1, 6),
}
UPDATE_NOTIFICATION_FREQUENCY_DEFAULT_VALUES = {
    'yearly': 7,
    'everyHalfYear': 7,
    'quarterly': 7,
    'monthly': 3,
    'weekly': 1,
}

TYPE = (
    ('application', _('application')),
    ('dataset', _('dataset')),
    ('article', _('article'))
)


class Dataset(ExtendedModel):
    LICENSE_CC0 = 1
    LICENSE_CC_BY = 2
    LICENSE_CC_BY_SA = 3
    LICENSE_CC_BY_NC = 4
    LICENSE_CC_BY_NC_SA = 5
    LICENSE_CC_BY_ND = 6
    LICENSE_CC_BY_NC_ND = 7
    LICENSES = (
        (LICENSE_CC0, "CC0 1.0"),
        (LICENSE_CC_BY, "CC BY 4.0"),
        (LICENSE_CC_BY_SA, "CC BY-SA 4.0"),
        (LICENSE_CC_BY_NC, "CC BY-NC 4.0"),
        (LICENSE_CC_BY_NC_SA, "CC BY-NC-SA 4.0"),
        (LICENSE_CC_BY_ND, "CC BY-ND 4.0"),
        (LICENSE_CC_BY_NC_ND, "CC BY-NC-ND 4.0"),
    )
    LICENSE_CODE_TO_NAME = dict(LICENSES)

    SIGNALS_MAP = {
        'updated': (
            rdf_signals.update_graph_with_conditional_related,
            search_signals.update_document_with_related,
            core_signals.notify_updated),
        'published': (
            rdf_signals.create_graph,
            search_signals.update_document_with_related,
            core_signals.notify_published),
        'restored': (
            rdf_signals.create_graph,
            search_signals.update_document_with_related,
            core_signals.notify_restored),
        'removed': (
            remove_related_resources,
            rdf_signals.delete_graph,
            search_signals.remove_document_with_related,
            core_signals.notify_removed),
        'post_m2m_added': (search_signals.update_document_related, rdf_signals.update_graph,),
        'post_m2m_removed': (search_signals.update_document_related, rdf_signals.update_graph,),
        'post_m2m_cleaned': (search_signals.update_document_related, rdf_signals.update_graph,)
    }
    ext_ident = models.CharField(
        max_length=36, blank=True, editable=False, verbose_name=_('external identifier'),
        help_text=_('external identifier of dataset taken during import process (optional)'))
    title = models.CharField(max_length=300, null=True, verbose_name=_("Title"))
    version = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Version"))
    url = models.CharField(max_length=1000, blank=True, null=True, verbose_name=_("Url"))
    notes = models.TextField(verbose_name=_("Notes"), null=True, blank=False)

    license_chosen = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None, verbose_name='',
        choices=LICENSES
    )

    license_old_id = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("License ID"))
    license = models.ForeignKey('licenses.License', on_delete=models.DO_NOTHING, blank=True, null=True,
                                verbose_name=_("License ID"))

    license_condition_db_or_copyrighted = models.TextField(
        blank=True, null=True,
        verbose_name=_(
            "Conditions for using public information that meets the characteristics of the work or constitute "
            "a database (Article 13 paragraph 2 of the Act on the re-use of public sector information)")
    )
    license_condition_personal_data = models.CharField(
        max_length=300, blank=True, null=True,
        verbose_name=_(
            "Conditions for using public sector information containing personal data (Article 14 paragraph 1 "
            "point 4 of the Act on the re-use of public Sector Information)")
    )
    license_condition_modification = models.NullBooleanField(
        null=True, blank=True, default=None,
        verbose_name=_("The recipient should inform about the processing of the information when it modifies it"))
    license_condition_original = models.NullBooleanField(null=True, blank=True, default=None)
    license_condition_responsibilities = models.TextField(
        blank=True, null=True,
        verbose_name=_("The scope of the provider's responsibility for the information provided"))
    license_condition_source = models.NullBooleanField(
        null=True, blank=True, default=None,
        verbose_name=_("The recipient should inform about the date, time of completion and obtaining information from"
                       " the obliged entity"))
    license_condition_timestamp = models.NullBooleanField(null=True, blank=True)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='datasets',
                                     verbose_name=_('Institution'))
    customfields = JSONField(blank=True, null=True, verbose_name=_("Customfields"))
    update_frequency = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Update frequency"))
    is_update_notification_enabled = models.BooleanField(
        default=True, verbose_name=_('turn on notification'))
    update_notification_frequency = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_('set notifications frequency'))
    update_notification_recipient_email = models.EmailField(
        blank=True, verbose_name=_('the person who is the notifications recipient'))

    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, blank=True, null=True,
                                 verbose_name=_('Category'), limit_choices_to=Q(code=''))

    categories = models.ManyToManyField('categories.Category',
                                        db_table='dataset_category',
                                        verbose_name=_('Categories'),
                                        related_name='datasets',
                                        related_query_name="dataset",
                                        limit_choices_to=~Q(code=''))

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
    source = models.ForeignKey(
        'harvester.DataSource',
        models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('source'),
        related_name='datasource_datasets',
    )
    verified = models.DateTimeField(blank=True, default=now, verbose_name=_("Update date"))
    downloads_count = models.PositiveIntegerField(verbose_name=_('download counter'), default=0)
    image = models.ImageField(
        max_length=200, storage=get_storage('datasets'),
        upload_to='dataset_logo/%Y%m%d', blank=True, null=True, verbose_name=_('Image URL'),
    )
    image_alt = models.CharField(max_length=255, blank=True, verbose_name=_('Alternative text'))
    dcat_vocabularies = JSONField(blank=True, null=True, verbose_name=_("Controlled Vocabularies"))
    has_high_value_data = models.BooleanField(verbose_name=_('Has high value data'), default=False)

    def __str__(self):
        return self.title

    @cached_property
    def has_table(self):
        return self.resources.filter(has_table=True).exists()

    @cached_property
    def has_map(self):
        return self.resources.filter(has_map=True).exists()

    @cached_property
    def has_chart(self):
        return self.resources.filter(has_chart=True).exists()

    @property
    def comment_editors(self):
        emails = []
        if self.source:
            emails.extend(self.source.emails_list)
        else:
            if self.update_notification_recipient_email and is_enabled('S36_dataset_resource_comment_recipient.be'):
                emails.append(self.update_notification_recipient_email)
            elif self.modified_by:
                emails.append(self.modified_by.email)
            else:
                emails.extend(user.email for user in self.organization.users.all())
        return emails

    @property
    def comment_mail_recipients(self):
        return [config.CONTACT_MAIL, ] + self.comment_editors

    @property
    def is_imported(self):
        return bool(self.source)

    @property
    def is_imported_from_ckan(self):
        return self.is_imported and self.source.is_ckan

    @property
    def is_imported_from_xml(self):
        return self.is_imported and self.source.is_xml

    @property
    def institution(self):
        return self.organization

    @property
    def source_title(self):
        return self.source.name if self.source else None

    @property
    def source_type(self):
        return self.source.source_type if self.source else None

    @property
    def source_url(self):
        return self.source.portal_url if self.source else None

    @property
    def formats(self):
        items = [x.formats_list for x in self.resources.all() if x.formats_list]
        return sorted(set([item for sublist in items for item in sublist]))

    @property
    def types(self):
        return list(self.resources.values_list('type', flat=True).distinct())

    @property
    def frontend_url(self):
        return f'/dataset/{self.ident}'

    @property
    def frontend_absolute_url(self):
        return self._get_absolute_url(self.frontend_url)

    @property
    def openness_scores(self):
        return list(set(res.openness_score for res in self.resources.all()))

    @property
    def keywords_list(self):
        return [tag.to_dict for tag in self.tags.all()]

    @property
    def keywords(self):
        return self.tags

    @property
    def tags_list_as_str(self):
        return ', '.join(sorted([str(tag) for tag in self.tags.all()], key=str.lower))

    def tags_as_str(self, lang):
        return ', '.join(sorted([tag.name for tag in self.tags.filter(language=lang)], key=str.lower))

    @property
    def categories_list_as_html(self):
        categories = self.categories.all()
        return mark_safe('<br>'.join(category.title for category in categories)) if categories else '-'

    @property
    def categories_list_str(self):
        return ', '.join(self.categories.all().values_list('title', flat=True))

    @property
    def license_code(self):
        license_ = self.LICENSE_CC0
        if self.license_condition_source or self.license_condition_modification or self.license_condition_responsibilities:
            license_ = self.LICENSE_CC_BY
        if self.license_chosen and self.license_chosen > license_:
            license_ = self.license_chosen
        return license_

    @property
    def license_name(self):
        return self.LICENSE_CODE_TO_NAME.get(self.license_code)

    @property
    def license_link(self):
        url = settings.LICENSES_LINKS.get(self.license_name)
        return f'{url}legalcode.{get_language()}'

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

    @property
    def published_resources_count(self):
        return self.resources.count()

    @property
    def visualization_types(self):
        return list(set(itertools.chain(*[r.visualization_types for r in self.resources.all()])))

    @property
    def model_name(self):
        return self._meta.model_name

    @classmethod
    def accusative_case(cls):
        return _("acc: Dataset")

    @property
    def image_url(self):
        return self.image.url if self.image else ''

    @property
    def image_absolute_url(self):
        return self._get_absolute_url(self.image_url, use_lang=False) if self.image_url else ''

    @property
    def dataset_logo(self):
        if self.image_absolute_url:
            return mark_safe('<a href="%s" target="_blank"><img src="%s" width="%d" alt="%s" /></a>' % (
                self.admin_change_url,
                self.image_absolute_url,
                100,
                self.image_alt if self.image_alt else ''
            ))
        return ''

    @property
    def computed_downloads_count(self):
        return ResourceDownloadCounter.objects.filter(
            resource__dataset_id=self.pk).aggregate(count_sum=Sum('count'))['count_sum'] or 0\
            if is_enabled('S16_new_date_counters.be') else self.downloads_count

    @property
    def computed_views_count(self):
        return ResourceViewCounter.objects.filter(
            resource__dataset_id=self.pk).aggregate(count_sum=Sum('count'))['count_sum'] or 0\
            if is_enabled('S16_new_date_counters.be') else self.views_count

    def to_rdf_graph(self):
        schema = self.get_rdf_serializer_schema()
        return schema(many=False).dump(self) if schema else None

    def as_sparql_create_query(self):
        g = self.to_rdf_graph()
        data = ''.join([f'{s.n3()} {p.n3()} {o.n3()} . ' for s, p, o in g.triples((None, None, None))])
        namespaces_dict = {prefix: ns for prefix, ns in g.namespaces()}
        return 'INSERT DATA { %(data)s }' % {'data': data}, namespaces_dict

    def clean(self):
        _range = UPDATE_FREQUENCY_NOTIFICATION_RANGES.get(self.update_frequency)
        if (_range and self.update_notification_frequency and
                self.update_notification_frequency not in range(_range[0], _range[1] + 1)):
            msg = _('The value must be between %(min)s and %(max)s') % {'min': _range[0], 'max': _range[1]}
            raise ValidationError({'update_notification_frequency': msg})

    @property
    def frequency_display(self):
        return dict(UPDATE_FREQUENCY).get(self.update_frequency)

    @property
    def dataset_update_notification_recipient(self):
        return self.update_notification_recipient_email or self.modified_by.email

    @property
    def regions(self):
        resources_ids = list(self.resources.values_list('pk', flat=True))
        return Region.objects.filter(resource__pk__in=resources_ids).distinct()

    i18n = TranslationField(fields=("title", "notes", "image_alt"))
    objects = DatasetManager()
    trash = TrashManager()
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
    signal_logger.debug(
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


class DatasetTrash(Dataset, metaclass=TrashModelBase):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


def update_related_watchers(sender, instance, *args, state=None, **kwargs):
    state = 'm2m_{}'.format(state)

    signal_logger.debug(
        '{} {}'.format(sender._meta.object_name, state),
        extra={
            'sender': '{}.{}'.format(sender._meta.app_label, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.app_label, instance._meta.object_name),
            'instance_id': instance.id,
            'state': state,
            'signal': 'notify_{}'.format(state)
        },
        exc_info=1
    )
    instances = list(instance.applications.all()) + list(instance.articles.all())
    instances.append(instance.organization)

    for i in instances:
        update_model_watcher_task.s(
            i._meta.app_label,
            i._meta.object_name,
            i.id,
            obj_state=state
        ).apply_async(
            countdown=1
        )


core_signals.notify_published.connect(update_watcher, sender=Dataset)
core_signals.notify_restored.connect(update_watcher, sender=Dataset)
core_signals.notify_updated.connect(update_watcher, sender=Dataset)
core_signals.notify_removed.connect(update_watcher, sender=Dataset)

core_signals.notify_restored.connect(update_related_watchers, sender=Dataset)
core_signals.notify_updated.connect(update_related_watchers, sender=Dataset)
core_signals.notify_removed.connect(update_related_watchers, sender=Dataset)

core_signals.notify_published.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_restored.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_updated.connect(update_watcher, sender=DatasetTrash)
core_signals.notify_removed.connect(update_watcher, sender=DatasetTrash)
