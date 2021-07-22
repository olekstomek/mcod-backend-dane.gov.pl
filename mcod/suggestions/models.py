from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker, Choices
from model_utils.fields import MonitorField
from modeltrans.fields import TranslationField

from mcod.core.db.models import ExtendedModel, TrashModelBase, STATUS_CHOICES
from mcod.datasets.tasks import send_dataset_comment
from mcod.resources.tasks import send_resource_comment
from mcod.suggestions.managers import (
    AcceptedDatasetSubmissionTrashManager,
    AcceptedDatasetSubmissionManager,
    DatasetCommentManager,
    DatasetCommentTrashManager,
    DatasetSubmissionTrashManager,
    DatasetSubmissionManager,
    ResourceCommentManager,
    ResourceCommentTrashManager,
)
from mcod.suggestions.tasks import send_data_suggestion, send_dataset_suggestion_mail_task

User = get_user_model()


ACCEPTED_DATASET_SUBMISSION_STATUS_CHOICES = [
    *STATUS_CHOICES,
    ('publication_finished', _('Publication finished')),
]

ACCEPTED_DATASET_SUBMISSION_STATUS_CHOICES_NO_PUBLISHED = [
    (value, description)
    for value, description in ACCEPTED_DATASET_SUBMISSION_STATUS_CHOICES
    if value != 'published'
]


class Suggestion(models.Model):
    notes = models.TextField()
    send_date = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=Suggestion)
def handle_suggestion_post_save(sender, instance, *args, **kwargs):
    data_suggestion = {"notes": instance.notes}
    send_data_suggestion.s(instance.id, data_suggestion).apply_async(countdown=1)


class DatasetSubmissionMixin(ExtendedModel):
    DECISION_CHOICES = (
        ('accepted', _('Proposal accepted')),
        ('rejected', _('Proposal rejected')),
    )
    title = models.CharField(max_length=300, blank=False, verbose_name=_("Title, type, domain od propossed data"))
    notes = models.TextField(verbose_name=_("Data description"), blank=False)
    organization_name = models.CharField(max_length=100, blank=True, verbose_name=_("Institution name"))
    data_link = models.URLField(verbose_name=_('Link to data'), max_length=2000, blank=True, null=True)
    potential_possibilities = models.TextField(verbose_name=_('provide potential data use'), blank=True)
    comment = models.TextField(verbose_name=_("Comment"), null=True, blank=True)
    submission_date = models.DateField(null=True, verbose_name=_('Submission date'))
    decision = models.CharField(max_length=8, choices=DECISION_CHOICES, blank=True, verbose_name=_('decision'))
    decision_date = models.DateField(null=True, verbose_name=_("Decision date"))

    class Meta(ExtendedModel.Meta):
        abstract = True
        default_manager_name = 'objects'
        ordering = ('-submission_date',)
        verbose_name = _('Dataset submission')
        verbose_name_plural = _('Dataset submissions')

    def __str__(self):
        return self.title

    @property
    def is_accepted(self):
        return self.decision == 'accepted'

    @property
    def is_rejected(self):
        return self.decision == 'rejected'

    @property
    def truncated_notes(self):
        return self.truncatechars(self.notes)


class DatasetSubmission(DatasetSubmissionMixin):
    created_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('created by'),
        related_name='datasetsubmissions_created',
    )
    modified_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('modified by'),
        related_name='datasetsubmissions_modified',
    )
    submitted_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, editable=False, verbose_name=_('reported by'),
        related_name='datasetsubmissions_submitted',
    )
    accepted_dataset_submission = models.OneToOneField(
        'suggestions.AcceptedDatasetSubmission', on_delete=models.CASCADE, null=True, blank=True,
        verbose_name=_('accepted dataset submission'))
    # user_opinions = models.ManyToManyField(User, through='SubmissionOpinion',
    #                                        related_name='dataset_submission_opinions')

    objects = DatasetSubmissionManager()
    trash = DatasetSubmissionTrashManager()
    i18n = TranslationField()
    tracker = FieldTracker()

    class Meta(DatasetSubmissionMixin.Meta):
        pass

    @classmethod
    def convert_to_accepted(cls, obj_id):
        obj = cls.objects.filter(id=obj_id, accepted_dataset_submission__isnull=True).first()
        if obj:
            data = model_to_dict(
                obj,
                fields=['title', 'notes', 'organization_name', 'data_link', 'potential_possibilities', 'comment',
                        'submission_date', 'decision', 'decision_date', 'created_by', 'modified_by'])
            data['status'] = 'draft'
            data['is_active'] = True
            data['modified_by_id'] = data.pop('modified_by')
            data['created_by_id'] = data.pop('created_by') or data['modified_by_id']
            accepted = AcceptedDatasetSubmission.objects.create(**data)
            obj.accepted_dataset_submission = accepted
            obj.save()
            return accepted

    @classmethod
    def accusative_case(cls):
        return _("acc: Dataset submission")


