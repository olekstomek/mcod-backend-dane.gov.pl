import json
from unittest import mock
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import pytest
from falcon.testing import TestClient
from pytest_bdd import given, parsers, then, when

from mcod.api import app
from mcod.core.api.versions import VERSIONS
from mcod.core.registries import factories_registry
from mcod.watchers.factories import (
    NotificationFactory,
    SearchQueryWatcherFactory,
    SubscriptionFactory,
)
from mcod.watchers.models import SubscribedObjectDoesNotExist, SubscriptionCannotBeCreated
from mcod.watchers.tasks import update_query_watchers_task


def create_subscription(user, factory_name, instance_id, subscription_id, subscription_name, instance_removed=False,
                        instance_status='published'):
    _factory = factories_registry.get_factory(factory_name)
    instance = _factory(pk=instance_id, is_removed=instance_removed, status=instance_status)
    data = {
        'name': subscription_name,
        'object_name': factory_name.lower(),
        'object_ident': instance.id
    }
    return SubscriptionFactory.create(user=user, data=data, force_id=subscription_id)


def create_notification(
        notification_id,
        subscription_id,
        notification_type='object_updated',
        notification_status='new'
):
    s_model = SubscriptionFactory._meta.model
    subscription = s_model.objects.get(pk=subscription_id)
    return NotificationFactory.create(pk=notification_id, subscription=subscription,
                                      notification_type=notification_type,
                                      status=notification_status)


@given('admin has subscription with id 900 of <object_type> with id 900 as admin-subscription-900')
def admin_subscription_with_id_of_an_factory_1(admin, object_type, context):
    create_subscription(admin, object_type, 900, 900, 'admin-subscription-900')


@given('admin has subscription with id 901 of <object_type> with id 901 as admin-subscription-901')
def admin_subscription_with_id_of_an_factory_2(admin, object_type, context):
    create_subscription(admin, object_type, 901, 901, 'admin-subscription-901')


@given('admin has subscription with id 902 of <object_type> with id 902 as admin-subscription-902')
def admin_subscription_with_id_of_an_factory_3(admin, object_type, context):
    create_subscription(admin, object_type, 902, 902, 'admin-subscription-902')


