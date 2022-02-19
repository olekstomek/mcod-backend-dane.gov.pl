import json
import os
import uuid
from io import BytesIO

import factory
import pytest
import requests
import requests_mock
from dateutil import parser
from django.apps import apps
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import datetime
from pytest_bdd import given, when, then
from pytest_bdd import parsers

from mcod import settings
from mcod.core.tests.fixtures.bdd.common import copyfile, prepare_file
from mcod.counters.factories import ResourceViewCounterFactory, ResourceDownloadCounterFactory
from mcod.counters.lib import Counter
from mcod.counters.tasks import save_counters
from mcod.datasets.factories import DatasetFactory
from mcod.harvester.factories import DataSourceFactory
from mcod.resources.archives import ArchiveReader, UnsupportedArchiveError
from mcod.resources.factories import ChartFactory, ResourceFactory, TaskResultFactory, ResourceFileFactory
from mcod.resources.file_validation import analyze_file, check_support
from mcod.unleash import is_enabled


@pytest.fixture
def httpsserver_custom(request):
    """Custom version of pytest_localserver's httpsserver.
    See: https://github.com/diazona/pytest-localserver/issues/2#issuecomment-919358939
    Stronger cert was generated with command:
        $ openssl req -new -x509 -sha256 -keyout server.pem -out server.pem -nodes
    """
    from pytest_localserver import https
    certificate = os.path.join(settings.TEST_CERTS_PATH, 'server.pem')
    server = https.SecureContentServer(cert=certificate, key=certificate)
    server.start()
    request.addfinalizer(server.stop)
    return server


def create_res(ds, editor, **kwargs):
    from mcod.resources.models import Resource, ResourceFile
    _fname = kwargs.pop('filename')
    _kwargs = {
        'title': 'Analysis of fake news sites and viral posts',
        'description': 'Over the past four years, BuzzFeed News has maintained lists of sites that '
                       'publish completely fabricated stories. As we encounter new ones and debunk '
                       'their content, we add them to the list.',
        'file': _fname,
        'link': f'https://falconframework.org/media/resources/{_fname}',
        'format': 'csv',
        'openness_score': 3,
        'views_count': 10,
        'downloads_count': 20,
        'dataset': ds,
        'created_by': editor,
        'modified_by': editor,
        'data_date': datetime.today(),
    }
    if is_enabled('S41_resource_has_high_value_data'):
        _kwargs['has_high_value_data'] = False
    _kwargs.update(**kwargs)

    if is_enabled('S40_new_file_model.be'):
        with open(os.path.join(settings.RESOURCES_MEDIA_ROOT, _fname), 'rb') as f:
            from mcod.resources.link_validation import session
            adapter = requests_mock.Adapter()
            adapter.register_uri('GET', _kwargs['link'], content=f.read(), headers={'Content-Type': 'application/csv'})
            session.mount('https://falconframework.org', adapter)
        _kwargs.pop('file')
        res = Resource.objects.create(**_kwargs)
        ResourceFile.objects.create(
            is_main=True,
            resource=res,
            file=os.path.join(settings.RESOURCES_MEDIA_ROOT, _fname),
            format='csv'
        )
    else:
        res = Resource(**_kwargs)
        res.tracker.saved_data['link'] = res.link
        res.save()
    res = Resource.objects.get(pk=res.pk)
    return res


@pytest.fixture
def buzzfeed_fakenews_resource(buzzfeed_dataset, buzzfeed_editor, mocker):
    _name = 'buzzfeed-2018-fake-news-1000-lines.csv'
    copyfile(
        os.path.join(settings.TEST_SAMPLES_PATH, _name),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, _name)
    )
    return create_res(buzzfeed_dataset, buzzfeed_editor, filename=_name)


@pytest.fixture
def resource_with_date_and_datetime(buzzfeed_dataset, buzzfeed_editor, mocker):
    _name = 'date_and_datetime.csv'
    copyfile(
        os.path.join(settings.TEST_SAMPLES_PATH, _name),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, _name)
    )

    return create_res(buzzfeed_dataset, buzzfeed_editor, filename=_name)


