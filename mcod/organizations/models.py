import logging

import phonenumbers
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.dispatch import receiver
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField

from mcod.core import signals as core_signals
from mcod.core import storages
from mcod.core.api.search import signals as search_signals
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel, update_watcher
from mcod.organizations.signals import remove_related_datasets

User = get_user_model()
INSTITUTION_TYPE_CHOICES = (('local', _('Local goverment')),
                            ('state', _('Public goverment')),
                            ('other', _('Other')),)

signal_logger = logging.getLogger('signals')


class Organization(ExtendedModel):
    SIGNALS_MAP = {
        'removed': (remove_related_datasets, search_signals.remove_document_with_related, core_signals.notify_removed),
    }

    title = models.CharField(max_length=100, verbose_name=_('Title'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    image = models.ImageField(max_length=254, storage=storages.get_storage('organizations'),
                              upload_to='%Y%m%d',
                              blank=True, null=True, verbose_name=_('Image URL'))
    postal_code = models.CharField(max_length=6, null=True, verbose_name=_('Postal code'))
    city = models.CharField(max_length=200, null=True, verbose_name=_("City"))
    street_type = models.CharField(max_length=50, null=True, verbose_name=_("Street type"))
    street = models.CharField(max_length=200, null=True, verbose_name=_("Street"))
    street_number = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Street number"))
    flat_number = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Flat number"))

    email = models.CharField(max_length=300, null=True, verbose_name=_("Email"))
    epuap = models.CharField(max_length=500, null=True, verbose_name=_("EPUAP"))
    fax = models.CharField(max_length=50, null=True, verbose_name=_("Fax"))
    fax_internal = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('int.'))

    institution_type = models.CharField(
        max_length=50,
        choices=INSTITUTION_TYPE_CHOICES,
        default=INSTITUTION_TYPE_CHOICES[1][0],
        verbose_name=_("Institution type")
    )
    regon = models.CharField(max_length=20, null=True, verbose_name=_("REGON"))
    tel = models.CharField(max_length=50, null=True, verbose_name=_("Phone"))
    tel_internal = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('int.'))
    website = models.CharField(max_length=200, null=True, verbose_name=_("Website"))

    i18n = TranslationField(fields=('title', 'description', 'slug'))

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='organizations_created'
    )
    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='organizations_modified'
    )

    def __str__(self):
        if self.title:
            return self.title
        return self.slug

    def get_url_path(self):
        if self.id:
            try:
                return reverse("admin:applications_application_change", kwargs={"object_id": self.id})
            except NoReverseMatch:
                return ""
        return ""

    @property
    def image_url(self):
        try:
            return self.image.url
        except ValueError:
            return ''

    @property
    def short_description(self):
        clean_text = ""
        if self.description:
            clean_text = ''.join(BeautifulSoup(self.description, "html.parser").stripped_strings)
        return clean_text

    @property
    def api_url(self):
        return '/institutions/{}'.format(self.id)

    @property
    def description_html(self):
        return format_html(self.description)

    @property
    def datasets_count(self):
        return self.datasets.count()

    @classmethod
    def accusative_case(cls):
        return _("acc: Institution")

    @property
    def published_datasets(self):
        return self.datasets.filter(status='published')

    @property
    def address_display(self):
        city = ' '.join(i.strip() for i in [self.postal_code, self.city] if i)
        if not city:
            return None
        number = '/'.join(i.strip() for i in [self.street_number, self.flat_number] if i)
        addres_line = city
        if self.street:
            street = ' '.join(i.strip() for i in [self.street_type, self.street, number] if i)
            addres_line = ', '.join(i for i in [addres_line, street] if i)

        return addres_line

    @property
    def phone_display(self):
        if not self.tel:
            return None
        try:
            p = phonenumbers.parse(self.tel, 'PL')
            phone = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except phonenumbers.phonenumberutil.NumberParseException:
            return None
        return _(' int. ').join(i.strip() for i in [phone, self.tel_internal] if i)

    @property
    def fax_display(self):
        if not self.fax:
            return None
        try:
            p = phonenumbers.parse(self.fax, 'PL')
            fax = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except phonenumbers.phonenumberutil.NumberParseException:
            return None
        return _(' int. ').join(i.strip() for i in [fax, self.fax_internal] if i)

    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()

    tracker = FieldTracker()
    slugify_field = 'title'

    short_description.fget.short_description = _("Description")

    class Meta:
        db_table = "organization"
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(remove_related_datasets, sender=Organization)
def remove_datasets_after_organization_removed(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Removing related datasets',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'remove_related_datasets'
        },
        exc_info=1
    )

    if instance.is_removed:
        instance.datasets.all().delete()

    elif instance.status == sender.STATUS.draft:
        for dataset in instance.datasets.all():
            dataset.status = dataset.STATUS.draft
            dataset.save()


class OrganizationTrash(Organization):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


core_signals.notify_published.connect(update_watcher, sender=Organization)
core_signals.notify_restored.connect(update_watcher, sender=Organization)
core_signals.notify_updated.connect(update_watcher, sender=Organization)
core_signals.notify_removed.connect(update_watcher, sender=Organization)

core_signals.notify_published.connect(update_watcher, sender=OrganizationTrash)
core_signals.notify_restored.connect(update_watcher, sender=OrganizationTrash)
core_signals.notify_updated.connect(update_watcher, sender=OrganizationTrash)
core_signals.notify_removed.connect(update_watcher, sender=OrganizationTrash)