class AcceptedDatasetSubmission(DatasetSubmissionMixin):
    STATUS = Choices(*ACCEPTED_DATASET_SUBMISSION_STATUS_CHOICES)
    PUBLISHED_STATUSES = (STATUS.published, STATUS.publication_finished)
    created_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('created by'),
        related_name='accepteddatasetsubmissions_created',
    )
    modified_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('modified by'),
        related_name='accepteddatasetsubmissions_modified',
    )
    submitted_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, editable=False, verbose_name=_('reported by'),
        related_name='accepteddatasetsubmissions_submitted',
    )
    is_active = models.BooleanField(default=False, verbose_name=_('proposal active'))

    is_published_for_all = models.BooleanField(default=False, verbose_name=_('publish for all users'))

    publication_finished_comment = models.TextField(blank=True, verbose_name=_('describe how the case was resolved'))
    publication_finished_at = MonitorField(monitor='status', when=['publication_finished', ],
                                           verbose_name=_("date of completion of publication"))

    @property
    def feedback_counters(self):
        return {
            'plus': self.feedback.filter(opinion='plus').count(),
            'minus': self.feedback.filter(opinion='minus').count()
        }

    @property
    def frontend_url(self):
        return f'/dataset/submissions/accepted/{self.id}'

    @property
    def frontend_absolute_url(self):
        return self._get_absolute_url(self.frontend_url)

    @classmethod
    def accusative_case(cls):
        return _('acc: Accepted dataset submission')

    @property
    def state_published(self):
        if all([
            self.status in self.PUBLISHED_STATUSES,
            not self.is_removed,
        ]):
            if self.is_created:
                return True
            else:
                if not self.was_published:
                    if self.was_removed:
                        return True
                    else:
                        if self.prev_status in (None, self.STATUS.draft):
                            return True
        return False

    @property
    def state_removed(self):
        if all([
            not self.is_created,
            not self.was_removed,
            self.prev_status in self.PUBLISHED_STATUSES
        ]):
            if self.status == self.STATUS.draft:
                return True
            elif self.status in self.PUBLISHED_STATUSES and self.is_removed:
                return True
        return False

    @property
    def state_restored(self):
        if all([
            self.status in self.PUBLISHED_STATUSES,
            not self.is_removed,
            not self.is_created,
            self.was_published
        ]):
            if self.was_removed:
                return True
            elif self.prev_status == self.STATUS.draft:
                return True
        return False

    @property
    def state_updated(self):
        if all([
            self.status in self.PUBLISHED_STATUSES,
            not self.is_removed,
            not self.is_created,
            self.prev_status in self.PUBLISHED_STATUSES,
            not self.was_removed
        ]):
            return True
        return False

    objects = AcceptedDatasetSubmissionManager()
    trash = AcceptedDatasetSubmissionTrashManager()
    i18n = TranslationField(fields=('title', 'notes', 'organization_name', 'potential_possibilities'))
    tracker = FieldTracker()

    class Meta(DatasetSubmissionMixin.Meta):
        verbose_name = _('Accepted dataset submission')
        verbose_name_plural = _('Accepted dataset submissions')


class DatasetSubmissionTrash(DatasetSubmission, metaclass=TrashModelBase):
    class Meta(DatasetSubmission.Meta):
        proxy = True
        verbose_name = _('Dataset submission - Trash')
        verbose_name_plural = _('Dataset submissions - Trash')


class AcceptedDatasetSubmissionTrash(AcceptedDatasetSubmission, metaclass=TrashModelBase):
    class Meta(AcceptedDatasetSubmission.Meta):
        proxy = True
        verbose_name = _('Accepted dataset submission - Trash')
        verbose_name_plural = _('Accepted dataset submissions - Trash')


class CommentMixin(ExtendedModel):
    DECISION_CHOICES = (
        ('accepted', _('Comment accepted')),
        ('rejected', _('Comment rejected')),
    )
    comment = models.TextField(blank=True, verbose_name=_('comment'))
    editor_comment = models.TextField(blank=True, verbose_name=_('comment'))
    report_date = models.DateField(verbose_name=_('report date'))
    decision = models.CharField(max_length=8, verbose_name=_('decision'), choices=DECISION_CHOICES, blank=True)
    decision_date = models.DateField(verbose_name=_('decision date'), null=True, blank=True)
    is_data_provider_error = models.BooleanField(default=False, verbose_name=_('data provider error'))
    is_user_error = models.BooleanField(default=False, verbose_name=_('user error'))
    is_portal_error = models.BooleanField(default=False, verbose_name=_('portal error'))
    is_other_error = models.BooleanField(default=False, verbose_name=_('other error'))

    i18n = TranslationField()

    class Meta(ExtendedModel.Meta):
        default_manager_name = 'objects'
        abstract = True

    @property
    def is_accepted(self):
        return self.decision == 'accepted'

    @property
    def is_rejected(self):
        return self.decision == 'rejected'

    @property
    def truncated_comment(self):
        return self.truncatechars(self.comment)


