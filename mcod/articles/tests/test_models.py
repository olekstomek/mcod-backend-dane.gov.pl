# from django.test import TestCase

# Create your tests here.
import pytest
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings
from django.db.models import QuerySet
from django.test import Client
from django.utils import translation
from django.utils.encoding import smart_str

from mcod.articles.models import Article


class TestArticleModel(object):
    def test_can_not_create_empty_article(self):
        with pytest.raises(ValidationError)as e:
            a = Article()
            a.full_clean()
        # assert "'slug'" in str(e.value)
        assert "'title'" in str(e.value)

    def test_create_article(self, article_category):
        a = Article()
        a.slug = "test-name"
        a.title = "Test name"
        a.notes = "Description"
        a.category = article_category
        assert a.full_clean() is None
        assert a.id is None
        a.save()
        assert a.id is not None

    def test_article_fields(self, article):
        article_dict = article.__dict__
        fields = [
            "id",
            "slug",
            "title",
            "notes",
            "license_old_id",
            "author",
            "created_by_id",
            "is_removed",
            "created",
            "status",
            "status_changed",
            "modified_by_id",
            "license_id",

        ]
        for f in fields:
            assert f in article_dict
        assert isinstance(article.tags.all(), QuerySet)

    def test_safe_delete(self, article):
        assert article.status == 'published'
        article.delete()
        assert article.is_removed is True
        with pytest.raises(ObjectDoesNotExist):
            Article.objects.get(id=article.id)
        assert Article.trash.get(id=article.id)

    def test_unsafe_delete(self, article):
        assert article.status == 'published'
        article.delete(soft=False)
        # assert valid_article.state == 'deleted'
        with pytest.raises(ObjectDoesNotExist) as e:
            Article.objects.get(id=article.id)
        assert "Article matching query does not exist." in str(e.value)
        with pytest.raises(ObjectDoesNotExist) as e:
            Article.raw.get(id=article.id)
        assert "Article matching query does not exist." in str(e.value)

    def test_article_frontent_absolute_url_with_lang(self, article):
        with translation.override('pl'):
            assert article.frontend_absolute_url == f'{settings.BASE_URL}/pl/article/{article.ident}'


class TestArticleUserRoles(object):
    def test_editor_doesnt_see_articles_in_admin_panel(self, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.get("/")
        assert response.status_code == 200
        assert '/articles/' not in smart_str(response.content)

    def test_editor_cant_go_to_articles_in_admin_panel(self, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.get("/articles/")
        assert response.status_code == 404

    def test_admin_can_see_articles_in_admin_panel(self, admin):
        client = Client()
        client.force_login(admin)
        response = client.get("/")
        assert response.status_code == 200
        assert '/articles' in smart_str(response.content)

    def test_admin_can_go_to_articles_in_admin_panel(self, admin):
        client = Client()
        client.force_login(admin)
        response = client.get("/articles/")
        assert response.status_code == 200


def test_article_category_translations(article_category):
    article_category.name = 'A'
    article_category.description = 'a opis'
    article_category.name_en = 'B'
    article_category.description_en = 'b description'

    assert article_category.name == 'A'
    assert article_category.description == 'a opis'

    translation.activate('en')
    assert article_category.name_i18n == 'B'
    # Check if fallback lang working
    assert article_category.description_i18n == 'b description'

    translation.activate('pl')
    assert article_category.name_i18n == 'A'
    assert article_category.description_i18n == 'a opis'
