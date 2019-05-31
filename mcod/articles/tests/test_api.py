import pytest
from falcon import testing, HTTP_OK
from mcod.api import app
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper


@pytest.fixture
def client14():
    return testing.TestClient(app, headers={
        'X-API-VERSION': '1.4',
        'Accept-Language': 'pl'
    })


@pytest.mark.django_db
class TestArticlesApiRoutes(ElasticCleanHelper):

    def test_articles_routes(self, valid_article, client14):
        paths = [
            "/articles",
            f'/articles/{valid_article.id}',
            f'/articles/{valid_article.id},{valid_article.slug}',
            f'/articles/{valid_article.id}/datasets',
            f'/articles/{valid_article.id},{valid_article.slug}/datasets',
        ]

        for p in paths:
            resp = client14.simulate_get(p)
            assert resp.status == HTTP_OK


@pytest.mark.django_db
class TestArticlesAPISlugInResponses(ElasticCleanHelper):

    def test_articles_list(self, valid_article, client14):
        resp = client14.simulate_get('/articles/')
        assert HTTP_OK == resp.status
        assert f"{valid_article.id},{valid_article.slug}" in resp.json['data'][0]['links']['self']

    def test_article_details(self, valid_article, client14):
        resp = client14.simulate_get(f'/articles/{valid_article.id}')
        assert HTTP_OK == resp.status
        assert f"{valid_article.id},{valid_article.slug}" in resp.json['data']['links']['self']

    # TODO: check that
    # def test_article_dataset_list(self, valid_article, valid_dataset, valid_dataset2, client14):
    #     valid_article.datasets.add(valid_dataset)
    #     valid_article.save()
    #     resp = client14.simulate_get(f'/articles/{valid_article.id}/datasets')
    #     assert HTTP_OK == resp.status
    #     # assert len(resp.json['data']) == 1  # TODO: Fix that!!
    #     assert f"{valid_dataset.id},{valid_dataset.slug}" in resp.json['data'][0]['links']['self']
