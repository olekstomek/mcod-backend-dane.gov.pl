import pytest
from namedlist import namedlist
from mcod.organizations.forms import OrganizationForm
from mcod.organizations.models import Organization
from mcod.lib.helpers import change_namedlist

fields = [
    'slug',
    'title',
    'institution_type',
    'postal_code',
    'city',
    'street',
    'street_number',
    'flat_number',
    'street_type',
    'email',
    'fax',
    'tel',
    'epuap',
    'regon',
    'website',
    'status',
    'validity'
]

entry = namedlist('entry', fields)

empty = entry(
    slug=None,
    title=None,
    institution_type=None,
    postal_code=None,
    city=None,
    street=None,
    street_number=None,
    flat_number=None,
    street_type=None,
    email=None,
    fax=None,
    tel=None,
    epuap=None,
    regon=None,
    website=None,
    status=None,
    validity=False
)

minimal = change_namedlist(empty, {
    'title': "Organization title",
    'slug': "organization-title",
    'institution_type': 'local',
    'postal_code': "00-001",
    'city': "Warszawa",
    'street': "Królewska",
    'street_number': 1,
    'flat_number': 1,
    'street_type': "ul",
    'email': "r@wp.pl",
    'fax': "123123123",
    'tel': "123123123",
    'epuap': "123123123",
    'regon': "123456785",
    'website': "http://test.pl",
    'status': 'draft',
    'validity': True
})

validity_false = change_namedlist(minimal, {'validity': False})


@pytest.mark.django_db
class TestOrganizationFormValidity:
    """
    * - Not null fields:

    """

    @pytest.mark.parametrize(
        ", ".join(fields),
        [
            # correct scenarios
            minimal,  # minimal is full :)
            # incorrect scenarios
            # institution_type
            #   wrongo choice
            change_namedlist(
                validity_false, {
                    'title': 'Wrong institution type choice',
                    'institution_type': '12345'}
            ),
            # postal_code
            #   wrong postal_code format
            change_namedlist(validity_false, {'postal_code': '12345'}),
            # city
            change_namedlist(
                validity_false,
                {
                    'title': "Too long city name",
                    'city': 'a' * 201,
                }
            ),
            # street_type
            change_namedlist(
                validity_false,
                {
                    'title': "Too long street_type",
                    'street_type': 'a' * 51,
                }
            ),
            # street_number
            change_namedlist(
                validity_false,
                {
                    'title': "Too long street_number",
                    'street_type': 'a' * 201,
                }
            ),
            # flat_number
            change_namedlist(
                validity_false,
                {
                    'title': "Too long flat_number",
                    'street_type': 'a' * 201,
                }
            ),
            # email
            change_namedlist(
                validity_false,
                {
                    'title': "Too long email",
                    'email': 'a@' + 'a' * 300 + '.pl',
                }
            ),
            change_namedlist(
                validity_false,
                {
                    'title': "Wrong email type",
                    'email': 'a',
                }
            ),
            # regon
            change_namedlist(
                validity_false,
                {
                    'title': "Wrong regon",
                    'regon': '123456789',
                }
            ),
            # website
            change_namedlist(
                validity_false,
                {
                    'title': "Wrong website",
                    'website': '123456789',
                }
            ),
        ])
    def test_dataset_form_validity(self,
                                   slug,
                                   title,
                                   institution_type,
                                   postal_code,
                                   city,
                                   street,
                                   street_number,
                                   flat_number,
                                   street_type,
                                   email,
                                   fax,
                                   tel,
                                   epuap,
                                   regon,
                                   website,
                                   status,
                                   validity,
                                   ):
        form = OrganizationForm(data={
            'slug': slug,
            'title': title,
            'institution_type': institution_type,
            'postal_code': postal_code,
            'city': city,
            'street': street,
            'street_number': street_number,
            'flat_number': flat_number,
            'street_type': street_type,
            'email': email,
            'fax': fax,
            'tel': tel,
            'epuap': epuap,
            'regon': regon,
            'website': website,
            'status': status,
        })

        assert form.is_valid() is validity

    def test_create_and_save(self):
        data = {
            'title': "Organization title",
            'slug': "organization-title-1",
            'institution_type': 'local',
            'postal_code': "00-001",
            'city': "Warszawa",
            'street': "Królewska",
            'street_number': 1,
            'flat_number': 1,
            'street_type': "ul",
            'email': "r@wp.pl",
            'fax': "123123123",
            'tel': "123123123",
            'epuap': "123123123",
            'regon': "123456785",
            'website': "http://test.pl",
            'status': 'draft',
        }
        form = OrganizationForm(data=data)
        assert form.is_valid()
        form.save()
        last_ds = Organization.objects.last()
        assert last_ds.title == data['title']

    def test_save_add_users_to_existing_organization(self, valid_organization, editor_user):
        data = {
            'title': "Organization title",
            'slug': "organization-title-2",
            'institution_type': 'local',
            'postal_code': "00-001",
            'city': "Warszawa",
            'street': "Królewska",
            'street_number': 1,
            'flat_number': 1,
            'street_type': "ul",
            'email': "r@wp.pl",
            'fax': "123123123",
            'tel': "123123123",
            'epuap': "123123123",
            'regon': "123456785",
            'website': "http://test.pl",
            'status': 'draft',
            'users': [editor_user.id, ]
        }

        assert editor_user not in valid_organization.users.all()
        form = OrganizationForm(data=data, instance=valid_organization)
        assert form.instance.pk
        assert form.is_valid()
        saved_org = form.save(commit=False)
        assert editor_user in saved_org.users.all()

    def test_create_organization_and_add_users(self, editor_user):
        data = {
            'title': "Organization title",
            'slug': "organization-title-10",
            'institution_type': 'local',
            'postal_code': "00-001",
            'city': "Warszawa",
            'street': "Królewska",
            'street_number': 1,
            'flat_number': 1,
            'street_type': "ul",
            'email': "r@wp.pl",
            'fax': "123123123",
            'tel': "123123123",
            'epuap': "123123123",
            'regon': "123456785",
            'website': "http://test.pl",
            'status': 'draft',
            'users': [editor_user.id, ]
        }

        form = OrganizationForm(data=data)
        assert form.is_valid()
        saved_org = form.save()
        assert editor_user in saved_org.users.all()

    def test_add_users_to_unsaved_organization(self, editor_user):
        data = {
            'title': "Organization title",
            'slug': "organization-title",
            'institution_type': 'local',
            'postal_code': "00-001",
            'city': "Warszawa",
            'street': "Królewska",
            'street_number': 1,
            'flat_number': 1,
            'street_type': "ul",
            'email': "r@wp.pl",
            'fax': "123123123",
            'tel': "123123123",
            'epuap': "123123123",
            'regon': "123456785",
            'website': "http://test.pl",
            'status': 'draft',
            'users': [editor_user.id, ]
        }

        form = OrganizationForm(data=data)
        assert form.is_valid()
        saved_org = form.save(commit=False)
        with pytest.raises(ValueError):
            saved_org.users.all()