@pytest.fixture
def geo_tabular_data_resource(buzzfeed_dataset, buzzfeed_editor, mocker):
    _name = 'geo.csv'
    copyfile(
        os.path.join(settings.TEST_SAMPLES_PATH, _name),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, _name)
    )
    res_attrs = {
        'filename': _name,
        'title': 'Geo tab test',
        'description': 'more than 20 characters'
    }
    return create_res(buzzfeed_dataset, buzzfeed_editor, **res_attrs)


@pytest.fixture
def remote_file_resource(buzzfeed_dataset, buzzfeed_editor, mocker, httpserver):
    from mcod.resources.models import Resource

    simple_csv_path = os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv')
    httpserver.serve_content(
        content=open(simple_csv_path).read(),
        headers={
            'content-type': 'application/csv'
        },
    )

    res = Resource(
        title='Remote file resource',
        description='Remote file resource',
        link=httpserver.url,
        format='csv',
        openness_score=3,
        views_count=10,
        downloads_count=20,
        dataset=buzzfeed_dataset,
        created_by=buzzfeed_editor,
        modified_by=buzzfeed_editor,
        data_date=datetime.today()
    )
    res.save()
    return res


@pytest.fixture
def other_remote_file_resource(buzzfeed_dataset, buzzfeed_editor, mocker, httpserver):
    from mcod.resources.models import Resource

    simple_csv_path = os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv')
    httpserver.serve_content(
        content=open(simple_csv_path).read(),
        headers={
            'content-type': 'application/csv'
        },
    )

    res = Resource(
        title='Other remote file resource',
        description='Other remote file resource',
        link=httpserver.url,
        format='csv',
        openness_score=3,
        views_count=10,
        downloads_count=20,
        dataset=buzzfeed_dataset,
        created_by=buzzfeed_editor,
        modified_by=buzzfeed_editor,
        data_date=datetime.today()
    )
    res.save()
    return res


@pytest.fixture
def remote_file_resource_of_api_type(buzzfeed_dataset, buzzfeed_editor, httpserver):
    from mcod.resources.models import Resource
    httpserver.serve_content(
        content=get_json_file().read(),
        headers={
            'content-type': 'application/json'
        },
    )
    res = Resource(
        title='Remote file resource',
        description='Remote file resource',
        link=httpserver.url,
        format='json',
        openness_score=3,
        views_count=10,
        downloads_count=20,
        dataset=buzzfeed_dataset,
        created_by=buzzfeed_editor,
        modified_by=buzzfeed_editor,
        data_date=datetime.today(),
        type='api',
    )
    res.save()
    return res


@pytest.fixture
def remote_file_resource_with_forced_file_type(remote_file_resource):
    remote_file_resource.type = 'file'
    remote_file_resource.forced_file_type = True
    remote_file_resource.save()
    return remote_file_resource


@pytest.fixture
def local_file_resource(buzzfeed_dataset, buzzfeed_editor, mocker):
    _name = 'geo.csv'
    copyfile(
        os.path.join(settings.TEST_SAMPLES_PATH, _name),
        os.path.join(settings.RESOURCES_MEDIA_ROOT, _name)
    )
    res_attrs = {
        'filename': _name,
        'title': 'Local file resource',
        'description': 'Local file resource'
    }
    res = create_res(buzzfeed_dataset, buzzfeed_editor, **res_attrs)
    ChartFactory.create(resource=res, is_default=True)
    return res


@pytest.fixture
def resource_with_xls_file(example_xls_file):
    from mcod.resources.models import Resource
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory.create(
            type='file',
            format='xls',
            link=None,
            main_file__file=example_xls_file,
        )
        res = Resource.objects.get(pk=res.pk)
    else:
        res = ResourceFactory.create(
            type='file',
            format='xls',
            link=None,
            file=example_xls_file,
        )
        res.revalidate()
    res.increase_openness_score()
    return res


@pytest.fixture
def onlyheaderscsv_resource(onlyheaders_csv_file):
    from mcod.resources.models import Resource
    if is_enabled('S40_new_file_model.be'):
        resource = ResourceFactory.create(
            type='file',
            format='csv',
            link=None,
            main_file__file=onlyheaders_csv_file,
        )
        resource = Resource.objects.get(pk=resource.pk)
    else:
        resource = ResourceFactory.create(
            type='file',
            format='csv',
            link=None,
            file=onlyheaders_csv_file,
        )
    return resource


