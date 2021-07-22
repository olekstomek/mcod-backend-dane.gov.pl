import json
import time
import csv
import io
import os
import xml.etree.ElementTree as ET

import pytest
import xmlschema
from dateutil import parser
from django.apps import apps
from django.conf import settings
from pytest_bdd import given, when, then
from pytest_bdd import parsers

from mcod.categories.factories import CategoryFactory
from mcod.core.tests.fixtures.bdd.common import prepare_file, copyfile, create_object
from mcod.datasets.factories import DatasetFactory
from mcod.harvester.factories import DataSourceFactory
from mcod.resources.factories import ChartFactory, ResourceFactory
from mcod.tags.factories import TagFactory


@given(parsers.parse('dataset'))
def dataset():
    _dataset = DatasetFactory.create()
    TagFactory.create_batch(2, datasets=(_dataset,))
    return _dataset


#
# @given(parsers.parse('draft dataset'))
# def draft_dataset():
#     _dataset = DatasetFactory.create(status="draft", title='Draft dataset')
#     return _dataset


@given(parsers.parse('removed dataset'))
def removed_dataset():
    _dataset = DatasetFactory.create(is_removed=True, title='Removed dataset')
    return _dataset


# @given(parsers.parse('dataset with id {dataset_id:d}'))
# def dataset_with_id(dataset_id):
#     _dataset = DatasetFactory.create(id=dataset_id, title='dataset %s' % dataset_id)
#     return _dataset


@given(parsers.parse('second dataset with id {dataset_id:d}'))
def second_dataset_with_id(dataset_id):
    _dataset = DatasetFactory.create(id=dataset_id, title='Second dataset %s' % dataset_id)
    return _dataset


@given(parsers.parse('another dataset with id {dataset_id:d}'))
def another_dataset_with_id(dataset_id):
    _dataset = DatasetFactory.create(id=dataset_id, title='Another dataset %s' % dataset_id)
    return _dataset


#
# @given(parsers.parse('draft dataset with id {dataset_id:d}'))
# def draft_dataset_with_id(dataset_id):
#     _dataset = DatasetFactory.create(id=dataset_id, title='Draft dataset {}'.format(dataset_id),
#                                      status='draft')
#     return _dataset


@given(parsers.parse('dataset with resources'))
def dataset_with_resources():
    _dataset = DatasetFactory.create()
    ResourceFactory.create_batch(2, dataset=_dataset)
    return _dataset


@given(parsers.parse('dataset with id {dataset_id:d} and institution {organization_id:d}'))
def dataset_with_organization(dataset_id, organization_id):
    organization = create_object('institution', organization_id)
    return create_object('dataset', dataset_id, organization=organization)


@given(parsers.parse('dataset with chart as visualization type'))
def dataset_with_chart_as_visualization_type():
    _dataset = DatasetFactory.create()
    _resource = ResourceFactory(
        dataset=_dataset,
        link='https://github.com/frictionlessdata/goodtables-py/blob/master/data/valid.csv',
    )
    ChartFactory.create(resource=_resource, is_default=True)
    _dataset.save()
    return _dataset


@given(parsers.parse('dataset with map as visualization type'))
def dataset_with_map_as_visualization_type(geo_tabular_data_resource):
    return geo_tabular_data_resource.dataset


@given(parsers.parse('dataset for data {dataset_data} imported from {source_type} named {name} with url {portal_url}'))
def imported_dataset(dataset_data, source_type, name, portal_url):
    dataset_data = json.loads(dataset_data)
    _source = DataSourceFactory.create(source_type=source_type, name=name, portal_url=portal_url)
    _dataset = DatasetFactory.create(source=_source, **dataset_data)
    ResourceFactory.create(dataset=_dataset)
    return _dataset


@given(parsers.parse('resource with id {resource_id} imported from {source_type} named {name} with url {portal_url}'))
def imported_resource(resource_id, source_type, name, portal_url):
    _source = DataSourceFactory.create(source_type=source_type, name=name, portal_url=portal_url)
    _dataset = DatasetFactory.create(source=_source)
    _resource = ResourceFactory.create(id=resource_id, dataset=_dataset)
    return _resource


@given(parsers.parse('resource with id {resource_id} imported from {source_type} named {name} with url {portal_url}'
                     ' and type {res_type}'))
