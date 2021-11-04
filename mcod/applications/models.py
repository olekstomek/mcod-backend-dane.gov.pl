# -*- coding: utf-8 -*-
import base64
import logging
import os
from mimetypes import guess_type, guess_extension

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.postgres.indexes import GinIndex
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from modeltrans.fields import TranslationField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, StreamFieldPanel
from wagtail.api import APIField
from wagtail.core import blocks
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index

from mcod.applications.managers import ApplicationProposalManager, ApplicationProposalTrashManager
from mcod.applications.signals import generate_thumbnail, update_application_document
from mcod.applications.tasks import generate_logo_thumbnail_task
from mcod.core import signals as core_signals, storages
from mcod.core.api.search import signals as search_signals
from mcod.core.db.managers import TrashManager
from mcod.core.db.models import ExtendedModel, update_watcher, TrashModelBase
from mcod.core.managers import SoftDeletableManager


User = get_user_model()

signal_logger = logging.getLogger('signals')

MAIN_PAGE_ORDERING_CHOICES = [
    (1, _("First")),
    (2, _("Second")),
    (3, _("Third")),
    (4, _("Fourth")),
]


class ApplicationIndexPage(Page):
    under_title_cb = StreamField([
        ('paragraph', blocks.RichTextBlock(features=settings.CMS_RICH_TEXT_FIELD_FEATURES, label="Blok tekstu")),
        ('image', ImageChooserBlock(label="Obrazek")),
        # ('cta', CTABlock(label='Wezwanie do działania (CTA)'))
    ],
        default='',
        blank=True,
        verbose_name="Blok pod tytułem",
        help_text="Zawartość bloku, który znajdzie się pod tytułem strony głównej (nad wyszukiwarką).",
    )
    under_list_cb = StreamField([
        ('paragraph', blocks.RichTextBlock(features=settings.CMS_RICH_TEXT_FIELD_FEATURES, label="Blok tekstu")),
        ('image', ImageChooserBlock(label="Obrazek")),
        # ('cta', CTABlock(label='Wezwanie do działania (CTA)'))
    ],
        default='',
        blank=True,
        verbose_name="Blok pod listą aplikacji",
        help_text="Zawartość bloku, który znajdzie się pod listą aplikacji.",
    )

    subpage_types = ['applications.ApplicationPage']

    # parent_page_types = ['wagtailtrans.TranslatableSiteRootPage']

    api_fields = [
        APIField('title'),
        APIField('slug'),
        APIField('url_path'),
        APIField('seo_title'),
        APIField('show_in_menus'),
        APIField('search_description'),
        APIField('first_published_at'),
        APIField('last_published_at'),
        APIField('latest_revision_created_at'),
        APIField('under_title_cb'),
        APIField('under_list_cb'),
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel('under_title_cb'),
        StreamFieldPanel('under_list_cb'),
    ]

    max_count = 1

    class Meta:
        verbose_name = "Lista aplikacji"
        verbose_name_plural = "Listy aplikacji"


class ApplicationPage(Page):
    intro = RichTextField(default='',
                          blank=True,
                          verbose_name="Intro",
                          help_text="Krótki opis, streszczenie, zajawka.",
                          features=settings.CMS_RICH_TEXT_FIELD_FEATURES
                          )
    body = StreamField([
        ('h1', blocks.CharBlock(classname="full title", icon='fa-header', label="H1")),
        ('h2', blocks.CharBlock(classname="full title", icon='fa-header', label="H2")),
        ('h3', blocks.CharBlock(classname="full title", icon='fa-header', label="H3")),
        ('h4', blocks.CharBlock(classname="full title", icon='fa-header', label="H4")),
        ('paragraph', blocks.RichTextBlock(features=settings.CMS_RICH_TEXT_FIELD_FEATURES, label="Blok tekstu")),
        ('image', ImageChooserBlock(label="Obrazek")),
        ('blockquote', blocks.BlockQuoteBlock(label="Cytat")),
        ('document', DocumentChooserBlock(label="Dokument")),
        ('media', EmbedBlock(label='Media'))
    ], verbose_name="Treść", help_text="Właściwa treść strony.")
    is_featured = models.BooleanField(default=False, verbose_name="Wyróżnione",
                                      help_text="Czy ten artykuł ma zostać wyróżniony?")

    app_url_path = models.TextField(default='', blank=True, verbose_name='Link URL do aplikacji')

    api_fields = [
        APIField('intro'),
        APIField('body'),
        APIField('is_featured'),
        # APIField('tags'),
        APIField('app_url_path')
    ]

    search_fields = Page.search_fields + [
        index.SearchField('title', partial_match=True, boost=10),
        index.SearchField('intro', partial_match=True),
        index.SearchField('body', partial_match=True),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        StreamFieldPanel('body'),
        # FieldPanel('tags', classname="full"),
        FieldPanel('app_url_path')
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('is_featured'),
        ], heading="Publikacja"),
        MultiFieldPanel(Page.promote_panels, "Ustawienia"),
    ]

    parent_page_types = [
        'applications.ApplicationIndexPage',
    ]

    class Meta:
        verbose_name = "Aplikacja"
        verbose_name_plural = "Aplikacje"