@pytest.fixture
def resource_with_success_tasks_statuses(remote_file_resource):
    tasks = TaskResultFactory.create_batch(size=3, status='SUCCESS')
    remote_file_resource.link_tasks.add(tasks[0])
    remote_file_resource.file_tasks.add(tasks[1])
    remote_file_resource.data_tasks.add(tasks[2])
    remote_file_resource.link_tasks_last_status = tasks[0].status
    remote_file_resource.save()
    return remote_file_resource


@pytest.fixture
def resource_with_failure_tasks_statuses(other_remote_file_resource):
    tasks = TaskResultFactory.create_batch(size=3, status='FAILURE')
    other_remote_file_resource.link_tasks.add(tasks[0])
    other_remote_file_resource.file_tasks.add(tasks[1])
    other_remote_file_resource.data_tasks.add(tasks[2])
    other_remote_file_resource.link_tasks_last_status = tasks[0].status
    other_remote_file_resource.save()
    return other_remote_file_resource


@given(parsers.parse('resource'))
def resource():
    res = ResourceFactory.create()
    return res


@given(parsers.parse('resource'))
def resource_with_file(file_csv):
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory.create(
            type="file",
            format='csv',
            main_file__file=factory.django.FileField(
                from_path=os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv'), filename='simple.csv'
            )
        )
    else:
        res = ResourceFactory.build(
            type="file",
            format='csv',
            file=File(file_csv)
        )
    return res


@pytest.fixture
def resource_with_counters():
    res = ResourceFactory.create()
    ResourceViewCounterFactory.create_batch(size=2, resource=res)
    ResourceDownloadCounterFactory.create_batch(size=2, resource=res)
    return res


@pytest.fixture
def imported_ckan_resource():
    _source = DataSourceFactory.create(source_type='CKAN', name='Test name', portal_url='http://example.com')
    _dataset = DatasetFactory.create(source=_source)
    _resource = ResourceFactory.create(dataset=_dataset)
    return _resource


def get_html_file():
    return BytesIO(
        b'''
        <html>
        </html>
        '''
    )


def get_json_file():
    return BytesIO(
        b'''
        {}
        '''
    )


@given(parsers.parse('resource of type website'))
def resource_of_type_website():
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory.create(
            type="website",
            format=None,
            main_file__file=factory.django.FileField(
                from_func=get_html_file, filename='{}.html'.format(str(uuid.uuid4()))
            ),
            main_file__content_type="text/html",
        )
    else:
        res = ResourceFactory.create(
            type="website",
            format=None,
            file=factory.django.FileField(from_func=get_html_file, filename='{}.html'.format(str(uuid.uuid4()))),
            content_type="text/html",
        )
    return res


@given(parsers.parse('resource of type api'))
def resource_of_type_api():
    from mcod.resources.models import Resource
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory(
            type="api",
            format=None,
            main_file__file=factory.django.FileField(from_func=get_json_file, filename='{}.json'.format(str(uuid.uuid4()))),
            main_file__content_type="application/json",
        )
        res = Resource.objects.get(pk=res.pk)
    else:
        res = ResourceFactory.create(
            type="api",
            format=None,
            file=factory.django.FileField(from_func=get_json_file, filename='{}.json'.format(str(uuid.uuid4()))),
            content_type="application/json",

        )
    return res


@given(parsers.parse('resource with buzzfeed file'))
def resource_with_buzzfeed_file(buzzfeed_fakenews_resource):
    return buzzfeed_fakenews_resource


@given(parsers.parse('resource created at {created}'))
def resources_created_at(created):
    date = parser.parse(created)
    res = ResourceFactory.create(created=date)
    return res


@given(parsers.parse('three resources with created dates in {dates}'))
def three_resources_with_different_created_at(dates):
    dates_ = dates.split("|")
    resources = []
    for d in dates_:
        date = parser.parse(d)
        res = ResourceFactory.create(created=date)
        resources.append(res)
    return resources