def imported_resource_of_type(resource_id, source_type, name, portal_url, res_type):
    _source = DataSourceFactory.create(source_type=source_type, name=name, portal_url=portal_url)
    _dataset = DatasetFactory.create(source=_source)
    _resource = ResourceFactory.create(id=resource_id, dataset=_dataset, type=res_type)
    return _resource


@given(parsers.parse('dataset with resource'))
def dataset_with_resource():
    _dataset = DatasetFactory.create()
    ResourceFactory.create(dataset=_dataset)
    CategoryFactory.create_batch(2, datasets=(_dataset,))
    return _dataset


@given(parsers.parse('dataset with id {dataset_id:d}'))
def dataset_with_id(dataset_id):
    _dataset = DatasetFactory.create(
        id=dataset_id,
        title=f'test dataset with id {dataset_id}',
    )
    return _dataset


@given(parsers.parse('dataset with id {dataset_id:d} and {num:d} resources'))
def dataset_with_id_and_datasets(dataset_id, num):
    _dataset = DatasetFactory.create(id=dataset_id, title='dataset {} with resources'.format(dataset_id))
    ResourceFactory.create_batch(num, dataset=_dataset)
    return _dataset


@given(parsers.parse('dataset with title {title} and {num:d} resources'))
def dataset_with_title_and_x_resources(title, num):
    _dataset = DatasetFactory.create(title=title)
    ResourceFactory.create_batch(num, dataset=_dataset)
    return _dataset


@given(parsers.parse('{number_of_datasets:d} datasets with {num:d} resources'))
def number_of_datasets_with_resources(number_of_datasets, num):
    for x in range(number_of_datasets):
        _dataset = DatasetFactory.create()
        ResourceFactory.create_batch(num, dataset=_dataset)


@given(parsers.parse('{number_of_datasets:d} datasets with {num:d} resources with {res_type} type'))
def number_of_datasets_with_resources_with_type(number_of_datasets, num, res_type):
    for x in range(number_of_datasets):
        _dataset = DatasetFactory.create()
        ResourceFactory.create_batch(num, dataset=_dataset, type=res_type)


@given(parsers.parse('Datasets with resources of type {datasets_data}'))
def datasets_with_resources_of_type(datasets_data):
    data = json.loads(datasets_data)
    for item in data:
        _dataset = DatasetFactory.create()
        for res_type, res_count in item.items():
            ResourceFactory.create_batch(res_count, dataset=_dataset, type=res_type)
    time.sleep(1)  # time to index data before request is made.


@given(parsers.parse('3 datasets'))
def datasets():
    return DatasetFactory.create_batch(3)


@given(parsers.parse('{num:d} datasets'))
def x_datasets(num):
    return DatasetFactory.create_batch(num)


@when(parsers.parse('remove dataset with id {dataset_id}'))
@then(parsers.parse('remove dataset with id {dataset_id}'))
def remove_dataset(dataset_id):
    model = apps.get_model('datasets', 'dataset')
    inst = model.objects.get(pk=dataset_id)
    inst.is_removed = True
    inst.save()


@when(parsers.parse('restore dataset with id {dataset_id}'))
@then(parsers.parse('restore dataset with id {dataset_id}'))
def restore_dataset(dataset_id):
    model = apps.get_model('datasets', 'dataset')
    inst = model.raw.get(pk=dataset_id)
    inst.is_removed = False
    inst.save()


@when(parsers.parse('change status to {status} for dataset with id {dataset_id}'))
@then(parsers.parse('change status to {status} for dataset with id {dataset_id}'))
def change_dataset_status(status, dataset_id):
    model = apps.get_model('datasets', 'dataset')
    inst = model.objects.get(pk=dataset_id)
    inst.status = status
    inst.save()


@then(parsers.parse('api\'s response datasets contain valid links to related resources'))
def api_response_datasets_contain_valid_links_to_related_resources(context):
    dataset_model = apps.get_model('datasets.Dataset')
    for x in context.response.json['data']:
        obj = dataset_model.objects.get(id=x['id'])
        assert obj.ident in x['relationships']['resources']['links']['related']


@then(parsers.parse("api's response data is None"))
def api_response_data_is_none(context):
    data = context.response.json['data']
    assert data is None


@given(parsers.parse('three datasets with created dates in {dates}'))
def three_datasets_with_different_created_at(dates):
    dates_ = dates.split("|")
    datasets = []
    for d in dates_:
        d = parser.parse(d)
        ds = DatasetFactory.create(created=d)
        datasets.append(ds)
    return datasets


