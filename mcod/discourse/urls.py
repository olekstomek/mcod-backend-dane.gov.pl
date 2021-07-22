from django.urls import path

from mcod.discourse.views import DiscourseLoginView, SSOProviderView
from mcod import settings


urlpatterns = [
    path('connect/login', DiscourseLoginView.as_view(), name='discourse-login'),
    path('connect/start', SSOProviderView.as_view(
        sso_secret=settings.DISCOURSE_SSO_SECRET,
        sso_redirect=settings.DISCOURSE_SSO_REDIRECT), name='discourse-sso'),
]