@given(parsers.parse('default charts for resource with id {resource_id:d} with ids {charts_ids_str}'))
def default_charts_for_resource_id(context, resource_id, charts_ids_str):
    resource = ResourceFactory.create(id=resource_id)
    for chart_id in charts_ids_str.split(','):
        ChartFactory.create(id=chart_id, resource=resource, created_by=context.user, is_default=True, chart={})


@given(parsers.parse('private chart for resource with id {resource_id:d} with id {chart_id}'))
def private_chart_for_resource_id_with_id(context, resource_id, chart_id):
    resource = ResourceFactory.create(id=resource_id)
    ChartFactory.create(id=chart_id, resource=resource, created_by=context.user, is_default=False, chart={})


@given(parsers.parse('two charts for resource with {data_str}'))
def two_charts_for_resource_id(context, data_str):
    data = json.loads(data_str)
    resource = ResourceFactory.create(**data)
    ChartFactory.create(resource=resource, created_by=context.user, is_default=True)
    ChartFactory.create(resource=resource, created_by=context.user, is_default=False)


@given(parsers.parse('resource with date and datetime'))
def _resource_with_date_and_datetime(csv_with_date_and_datetime):
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory.create(
            type='file',
            format='csv',
            main_file__file=File(csv_with_date_and_datetime)
        )
    else:
        res = ResourceFactory.build(
            type='file',
            format='csv',
            file=File(csv_with_date_and_datetime)
        )
    return res


@given(parsers.parse('resource with id {res_id} and xls file converted to csv'))
def resource_with_xls_file_converted_to_csv(res_id, example_xls_file, buzzfeed_dataset, buzzfeed_editor):
    if is_enabled('S40_new_file_model.be'):
        from mcod.resources.models import Resource
        params = {
            'id': res_id,
            'type': 'file',
            'format': 'xls',
            'link': None,
            'filename': 'example_xls_file.xls',
            'openness_score': 1
        }
        res = create_res(buzzfeed_dataset, buzzfeed_editor, **params)
        resource_score, files_score = res.get_openness_score()
        Resource.objects.filter(pk=res.pk).update(openness_score=resource_score)
        res.revalidate()
    else:
        res = ResourceFactory.create(
            id=res_id,
            type='file',
            format='xls',
            link=None,
            file=example_xls_file,
        )
        res.revalidate()
        res.increase_openness_score()
    return res


@given(parsers.parse('resource with csv file converted to jsonld with params {params_str}'))
def resource_with_csv_file_converted_to_jsonld(csv2jsonld_csv_file, csv2jsonld_jsonld_file, params_str):
    from mcod.resources.models import Resource
    params = json.loads(params_str)
    obj_id = params.pop('id')
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory(
            main_file__file=csv2jsonld_csv_file,
            id=obj_id,
            type='file',
            format='csv',
            link=None,
            **params,)
        ResourceFileFactory.create(
            file=csv2jsonld_jsonld_file,
            format='jsonld',
            resource=res,
            is_main=False
        )
        resource_score, files_score = res.get_openness_score()
        Resource.objects.filter(pk=res.pk).update(openness_score=resource_score)
        res = Resource.objects.get(pk=res.pk)
        res.revalidate()
    else:
        res = ResourceFactory.create(
            id=obj_id,
            type='file',
            format='csv',
            link=None,
            file=csv2jsonld_csv_file,
            jsonld_file=csv2jsonld_jsonld_file,
            **params,
        )
        res.openness_score = res.get_openness_score()
        res.save()
    return res


@given(parsers.parse('resource with id {res_id} and simple csv file'))
def resource_with_simple_csv(res_id, simple_csv_file):
    if is_enabled('S40_new_file_model.be'):
        res = ResourceFactory(
            id=res_id,
            type='file',
            format='csv',
            link=None,
            main_file__file=simple_csv_file,
        )
        res.data_tasks_last_status = res.data_tasks.all().last().status
        res.file_tasks_last_status = res.file_tasks.all().last().status
        res.save()

    else:
        res = ResourceFactory.create(
            id=res_id,
            type='file',
            format='csv',
            link=None,
            file=simple_csv_file,
        )
        res.tracker.saved_data['file'] = None
        res.save()
    return res


