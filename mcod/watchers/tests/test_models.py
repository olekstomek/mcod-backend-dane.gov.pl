import pytest
from django.db import transaction
from django.db.models import fields
from django.db.utils import IntegrityError
from django.utils.timezone import now, timedelta
from pytest_bdd import given, then, scenario

from mcod.watchers.models import ModelWatcher, WATCHER_TYPE_MODEL, InvalidRefField, ObjectCannotBeWatched, \
    watcher_updated, SearchQueryWatcher


@pytest.mark.django_db
@scenario('features/test_models.feature', 'Test model-watcher model')
def test_model_watcher():
    pass


# @pytest.mark.django_db
# @scenario('features/test_models.feature', 'Test query-watcher model')
# def test_query_watcher():
#     pass


@given('I have an instance of <object_name>')
def model_instance(request, object_name):
    factory_cls = request.getfixturevalue('{}_factory'.format(object_name))
    return factory_cls()


@then('I can create a model-watcher from an instance of <object_name>')
def create_watcher_from_instance(model_instance, object_name):
    watcher = ModelWatcher.objects.create_from_instance(model_instance)
    assert model_instance.is_watchable is True
    assert watcher.watcher_type == WATCHER_TYPE_MODEL
    assert str(model_instance.id) == watcher.object_ident
    object_name = '{}.{}'.format(model_instance._meta.app_label, model_instance._meta.object_name)
    assert watcher.object_name == object_name
    ref_field = getattr(model_instance, 'watcher_ref_field', 'modified')
    assert ref_field == watcher.ref_field
    ref_field_value = getattr(model_instance, ref_field)
    assert str(ref_field_value) == str(watcher.ref_value)
    d = now() - timedelta(seconds=20)
    assert d <= watcher.last_ref_change


@then("I can't create a model-watcher from given instance of <object_name> again")
def cannot_create_watcher_from_given_instance_again(mocker, model_instance, object_name):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ModelWatcher.objects.create_from_instance(model_instance)


@then("I can't create a model-watcher if an instance of <object_name> is not watchable")
def cannot_create_watcher_if_instance_not_watchable(mocker, model_instance, object_name):
    mocker.patch.object(model_instance.__class__, 'is_watchable', new_callable=mocker.PropertyMock, return_value=False)
    with pytest.raises(ObjectCannotBeWatched):
        ModelWatcher.objects.create_from_instance(model_instance)
    mocker.stopall()


@then("I can't get not existing a model-watcher for an instance of <object_name>")
def cannot_get_not_existing_watcher(mocker, model_instance, object_name):
    mock = mocker.MagicMock(model_instance)
    mock.id = 99999999
    with pytest.raises(ModelWatcher.DoesNotExist):
        ModelWatcher.objects.get_from_instance(mock)
    mocker.stopall()


@then("I can't create a model-watcher if an instance of <object_name> doesn't implement ref_field")
def cannot_create_watcher_if_not_ref_field(mocker, model_instance, object_name):
    mock = mocker.MagicMock(model_instance)
    mock.watcher_ref_field = 'this_field_does_not_exist'

    with pytest.raises(InvalidRefField):
        ModelWatcher.objects.create_from_instance(mock)

    mocker.stopall()


@then("I can get a model-watcher from an instance of <object_name>")
def get_watcher_from_instance(model_instance, object_name):
    assert model_instance.is_watchable is True
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert watcher.watcher_type == WATCHER_TYPE_MODEL
    assert str(model_instance.id) == watcher.object_ident
    object_name = '{}.{}'.format(model_instance._meta.app_label, model_instance._meta.object_name)
    assert watcher.object_name == object_name
    ref_field = getattr(model_instance, 'watcher_ref_field', 'modified')
    assert ref_field == watcher.ref_field
    ref_field_value = getattr(model_instance, ref_field)
    assert str(ref_field_value) == str(watcher.ref_value)
    d = now() - timedelta(seconds=20)
    assert d <= watcher.last_ref_change


