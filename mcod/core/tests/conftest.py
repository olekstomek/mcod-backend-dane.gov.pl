import base64
import csv
import io
import json
import os
import random
from collections import namedtuple
from datetime import date

import elasticsearch_dsl
import factory
import falcon
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from falcon import testing
from pytest_factoryboy import register

from mcod import settings
from mcod.api import app
from mcod.applications.factories import ApplicationFactory
from mcod.applications.models import Application
from mcod.articles.factories import ArticleFactory
from mcod.articles.models import Article, ArticleCategory
from mcod.categories.models import Category
from mcod.core.tests import factories
from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.organizations.factories import OrganizationFactory
from mcod.organizations.models import Organization
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource
from mcod.tags.models import Tag
from mcod.users.factories import UserFactory, EditorFactory, AdminFactory

User = get_user_model()


def random_csv_data(columns=5, rows=100):
    _faker_types = [
        ('text', {'max_nb_chars': 100}),
        ('time', {'pattern': '%H:%M:%S', 'end_datetime': None}),
        ('date', {'pattern': '%d-%m-%Y', 'end_datetime': None}),
        ('month_name', {}),
        ('catch_phrase', {}),
        ('bs', {}),
        ('company', {}),
        # ('int', {}),
        ('country', {}),
        ('city', {}),
        ('street_name', {}),
        ('address', {}),
    ]

    header_types = [random.randint(0, len(_faker_types) - 1) for col in range(columns)]
    _headers = [_faker_types[idx][0].title() for idx in header_types]

    f = io.StringIO()
    _writer = csv.writer(f)
    _writer.writerow(
        _headers
    )

    for row in range(rows):
        row = []
        for header_idx in header_types:
            provider, extra_kwargs = _faker_types[header_idx]
            row.append(
                factory.Faker(provider, locale='pl_PL').generate(extra_kwargs)
            )
        _writer.writerow(row)

    return f.getvalue()


@pytest.fixture
def ten_users():
    return factories.UserFactory.create_batch(
        10
    )


@pytest.fixture
def ten_editors():
    return factories.EditorFactory.create_batch(
        10
    )


@pytest.fixture
def ten_resources():
    return factories.ResourceFactory.create_batch(
        10, file__data=random_csv_data(
            columns=random.randint(5, 10),
            rows=random.randint(20, 200)
        )
    )


@pytest.fixture
def client():
    return testing.TestClient(app, headers={'X-API-VERSION': '1.0'})


@pytest.fixture
def client10():
    return testing.TestClient(app, headers={'X-API-VERSION': '1.0'})


@pytest.fixture
def client14():
    return testing.TestClient(app, headers={
        'X-API-VERSION': '1.4',
        'Accept-Language': 'pl'
    })


@pytest.fixture
def token_exp_delta():
    return 315360000  # 10 years


@pytest.fixture
def active_user():
    usr = User.objects.create_user('test-active@example.com', 'Britenet.1')
    usr.state = 'active'
    usr.save()
    return usr


@pytest.fixture
def admin_user():
    usr = User.objects.create_user('test-admin@example.com', 'Britenet.1')
    usr.fullname = 'System Administrator'
    usr.state = 'active'
    usr.is_staff = True
    usr.is_superuser = True

    usr.save()
    return usr


@pytest.fixture
def admin_user2():
    usr = User.objects.create_user('test-admin2@example.com', 'Britenet.1')
    usr.state = 'active'
    usr.is_staff = True
    usr.is_superuser = True
    usr.save()
    return usr


@pytest.fixture
def editor_user():
    usr = User.objects.create_user('test-editor@example.com', 'Britenet.1')
    usr.state = 'active'
    usr.is_staff = True
    usr.fullname = "Test Editor"
    usr.phone = '+48123123123'
    usr.save()
    return usr


@pytest.fixture
def inactive_user():
    usr = User.objects.create_user('test-inactive@example.com', 'Britenet.1')
    return usr