@given(parsers.parse('draft resource'))
def draft_resource():
    res = ResourceFactory.create(status="draft", title='Draft resource')
    return res


@given(parsers.parse('removed resource'))
def removed_resource():
    res = ResourceFactory.create(is_removed=True, title='Removed resource')
    return res


#
# @given(parsers.parse('resource with id {resource_id:d}'))
# def resource_with_id(resource_id):
#     res = ResourceFactory.create(id=resource_id, title='resource %s' % resource_id)
#     return res


@given(parsers.parse('second resource with id {resource_id:d}'))
def second_resource_with_id(resource_id):
    res = ResourceFactory.create(id=resource_id, title='Second resource %s' % resource_id)
    return res


@given(parsers.parse('another resource with id {resource_id:d}'))
def another_resource_with_id(resource_id):
    res = ResourceFactory.create(id=resource_id, title='Another resource %s' % resource_id)
    return res


@given(parsers.parse('draft resource with id {resource_id:d}'))
def draft_resource_with_id(resource_id):
    res = ResourceFactory.create(id=resource_id, title='Draft resource {}'.format(resource_id),
                                 status='draft')
    return res


@given(parsers.parse('removed resource with id {resource_id:d}'))
def removed_resource_with_id(resource_id):
    res = ResourceFactory.create(id=resource_id, title='Removed resource {}'.format(resource_id),
                                 is_removed=True)
    return res


@given(parsers.parse('3 resources'))
def resources():
    return ResourceFactory.create_batch(3)


@given(parsers.parse("{num:d} resources with type {res_type}"))
def resource_with_type(num, res_type):
    return ResourceFactory.create_batch(num, type=res_type)


@given(parsers.parse('{num:d} resources'))
def x_resources(num):
    return ResourceFactory.create_batch(num)


@when(parsers.parse('remove resource with id {resource_id}'))
@then(parsers.parse('remove resource with id {resource_id}'))
def remove_resource(resource_id):
    model = apps.get_model('resources', 'resource')
    inst = model.objects.get(pk=resource_id)
    inst.is_removed = True
    inst.save()


@then(parsers.parse('resource with id {resource_id:d} {counter_type} is {val:d}'))
def resource_views_count_is(resource_id, counter_type, val):
    model = apps.get_model('resources', 'resource')
    obj = model.objects.get(pk=resource_id)
    if is_enabled('S16_new_date_counters.be'):
        current_count = getattr(obj, f'computed_{counter_type}')
    else:
        current_count = getattr(obj, counter_type)
    assert current_count == val


@given(parsers.parse('resource with id {resource_id:d} and {counter_type} is {val:d}'))
def given_resource_views_count_is(resource_id, counter_type, val):
    kwargs = {
        'id': resource_id,
        counter_type: val,
        'type': 'file'
    }
    return ResourceFactory.create(**kwargs)


@given(parsers.parse('unpublished resource with id {resource_id:d} and {counter_type} is {val:d}'))
def given_unpublished_resource_views_count_is(resource_id, counter_type, val):
    kwargs = {
        'id': resource_id,
        counter_type: val,
        'status': 'draft',
        'type': 'file'
    }
    return ResourceFactory.create(**kwargs)


@then(parsers.parse('resource csv file has {columns} as headers'))
def resource_csv_file_has_headers(resource_with_xls_file_converted_to_csv, columns):
    res = resource_with_xls_file_converted_to_csv
    with open(res.csv_converted_file.path, 'r') as outfile:
        first_line = outfile.readline().rstrip('\n')
        assert columns == first_line
#
# @when(parsers.parse('restore resource with id {resource_id}'))
# @then(parsers.parse('restore resource with id {resource_id}'))
# def restore_resource(resource_id):
#     model = apps.get_model('resources', 'resource')
#     inst = model.raw.get(pk=resource_id)
#     inst.is_removed = False
#     inst.save()
#
#
# @when(parsers.parse('change status to {status} for resource with id {resource_id}'))
# @then(parsers.parse('change status to {status} for resource with id {resource_id}'))
# def change_resource_status(status, resource_id):
#     model = apps.get_model('resources', 'resource')
#     inst = model.objects.get(pk=resource_id)
#     inst.status = status
#     inst.save()


