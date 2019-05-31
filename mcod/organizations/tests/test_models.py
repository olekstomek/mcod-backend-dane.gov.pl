import pytest
from datetime import date

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization


@pytest.mark.django_db
class TestOrganizationModel:

    def test_organization_create(self):
        organization = Organization()
        organization.slug = "test"
        organization.title = "test"
        organization.postal_code = "00-001"
        organization.city = "Warszwa"
        organization.street = "Królewska"
        organization.street_number = "27"
        organization.flat_number = "1"
        organization.street_type = "ul"
        organization.email = "email@email.pl"
        organization.fax = "123123123"
        organization.tel = "123123123"
        organization.epuap = "epuap"
        organization.regon = "123123123"
        organization.website = "www.www.www"
        assert organization.id is None
        organization.save()
        assert organization.id is not None
        assert Organization.objects.last().id == organization.id

    def test_required_fields_validation(self):
        org = Organization()
        with pytest.raises(ValidationError) as e:
            org.full_clean()
        e = str(e.value)
        assert "'title'" in e
        assert "'postal_code'" in e
        assert "'city'" in e
        assert "'street'" in e
        # assert "'street_number'" in e
        # assert "'flat_number'" in e
        assert "'street_type'" in e
        assert "'email'" in e
        assert "'fax'" in e
        assert "'tel'" in e
        assert "'epuap'" in e
        assert "'regon'" in e
        assert "'website'" in e

    # def test_name_uniqness(self, valid_organization):
    #     org = Organization()
    #     org.slug = valid_organization.slug
    #     with pytest.raises(ValidationError) as e:
    #         org.full_clean()
    #
    #     assert "'slug': " in str(e.value)

    def test_str(self, valid_organization):
        valid_organization.name = 'test-name'
        valid_organization.title = 'Title'
        assert 'Title' == str(valid_organization)

    def test_str_no_title(self, valid_organization):
        valid_organization.slug = 'test-name'
        valid_organization.title = ''
        assert 'test-name' == str(valid_organization)

    def test_get_url_path(self, valid_organization):
        assert f'/applications/application/{valid_organization.id}/change/' == valid_organization.get_url_path()

    def test_get_url_path_no_reverse(self):
        org = Organization()
        assert '' == org.get_url_path()

    def test_short_description(self):
        org = Organization()
        org.description = "<p>Paragraph</p>"
        assert 'Paragraph' == org.short_description

    def test_short_description_no_description(self):
        org = Organization()
        org.description = None
        assert '' == org.short_description

    def test_image_url_and_path(self, valid_organization):
        assert not valid_organization.image
        valid_organization.image = SimpleUploadedFile("somefile.jpg", b"""1px""")
        valid_organization.save()
        assert valid_organization.image
        date_folder = date.today().isoformat().replace('-', '')
        image_name = valid_organization.image.name
        assert valid_organization.image.url == f"/media/images/organizations/{image_name}"
        assert valid_organization.image.path == f"{settings.IMAGES_MEDIA_ROOT}/organizations/{image_name}"
        assert date_folder in valid_organization.image.url
        assert date_folder in valid_organization.image.path

    def test_organizations_datasets_count(self, valid_organization, valid_dataset):
        assert valid_organization.datasets_count == 1

    def test_delete_organizations_also_delete_his_datasets(self, valid_organization, valid_dataset):
        assert valid_dataset in valid_organization.datasets.all()
        valid_organization.delete()
        assert valid_dataset not in Dataset.objects.all()
        assert valid_dataset in Dataset.deleted.all()

    def test_changing_organization_to_draft_also_set_draft_for_his_datasets(self, valid_organization, valid_dataset):
        assert valid_dataset in valid_organization.datasets.all()
        assert valid_organization.status == 'published'
        assert valid_organization.datasets.all().first().status == 'published'

        valid_organization.status = 'draft'
        valid_organization.save()

        assert valid_organization.status == 'draft'
        assert valid_organization.datasets.all().first().status == 'draft'

    def test_changing_organization_to_published_didnt_publish_his_datasets(self, valid_organization, valid_dataset):
        assert valid_dataset in valid_organization.datasets.all()
        assert valid_organization.status == 'published'
        assert valid_organization.datasets.all().first().status == 'published'

        valid_organization.status = 'draft'
        valid_organization.save()

        assert valid_organization.status == 'draft'
        assert valid_organization.datasets.all().first().status == 'draft'

        valid_organization.status = 'published'
        valid_organization.save()

        assert valid_organization.status == 'published'
        assert valid_organization.datasets.all().first().status == 'draft'