@given(parsers.cfparse('admin has subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def admin_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    create_subscription(admin, object_type, f_id, s_id, s_name)


@given(parsers.cfparse('admin has second subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def second_admin_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    create_subscription(admin, object_type, f_id, s_id, s_name)


@given(parsers.cfparse('admin has third subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def third_admin_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    create_subscription(admin, object_type, f_id, s_id, s_name)


@given('subscription with id 999 of <object_type> with id 999 as subscription-999')
def subscription_with_id_of_an_factory_1(object_type, context):
    create_subscription(context.user, object_type, 999, 999, 'subscription-999')


@given('subscription with id 998 of <object_type> with id 998 as subscription-998')
def subscription_with_id_of_an_factory_2(object_type, context):
    create_subscription(context.user, object_type, 998, 998, 'subscription-998')


@given('subscription with id 997 of <object_type> with id 997 as subscription-997')
def subscription_with_id_of_an_factory_3(object_type, context):
    create_subscription(context.user, object_type, 997, 997, 'subscription-997')


@given('subscription with id 996 of <object_type> with id 996 as subscription-996')
def subscription_with_id_of_an_factory_4(object_type, context):
    create_subscription(context.user, object_type, 996, 996, 'subscription-996')


@given('subscription with id 995 of <object_type> with id 995 as subscription-995')
def subscription_with_id_of_an_factory_5(object_type, context):
    create_subscription(context.user, object_type, 995, 995, 'subscription-995')


@given(parsers.cfparse('logged user has subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
@given(parsers.cfparse('subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id)
    except model.DoesNotExist:
        instance = _factory(pk=f_id)
    data = {
        'name': s_name,
        'object_name': object_type.lower(),
        'object_ident': instance.id
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.cfparse('second subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def second_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id)
    except model.DoesNotExist:
        instance = _factory(pk=f_id)
    data = {
        'name': s_name,
        'object_name': object_type.lower(),
        'object_ident': instance.id
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.cfparse('third subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def third_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id)
    except model.DoesNotExist:
        instance = _factory(pk=f_id)
    data = {
        'name': s_name,
        'object_name': object_type.lower(),
        'object_ident': instance.id
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.cfparse('fourth subscription with id {s_id:d} of {object_type} with id {f_id:d} as {s_name}'))
def fourth_subscription_with_id_of_an_factory(admin, s_id, object_type, f_id, s_name, context):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id)
    except model.DoesNotExist:
        instance = _factory(pk=f_id)
    data = {
        'name': s_name,
        'object_name': object_type.lower(),
        'object_ident': instance.id
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.cfparse('subscription with id {s_id:d} of draft {factory_name} with id {f_id:d} as {s_name}'))
def subscription_with_id_of_draft_factory(admin, s_id, factory_name, f_id, s_name, context):
    _factory = factories_registry.get_factory(factory_name)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id, status='draft')
    except model.DoesNotExist:
        instance = _factory(pk=f_id, status='draft')
    data = {
        'name': s_name,
        'object_name': factory_name.lower(),
        'object_ident': instance.id
    }

    with pytest.raises(SubscriptionCannotBeCreated):
        SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.cfparse('subscription with id {s_id:d} of removed {factory_name} with id {f_id:d} as {s_name}'))
def subscription_with_id_of_removed_factory(admin, s_id, factory_name, f_id, s_name, context):
    _factory = factories_registry.get_factory(factory_name)
    model = _factory._meta.model
    try:
        instance = model.objects.get(pk=f_id, is_removed=True)
    except model.DoesNotExist:
        instance = _factory(pk=f_id, is_removed=True)
    data = {
        'name': s_name,
        'object_name': factory_name.lower(),
        'object_ident': instance.id
    }
    with pytest.raises(SubscribedObjectDoesNotExist):
        SubscriptionFactory.create(user=context.user, data=data, force_id=s_id)


@given(parsers.parse('{total:d} subscriptions of random {factory_name}'))
def x_subscriptions_of_random_factory(total, factory_name, context):
    _factory = factories_registry.get_factory(factory_name)
    instances = _factory.create_batch(total)
    for instance in instances:
        data = {
            'object_name': instance._meta.object_name.lower(),
            'object_ident': instance.id
        }
        SubscriptionFactory.create(user=context.user, data=data)


@given(parsers.parse('and {total:d} subscriptions of random {factory_name}'))
def and_x_subscriptions_of_random_factory(total, factory_name, context):
    _factory = factories_registry.get_factory(factory_name)
    instances = _factory.create_batch(total)
    for instance in instances:
        data = {
            'object_name': instance._meta.object_name.lower(),
            'object_ident': instance.id
        }
        SubscriptionFactory.create(user=context.user, data=data)


@given(parsers.parse('also {total:d} subscriptions of random {factory_name}'))
def also_x_subscriptions_of_random_factory(total, factory_name, context):
    _factory = factories_registry.get_factory(factory_name)
    instances = _factory.create_batch(total)
    for instance in instances:
        data = {
            'object_name': instance._meta.object_name.lower(),
            'object_ident': instance.id
        }
        SubscriptionFactory.create(user=context.user, data=data)


@when(parsers.parse('api request body object customfield {attr_name} is {attr_value}'))
def api_request_object_customfield(attr_name, attr_value, context):
    customfields = context.obj.attrs.setdefault('customfields', {})
    customfields[attr_name] = attr_value


@then(parsers.parse('api response customfield {attr_name} in item at position {item_idx:d} is {attr_value}'))
def api_check_given_item_customfield(attr_name, item_idx, attr_value, context):
    items = context.response.json['data']
    if not isinstance(items, list):
        items = [items, ]
    item = items[item_idx - 1]
    assert str(item['attributes']['customfields'][attr_name]) == str(attr_value)


@given(parsers.parse('query subscription with id {s_id:d} for url {query_url} as {s_name}'))
def query_subscription_with_id(s_id, query_url, s_name, context):
    data = {
        'name': s_name,
        'object_name': 'query',
        'object_ident': query_url
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=int(s_id))


@given(parsers.parse('second query subscription with id {s_id:d} for url {query_url} as {s_name}'))
def second_query_subscription_with_id(s_id, query_url, s_name, context):
    data = {
        'name': s_name,
        'object_name': 'query',
        'object_ident': query_url
    }
    SubscriptionFactory.create(user=context.user, data=data, force_id=int(s_id))


@given(parsers.parse('query subscription with id {s_id:d} for url {query_url} with {meta_count} results'))
def query_subscription_with_id_and_watcher_ref_value(s_id, query_url, meta_count, context):
    API_VERSION = str(max(VERSIONS))
    search_query_watcher = SearchQueryWatcherFactory.create(
        object_name='query',
        object_ident=query_url,
        ref_field='/meta/count',
        customfields={
            'headers': {
                'X-API-VERSION': API_VERSION,
                'api_version': API_VERSION,
            },
        }
    )
    # TODO remove setting ref_value here, once SearchQueryWatcher has implemented ref_value initialization on creation
    search_query_watcher.ref_value = meta_count
    search_query_watcher.save()

    data = {
        'name': str(uuid4()),
        'object_name': 'query',
        'object_ident': query_url,
    }
    SubscriptionFactory.create(user=context.user, data=data, watcher=search_query_watcher, force_id=int(s_id))


@given(parsers.cfparse('admin has query subscription with id {s_id:d} for url {query_url} as {s_name}'))
def admin_subscription_of_query(admin, s_id, query_url, s_name, context):
    data = {
        'name': s_name,
        'object_name': 'query',
        'object_ident': query_url
    }
    SubscriptionFactory.create(user=admin, data=data, force_id=int(s_id))


@given(parsers.cfparse('notification with id {not_id:d} for subscription with id {sub_id:d}'))
def notification_with_id_for_subscription(not_id, sub_id, context):
    return create_notification(not_id, sub_id)


@given(parsers.cfparse('second notification with id {not_id:d} for subscription with id {sub_id:d}'))
def second_notification_with_id_for_subscription(not_id, sub_id, context):
    return create_notification(not_id, sub_id)


@given(parsers.cfparse('third notification with id {not_id:d} for subscription with id {sub_id:d}'))
def third_notification_with_id_for_subscription(not_id, sub_id, context):
    return create_notification(not_id, sub_id)


@then('trigger query watcher update')
def trigger_query_watcher_update():
    def get(url, headers, allow_redirects=False, verify=True, timeout=1):
        url = urlunsplit(urlsplit(url)._replace(scheme='')._replace(netloc=''))
        return TestClient(app).simulate_get(url, headers=headers)

    with mock.patch('requests.get', get), mock.patch('falcon.testing.client.Result.json', lambda self: json.loads(self.text)):
        update_query_watchers_task()