@pytest.fixture
def blocked_user():
    usr = User.objects.create_user('test-blocked@example.com', 'Britenet.1')
    usr.state = 'blocked'
    usr.save()
    return usr


@pytest.fixture
def user_with_organization(valid_organization):
    usr = User.objects.create_user('test-editor@example.com', 'Britenet.1')
    usr.state = 'active'
    usr.organizations.set([valid_organization])
    usr.is_staff = True
    usr.fullname = "Organization Editor"
    usr.phone = '+48123123123'
    usr.save()
    return usr


@pytest.fixture
def deleted_user():
    usr = User.objects.create_user('test-deleted@example.com', 'Britenet.1')
    usr.is_removed = True
    usr.save()
    return usr


# @pytest.fixture
# def draft_user():
#     usr = User.objects.create_user('test-draft@example.com', 'Britenet.1')
#     usr.state = 'draft'
#     usr.save()
#     return usr


@pytest.fixture
def sessions_cache():
    return caches[settings.SESSION_CACHE_ALIAS]


@pytest.fixture
def default_cache():
    return caches['default']


@pytest.fixture
def invalid_passwords():
    return [
        'abcd1234',
        'abcdefghi',
        '123456789',
        'alpha101',
        '92541001101',
        '9dragons',
        '@@@@@@@@',
        '.........',
        '!!!!!!!!!!!',
        '12@@@@@@@',
        '!!@#$$@ab@@',
        'admin@mc.gov.pl',
        '1vdsA532A66',
    ]


@pytest.fixture
def invalid_passwords_with_user():
    return [
        'abcd1234',
        'abcdefghi',
        '123456789',
        'aaa@bbb.cc',
        'aaa@bbb.c12',
        'bbb@aaa.cc',
        'TestUser123',
        'Test User',
        'Test.User',
        'User.Test123',
        'alpha101',
        '92541001101',
        '9dragons',
        '@@@@@@@@',
        '.........',
        '!!!!!!!!!!!',
        '12@@@@@@@',
        '!!@#$$@ab@@',
        'admin@mc.gov.pl',
        '1vdsA532A66',
    ]


@pytest.fixture
def valid_passwords():
    passwords = [
        '12@@@@@@Ab@',
        '!!@#$$@aBB1@@',
        'Iron.Man.Is.Th3.Best'
        'Admin7@mc.gov.pl',
        '1vDsA532A.6!6',
    ]
    passwords.extend(['Abcd%s1234' % v for v in settings.SPECIAL_CHARS])
    return passwords


@pytest.fixture
def valid_organization():
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
    organization.save()
    return organization


@pytest.fixture
def valid_organization2():
    organization = Organization()
    organization.slug = "zlodzieje-cienia"
    organization.title = "Złodzieje cienia"
    organization.postal_code = "00-002"
    organization.city = "Wrota Baldura"
    organization.street = "Schowana"
    organization.street_number = "3"
    organization.flat_number = "1"
    organization.street_type = "ul"
    organization.email = "email@shadowthieves.bg"
    organization.fax = "321321321"
    organization.tel = "321321321"
    organization.epuap = "shthv"
    organization.regon = "321321321"
    organization.website = "www.shadowthieves.bg"
    organization.save()
    return organization


@pytest.fixture
def inactive_organization():
    organization = Organization()
    organization.slug = "test"
    organization.title = "test"
    return organization


