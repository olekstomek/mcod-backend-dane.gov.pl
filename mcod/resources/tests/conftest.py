import os
from shutil import copyfile

import pytest
from django.core.files import File
from django.utils.timezone import datetime
from falcon import HTTP_OK
from openapi_core import create_spec
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from pytest_bdd import given, when, then, parsers

from mcod import settings
from mcod.api import app
from mcod.core.tests.conftest import *  # noqa
from mcod.core.tests.helpers.openapi_wrappers import FalconOpenAPIWrapper
from mcod.core.utils import jsonapi_validator
from mcod.resources.models import Resource


@pytest.fixture
def journalism_category(admin_user):
    from mcod.categories.models import Category
    return Category.objects.create(
        slug='Dziennikarstwo',
        title='Dziennikarstwo',
        title_en='Journalism',
        description='Różnego rodzaju analizy i statystyki związane z dziennikarstwem.',
        description_en='Various analysis, statistics and data related to journalism.',
        created_by=admin_user,
        modified_by=admin_user,
        status='published'
    )


@pytest.fixture
def fakenews_tag(admin_user):
    from mcod.tags.models import Tag
    return Tag.objects.create(
        name='fakenews',
        created_by=admin_user,
        modified_by=admin_user,
        status='published'
    )


@pytest.fixture
def top50_tag(admin_user):
    from mcod.tags.models import Tag
    return Tag.objects.create(
        name='top50',
        created_by=admin_user,
        modified_by=admin_user,
        status='published'
    )


@pytest.fixture
def analysis_tag(admin_user):
    from mcod.tags.models import Tag
    return Tag.objects.create(
        name='analysis',
        created_by=admin_user,
        modified_by=admin_user,
        status='published'
    )


@pytest.fixture
def cc_4_license():
    from mcod.licenses.models import License
    return License.objects.create(
        name='CC-BY-NC-4.0',
        title='Creative Commons Attribution-NonCommercial 4.0',
        url='https://creativecommons.org/licenses/by-nc/4.0/'
    )


@pytest.fixture
def buzzfeed_organization(admin_user):
    from mcod.organizations.models import Organization

    _name = 'buzzfeed-logo.jpg'
    copyfile(
        os.path.join(settings.TEST_DATA_PATH, _name),
        os.path.join(settings.IMAGES_MEDIA_ROOT, _name)
    )

    return Organization.objects.create(
        title='Buzzfeed',
        description='BuzzFeed has breaking news, vital journalism, quizzes, videos',
        image='buzzfeed-logo.jpg',
        email='buzzfeed@test-buzzfeed.com',
        institution_type='state',
        website='https://www.buzzfeed.com',
        slug='buzzfeed',
        created_by=admin_user,
        modified_by=admin_user
    )


@pytest.fixture
def buzzfeed_editor(buzzfeed_organization):
    from mcod.users.models import User
    usr = User.objects.create_user('buzzfeed@test-dane.gov.pl', 'Britenet.1')
    usr.fullname = 'Buzzfeed Editor'
    usr.state = 'active'
    usr.is_staff = True
    usr.is_superuser = False
    usr.save()
    usr.organizations.add(buzzfeed_organization)
    return usr


@pytest.fixture
def buzzfeed_dataset(journalism_category, cc_4_license, buzzfeed_organization, buzzfeed_editor, fakenews_tag,
                     top50_tag):
    from mcod.datasets.models import Dataset
    ds = Dataset.objects.create(
        title="Analizy, dane i statystki stworzone przez Buzzfeed.com",
        slug="analizy-buzzfeed",
        notes="Open - source data, analysis, libraries, tools, and guides from BuzzFeed's newsroom.",
        url="https://github.com/BuzzFeedNews/",
        views_count=242,
        license=cc_4_license,
        organization=buzzfeed_organization,
        update_frequency='yearly',
        category=journalism_category,
        created_by=buzzfeed_editor,
        modified_by=buzzfeed_editor,
    )
    ds.tags.add(fakenews_tag, top50_tag)

    return ds


@pytest.fixture
def buzzfeed_fakenews_resource(buzzfeed_dataset, buzzfeed_editor, mocker):
    from mcod.resources.models import Resource
    _name = 'buzzfeed-2018-fake-news-1000-lines.csv'
    copyfile(
        os.path.join(settings.TEST_DATA_PATH, _name),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, _name)
    )

    res = Resource(
        title='Analysis of fake news sites and viral posts',
        description='Over the past four years, BuzzFeed News has maintained lists of sites that '
                    'publish completely fabricated stories. As we encounter new ones and debunk '
                    'their content, we add them to the list.',
        file=_name,
        link=f'http://falconframework.org/media/resources/{_name}',
        format='csv',
        openness_score=3,
        views_count=10,
        downloads_count=20,
        dataset=buzzfeed_dataset,
        created_by=buzzfeed_editor,
        modified_by=buzzfeed_editor,
        data_date=datetime.today()
    )
    res.tracker.saved_data['link'] = res.link

    res.save()

    return res


@given('I have buzzfeed resource with tabular data')
def tabular_resource(buzzfeed_fakenews_resource):
    return buzzfeed_fakenews_resource


@when(parsers.parse('I use api version {version}'))
def set_api_version(container, version):
    container['request_data']['headers']['X-API-VERSION'] = version


@when(parsers.parse('my language is {lang}'))
def set_language(container, lang):
    container['request_data']['headers']['Accept-Language'] = lang


@when('I send request')
def sent_request(client14, container, spec_url='/spec/1.4'):
    version = container['request_data']['headers'].get('X-API-VERSION') or '1.4'
    resp = client14.simulate_get('/spec/{}'.format(version))
    assert HTTP_OK == resp.status
    spec = create_spec(resp.json)
    req = FalconOpenAPIWrapper(
        app, **container['request_data']
    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors
    container['response'] = req.request


@when(parsers.cfparse('I set request parameter {param} to {value}'))
def set_request_parameter(container, param, value):
    container['request_data']['query'][param] = value


@then('response format should be valid')
def valid_response(container, tabular_resource):
    resp = container['response']

    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)

    assert valid is True


@then(parsers.parse('items count should be equal to {items_count:d}'))
def valid_items_count(container, tabular_resource, items_count):
    resp = container['response']
    meta = resp.json['meta']
    assert meta['count'] == items_count


@then(parsers.parse('all list items should be of type {item_type}'))
def valid_items_type(container, item_type):
    resp = container['response']
    for data in resp.json['data']:
        assert data['type'] == item_type


def prepare_file(filename):
    copyfile(
        os.path.join(settings.TEST_DATA_PATH, filename),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, filename)
    )

    return os.path.join(settings.RESOURCES_MEDIA_ROOT, filename)


@pytest.fixture
def single_file_pack():
    return prepare_file('single_file.tar.gz')


@pytest.fixture
def multi_file_pack():
    return prepare_file('multi_file.rar')


@pytest.fixture
def spreedsheet_xlsx_pack():
    return prepare_file('sheet_img.xlsx')


@pytest.fixture
def document_docx_pack():
    return prepare_file('doc_img.docx')


@pytest.fixture
def table_resource_with_invalid_schema(valid_dataset):
    resource = Resource()
    resource.url = "http://smth.smwhere.com"
    resource.title = "File resource name"
    resource.type = "file"
    resource.format = 'XLSX'
    resource.file = File(open(prepare_file('wrong_schema_table.xlsx'), 'rb'))
    resource.file.open('rb')
    resource.dataset = valid_dataset
    resource.save()
    return resource


@pytest.fixture
def shapefile():
    return prepare_file('Mexico_and_US_Border.zip')
