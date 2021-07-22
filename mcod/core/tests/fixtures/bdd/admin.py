import json

from django.test import Client
from django.urls import reverse
from pytest_bdd import given, then, when

from mcod.core.registries import factories_registry
from mcod.users.forms import UserCreationForm


@given('UserCreationForm with <posted_data>', target_fixture='user_creation_form')
def user_create_form_with_posted_data(posted_data):
    form = UserCreationForm(data=json.loads(posted_data))
    return form


@then('form validation equals <expected_validation>')
def form_validation_euqals(user_creation_form, expected_validation):
    validation_value = expected_validation == 'true'
    assert user_creation_form.is_valid() == validation_value


@when('admin user runs restore action for selected <object_type> objects with ids <restored_object_ids>')
def admin_user_runs_restore_action(admin_context, object_type, restored_object_ids):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    client = Client()
    client.force_login(admin_context.admin.user)
    page_url = reverse(f'admin:{model._meta.app_label}_{model.__name__}trash_changelist'.lower())
    data = {'action': 'restore_objects', '_selected_action': restored_object_ids.split(',')}
    response = client.post(page_url, data=data, follow=True)
    admin_context.response = response


@then('<object_type> objects with ids <restored_object_ids> are restored from trash')
def objects_with_ids_are_restored_from_trash(object_type, restored_object_ids):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    ids_list = restored_object_ids.split(',')
    assert model.objects.filter(
        pk__in=ids_list,
        is_removed=False
    ).count() == len(ids_list)


@then('<object_type> objects with ids <unrestored_object_ids> are still in trash')
def objects_with_ids_are_still_in_trash(object_type, unrestored_object_ids):
    _factory = factories_registry.get_factory(object_type)
    ids_list = unrestored_object_ids.split(',')
    model = _factory._meta.model
    assert model.raw.filter(
        pk__in=ids_list,
        is_removed=True
    ).count() == len(ids_list)