@pytest.fixture
def articles_list():
    a2 = Article()
    a2.slug = "article-2"
    a2.title = "Article 2"
    a2.status = "published"
    a2.category_id = 1
    a2.save()

    del_a2 = Article()
    del_a2.slug = "article-deleted"
    del_a2.title = "Article Deleted"
    del_a2.status = "published"
    del_a2.category_id = 1
    del_a2.save()
    del_a2.delete()

    a_draft = Article()
    a_draft.slug = "article-draft"
    a_draft.title = "Article draft"
    a_draft.status = "draft"
    a_draft.category_id = 1
    a_draft.save()

    a_other_category = Article()
    a_other_category.slug = "article-other-category"
    a_other_category.title = "Article other category"
    a_other_category.status = "published"
    a_other_category.category_id = 2
    a_other_category.save()

    a_last = Article()
    a_last.slug = "article-last"
    a_last.title = "Article last"
    a_last.status = "published"
    a_last.category_id = 1
    a_last.save()

    return [_valid_article(), a2, del_a2, a_draft, a_other_category, a_last]


@pytest.fixture
def applications_list():
    del_app = Application()
    del_app.title = "Deleted application"
    del_app.slug = "app-del"
    del_app.url = "http://deleted.app.com"
    del_app.status = 'published'
    del_app.save()
    del_app.delete()

    app_last = Application()
    app_last.title = "Last application"
    app_last.slug = "app-last"
    app_last.url = "http://last.app.com"
    app_last.status = 'published'
    app_last.save()

    return [_valid_application(), _valid_application2(), del_app, app_last]


def _valid_application():
    a = Application()
    a.slug = "test-name"
    a.title = "Test name"
    a.notes = "Treść"
    a.url = "http://smth.smwheere.com"
    a.status = 'published'
    a.save()
    return a


def _valid_application2():
    app2 = Application()
    app2.title = "Second application"
    app2.slug = "app2"
    app2.url = "http://second.app.com"
    app2.status = 'published'
    app2.save()
    return app2


@pytest.fixture
def valid_application():
    return _valid_application()


@pytest.fixture
def valid_application2():
    return _valid_application2()


@pytest.fixture
def valid_application_with_logo(small_image):
    app = Application()
    app.title = "Application with logo"
    app.slug = "app-logo"
    app.url = "http://logo.app.com"
    app.status = 'published'
    app.image = small_image
    app.save()
    return app


@pytest.fixture
def unsave_application():
    a = Application()
    a.slug = "test-name"
    a.title = "Test name"
    a.url = "http://smth.smwheere.com"
    return a


def _valid_article():
    article, created = Article.objects.get_or_create(
        slug="test-name",
        title="Test name",
        category_id=1
    )
    return article


@pytest.fixture
def valid_article():
    return _valid_article()


@pytest.fixture
def draft_article():
    a = Article()
    a.slug = "draft"
    a.title = "Draft"
    a.status = 'draft'
    a.category_id = 1
    a.save()
    return a


@pytest.fixture
def unsave_article():
    a = Article()
    a.slug = "test-name"
    a.title = "Test name"
    return a


@pytest.fixture
def valid_dataset(valid_organization):
    a = Dataset()
    a.slug = "test-dataset-name"
    a.title = "test name"
    a.organization = valid_organization
    a.update_frequency = 'weekly'
    a.save()
    return a


@pytest.fixture
def valid_dataset2(valid_organization):
    a = Dataset()
    a.slug = "test-dataset-name2"
    a.title = "test name2"
    a.organization = valid_organization
    a.save()
    return a


@pytest.fixture
def dataset_org2(valid_organization2):
    a = Dataset()
    a.slug = "to-kill"
    a.title = "Zlecenia zabójstw"
    a.organization = valid_organization2
    a.save()
    return a


@pytest.fixture
def dataset_list(valid_dataset, valid_dataset2, dataset_org2):
    return [valid_dataset2, dataset_org2, valid_dataset]


@pytest.fixture
def valid_tag():
    tag, created = Tag.objects.get_or_create(name='test')
    return tag


@pytest.fixture
def valid_resource(valid_dataset):
    resource = Resource()
    resource.link = "http://falconframework.org"
    resource.title = "Resource name"
    resource.resource_type = "Table"
    resource.dataset = valid_dataset
    resource.data_date = date.today()
    resource.tracker.saved_data['link'] = resource.link
    resource.save()
    return resource


