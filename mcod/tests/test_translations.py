import falcon
import pytest
from django.apps import apps
from mcod import settings


@pytest.mark.django_db
class TestApplicationsTranslations:
    @classmethod
    def setup_class(cls):
        cls.fixtures = {
            'category': apps.get_model('categories', 'Category')(title="Some category")
        }

    @pytest.mark.parametrize(
        'app, model_name, fields',
        [
            ('applications', 'Application', ('title', 'notes', 'slug')),
            ('articles', 'Article', ('title', 'notes', 'slug')),
            ('categories', 'Category', ('title', 'description', 'slug')),
            ('datasets', 'Dataset', ('title', 'notes', 'slug')),
            ('organizations', 'Organization', ('title', 'description', 'slug')),
            ('resources', 'Resource', ('title', 'description')),
            ('tags', 'Tag', ('name', )),
        ]
    )
    def test_models(self, app, model_name, fields):
        Model = apps.get_model(app, model_name)

        obj = Model()
        for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
            for field in fields:
                assert hasattr(obj, f'{field}_{lang}')
                setattr(obj, f'{field}_{lang}', f'{field}_{lang}')
                assert hasattr(obj, f'{field}_translated')

        for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
            for field in fields:
                assert getattr(obj, f'{field}_{lang}', f'{field}_{lang}') == f'{field}_{lang}'

    def test_detail_views(self, client, valid_application, valid_article, valid_dataset,
                          valid_resource, valid_organization):
        modules = [
            (valid_application, '/applications/%d', ('title', 'notes', 'slug')),
            (valid_article, '/articles/%d', ('title', 'notes', 'slug')),
            (valid_dataset, '/datasets/%d', ('title', 'notes')),
            (valid_organization, '/institutions/%d', ('title', 'description', 'slug')),
            (valid_resource, '/resources/%d', ('title', 'description')),
        ]
        for obj, url, fields in modules:
            for field in fields:
                for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
                    setattr(obj, f"{field}_{lang}", f"{field}_{lang}")
            obj.save()

            for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
                resp = client.simulate_get(path=url % obj.id, headers={"Accept-Language": lang})

                assert resp.status == falcon.HTTP_200
                data = resp.json['data']

                for field in fields:
                    assert field in data['attributes']
                    assert data['attributes'][field] == f"{field}_{lang}"

    def test_list_views(self, client, valid_application, valid_article, valid_dataset,
                        valid_resource, valid_organization):
        modules = [
            (valid_application, '/applications', ('title', 'notes', 'slug')),
            (valid_article, '/articles', ('title', 'notes', 'slug')),
            (valid_dataset, '/datasets', ('title', 'notes')),
            (valid_organization, '/institutions', ('title', 'description', 'slug')),
            (valid_resource, '/resources', ('title', 'description')),
        ]
        for obj, url, fields in modules:
            for field in fields:
                for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
                    setattr(obj, f"{field}_{lang}", f"{field}_{lang}")
            obj.save()

            for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
                resp = client.simulate_get(path=url,
                                           headers={"Accept-Language": lang},
                                           query_string=f"id={obj.id}")

                assert resp.status == falcon.HTTP_200
                data = resp.json['data'][0]

                for field in fields:
                    assert field in data['attributes']
                    assert data['attributes'][field] == f"{field}_{lang}"
