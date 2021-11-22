import datetime
import dpath
import json
import os
import re
import shutil
import smtplib

from django.apps import apps
from django.test import Client
from django.utils import translation
import requests_mock

from pytest_bdd import given, parsers, then, when

from mcod import settings
from mcod.core.api.rdf.namespaces import NAMESPACES
from mcod.core.registries import factories_registry


def copyfile(src, dst):
    shutil.copyfile(src, dst)
    return dst


def prepare_file(filename):
    src = str(os.path.join(settings.TEST_SAMPLES_PATH, filename))
    dst = str(os.path.join(settings.RESOURCES_MEDIA_ROOT, filename))
    copyfile(src, dst)

    return dst


def prepare_dbf_file(filename):
    dbf_path = os.path.join(settings.DATA_DIR, 'dbf_examples')
    return os.path.join(dbf_path, filename)


def create_object(obj_type, obj_id, is_removed=False, status='published', **kwargs):
    _factory = factories_registry.get_factory(obj_type)
    kwargs['pk'] = obj_id
    if obj_type != 'tag':
        kwargs['is_removed'] = is_removed
    if 'user' not in obj_type:
        kwargs['status'] = status
    return _factory(**kwargs)


@given('list of sent emails is empty')
def email_file_path_is_empty():
    shutil.rmtree(settings.EMAIL_FILE_PATH, ignore_errors=True)


@then('remove <object_type> with id 999')
def remove_object_with_id_999(object_type):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.objects.get(pk=999)
    instance.is_removed = True
    instance.save()


@then('restore <object_type> with id 999')
def restore_object_with_id_999(object_type):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.raw.get(pk=999)
    instance.is_removed = False
    instance.save()


