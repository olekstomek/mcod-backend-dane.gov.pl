import pytest
from django.test import Client
from django.contrib import auth

from mcod.lib.rules import assigned_to_organization


@pytest.mark.django_db
class TestDatasetRules:

    def test_anonymous_user(self):
        client = Client()
        user = auth.get_user(client)
        assert not assigned_to_organization(user)

    def test_user_without_organization(self, editor_user):
        assert not assigned_to_organization(editor_user)

    def test_user_in_organization(self, user_with_organization):
        assert assigned_to_organization(user_with_organization)