@pytest.fixture
def valid_resource_with_file(valid_dataset, file_csv):
    resource = Resource()
    resource.title = "File resource name"
    resource.resource_type = "Table"
    resource.type = "file"
    resource.format = 'csv'
    resource.file = File(file_csv)
    resource.file.open('r')
    resource.dataset = valid_dataset
    resource.tracker.saved_data['link'] = resource.link
    resource.save()
    return resource


def prepare_file(name, content):
    os.makedirs('media/resources/test', exist_ok=True)
    f = open(f"media/resources/test/{name}", 'w')
    f.write(content)
    f.close()
    return f


@pytest.fixture
def file_csv():
    content = "a;b;c;d;\n" \
              "1;2;3;4;\n" \
              "5;6;7;8;\n" \
              "9;0;1;2;\n" \
              "3;4;5;6;\n" \
              "7;8;9;0;\n" \
              "1;2;;4;\n"
    return prepare_file('test_file.csv', content)


xml_sample = """<?xml version="1.0"?>
<note>
    <to>Tove</to>
    <from>Jani</from>
    <heading>Reminder</heading>
    <body>Don't forget me this weekend!</body>
</note>"""


@pytest.fixture
def file_xml():
    return prepare_file('test_file.xml', xml_sample)


@pytest.fixture
def file_html():
    content = """<!DOCTYPE html>
<html>
    <head>
        <title>Test File</title>
    </head>
    <body>
        <h2>The href Attribute</h2>
        <p>HTML links are defined with the a tag. The link address is specified in the href attribute:</p>
        <a href=\"https://www.w3schools.com\">This is a link</a>
        Some sample text
    </body>
</html>"""
    return prepare_file('test_file.html', content)


@pytest.fixture
def file_rdf():
    content = """<?xml version="1.0"?>
<rdf:RDF
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:si="https://www.w3schools.com/rdf/">
  <rdf:Description rdf:about="https://www.w3schools.com">
    <si:title>W3Schools</si:title>
    <si:author>Jan Egil Refsnes</si:author>
  </rdf:Description>
</rdf:RDF>"""
    return prepare_file('test_file.rdf', content)


json_sample = """{"menu": {
  "id": "file",
  "value": "File",
  "popup": {
    "menuitem": [
      {"value": "New", "onclick": "CreateNewDoc()"},
      {"value": "Open", "onclick": "OpenDoc()"},
      {"value": "Close", "onclick": "CloseDoc()"}
    ]
  }
}}"""


@pytest.fixture
def file_json():
    return prepare_file('test_file.json', json_sample)


jsonapi_sample = {
    "data": {
        "type": "institutions",
        "attributes": {
            "street": "Test",
            "flat_number": None,
            "email": "test@nowhere.tst",
            "slug": "test",
            "created": "2015-05-18 13:21:00.528480+00:00",
            "website": "http://www.uke.gov.pl/",
            "modified": "2017-12-01 10:05:09.055606+00:00"
        },
        "id": "10",
        "relationships": {
            "datasets": {
                "links": {
                    "related": {
                        "href": "/institutions/10/datasets",
                        "meta": {
                            "count": 0
                        }
                    }
                },
                "data": []
            }
        },
        "links": {
            "self": "/institutions/10"
        }
    },
    "links": {
        "self": "/institutions/10"
    },
    "meta": {
        "language": "pl",
        "params": {},
        "path": "/institutions/10",
        "rel_uri": "/institutions/10"
    }
}


@pytest.fixture
def file_jsonapi():
    content = json.dumps(jsonapi_sample)
    return prepare_file('test_jsonapi.json', content)


@pytest.fixture
def file_txt():
    content = "jhshjgfjkhgsdfkjas   123423 sdfasfoipm\n<br/>\n{\"fake\": \"json\"}\n" \
              "<fake>xml</fake>\nyweqioeruxczvb 12  123\t\n\t76ytgfvbnju8765rtfd"
    return prepare_file('test_noformat.txt', content)