@given(parsers.parse('remove {object_type} with id {object_id:d}'))
def remove_object_with_id_pp(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.objects.get(pk=object_id)
    instance.is_removed = True
    instance.save()


@then(parsers.parse('remove {object_type} with id {object_id:d}'))
def remove_object_with_id_p(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.objects.get(pk=object_id)
    instance.is_removed = True
    instance.save()


@then(parsers.parse('restore {object_type} with id {object_id:d}'))
def restore_object_with_id_p(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.raw.get(pk=object_id)
    instance.is_removed = False
    instance.save()


@given(parsers.parse('restore {object_type} with id {object_id:d}'))
def restore_object_with_id_pp(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    model = _factory._meta.model
    instance = model.raw.get(pk=object_id)
    instance.is_removed = False
    instance.save()


@given('<object_type> with id 900')
def object_with_id_900_p(object_type):
    return create_object(object_type, 900)


@given('<object_type> with id 901')
def object_with_id_901_p(object_type):
    return create_object(object_type, 901)


@given('<object_type> with id 902')
def object_with_id_902_p(object_type):
    return create_object(object_type, 902)


@given('<object_type> with id 903')
def object_with_id_903_p(object_type):
    return create_object(object_type, 903)


@given('<object_type> with id 904')
def object_with_id_904_p(object_type):
    return create_object(object_type, 904)


@given('<object_type> with id 905')
def object_with_id_905_p(object_type):
    return create_object(object_type, 905)


@given('<object_type> with id 906')
def object_with_id_906_p(object_type):
    return create_object(object_type, 906)


@given('<object_type> with id 907')
def object_with_id_907_p(object_type):
    return create_object(object_type, 907)


@given('<object_type> with id 908')
def object_with_id_908_p(object_type):
    return create_object(object_type, 908)


@given('<object_type> with id 909')
def object_with_id_909_p(object_type):
    return create_object(object_type, 909)


@given('<object_type> with id 910')
def object_with_id_910_p(object_type):
    return create_object(object_type, 910)


@given(parsers.parse('{object_type} with id 900'))
def object_with_id_900(object_type):
    return create_object(object_type, 900)


@given(parsers.parse('{object_type} with id 901'))
def object_with_id_901(object_type):
    return create_object(object_type, 901)


@given(parsers.parse('{object_type} with id 902'))
def object_with_id_902(object_type):
    return create_object(object_type, 902)


@given(parsers.parse('{object_type} with id 903'))
def object_with_id_903(object_type):
    return create_object(object_type, 903)


@given(parsers.parse('{object_type} with id 904'))
def object_with_id_904(object_type):
    return create_object(object_type, 904)


@given(parsers.parse('{object_type} with id 905'))
def object_with_id_905(object_type):
    return create_object(object_type, 905)


@given(parsers.parse('{object_type} with id 906'))
def object_with_id_906(object_type):
    return create_object(object_type, 906)


@given(parsers.parse('{object_type} with id 907'))
def object_with_id_907(object_type):
    return create_object(object_type, 907)


@given(parsers.parse('{object_type} with id 908'))
def object_with_id_908(object_type):
    return create_object(object_type, 908)


@given(parsers.parse('{object_type} with id 909'))
def object_with_id_909(object_type):
    return create_object(object_type, 909)


@given(parsers.parse('{object_type} with id 910'))
def object_with_id_910(object_type):
    return create_object(object_type, 910)


@then(parsers.parse('set status draft on {object_type} with id {object_id:d}'))
def draft_object_with_id_999_p(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory(pk=object_id)
    instance.status = 'draft'
    instance.save()


@then(parsers.parse('set {attr_name} to {attr_value} on {object_type} with id {object_id:d}'))
def attr_to_object_with_id_p(attr_name, attr_value, object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory._meta.model.objects.get(pk=object_id)
    setattr(instance, attr_name, attr_value)
    instance.save()


@given(parsers.parse('set {attr_name} to {attr_value} on {object_type} with id {object_id:d}'))
def attr_to_object_with_id_ppp(attr_name, attr_value, object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory._meta.model.objects.get(pk=object_id)
    setattr(instance, attr_name, attr_value)
    instance.save()


@then(parsers.parse('set status published on {object_type} with id {object_id:d}'))
def publish_object_with_id_999_p(object_type, object_id):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory(pk=object_id)
    instance.status = 'published'
    instance.save()


@given(parsers.parse('{object_type} with id {object_id:d}'))
def object_with_id(object_type, object_id):
    return create_object(object_type, object_id)


def translated_object_type(object_type):
    params = {
        'application': {
            "id": 999,
            "title": "title_pl",
            "title_en": "title_en",
            "notes": "notes_pl",
            "notes_en": "notes_en",
            "slug": "slug_pl",
            "slug_en": "slug_en",
        },
        'article': {
            "id": 999,
            "title": "title_pl",
            "title_en": "title_en",
            "notes": "notes_pl",
            "notes_en": "notes_en",
            "slug": "slug_pl",
            "slug_en": "slug_en",
        },
        'dataset': {
            "id": 999,
            "title": "title_pl",
            "title_en": "title_en",
            "notes": "notes_pl",
            "notes_en": "notes_en",
            "slug": "slug_pl",
            "slug_en": "slug_en",
        },
        'institution': {
            "id": 999,
            "title": "title_pl",
            "title_en": "title_en",
            "description": "description_pl",
            "description_en": "description_en",
            "slug": "slug_pl",
            "slug_en": "slug_en",
        },
        'resource': {
            "id": 999,
            "title": "title_pl",
            "title_en": "title_en",
            "description": "description_pl",
            "description_en": "description_en",
        },
    }
    kwargs = params[object_type]
    object_id = kwargs.pop("id")
    obj = create_object(object_type, object_id, **kwargs)
    for field in kwargs:
        if field in ['title', 'description', 'notes', 'slug']:
            assert hasattr(obj, f'{field}_translated')
    return obj


@given('<object_type> created with params <params>')
@given(parsers.parse('{object_type} created with params {params}'))
def object_type_created_with_params(context, object_type, params):
    params = json.loads(params)
    if object_type.endswith('report'):
        _factory = factories_registry.get_factory(object_type)
        return _factory.create(**params)
    object_id = params.pop('id')
    tags = params.pop('tags', [])
    tag_factory = factories_registry.get_factory('tag')
    _tags = []
    for name in tags:
        tag = tag_factory.create(name=name)
        _tags.append(tag)
    if _tags:
        params['tags'] = _tags
    if object_type == 'chart':
        params['created_by'] = context.user
    create_object(object_type, object_id, **params)


@given('translated objects')
def translated_objects():
    for object_type in ['application', 'article', 'dataset', 'institution', 'resource']:
        translated_object_type(object_type)


@given(parsers.parse('{object_type} with id {object_id:d} and {field_name1} is {value1} and {field_name2} is {value2}'))
def object_with_id_and_2_params(object_type, object_id, field_name1, value1, field_name2, value2):
    return create_object(object_type, object_id, **{field_name1: value1, field_name2: value2})


@given(parsers.parse('{object_type} with id {object_id:d} and {field_name} is {value}'))
def object_with_id_and_param_p(object_type, object_id, field_name, value):
    return create_object(object_type, object_id, **{field_name: value})


@given(parsers.parse('another {object_type} with id {object_id:d} and {field_name} is {value}'))
def another_object_with_id_and_param_p(object_type, object_id, field_name, value):
    return create_object(object_type, object_id, **{field_name: value})


@given(parsers.parse(
    'another {object_type} with id {object_id:d} and {field_name1} is {value1} and {field_name2} is {value2}'))
def another_object_with_id_and_2_params(object_type, object_id, field_name1, value1, field_name2, value2):
    return create_object(object_type, object_id, **{field_name1: value1, field_name2: value2})


@given(parsers.parse(
    'one more {object_type} with id {object_id:d} and {field_name1} is {value1} and {field_name2} is {value2}'))
def one_more_object_with_id_and_2_params(object_type, object_id, field_name1, value1, field_name2, value2):
    return create_object(object_type, object_id, **{field_name1: value1, field_name2: value2})


@given(parsers.parse('6 random instances of {object_type}'))
def six_articles(object_type):
    _factory = factories_registry.get_factory(object_type)
    return _factory.create_batch(6)


@then(parsers.parse('6 random instances of {object_type}'))
def six_articles_p(object_type):
    _factory = factories_registry.get_factory(object_type)
    return _factory.create_batch(6)


@then('set status draft on <object_type> with id 999')
def draft_object_with_id_999(object_type):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory(pk=999)
    instance.status = 'draft'
    instance.save()


@then('set status published on <object_type> with id 999')
def publish_object_with_id_999(object_type):
    _factory = factories_registry.get_factory(object_type)
    instance = _factory(pk=999)
    instance.status = 'published'
    instance.save()


@when(parsers.parse('admin request body field {field} is {value}'))
def admin_request_body_field(context, field, value):
    dpath.new(context.obj, field, value)


@when(parsers.parse('admin\'s request method is {request_method}'))
def admin_request_method(admin_context, request_method):
    admin_context.admin.method = request_method


@given(parsers.parse('admin\'s request logged user is {user_type}'))
@given('admin\'s request logged user is <user_type>')
def admin_request_logged_user_is(admin_context, user_type):
    _factory = factories_registry.get_factory(user_type)
    assert _factory is not None
    admin_context.admin.user = _factory.create(
        email='{}@dane.gov.pl'.format(user_type.replace(' ', '_')),
        password='12345.Abcde',
        phone='0048123456789',
    )


@given(parsers.parse('admin\'s request logged {user_type} created with params {user_params}'))
def admin_request_logged_user_with_id(admin_context, user_type, user_params):
    _factory = factories_registry.get_factory(user_type)
    assert _factory is not None
    data = json.loads(user_params)
    admin_context.admin.user = _factory(**data)


@when(parsers.parse('admin\'s request posted {data_type} data is {req_post_data}'))
@when('admin\'s request posted <data_type> data is <req_post_data>')
def api_request_post_data(admin_context, data_type, req_post_data):
    post_data = json.loads(req_post_data)
    default_post_data = {
        'application': {
            "title": "Application title",
            "slug": "application-title",
            "notes": "opis",
            "url": "http://test.pl",
            "status": "published",
        },
        'article': {
            "title": "Test with article title",
            "slug": "",
            "notes": "Tresc",
            "status": "published",
            "category": None,
        },
        'course': {
            "modules-TOTAL_FORMS": "1",
            "modules-INITIAL_FORMS": "0",
            "modules-MIN_NUM_FORMS": "1",
            "modules-MAX_NUM_FORMS": "1000",

            "modules-0-id": "",
            "modules-0-course": "",
            "modules-0-start": "",
            "modules-0-number_of_days": "",
            "modules-0-type": "",

            "modules-__prefix__-id": "",
            "modules-__prefix__-course": "",
            "modules-__prefix__-start": "",
            "modules-__prefix__-number_of_days": "",
            "modules-__prefix__-type": "",

            "_save": "",
            "title": "",
            "participants_number": "",
            "venue": "",
            "notes": "",
            "file": "",
            "materials_file": "",
            "status": "published",
        },
        'dataset': {
            "title": "Test with dataset title",
            "notes": "more than 20 characters",
            "status": "published",
            "update_frequency": "weekly",
            "url": "http://www.test.pl",
            "organization": [],
            "tags": [],

            "resources-TOTAL_FORMS": "0",
            "resources-INITIAL_FORMS": "0",
            "resources-MIN_NUM_FORMS": "0",
            "resources-MAX_NUM_FORMS": "1000",
            "resources-2-TOTAL_FORMS": "0",
            "resources-2-INITIAL_FORMS": "0",
            "resources-2-MIN_NUM_FORMS": "0",
            "resources-2-MAX_NUM_FORMS": "1000",
        },
        'datasource': {
            '_save': [''],
            'name': [''],
            'description': [''],
            'source_type': [''],
            'source_hash': [''],
            'xml_url': [''],
            'portal_url': ['http://example.com'],
            'api_url': [''],
            'organization': [],
            'frequency_in_days': [],
            'status': [''],
            'license_condition_db_or_copyrighted': [''],
            'categories': [],
            'institution_type': ['local'],
            'imports-TOTAL_FORMS': ['0'],
            'imports-INITIAL_FORMS': ['0'],
            'imports-MIN_NUM_FORMS': ['0'],
            'imports-MAX_NUM_FORMS': ['0'],
            'datasource_datasets-TOTAL_FORMS': ['0'],
            'datasource_datasets-INITIAL_FORMS': ['0'],
            'datasource_datasets-MIN_NUM_FORMS': ['0'],
            'datasource_datasets-MAX_NUM_FORMS': ['0']
        },
        'datasetsubmission': {

        },
        'institution': {
            "_save": "",
            "institution_type": "local",
            "title": "Instytucja testowa X",
            "slug": "",
            "abbreviation": "TEST",
            "status": "published",
            "description": "",
            "image": "",
            "postal_code": "00-060",
            "city": "Warszawa",
            "street_type": "ul",
            "street": "Królewska",
            "street_number": "27",
            "flat_number": "",
            "email": "test@dane.gov.pl",
            "tel": "222500110",
            "tel_internal": "",
            "fax": "",
            "fax_internal": "",
            "epuap": "123",
            "regon": "145881488",
            "website": "https://mc.gov.pl",
            "title_en": "",
            "description_en": "",
            "slug_en": "",

            "datasets-TOTAL_FORMS": "0",
            "datasets-INITIAL_FORMS": "0",
            "datasets-MIN_NUM_FORMS": "0",
            "datasets-MAX_NUM_FORMS": "0",

            "datasets-2-TOTAL_FORMS": "0",
            "datasets-2-INITIAL_FORMS": "0",
            "datasets-2-MIN_NUM_FORMS": "0",
            "datasets-2-MAX_NUM_FORMS": "1000",

            "datasets-__prefix__-id": "",
            "datasets-__prefix__-organization": "",
            "datasets-2-__prefix__-title": "",
            "datasets-2-__prefix__-notes": "",
            "datasets-2-__prefix__-url": "",
            "datasets-2-__prefix__-update_frequency": "notApplicable",
            "datasets-2-__prefix__-category": "",
            "datasets-2-__prefix__-status": "published",
            "datasets-2-__prefix__-license_condition_responsibilities": "",
            "datasets-2-__prefix__-license_condition_db_or_copyrighted": "",
            "datasets-2-__prefix__-license_condition_personal_data": "",
            "datasets-2-__prefix__-id": "",
            "datasets-2-__prefix__-organization": "",
            "json_key[datasets-2-__prefix__-customfields]": "key",
            "json_value[datasets-2-__prefix__-customfields]": "value",

            # default dataset formset data if: "datasets-2-TOTAL_FORMS": > 0.
            "datasets-2-0-title": "test",
            "datasets-2-0-notes": "<p>123</p>",
            "datasets-2-0-url": "",
            "json_key[datasets-2-0-customfields]": "key",
            "json_value[datasets-2-0-customfields]": "value",
            "datasets-2-0-update_frequency": "notApplicable",
            "datasets-2-0-category": "",
            "datasets-2-0-status": "published",
            "datasets-2-0-license_condition_responsibilities": "",
            "datasets-2-0-license_condition_db_or_copyrighted": "",
            "datasets-2-0-license_condition_personal_data": "",
            "datasets-2-0-id": "",
            "datasets-2-0-organization": "",
        },
        'lab_event': {
            "reports-TOTAL_FORMS": "1",
            "reports-INITIAL_FORMS": "0",
            "reports-MIN_NUM_FORMS": "1",
            "reports-MAX_NUM_FORMS": "2",

            "reports-0-id": "",
            "reports-0-lab_event": "",
            "reports-0-link": "",
            "reports-0-file": "",

            "reports-__prefix__-id": "",
            "reports-__prefix__-lab_event": "",
            "reports-__prefix__-link": "",
            "reports-__prefix__-file": "",

            "_save": "",
            "title": "",
            "notes": "",
            "event_type": "",
            "execution_date": "",
        },
        'resource': {
            "Resource_file_tasks-INITIAL_FORMS": "0",
            "Resource_file_tasks-MAX_NUM_FORMS": "1000",
            "Resource_file_tasks-MIN_NUM_FORMS": "0",
            "Resource_file_tasks-TOTAL_FORMS": "3",

            "Resource_data_tasks-INITIAL_FORMS": "0",
            "Resource_data_tasks-MAX_NUM_FORMS": "1000",
            "Resource_data_tasks-MIN_NUM_FORMS": "0",
            "Resource_data_tasks-TOTAL_FORMS": "3",

            "Resource_link_tasks-INITIAL_FORMS": "0",
            "Resource_link_tasks-MAX_NUM_FORMS": "1000",
            "Resource_link_tasks-MIN_NUM_FORMS": "0",
            "Resource_link_tasks-TOTAL_FORMS": "3",

            "_save": "",
            "from_resource": "",
            "title_en": "",
            "description_en": "",
            "slug_en": "",
        },
        'user': {
            "email": "",
            "fullname": "",
            "phone": "",
            "phone_internal": "",
            "is_staff": False,
            "is_superuser": False,
            "state": "active",
            "organizations": []
        }
    }
    assert data_type in default_post_data.keys()
    default_post_data["datasets-2-0-tags_pl"] = []
    default_post_data["datasets-2-0-tags_en"] = []
    data = default_post_data.get(data_type, {}).copy()
    data.update(post_data)
    admin_context.obj = data


@then(parsers.parse('admin\'s response status code is {status_code:d}'))
def admin_response_status_code(admin_context, status_code):
    assert status_code == admin_context.response.status_code, 'Response status should be "%s", is "%s"' % (
        status_code,
        admin_context.response.status_code
    )


@then(parsers.parse("admin's response status code is 200 if {has_trash:d} else 404"))
@then("admin's response status code is 200 if <has_trash> else 404")
def admin_response_status_code_is_200_or_404(admin_context, has_trash):
    status_code = 200 if has_trash else 404
    assert status_code == admin_context.response.status_code, 'Response status should be "%s", is "%s"' % (
        status_code,
        admin_context.response.status_code
    )


@then(parsers.parse('admin\'s response page is not editable'))
def admin_response_page_not_editable(admin_context):
    assert admin_context.response.status_code == 200
    cnt = admin_context.response.content.decode()
    assert '<button type="submit" class="btn btn-high  btn-info" name="_save" >Zapisz</button>' not in cnt
    assert '<button type="submit" name="_continue" class="btn btn-high">Zapisz i kontynuuj edycję</button>' not in cnt
    assert '<button type="submit" name="_addanother" class="btn">Zapisz i dodaj kolejny</button>' not in cnt
    assert 'id="duplicate_button"' not in cnt
    assert 'id="revalidate_button"' not in cnt


@then(parsers.parse('admin\'s response page contains {contained_value}'))
@then('admin\'s response page contains <contained_value>')
def admin_response_page_contains(admin_context, contained_value):
    content = admin_context.response.content.decode()
    assert contained_value in content, f'Page content should contain phrase: \"{contained_value}\"'


@then(parsers.parse('admin\'s response page form contains {contained_value} and {another_value}'))
@then('admin\'s response page form contains <contained_value> and <another_value>')
def admin_response_page_contains_values(admin_context, contained_value, another_value):
    content = admin_context.response.content.decode()
    assert contained_value in content and another_value in content,\
        f'Page content should contain phrases: \"{contained_value}\" and \"{another_value}\"'


@then(parsers.parse('admin\'s response page not contains {value}'))
def admin_response_page_not_contains(admin_context, value):
    content = admin_context.response.content.decode()
    assert value not in content, f'Page content should not contain phrase: \"{value}\"'


@when(parsers.parse('admin\'s page {page_url} is requested'))
@when('admin\'s page <page_url> is requested')
def admin_page_is_requested(admin_context, page_url):
    client = Client()
    client.force_login(admin_context.admin.user)
    translation.activate('pl')
    if admin_context.admin.method == 'POST':
        response = client.post(page_url, data=getattr(admin_context, 'obj', None), follow=True)
    else:
        response = client.get(page_url, follow=True)
    admin_context.response = response


@when(parsers.parse('admin\'s page with mocked geo api {page_url} is requested'))
@when('admin\'s page with mocked geo api <page_url> is requested')
def admin_page_with_mocked_geo_api_is_requested(admin_context, page_url, main_regions_response,
                                                additional_regions_response):
    client = Client()
    main_reg_expr = re.compile(settings.PLACEHOLDER_URL + r'/parser/findbyid\?ids=\d{9,10}%2C\d{9,10}')
    additional_reg_expr = re.compile(
        settings.PLACEHOLDER_URL + r'/parser/findbyid\?ids=\d{8,10}%2C\d{8,10}%2C\d{8,10}%2C\d{8,10}')
    client.force_login(admin_context.admin.user)
    translation.activate('pl')
    if admin_context.admin.method == 'POST':
        with requests_mock.Mocker(real_http=True) as mock_request:
            mock_request.get(main_reg_expr, json=main_regions_response)
            mock_request.get(additional_reg_expr, json=additional_regions_response)
            response = client.post(page_url, data=getattr(admin_context, 'obj', None), follow=True)
    else:
        response = client.get(page_url, follow=True)
    admin_context.response = response


@then(parsers.parse('api\'s response data has length {number:d}'))
@then('api\'s response data has length <number>')
def api_response_data_has_length(context, number):
    data = context.response.json['data']
    v_len = len(data) if data else 0
    assert v_len == int(number), 'data length should be {}, but is {}'.format(number, v_len)


@when(parsers.parse('send_mail will raise SMTPException'))
def api_request_csrf_token(context, mocker):
    mocker.patch('mcod.users.models.send_mail', side_effect=smtplib.SMTPException)


@then(parsers.parse('sparql store contains {item_type} {item_value}'))
@then('sparql store contains <item_type> <item_value>')
def sparql_store_contains_subject(sparql_registry, item_type, item_value):
    items = {
        'subject': 's',
        'predicate': 'p',
        'object': 'o'
    }
    store_query = f'SELECT ?{items[item_type]} WHERE {{ GRAPH {sparql_registry.graph_name}' \
                  f' {{ ?s ?p ?o . FILTER (?{items[item_type]} = {item_value}) }} }}'
    response = sparql_registry.sparql_store.query(store_query, initNs=NAMESPACES)
    store_values = set([resp[0].n3() for resp in response])
    assert item_value in store_values


@then(parsers.parse('sparql store does not contain subject {subject}'))
@then('sparql store does not contain subject <subject>')
def sparql_store_does_not_contain_subject(sparql_registry, subject):
    store_query = f'SELECT ?s WHERE {{ GRAPH {sparql_registry.graph_name} {{ ?s ?p ?o . FILTER (?s = {subject}) }} }}'
    response = sparql_registry.sparql_store.query(store_query)
    store_subjects = set([resp[0].n3() for resp in response])
    assert subject not in store_subjects


@then(parsers.parse('sparql store contains triple with attributes {attributes}'))
@then('sparql store contains triple with attributes <attributes>')
def sparql_store_contains_triple(sparql_registry, attributes):
    parsed_attrs = json.loads(attributes)
    subject = parsed_attrs.get('subject') or '?s'
    predicate = parsed_attrs.get('predicate') or '?p'
    object = parsed_attrs.get('object') or '?o'
    store_query = f'ASK WHERE {{ GRAPH {sparql_registry.graph_name} {{ {subject} {predicate} {object} }} }}'
    response = sparql_registry.sparql_store.query(store_query, initNs=NAMESPACES)
    assert response.askAnswer


@then(parsers.parse('latest {obj_type} attribute {attr} is {value}'))
def latest_object_attribute_is(obj_type, attr, value):
    _factory = factories_registry.get_factory(obj_type)
    model = _factory._meta.model
    obj = model.raw.latest('id')
    assert getattr(obj, attr) == value


@given('removed <object_type> objects with ids <object_ids>')
def removed_objects_with_ids(object_type, object_ids):
    _factory = factories_registry.get_factory(object_type)
    split_ids = object_ids.split(',')
    for obj_id in split_ids:
        instance = _factory(pk=int(obj_id))
        instance.is_removed = True
        instance.save()


@then(parsers.parse('{object_type} with title {title} contains data {data_str}'))
def obj_with_title_attribute_is(object_type, title, data_str):
    model = apps.get_model(object_type)
    obj = model.objects.get(title=title)
    data = json.loads(data_str)
    for attr_name, attr_value in data.items():
        obj_attr = getattr(obj, attr_name)
        if isinstance(obj_attr, datetime.date):
            obj_attr = str(obj_attr)
        assert obj_attr == attr_value, f'{object_type} attribute {attr_name} should be {attr_value}, but is {obj_attr}'


@given('removed <object_type> objects with ids <object_with_related_removed_ids> and'
       ' removed related <related_object_type> through <relation_name>')
def removed_objects_with_ids_and_removed_related_object(
        object_type, object_with_related_removed_ids, related_object_type, relation_name):
    _factory = factories_registry.get_factory(object_type)
    _related_factory = factories_registry.get_factory(related_object_type)
    split_ids = object_with_related_removed_ids.split(',')
    related_object = _related_factory.create(is_removed=True)
    factory_kwargs = {'is_removed': True, relation_name: related_object}
    for obj_id in split_ids:
        factory_kwargs['pk'] = int(obj_id)
        _factory.create(**factory_kwargs)


@then(parsers.parse('{object_type} with id {obj_id} contains data {data_str}'))
@then('<object_type> with id <obj_id> contains data <data_str>')
def obj_with_id_attribute_is(object_type, obj_id, data_str):
    model = apps.get_model(object_type)
    obj = model.objects.get(id=obj_id)
    data = json.loads(data_str)
    for attr_name, attr_value in data.items():
        obj_attr = getattr(obj, attr_name)
        if isinstance(obj_attr, datetime.date):
            obj_attr = str(obj_attr)
        assert obj_attr == attr_value, f'{object_type} attribute {attr_name} should be {attr_value}, but is {obj_attr}'