class ApplicationMixin(ExtendedModel):
    title = models.CharField(max_length=300, verbose_name=_('title'))
    notes = models.TextField(verbose_name=_('Notes'), null=True)
    author = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Author'))
    url = models.URLField(max_length=300, verbose_name=_('App URL'), null=True)
    external_datasets = JSONField(blank=True, null=True, default=list, verbose_name=_('external datasets'))

    def __str__(self):
        return self.title

    class Meta(ExtendedModel.Meta):
        default_manager_name = 'objects'
        abstract = True

    @cached_property
    def illustrative_graphics_absolute_url(self):
        return self._get_absolute_url(
            self.illustrative_graphics.url, use_lang=False
        ) if self.illustrative_graphics else ''

    @cached_property
    def illustrative_graphics_url(self):
        url = self.illustrative_graphics.url if self.illustrative_graphics else ''
        if url:
            return self._get_absolute_url(url, use_lang=False)
        return url

    @property
    def illustrative_graphics_img(self):
        if self.illustrative_graphics_absolute_url:
            return mark_safe('<a href="%s" target="_blank"><img src="%s" width="%d" alt="" /></a>' % (
                self.admin_change_url,
                self.illustrative_graphics_absolute_url,
                100,
            ))

    def save_file(self, content, filename, field_name='image'):
        dt = self.created.date() if self.created else timezone.now().date()
        subdir = dt.isoformat().replace("-", "")
        if field_name == 'illustrative_graphics':
            subdir = os.path.join(field_name, subdir)
        field = getattr(self, field_name)
        dest_dir = os.path.join(field.storage.location, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content.read())
        return '%s/%s' % (subdir, filename)


