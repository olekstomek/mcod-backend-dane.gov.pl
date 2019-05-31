import pytest

from mcod.organizations.models import Organization
from mcod.users.forms import UserCreationForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email, password1, password2, fullname, is_staff, is_superuser, state, validity',
    [
        (
            'rtest1@test.pl',
            'password',
            'password',
            'R test',
            True,
            True,
            'active',
            True
        ),
        (
            'rtest1@test.pl', None, None, 'R test', True, True,
            'active',
            False
        ),
        (
            None, 'password', 'password', 'R test', True, True,
            'active',
            False
        ),

        (
            'rtest1@test.pl',
            'password',
            'password',
            'R test',
            True,
            True,
            None,
            False
        ),
    ])
def test_user_form_validity(admin_user, email, password1, password2, fullname, is_staff, is_superuser, state,
                            validity):
    form = UserCreationForm(data={
        'email': email,
        'password1': password1,
        'password2': password2,
        'fullname': fullname,
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        'state': state,
    })

    form.user = admin_user

    assert form.is_valid() is validity


@pytest.mark.django_db
def test_user_form_add_organization(admin_user, valid_organization):
    form = UserCreationForm(data={
        'email': 'rtest1@wp.pl',
        'password1': '123',
        'password2': '123',
        'fullname': 'R K',
        'is_staff': True,
        'is_superuser': False,
        'state': 'pending',
        'organizations': [valid_organization]
    })
    form.user = admin_user
    assert form.is_valid() is True
    user = form.save()
    organization = Organization.objects.get(id=valid_organization.id)
    assert user in organization.users.all()


@pytest.mark.django_db
def test_user_form_email_check_case_insensitive(admin_user, editor_user):
    form = UserCreationForm(data={
        'email': editor_user.email.upper(),
        'password1': '123',
        'password2': '123',
        'is_staff': True,
        'is_superuser': False,
        'state': 'active',
    })
    form.user = admin_user
    assert form.is_valid() is False
    assert 'email' in form.errors


@pytest.mark.django_db
def test_user_form_email_is_saved_with_small_letters(admin_user):
    form = UserCreationForm(data={
        'email': 'RTEST2@wp.pl',
        'password1': '123',
        'password2': '123',
        'fullname': 'R K',
        'is_staff': True,
        'is_superuser': False,
        'state': 'pending',
    })
    form.user = admin_user
    assert form.is_valid() is True
    user = form.save()
    assert user.email == "rtest2@wp.pl"