@pytest.fixture
def buzzfeed_editor(buzzfeed_organization):
    from mcod.users.models import User
    usr = User.objects.create_user('buzzfeed@test-dane.gov.pl', '12345.Abcde')
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
def onlyheaders_csv_file():
    return prepare_file('onlyheaders.csv')


@pytest.fixture
def csv2jsonld_csv_file():
    return prepare_file('csv2jsonld.csv')


@pytest.fixture
def csv2jsonld_jsonld_file():
    return prepare_file('csv2jsonld.jsonld')


@pytest.fixture
def example_xls_file():
    return prepare_file('example_xls_file.xls')


@pytest.fixture
def simple_csv_file():
    return prepare_file('simple.csv')


@pytest.fixture
def single_file_pack():
    return prepare_file('single_file.tar.gz')


@pytest.fixture
def single_csv_zip():
    return prepare_file('single_csv.zip')


@pytest.fixture
def multi_file_pack():
    return prepare_file('multi_file.rar')


@pytest.fixture
def multi_file_zip_pack():
    return prepare_file('multi_pdf_xlsx.zip')


@pytest.fixture
def spreedsheet_xlsx_pack():
    return prepare_file('sheet_img.xlsx')


@pytest.fixture
def document_docx_pack():
    return prepare_file('doc_img.docx')


# @pytest.fixture
# def shapefile_arch():
#     return prepare_file('Mexico_and_US_Border.zip')
#
#


@pytest.fixture
def example_ods_file():
    return prepare_file('example_ods_file.ods')


@given(parsers.parse('I have {file_type}'))
def validated_file(document_docx_pack, example_ods_file,
                   spreedsheet_xlsx_pack, multi_file_pack, single_csv_zip,
                   multi_file_zip_pack, file_type):
    if file_type == 'docx file':
        return document_docx_pack
    elif file_type == 'ods file':
        return example_ods_file
    elif file_type == 'xlsx file':
        return spreedsheet_xlsx_pack
    elif file_type == 'rar with many files':
        return multi_file_pack
    elif file_type == 'zip with one csv file':
        return single_csv_zip
    elif file_type == 'zip with many files':
        return multi_file_zip_pack


@given(parsers.parse('dataset with id {dataset_id}, slug {slug} and resources'))
def dataset_with_id_and_resources(dataset_id, slug):
    _dataset = DatasetFactory.create(id=dataset_id, slug=slug)
    ResourceFactory.create_batch(2, dataset=_dataset)
    return _dataset


@then(parsers.parse('api response is csv file with {record_count} records'), converters=dict(record_count=int))
def api_response_is_csv_file_with_records(context, record_count):
    csv_reader = csv.reader(io.StringIO(context.response.content.decode('utf-8')), delimiter=';')
    csv_record_count = -1
    for row in csv_reader:
        csv_record_count += 1
    assert record_count == csv_record_count


@then(parsers.parse('api response is xml file with {datasets_count} datasets and {resources_count} resources'), converters={
    'datasets_count': int,
    'resources_count': int,
})
def api_response_is_xml_file_with_datasets_and_resources(context, datasets_count, resources_count):
    root = ET.fromstring(context.response.content.decode('utf-8'))
    assert root.tag == 'catalog'
    assert len(root.findall('dataset')) == datasets_count
    assert len(root.findall('dataset/resources/resource')) == resources_count


@then("api's response body conforms to <lang_code> xsd schema")
def api_response_body_conforms_to_xsd_schema(context, lang_code):
    content = context.response.content.decode('utf-8')
    xsd_path = f'{settings.SCHEMAS_DIR}/{lang_code}/katalog.xsd'
    xml_schema = xmlschema.XMLSchema(xsd_path)
    xml_schema.validate(content)


@given(parsers.parse('created catalog csv file'))
def create_catalog_csv_file():
    src = str(os.path.join(settings.TEST_SAMPLES_PATH, 'datasets', 'pl', 'katalog.csv'))
    dest = str(os.path.join(settings.METADATA_MEDIA_ROOT, 'pl', 'katalog.csv'))
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    copyfile(src, dest)


@given(parsers.parse('created catalog xml file'))
def create_catalog_xml_file():
    for lang_code in ('pl', 'en'):
        src = str(os.path.join(settings.TEST_SAMPLES_PATH, 'datasets', lang_code, 'katalog.xml'))
        dest = str(os.path.join(settings.METADATA_MEDIA_ROOT, lang_code, 'katalog.xml'))
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        copyfile(src, dest)