class ApplicationProposal(ApplicationMixin):
    DECISION_CHOICES = (
        ('accepted', _('Proposal accepted')),
        ('rejected', _('Proposal rejected')),
    )
    applicant_email = models.EmailField(verbose_name=_('applicant email'), blank=True)
    image = models.ImageField(
        max_length=200, storage=storages.get_storage('applications'),
        upload_to='proposals/image/%Y%m%d', blank=True, null=True, verbose_name=_('image URL')
    )
    illustrative_graphics = models.ImageField(
        max_length=200, storage=storages.get_storage('applications'),
        upload_to='proposals/illustrative_graphics/%Y%m%d', blank=True, null=True,
        verbose_name=_('illustrative graphics'),
    )
    datasets = models.ManyToManyField(
        'datasets.Dataset', blank=True, verbose_name=_('datasets'), related_name='application_proposals')
    keywords = ArrayField(
        models.CharField(max_length=100), verbose_name=_('keywords'), default=list)
    report_date = models.DateField(verbose_name=_('report date'))

    decision = models.CharField(max_length=8, verbose_name=_('decision'), choices=DECISION_CHOICES, blank=True)
    decision_date = models.DateField(verbose_name=_('decision date'), null=True, blank=True)
    comment = models.TextField(verbose_name=_('comment'), blank=True)
    application = models.OneToOneField(
        'applications.Application', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('application'))
    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_('created by'),
        related_name='application_proposals_created'
    )

    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_('modified by'),
        related_name='application_proposals_modified'
    )

    objects = ApplicationProposalManager()
    trash = ApplicationProposalTrashManager()
    i18n = TranslationField()
    tracker = FieldTracker()

    class Meta(ApplicationMixin.Meta):
        verbose_name = _('Application Proposal')
        verbose_name_plural = _('Application Proposals')

    @cached_property
    def image_absolute_url(self):
        return self._get_absolute_url(self.image.url, use_lang=False) if self.image else ''

    @property
    def application_logo(self):
        if self.image_absolute_url:
            return mark_safe('<a href="%s" target="_blank"><img src="%s" width="%d" alt="" /></a>' % (
                self.admin_change_url,
                self.image_absolute_url,
                100,
            ))
        return ''

    @property
    def datasets_admin(self):
        res = ''
        for obj in self.datasets.order_by('title'):
            res += '<a href="{}" target="_blank">{}</a><br>'.format(obj.frontend_absolute_url, obj.title)
        return mark_safe(res)

    @property
    def external_datasets_admin(self):
        res = ''
        for x in self.external_datasets:
            url = x.get('url')
            title = x.get('title')
            if url:
                res += '<a href="{}" target="_blank">{}</a><br>'.format(url, title or url)
        return mark_safe(res)

    @property
    def is_accepted(self):
        return self.decision == 'accepted'

    @property
    def is_rejected(self):
        return self.decision == 'rejected'

    @property
    def keywords_as_str(self):
        return ','.join([x for x in self.keywords])

    @classmethod
    def convert_to_application(cls, app_proposal_id):  # noqa
        proposal = cls.objects.filter(id=app_proposal_id, application__isnull=True).first()
        if proposal:
            tag_model = apps.get_model('tags.Tag')
            data = model_to_dict(
                proposal,
                fields=['notes', 'author', 'url', 'title', 'image', 'illustrative_graphics', 'datasets',
                        'external_datasets', 'keywords', 'created_by', 'modified_by'])
            data['status'] = 'draft'
            data['modified_by_id'] = data.pop('modified_by')
            data['created_by_id'] = data.pop('created_by') or data['modified_by_id']
            image = data.pop('image')
            illustrative_graphics = data.pop('illustrative_graphics')
            datasets = data.pop('datasets')
            keywords = data.pop('keywords')
            application = Application.objects.create(**data)
            if image:
                application.image = application.save_file(image, os.path.basename(image.path))
            if illustrative_graphics:
                application.illustrative_graphics = application.save_file(
                    illustrative_graphics, os.path.basename(illustrative_graphics.path),
                    field_name='illustrative_graphics')
            if image or illustrative_graphics:
                application.save()
            if datasets:
                application.datasets.set(datasets)
            if keywords:
                tag_ids = []
                for name in keywords:
                    tag, created = tag_model.objects.get_or_create(
                        name=name, language='pl', defaults={'created_by_id': data['created_by_id']})
                    tag_ids.append(tag.id)
                if tag_ids:
                    application.tags.set(tag_ids)
            proposal.application = application
            proposal.save()
            return application

    @classmethod
    def create(cls, data):
        image = data.pop('image', None)
        illustrative_graphics = data.pop('illustrative_graphics', None)
        datasets_ids = data.pop('datasets', [])
        name = slugify(data['title'])
        if image:
            data['image'] = cls.decode_b64_image(image, name)
        if illustrative_graphics:
            data['illustrative_graphics'] = cls.decode_b64_image(illustrative_graphics, name)
        obj = cls.objects.create(**data)
        if datasets_ids:
            obj.datasets.set(datasets_ids)
        return obj

    @classmethod
    def decode_b64_image(cls, encoded_img, img_name):
        data_parts = encoded_img.split(';base64,')
        img_data = data_parts[-1].encode('utf-8')
        try:
            extension = guess_extension(guess_type(encoded_img)[0])
        except Exception:
            extension = None
        name = f'{img_name}{extension}' if extension else img_name
        try:
            decoded_img = base64.b64decode(img_data)
        except Exception:
            decoded_img = None
        return ContentFile(decoded_img, name=name) if decoded_img else None

    @classmethod
    def accusative_case(cls):
        return _("acc: Application proposal")


class ApplicationProposalTrash(ApplicationProposal, metaclass=TrashModelBase):

    class Meta(ApplicationProposal.Meta):
        proxy = True
        verbose_name = _("Application Proposal Trash")
        verbose_name_plural = _("Application Proposals Trash")