@then("I can update model-watcher from an instance of <object_name>")
def update_watcher(mocker, model_instance, object_name):
    def s(instance, prev_value=None, obj_state=None, **kwargs):
        d['ok'] = True

    d = {'ok': False}
    watcher_updated.connect(s, sender=ModelWatcher)

    ref_field = getattr(model_instance, 'watcher_ref_field', 'modified')
    mocker.patch.object(model_instance, ref_field, create=True, spec=fields.CharField)
    setattr(model_instance, ref_field, 'hacked')
    result = ModelWatcher.objects.update_from_instance(model_instance)
    assert result == 1
    watcher_updated.disconnect(s, sender=ModelWatcher)
    assert d['ok'] is True

    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert watcher.ref_value == 'hacked'
    mocker.stopall()
    result = ModelWatcher.objects.update_from_instance(model_instance)
    assert result == 1
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    ref_field_value = getattr(model_instance, ref_field)
    assert ref_field == watcher.ref_field
    assert str(ref_field_value) == str(watcher.ref_value)


@then("I can't update model-watcher if an instance of <object_name> hasn't changed")
def cannot_update_watcher_if_object_hasnt_changed(model_instance, object_name):
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    last_ref_change = watcher.last_ref_change
    result = ModelWatcher.objects.update_from_instance(model_instance)
    assert result == 0
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert last_ref_change == watcher.last_ref_change
    result = ModelWatcher.objects.update_from_instance(model_instance)
    assert result == 0
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert last_ref_change == watcher.last_ref_change


@then("I can force updating model-watcher even if an instance of <object_name> hasn't changed")
def force_update_watcher(model_instance, object_name):
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    last_ref_change = watcher.last_ref_change
    result = ModelWatcher.objects.update_from_instance(model_instance)
    assert result == 0
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert last_ref_change == watcher.last_ref_change
    result = ModelWatcher.objects.update_from_instance(model_instance, force=True)
    assert result == 1
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    assert watcher.last_ref_change != last_ref_change


@then("I can update model-watcher without sending notifications")
def turn_on_off_notifications(model_instance):
    def s(instance, prev_value=None, obj_state=None, **kwargs):
        assert 1 == 2

    watcher_updated.connect(s, sender=ModelWatcher)
    result = ModelWatcher.objects.update_from_instance(model_instance, notify_subscribers=False, force=True)
    watcher_updated.disconnect(s, sender=ModelWatcher)
    assert result == 1


@then("I can't update not existing model-watcher from an instance of <object_name>")
def cannot_update_not_existing_watcher(mocker, model_instance, object_name):
    mocker.patch.object(model_instance, 'id', spec=fields.AutoField)
    setattr(model_instance, 'id', 99999999)
    with pytest.raises(ModelWatcher.DoesNotExist):
        ModelWatcher.objects.update_from_instance(model_instance)
    mocker.stopall()


@then("I can remove model-watcher created from an instance of <object_name>")
def i_can_remove_watcher(model_instance, object_name):
    watcher = ModelWatcher.objects.get_from_instance(model_instance)
    watcher.delete()
    with pytest.raises(ModelWatcher.DoesNotExist):
        ModelWatcher.objects.get_from_instance(model_instance)


@given('I have an url')
def query_url(request):
    return "https://api.dane.gov.pl/datasets?page=1&per_page=5&q=imiona&sort="


@then("I can create a query-watcher from given url")
def create_watcher_from_url(query_url):
    watcher = SearchQueryWatcher.objects.create_from_url(query_url)
    assert model_instance.is_watchable is True
    assert watcher.watcher_type == WATCHER_TYPE_MODEL
    assert str(model_instance.id) == watcher.object_ident
    object_name = '{}.{}'.format(model_instance._meta.app_label, model_instance._meta.object_name)
    assert watcher.object_name == object_name
    ref_field = getattr(model_instance, 'watcher_ref_field', 'modified')
    assert ref_field == watcher.ref_field
    ref_field_value = getattr(model_instance, ref_field)
    assert str(ref_field_value) == str(watcher.ref_value)
    d = now() - timedelta(seconds=20)
    assert d <= watcher.last_ref_change

# @then("I can't create a query-watcher from given the same url again")
# def cannot_duplicate_watcher():
#     pass
#
#
# @then("I can get a query-watcher from an url")
# def can_get_watcher_from_url():
#     pass
#
#
# @then("I can't get not existing query-watcher for an url")
# def cannot_get_not_existing_watcher():
#     pass
#
#
# @then("I can update query-watcher data for given url")
# def update_query_watcher_from_url():
#     pass
#
#
# @then("I can't update not existing query-watcher from an url")
# def cannot_update_not_existing_watcher():
#     pass
