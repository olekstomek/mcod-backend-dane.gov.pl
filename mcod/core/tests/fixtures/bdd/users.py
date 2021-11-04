import json

from django.test import Client as DjangoClient
from django.core import mail
from pytest_bdd import given, then
from pytest_bdd import parsers

from mcod.core.caches import flush_sessions
from mcod.core.registries import factories_registry
from mcod.users.factories import (
    AdminFactory,
    EditorFactory,
    MeetingFactory,
    MeetingFileFactory,
    UserFactory,
)
from mcod.users.models import User
from mcod.newsletter.models import Subscription
from mcod.organizations.models import Organization
from mcod.resources.factories import ResourceFactory


@given(parsers.parse('{state} user with email {email_address} and password {password}'))
def user_with_state_email_and_password(context, state, email_address, password):
    assert state in ['active', 'pending']
    return UserFactory(
        email=email_address,
        password=password,
        state=state,
    )


@given(parsers.parse('{state} user for data{data_str}'))
def user_for_data(context, state, data_str):
    assert state in ['active', 'pending']
    data = json.loads(data_str)
    data['state'] = state
    return UserFactory(**data)


@given('session is flushed')
def session_is_flushed():
    flush_sessions()


@given(parsers.parse('logged active user'))
def logged_active_user(context):
    context.user = UserFactory(
        email='active_user@dane.gov.pl',
        password='12345.Abcde',
        state='active'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged agent user created with {params}'))
@given('logged agent user created with <params>')
def logged_agent_user_created_with_params(context, params):
    _factory = factories_registry.get_factory('agent user')
    kwargs = {
        'email': 'agent_user@dane.gov.pl',
        'password': '12345.Abcde',
    }
    kwargs.update(json.loads(params))
    context.user = _factory(**kwargs)
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged out agent user created with {params}'))
@given('logged out agent user created with <params>')
def logged_out_agent_user_created_with_params(context, params):
    _factory = factories_registry.get_factory('agent user')
    kwargs = {
        'email': 'agent_user@dane.gov.pl',
        'password': '12345.Abcde',
    }
    kwargs.update(json.loads(params))
    context.user = _factory(**kwargs)
    DjangoClient().logout()


@given(parsers.parse('logged extra agent with id {extra_agent_id:d} of agent with id {agent_id:d}'))
@given('logged extra agent with id <extra_agent_id> of agent with id <agent_id>')
def logged_extra_agent_with_id_of_agent_with_id(context, extra_agent_id, agent_id):
    _agent_factory = factories_registry.get_factory('agent user')
    _active_user_factory = factories_registry.get_factory('active user')
    agent = _agent_factory(
        id=agent_id,
        email='agent_user@dane.gov.pl',
        password='12345.Abcde',
    )
    user = _active_user_factory(
        id=extra_agent_id,
        email='extra_agent_user@dane.gov.pl',
        password='12345.Abcde',
    )
    user.extra_agent_of = agent
    user.save()
    context.user = user
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged {user_type}'))
@given('logged <user_type>')
def logged_user_type(context, user_type):
    _factory = factories_registry.get_factory(user_type)
    context.user = _factory(
        email='{}@dane.gov.pl'.format(user_type.replace(' ', '_')),
        password='12345.Abcde',
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse(
    'logged active user with email {email} and newsletter subscription enabled with code {activation_code}'))
def logged_active_user_with_newsletter_subscription_enabled(context, email, activation_code):
    user = UserFactory(
        email=email,
        password='12345.Abcde',
        state='active'
    )
    subscription = Subscription.subscribe(email, user=user)
    subscription.activation_code = activation_code
    subscription.confirm_subscription()
    context.user = user
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged active user with email {email_address} and password {password}'))
def logged_active_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='active'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged out {state} user with email {email} and password {password}'))
def logged_out_user_with_email_and_password(context, state, email, password):
    context.user = UserFactory(
        email=email,
        password=password,
        state=state,
    )
    DjangoClient().logout()


@given(parsers.parse('logged pending user'))
def logged_pending_user(context):
    context.user = UserFactory(
        email='pending_user@dane.gov.pl',
        password='12345.Abcde',
        state='pending'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged pending user with email {email_address} and password {password}'))
def logged_pending_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='pending'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged blocked user'))
def logged_blocked_user(context):
    context.user = UserFactory(
        email='blocked_user@dane.gov.pl',
        password='12345.Abcde',
        state='blocked'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged blocked user with email {email_address} and password {password}'))
def logged_blocked_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='blocked'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged removed user'))
def logged_removed_user(context):
    context.user = UserFactory(
        email='removed_user@dane.gov.pl',
        password='12345.Abcde',
        is_removed=True
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged removed user with email {email_address} and password {password}'))
def logged_removed_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        is_removed=True
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged admin user'))
def logged_admin(context, admin):
    context.user = admin
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged admin user with email {email_address} and password {password}'))
def logged_admin_with_email_and_password(context, email_address, password):
    context.user = AdminFactory(
        email=email_address,
        password=password,
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@given(parsers.parse('logged user is from organization of resource {res_id:d}'))
def logged_user_with_organization(context, res_id):
    resource = ResourceFactory.create(id=res_id)
    context.user.organizations.add(resource.dataset.organization)


@given(parsers.parse('editor with id {editor_id:d} from organization of resource {res_id:d}'))
def user_with_id_with_organization(context, editor_id, res_id):
    resource = ResourceFactory.create(id=res_id)
    editor = EditorFactory.create(id=editor_id)
    editor.organizations.add(resource.dataset.organization)


@given(parsers.parse('logged editor user with email {email_address} and password {password}'))
def logged_editor_with_email_and_password(context, email_address, password):
    context.user = EditorFactory(
        email=email_address,
        password=password,
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged active user attribute {user_attribute} is {user_attribute_value}'))
def logged_user_attribute_is(context, user_attribute, user_attribute_value):
    user = User.objects.get(id=context.user.id)
    assert str(getattr(user, user_attribute)) == user_attribute_value


@then(parsers.parse('user with id {user_id:d} attribute {user_attribute} is {user_attribute_value}'))
def user_attribute_is(context, user_id, user_attribute, user_attribute_value):
    user = User.objects.get(id=user_id)
    assert str(getattr(user, user_attribute)) == user_attribute_value


@then(parsers.parse('user with email {email} is related to institution with id {organization_id:d}'))
def user_organization_is(context, email, organization_id):
    user = User.objects.get(email=email)
    organization = Organization.objects.get(id=organization_id)
    assert user in organization.users.all()


@then(parsers.parse('logged as another active user'))
def logged_as_another_active_user(context):
    context.user = UserFactory(
        email='active_user@dane.gov.pl',
        password='12345.Abcde',
        state='active'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another active user with email {email_address} and password {password}'))
def logged_as_another_active_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='active'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another pending user'))
def logged_as_another_pending_user(context):
    context.user = UserFactory(
        email='pending_user@dane.gov.pl',
        password='12345.Abcde',
        state='pending'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another pending user with email {email_address} and password {password}'))
def logged_as_another_pending_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='pending'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another blocked user'))
def logged_as_another_blocked_user(context):
    context.user = UserFactory(
        email='blocked_user@dane.gov.pl',
        password='12345.Abcde',
        state='blocked'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another blocked user with email {email_address} and password {password}'))
def logged_as_another_blocked_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        state='blocked'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another removed user'))
def logged_as_another_removed_user(context):
    context.user = UserFactory(
        email='removed_user@dane.gov.pl',
        password='12345.Abcde',
        is_removed=True
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another removed user with email {email_address} and password {password}'))
def logged_as_another_removed_user_with_email_and_password(context, email_address, password):
    context.user = UserFactory(
        email=email_address,
        password=password,
        is_removed=True
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another admin user'))
def logged_as_another_admin(context):
    context.user = AdminFactory(
        email='admin@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another admin user with email {email_address} and password {password}'))
def logged_as_another_admin_with_email_and_password(context, email_address, password):
    context.user = AdminFactory(
        email=email_address,
        password=password,
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another editor user'))
def logged_as_another_editor(context):
    context.user = EditorFactory(
        email='editor@dane.gov.pl',
        password='12345.Abcde',
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('logged as another editor user with email {email_address} and password {password}'))
def logged_as_another_editor_with_email_and_password(context, email_address, password):
    context.user = EditorFactory(
        email=email_address,
        password=password,
        phone='0048123456789'
    )
    DjangoClient().force_login(context.user)


@then(parsers.parse('sent email contains {text}'))
@then('sent email contains <text>')
def sent_email_contains_text(context, text):
    assert len(mail.outbox) == 1
    assert text in mail.outbox[0].body, f'Phrase: "{text}" not found in email content.'


@then(parsers.parse('sent email recipient is {recipient}'))
@then('sent email recipient is <recipient>')
def sent_mail_recipient_is(context, recipient):
    assert recipient in mail.outbox[0].to


@then(parsers.parse('valid {link_type} link for {email} in mail content'))
def valid_link_for_email_in_mail_content(context, link_type, email):
    assert link_type in ['confirmation', 'reset']
    user = User.objects.get(email=email)
    links = {
        'confirmation': user.email_validation_absolute_url,
        'reset': user.password_reset_absolute_url,
    }
    assert len(mail.outbox) == 1
    assert links[link_type] in mail.outbox[0].body


@then(parsers.parse('password {password} is valid for user {email}'))
def password_is_valid_for_user_email(password, email):
    user = User.objects.get(email=email)
    assert user.check_password(password), f'password "{password}" is not valid for user: {email}'


@given(parsers.parse('logged {object_type} for data {user_data}'))
@given('logged <object_type> for data <user_data>')
def generic_user_with_data(object_type, user_data, context, admin_context):
    assert object_type.endswith(' user'), 'this keyword is only suited for creating users'
    factory_ = factories_registry.get_factory(object_type)
    if factory_ is None:
        raise ValueError('invalid object type: %s' % object_type)
    user_data = json.loads(user_data)
    user = admin_context.admin.user = context.user = factory_(**user_data)
    DjangoClient().force_login(user)


@given(parsers.parse('meeting with id {meeting_id:d} and {number:d} files'))
@given('meetings with id <meeting_id> and <number> files')
def meeting_with_files(meeting_id, number):
    obj = MeetingFactory(id=meeting_id)
    MeetingFileFactory.create_batch(int(number), meeting=obj)
    obj.save()
    return obj