class Application(ApplicationMixin):
    SIGNALS_MAP = {
        'updated': (generate_thumbnail, core_signals.notify_updated),
        'published': (generate_thumbnail, core_signals.notify_published),
        'restored': (generate_thumbnail, core_signals.notify_restored),
        'removed': (search_signals.remove_document, core_signals.notify_removed),
        'pre_m2m_added': (core_signals.notify_m2m_added,),
        'pre_m2m_removed': (core_signals.notify_m2m_removed,),
        'pre_m2m_cleaned': (core_signals.notify_m2m_cleaned,),
        'post_m2m_added': (update_application_document, search_signals.update_document_related,),
        'post_m2m_removed': (update_application_document, search_signals.update_document_related,),
        'post_m2m_cleaned': (update_application_document, search_signals.update_document_related,),
    }

    image = models.ImageField(
        max_length=200, storage=storages.get_storage('applications'),
        upload_to='%Y%m%d', blank=True, null=True, verbose_name=_("Image URL")
    )
    illustrative_graphics = models.ImageField(
        max_length=200, storage=storages.get_storage('applications'),
        upload_to='illustrative_graphics/%Y%m%d', blank=True, null=True, verbose_name=_('illustrative graphics'),
    )
    illustrative_graphics_alt = models.CharField(
        max_length=255, blank=True, verbose_name=_('illustrative graphics alternative text'))
    image_thumb = models.ImageField(
        storage=storages.get_storage('applications'),
        upload_to='%Y%m%d', blank=True, null=True
    )
    image_alt = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Alternative text"))
    datasets = models.ManyToManyField('datasets.Dataset',
                                      db_table='application_dataset',
                                      verbose_name=_('Datasets'),
                                      related_name='applications',
                                      related_query_name="application")
    tags = models.ManyToManyField('tags.Tag',
                                  blank=True,
                                  db_table='application_tag',
                                  verbose_name=_('Tag'),
                                  related_name='applications',
                                  related_query_name="application")

    main_page_position = models.PositiveSmallIntegerField(
        choices=MAIN_PAGE_ORDERING_CHOICES,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_('Positioning on the main page'),
    )

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='applications_created'
    )

    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='applications_modified'
    )

    @property
    def frontend_preview_url(self):
        return self._get_absolute_url(f'/application/preview/{self.ident}')

    @cached_property
    def image_url(self):
        url = self.image.url if self.image else ''
        if url:
            return self._get_absolute_url(url, use_lang=False)
        return url

    @cached_property
    def image_absolute_url(self):
        return self._get_absolute_url(
            self.image.url, use_lang=False) if self.image else ''

    @cached_property
    def image_thumb_url(self):
        url = self.image_thumb.url if self.image_thumb else ''
        if url:
            return self._get_absolute_url(url, use_lang=False)
        return url

    @cached_property
    def image_thumb_absolute_url(self):
        return self._get_absolute_url(
            self.image_thumb.url, use_lang=False) if self.image_thumb else ''

    @cached_property
    def has_image_thumb(self):
        return bool(self.image_thumb)

    def tags_as_str(self, lang):
        return ', '.join(sorted([tag.name for tag in self.tags.filter(language=lang)], key=str.lower))

    @property
    def keywords_list(self):
        return [tag.to_dict for tag in self.tags.all()]

    @property
    def keywords(self):
        return self.tags

    @cached_property
    def users_following_list(self):
        return [user.id for user in self.users_following.all()]

    @property
    def application_logo(self):
        if self.image_thumb_absolute_url or self.image_absolute_url:
            return mark_safe('<a href="%s" target="_blank"><img src="%s" width="%d" alt="%s" /></a>' % (
                self.admin_change_url,
                self.image_thumb_absolute_url or self.image_absolute_url,
                100,
                self.image_alt if self.image_alt else f'Logo aplikacji {self.title}'
            ))
        return ''

    @classmethod
    def accusative_case(cls):
        return _("acc: Application")

    def published_datasets(self):
        return self.datasets.filter(status='published')

    i18n = TranslationField(fields=("title", "notes", 'image_alt', 'illustrative_graphics_alt'))

    objects = SoftDeletableManager()
    trash = TrashManager()
    tracker = FieldTracker()
    slugify_field = 'title'

    class Meta(ApplicationMixin.Meta):
        verbose_name = _("Application")
        verbose_name_plural = _("Applications")
        db_table = "application"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(pre_save, sender=ApplicationProposal)
def handle_application_proposal_pre_save(sender, instance, *args, **kwargs):
    if not instance.report_date and instance.created:
        instance.report_date = instance.created.date()
    if instance.tracker.has_changed('decision'):
        instance.decision_date = timezone.now().date() if any([instance.is_accepted, instance.is_rejected]) else None


@receiver(generate_thumbnail, sender=Application)
def regenerate_thumbnail(sender, instance, *args, **kwargs):
    signal_logger.debug(
        'Regenerating thumbnail ',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'generate_thumbnail'
        },
        exc_info=1
    )
    if any([instance.tracker.has_changed('image'),
            instance.tracker.has_changed('status') and instance.status == instance.STATUS.published]):
        generate_logo_thumbnail_task.s(instance.id).apply_async(countdown=1)
    else:
        search_signals.update_document.send(sender, instance)


@receiver(update_application_document, sender=Application)
def update_application_document_handler(sender, instance, *args, **kwargs):
    if instance.status == instance.STATUS.published:
        search_signals.update_document.send(sender, instance, *args, **kwargs)


@receiver(pre_save, sender=Application)
def handle_application_pre_save(sender, instance, *args, **kwargs):
    if instance.is_removed and instance.main_page_position is not None:
        instance.main_page_position = None


class ApplicationTrash(Application, metaclass=TrashModelBase):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


core_signals.notify_published.connect(update_watcher, sender=Application)
core_signals.notify_restored.connect(update_watcher, sender=Application)
core_signals.notify_updated.connect(update_watcher, sender=Application)
core_signals.notify_removed.connect(update_watcher, sender=Application)

core_signals.notify_published.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_restored.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_updated.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_removed.connect(update_watcher, sender=ApplicationTrash)