@pytest.fixture
def base64_image():
    image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAADIEl" \
            "EQVR42mKQLz/JyAAF/LlHswXyAGWTA4AcWRCG+2wsY9u2bdu2bdu21dk4WXt3YtvunoxijfHd" \
            "G5yrjar68eoMvw8Tx4hzBE28TtCEawQNOUVQv1SC+qTwW5+UIVIg8vSKC+TmjfhJ6pZWp+HKW" \
            "3K/XQ/pF/Gcvhuu07frevp3XcfADdcYuO8J/bbcpsm8C/IXjQ7XkYLW/iT9FSL556GnlYlHnm" \
            "K2u3EBHx8+42PxMnwqUQbz4+d4QHxzMWXXbULaRypSA1HkT9jezt7ktPvvCYQHgwoFc0HWLOj" \
            "O3sSOrwYx53X0XnKB6kMT5EyN5SGSl7OA7ev8r1CeQ8li6MNyIm9IQfPUjscDnz7bSTmvpd3E" \
            "FDI32Y/0+7DTosADXG5fg8Dp7wI6UWDPuiRSHttwuEUBs8OTfvEF7cYlkqX+HlFAKNx3x30+W" \
            "l38K7RaKFEEQ2h29m9MJuWJHbMTjO/txJxWaTsyjqw1tyMFDUin37a7/y/w4T0Uzsur74PYuz" \
            "qeuIc23thBfWfnxCmVNsOiyVZlM1Kw8Lbf5tt8tDgD8nn88CMi+FCjHvdqtSb26GXOvnCit8L" \
            "D13aOalRaDzpB9vLrkUJ6JNJ/w82/CzjFtU8PHCHhJA5fwvGEhzw2WjA44JkZrhttHExXaN3/" \
            "GDlKr0YK7RzDwHXXcXn8/d1uNy/HTuN2xcYkHz7HqQ9gcIHJA/fNcPWV03P4rI7WfY6Qq9hyU" \
            "aBDJANXX8Fs82tgEZdUYZMcdZ97us+8dsMzC9zzJotiZ/R29qWrtOp5iFyFlyCJVTWk+ZR0ed" \
            "qmK0SfUjC9s3JZsXgS7n3ijoD75J3DB9vb+YzOzrJ9t+g2LJJazXbIuQou9s/F1xW31glrsFf" \
            "pO1tDmuh+6rKO+LNaIk+pQjDFx/nIGR1ymkr3oZHkzL9ICQmfUUf6O6b+JJXfWqdmz6Nyh+HR" \
            "dBIWdRwSSTshVBvBtU3vw7TpdYhW3Q9Qq8l2OSR8pkju6h+mfG0O/jXOWSptGpJVeJutwgayl" \
            "11LjlKryFl8BbmKLiNXocXkKrCQnPkW/DXORUqv/OIPGXytI4mF5NYAAAAASUVORK5CYII="
    return image, 857  # obraz i pierwotny rozmiar w bajtach


@pytest.fixture
def small_image(base64_image):
    decoded_img = base64.b64decode(base64_image[0].split(';base64,')[-1].encode())
    os.makedirs('media/images/applications/test/', exist_ok=True)
    with open("media/images/applications/test/clock.png", 'wb') as outfile:
        outfile.write(decoded_img)
    image = SimpleUploadedFile("clock.png", decoded_img)
    return image


@pytest.fixture
def valid_resource_with_description(valid_dataset):
    resource = Resource()
    resource.link = "http://falconframework.org"
    resource.title = "Resource name"
    resource.description = "Test Resource Description"
    resource.dataset = valid_dataset
    resource.status = 'published'
    resource.tracker.saved_data['link'] = resource.link
    resource.tracker.saved_data['file'] = resource.file
    resource.save()
    return resource


