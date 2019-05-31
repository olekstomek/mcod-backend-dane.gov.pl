import time
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import caches
from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from model_utils.models import SoftDeletableModel
from model_utils.models import TimeStampedModel

from mcod.core.api.search.tasks import update_document_task
from mcod.lib.jwt import decode_jwt_token

TOKEN_TYPES = (
    (0, _('Email validation token')),
    (1, _('Password reset token'))
)

session_cache = caches[settings.SESSION_CACHE_ALIAS]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('state', 'pending')
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('state', 'active')
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

    def get_or_none(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except User.DoesNotExist:
            return None

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD + '__iexact': username})


class User(AbstractBaseUser, PermissionsMixin, SoftDeletableModel, TimeStampedModel):
    email = models.EmailField(verbose_name=_("Email"), unique=True)
    password = models.CharField(max_length=130, verbose_name=_("Password"))
    fullname = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Full name"))
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Phone number'), db_column='tel')
    phone_internal = models.CharField(max_length=20, blank=True, null=True,
                                      verbose_name=_('int.'), db_column='tel_internal')
    is_staff = models.BooleanField(default=False, verbose_name=_('Editor'))  # is_staff ?
    is_superuser = models.BooleanField(verbose_name=_("Admin status"),
                                       help_text=_('Designates that this user has all permissions '
                                                   'without explicitly assigning them.'),
                                       default=False)
    state = models.CharField(max_length=20, verbose_name=_("State"), default='pending',
                             choices=settings.USER_STATE_CHOICES)  # wymagane, określone wartości
    email_confirmed = models.DateTimeField(null=True, blank=True, verbose_name=_("Email confirmation date"))
    organizations = models.ManyToManyField('organizations.Organization', db_table='user_organization',
                                           verbose_name=_('Organizations'), blank=True, related_name='users',
                                           related_query_name="user")
    followed_applications = models.ManyToManyField('applications.Application',
                                                   verbose_name=_('Followed applications'), blank=True,
                                                   through='users.UserFollowingApplication',
                                                   through_fields=('follower', 'application'),
                                                   related_name='users_following', related_query_name="user")
    followed_articles = models.ManyToManyField('articles.Article',
                                               verbose_name=_('Followed articles'), blank=True,
                                               through='users.UserFollowingArticle',
                                               through_fields=('follower', 'article'),
                                               related_name='users_following', related_query_name="user")
    followed_datasets = models.ManyToManyField('datasets.Dataset',
                                               verbose_name=_('Followed datasets'), blank=True,
                                               through='users.UserFollowingDataset',
                                               through_fields=('follower', 'dataset'),
                                               related_name='users_following', related_query_name="user")

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = 'user'
        default_manager_name = 'objects'

    def __str__(self):
        return self.email

    def check_session_valid(self, auth_header):
        try:
            user_payload = decode_jwt_token(auth_header)['user']
        except Exception:
            return False

        if 'session_key' not in user_payload:
            return False
        session_id = user_payload['session_key']
        session_data = session_cache.get('%s%s' % (KEY_PREFIX, session_id))
        if not session_data:
            return False

        if not set(('_auth_user_hash', '_auth_user_id')) <= set(session_data):
            return False

        if session_data['_auth_user_id'] != str(self.id):
            return False

        session_auth_hash = self.get_session_auth_hash()

        if session_data['_auth_user_hash'] != session_auth_hash:
            return False

        if not constant_time_compare(session_data['_auth_user_hash'], session_auth_hash):
            return False

        return True

    def _get_or_create_token(self, token_type):
        token = Token.objects.filter(
            user=self,
            token_type=token_type,
            expiration_date__gte=timezone.now()
        ).order_by('-expiration_date').first()

        if not token:
            token = Token.objects.create(
                user=self,
                token_type=token_type
            )
        return token.token

    @property
    def is_anonymous(self):
        return False

    @property
    def email_validation_token(self):
        return self._get_or_create_token(0)

    @property
    def password_reset_token(self):
        return self._get_or_create_token(1)

    @property
    def system_role(self):
        return 'staff' if self.is_staff or self.is_superuser else 'user'

    @property
    def count_datasets_created(self):
        return self.datasets_created.all().count()

    @property
    def count_datasets_modified(self):
        return self.datasets_modified.all().count()

    @property
    def is_normal_staff(self):
        return not self.is_superuser and self.is_staff

    @property
    def has_complete_staff_data(self):
        return all(field is not None
                   for field in (self.phone, self.fullname))

    @classmethod
    def accusative_case(cls):
        return _("acc: User")


@receiver(pre_save, sender=User)
def pre_save_handler(sender, instance, *args, **kwargs):
    instance.full_clean()
    if instance.is_removed is True:
        instance.email = f"{time.time()}_{uuid4()}@dane.gov.pl"
        instance.fullname = ""
        instance.status = "blocked"
        instance.is_staff = False
        instance.is_superuser = False


@receiver(user_logged_in)
def update_last_login(sender, request, user, **kwargs):
    user.last_login = timezone.now()
    user.save()


def get_token_expiration_date():
    return timezone.now() + timezone.timedelta(hours=settings.TOKEN_EXPIRATION_TIME)


class Token(TimeStampedModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE, blank=False, verbose_name=_('User'),
                             related_name='tokens')
    token = models.UUIDField(default=uuid4, editable=False, blank=False, verbose_name=_("Token"))
    token_type = models.IntegerField(default=0, choices=TOKEN_TYPES, blank=False, verbose_name=_('Token type'))
    expiration_date = models.DateTimeField(default=get_token_expiration_date, null=False, blank=False, editable=False,
                                           verbose_name=_('Expiration date'))

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
        db_table = 'token'

    @property
    def is_valid(self):
        return True if timezone.now() <= self.expiration_date else False

    def invalidate(self):
        if self.is_valid:
            self.expiration_date = timezone.now()
            self.save()


class FollowingModel(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def object_id(self):
        return getattr(self, self.object_type).id

    @property
    def object_type(self):
        return self._meta.db_table[len('user_following_'):]

    class Meta:
        abstract = True


class UserFollowingApplication(FollowingModel):
    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_following_application'


class UserFollowingArticle(FollowingModel):
    article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_following_article'


class UserFollowingDataset(FollowingModel):
    dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_following_dataset'


@receiver(post_delete, sender=UserFollowingApplication)
@receiver(post_save, sender=UserFollowingApplication)
@receiver(post_delete, sender=UserFollowingArticle)
@receiver(post_save, sender=UserFollowingArticle)
@receiver(post_delete, sender=UserFollowingDataset)
@receiver(post_save, sender=UserFollowingDataset)
def es_refresh(sender, instance, *args, **kwargs):
    resource_name = sender.__name__[13:].lower()
    resource = getattr(instance, resource_name)
    update_document_task.delay(resource._meta.app_label, resource._meta.object_name, resource.id)