def get_mock_response(mock_request, content_filename, headers):
    with open(content_filename, 'rb') as f:
        mock_request.get('http://mocker-test.com', headers=headers, content=f.read())
    return requests.get('http://mocker-test.com')


@pytest.fixture
@requests_mock.Mocker(kw='mock_request')
def xml_resource_api_response(file_xml, **kwargs):
    headers = {
        'Content-Type': 'text/xml'
    }
    return get_mock_response(kwargs['mock_request'], file_xml.name, headers)


@pytest.fixture
@requests_mock.Mocker(kw='mock_request')
def xml_resource_file_response(file_xml, **kwargs):
    headers = {
        'Content-Disposition': 'attachment; filename="example.xml"',
        'Content-Type': 'text/xml'
    }
    return get_mock_response(kwargs['mock_request'], file_xml.name, headers)


@pytest.fixture
@requests_mock.Mocker(kw='mock_request')
def html_resource_response(file_html, **kwargs):
    headers = {
        'Content-Type': 'text/html'
    }
    return get_mock_response(kwargs['mock_request'], file_html.name, headers)


@pytest.fixture
@requests_mock.Mocker(kw='mock_request')
def json_resource_response(file_json, **kwargs):
    headers = {
        'Content-Type': 'application/json'
    }
    return get_mock_response(kwargs['mock_request'], file_json.name, headers)


@pytest.fixture
@requests_mock.Mocker(kw='mock_request')
def jsonstat_resource_response(file_jsonstat, **kwargs):
    headers = {
        'Content-Type': 'application/json'
    }
    return get_mock_response(kwargs['mock_request'], file_jsonstat.name, headers)


@pytest.fixture
def shapefile_world():
    return [prepare_file('TM_WORLD_BORDERS-0.3.%s' % ext) for ext in ('shp', 'shx', 'prj', 'dbf')]


@pytest.fixture
def shapefile_trees():
    return [prepare_file('iglaste.tar.xz'), prepare_file('iglaste_other.tar.xz')]


@given(parsers.parse('resource with {filename} file and id {obj_id}'))
@given('resource with <filename> file and id <obj_id>')
def resource_with_id_and_filename(filename, dataset, obj_id):
    from mcod.resources.models import Resource
    full_filename = prepare_file(filename)
    with open(full_filename, 'rb') as outfile:
        if is_enabled('S40_new_file_model.be'):
            res = Resource.objects.create(
                id=obj_id,
                title='Local file resource',
                description='Resource with file',
                dataset=dataset,
                data_date=datetime.today(),
                status='published'
            )
            ResourceFileFactory.create(
                resource_id=res.pk,
                file=File(outfile),
            )
        else:
            Resource.objects.create(
                id=obj_id,
                title='Local file resource',
                description='Resource with file',
                file=File(outfile),
                dataset=dataset,
                data_date=datetime.today(),
                status='published'
            )


@given(parsers.parse('draft remote file resource of api type with id {obj_id}'))
@given('draft remote file resource of api type with id <obj_id>')
def draft_remote_file_resource(obj_id, httpsserver_custom):
    httpsserver_custom.serve_content(
        content=get_json_file().read(),
        headers={
            'content-type': 'application/json'
        },
    )
    kwargs = {
        'id': obj_id,
        'link': httpsserver_custom.url,
        'status': 'draft'
    }
    if is_enabled('S40_new_file_model.be'):
        kwargs['main_file'] = None
    else:
        kwargs['file'] = None
    res = ResourceFactory.create(**kwargs)
    return res


@then(parsers.parse('resource with id {obj_id} attributes are equal {expected_attr_vals}'))
@then('resource with id <obj_id> attributes are equal <expected_attr_vals>')
def resource_with_id_attr_is_equal(obj_id, expected_attr_vals):
    expected_vals = json.loads(expected_attr_vals)
    model = apps.get_model('resources', 'resource')
    obj = model.objects.get(pk=obj_id)
    actual_vals = {expected_attr: getattr(obj, expected_attr) for expected_attr in expected_vals.keys()}
    assert actual_vals == expected_vals, 'Expected values: {}, Actual values: {}'.format(expected_vals, actual_vals)