@pytest.fixture
def valid_resource2(valid_dataset2):
    resource = Resource()
    resource.link = "http://falconframework.org"
    resource.title = "Resource name2"
    resource.resource_type = "Table"
    resource.dataset = valid_dataset2
    resource.tracker.saved_data['link'] = resource.link
    resource.tracker.saved_data['file'] = resource.file
    resource.save()
    return resource


@pytest.fixture
def resource_without_dataset(valid_dataset):
    resource = Resource()
    resource.link = "http://falconframework.org"
    resource.title = "Resource name"
    resource.is_external = True
    resource.resource_type = "Table"
    # resource.dataset = valid_dataset
    resource.tracker.saved_data['link'] = resource.link
    resource.tracker.saved_data['file'] = resource.file

    resource.save()
    return resource


@pytest.fixture
def resource_in_dataset_org2(dataset_org2):
    resource = Resource()
    resource.link = "http://tokill.shadowthieves.bg/cowled_wizards"
    resource.title = "Zakapturzeni czarodzieje"
    resource.resource_type = "Table"
    resource.dataset = dataset_org2
    resource.save()
    return resource


@pytest.fixture
def removed_resource(valid_dataset2):
    resource = Resource()
    resource.link = "http://noth.nowhere.com"
    resource.title = "removed resource"
    resource.dataset = valid_dataset2
    resource.is_removed = True
    resource.save()
    return resource


@pytest.fixture
def draft_resource(valid_dataset2):
    resource = Resource()
    resource.link = "http://drafts.com"
    resource.title = "draft resource"
    resource.dataset = valid_dataset2
    resource.status = "draft"
    resource.save()
    return resource


@pytest.fixture
def resource_list(valid_resource, valid_resource_with_description, valid_resource2,
                  resource_in_dataset_org2):
    return [
        valid_resource2,
        valid_resource_with_description,
        resource_in_dataset_org2,
        valid_resource,
    ]


@pytest.fixture
def valid_category():
    category = Category.objects.create(
        title='Tytuł kategorii',
        slug='slug-kategorii',
        description='Opis kategorii',
        title_en='Category title',
        slug_en='category-slug',
    )
    return category


@pytest.fixture
def es_dsl_queryset():
    return elasticsearch_dsl.Search()


@pytest.fixture()
def fake_user():
    return namedtuple('User', 'email state fullname')


@pytest.fixture()
def fake_session():
    return namedtuple('Session', 'session_key')


@pytest.fixture
def fake_client():
    class XmlResource(object):
        def on_get(self, request, response):
            response.status = falcon.HTTP_200
            response.content_type = falcon.MEDIA_XML
            response.body = xml_sample

    class JsonResource(object):
        def on_get(self, request, response):
            response.status = falcon.HTTP_200
            response.content_type = falcon.MEDIA_JSON
            response.body = json_sample

    class JsonapiResource(object):
        def on_get(self, request, response):
            response.status = falcon.HTTP_200
            response.content_type = 'application/vnd.api+json; charset=UTF-8'
            response.body = json.dumps(jsonapi_sample)

    fake_api = falcon.API()
    fake_api.add_route("/xml", XmlResource())
    fake_api.add_route("/json", JsonResource())
    fake_api.add_route("/jsonapi", JsonapiResource())
    return testing.TestClient(fake_api)


@pytest.fixture
def valid_article_category2():
    ac, created = ArticleCategory.objects.get_or_create(
        name="O stronie",
        description="O stronie - stopka",
        name_en='About',
        description_en="About - footer",
    )
    return ac


@pytest.fixture
def valid_article_category():
    ac, created = ArticleCategory.objects.get_or_create(name='test_category', description='test_description')
    return ac


register(ArticleFactory)
register(ApplicationFactory)
register(OrganizationFactory)
register(UserFactory)
register(AdminFactory)
register(EditorFactory)
register(DatasetFactory)
register(ResourceFactory)