class DatasetComment(CommentMixin):
    dataset = models.ForeignKey(
        'datasets.Dataset', on_delete=models.CASCADE, related_name='comments', verbose_name=_('dataset'))
    created_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('created by'),
        related_name='dataset_comments_created',
    )

    modified_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('modified by'),
        related_name='dataset_comments_modified',
    )

    trash = DatasetCommentTrashManager()
    objects = DatasetCommentManager()
    tracker = FieldTracker()

    class Meta(CommentMixin.Meta):
        verbose_name = _('Dataset comment')
        verbose_name_plural = _('Dataset comments')

    def __str__(self):
        return self.dataset.title

    @property
    def data_url(self):
        return self.dataset.frontend_absolute_url

    @property
    def data_provider_url(self):
        return self.dataset.organization.frontend_absolute_url

    @property
    def editor_email(self):
        return ', '.join([x for x in self.dataset.comment_editors])

    @classmethod
    def accusative_case(cls):
        return _("acc: Dataset comment")


class DatasetCommentTrash(DatasetComment, metaclass=TrashModelBase):

    class Meta(DatasetComment.Meta):
        proxy = True
        verbose_name = _('Dataset Comment - Trash')
        verbose_name_plural = _('Dataset Comments - Trash')


class ResourceComment(CommentMixin):
    resource = models.ForeignKey(
        'resources.Resource', on_delete=models.CASCADE, related_name='comments', verbose_name=_('resource'))
    created_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('created by'),
        related_name='resource_comments_created',
    )

    modified_by = models.ForeignKey(
        User, models.DO_NOTHING, blank=True, null=True, verbose_name=_('modified by'),
        related_name='resource_comments_modified',
    )

    trash = ResourceCommentTrashManager()
    objects = ResourceCommentManager()
    tracker = FieldTracker()

    class Meta(CommentMixin.Meta):
        verbose_name = _('Resource comment')
        verbose_name_plural = _('Resource comments')

    def __str__(self):
        return self.resource.title

    @property
    def data_url(self):
        return self.resource.frontend_absolute_url

    @property
    def data_provider_url(self):
        return self.resource.dataset.organization.frontend_absolute_url

    @property
    def editor_email(self):
        return ', '.join([x for x in self.resource.comment_editors])

    @classmethod
    def accusative_case(cls):
        return _("acc: Resource comment")


class ResourceCommentTrash(ResourceComment, metaclass=TrashModelBase):

    class Meta(ResourceComment.Meta):
        proxy = True
        verbose_name = _('Resource Comment - Trash')
        verbose_name_plural = _('Resource Comments - Trash')


OPINION_CHOICES = [
    ('plus', _('Like')),
    ('minus', _('Dislike')),
]


class SubmissionFeedback(ExtendedModel):
    user = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
    )
    submission = models.ForeignKey(
        AcceptedDatasetSubmission,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        related_name='feedback'
    )
    opinion = models.CharField(
        max_length=6,
        choices=OPINION_CHOICES,
        default='plus',
        editable=True,
        verbose_name=_("Feedback")
    )

    i18n = TranslationField()

    tracker = FieldTracker()

    def get_unique_slug(self):
        return self.uuid

    def __str__(self):
        return f"{self.opinion} {self.submission.title} [{self.user.email}]"


@receiver(pre_save, sender=DatasetComment)
@receiver(pre_save, sender=ResourceComment)
def handle_datasetcomment_pre_save(sender, instance, *args, **kwargs):
    if not instance.report_date:
        instance.report_date = instance.created.date() if instance.created else timezone.now().date()


@receiver(pre_save, sender=DatasetComment)
@receiver(pre_save, sender=DatasetSubmission)
@receiver(pre_save, sender=ResourceComment)
def handle_dataset_submission_pre_save(sender, instance, *args, **kwargs):
    if instance.tracker.has_changed('decision'):
        instance.decision_date = timezone.now().date() if any([instance.is_accepted, instance.is_rejected]) else None


@receiver(post_save, sender=DatasetSubmission)
def handle_dataset_submission_post_save(sender, instance, created, *args, **kwargs):
    if created:
        send_dataset_suggestion_mail_task.s(instance.id).apply_async()


@receiver(post_save, sender=DatasetComment)
def handle_dataset_comment_post_save(sender, instance, created, *args, **kwargs):
    if created:
        send_dataset_comment.s(instance.dataset.id, instance.comment).apply_async(countdown=1)


@receiver(post_save, sender=ResourceComment)
def handle_resource_comment_post_save(sender, instance, created, *args, **kwargs):
    if created:
        send_resource_comment.s(instance.resource.id, instance.comment).apply_async(countdown=1)