@then(parsers.parse('resource field {r_field} is {r_value}'))
def resource_field_value_is(context, r_field, r_value):
    model = apps.get_model('resources', 'resource')
    resource = model.objects.latest('id')
    assert getattr(resource, r_field) == r_value


@then(parsers.parse('file is validated and result is {file_format}'))
@then('file is validated and result is <file_format>')
def file_format(validated_file, file_format):
    ext, file_info, encoding, path, file_mimetype, exc = analyze_file(validated_file)
    assert ext == file_format, f'Analyzed {validated_file} file format is not: "{file_format}", but: "{ext}"'


@then(parsers.parse('archive file is successfully unpacked and has {files_number} files'))
@then('archive file is successfully unpacked and has <files_number> files')
def file_archive(validated_file, files_number):
    with ArchiveReader(validated_file) as extracted:
        assert os.path.exists(extracted.tmp_dir)
        assert extracted
        assert len(extracted) == int(files_number)
        for path in extracted:
            assert os.path.isfile(path)
    assert not os.path.exists(extracted.tmp_dir)


@then(parsers.parse('file is validated and result mimetype is {mimetype}'))
@then('file is validated and result mimetype is <mimetype>')
def file_mimetype(validated_file, mimetype):
    extension, file_info, encoding, path, file_mimetype, exc = analyze_file(validated_file)
    assert file_mimetype == mimetype


@then(parsers.parse('file is validated and UnsupportedArchiveError is raised'))
def file_validation_exception(validated_file):
    with pytest.raises(UnsupportedArchiveError) as e:
        extension, file_info, file_encoding, path, file_mimetype, exc = analyze_file(validated_file)
        check_support(extension, file_mimetype)
        assert str(e.value) == 'archives-are-not-supported'


@given(parsers.parse('resource with id {res_id} is viewed and counter incrementing task is executed'))
def resourced_is_visited_and_counter_incremented(res_id):
    import time
    counter = Counter()
    counter.incr_view_count('resources', res_id)
    counter.save_counters()
    time.sleep(1)  # time for indexing in ES


@given(parsers.parse('resource with id {res_id} dataset id {dataset_id} and single main region'))
def resource_with_region(res_id, dataset_id, main_region, additional_regions):
    resource = ResourceFactory.create(id=res_id, dataset_id=dataset_id)
    resource.regions.set([main_region])
    resource.regions.add(*additional_regions, through_defaults={'is_additional': True})
    resource.save()


@when(parsers.parse('resource with id {obj_id} is revalidated'))
def resource_is_validated(obj_id):
    from mcod.resources.models import Resource
    from mcod.resources.link_validation import session
    res = Resource.objects.get(pk=obj_id)
    if res.link and res.main_file:
        adapter = requests_mock.Adapter()
        adapter.register_uri('GET', res.link, content=res.main_file.read(),
                             headers={'Content-Type': res.main_file_mimetype})
        session.mount(res.link, adapter)
    res.revalidate()


@when('request resource posted data contains simple file')
def posted_data_with_file(admin_context):
    _file = SimpleUploadedFile('test.html', get_html_file().read(), content_type='text/html')
    admin_context.obj['file'] = _file


@then('resource has assigned file')
def resource_created_with_file():
    from mcod.resources.models import Resource
    res = Resource.objects.all().latest('id')
    if is_enabled('S40_new_file_model.be'):
        assert res.file.name == ''
        assert res.main_file.name != ''
    else:
        assert res.file.name != ''


@then('counter incrementing task is executed')
def counter_incrementing_task_is_executed(context):
    save_counters()


@then(parsers.parse('Resource with title {title} has assigned file {filename}'))
def resource_file_name_id(title, filename):
    model = apps.get_model('resources', 'resource')
    obj = model.objects.get(title=title)
    assert obj.main_file.name.endswith(filename)