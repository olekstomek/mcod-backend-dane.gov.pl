# from django.test import TestCase

# Create your tests here.
import pytest
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import QuerySet
from django.test import Client
from django.utils import translation
from mcod.articles.models import Article


@pytest.mark.django_db
class TestArticleModel(object):
    def test_can_not_create_empty_article(self):
        with pytest.raises(ValidationError)as e:
            a = Article()
            a.full_clean()
        # assert "'slug'" in str(e.value)
        assert "'title'" in str(e.value)

    def test_create_article(self, valid_article_category):
        a = Article()
        a.slug = "test-name"
        a.title = "Test name"
        a.notes = "Description"
        a.category = valid_article_category
        assert a.full_clean() is None
        assert a.id is None
        a.save()
        assert a.id is not None

    def test_article_fields(self, valid_article):
        article_dict = valid_article.__dict__
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
        assert isinstance(valid_article.tags.all(), QuerySet)

    def test_safe_delete(self, valid_article):
        assert valid_article.status == 'published'
        valid_article.delete()
        assert valid_article.is_removed is True
        with pytest.raises(ObjectDoesNotExist):
            Article.objects.get(id=valid_article.id)
        assert Article.deleted.get(id=valid_article.id)

    def test_unsafe_delete(self, valid_article):
        assert valid_article.status == 'published'
        valid_article.delete(soft=False)
        # assert valid_article.state == 'deleted'
        with pytest.raises(ObjectDoesNotExist) as e:
            Article.objects.get(id=valid_article.id)
        assert "Article matching query does not exist." in str(e.value)
        with pytest.raises(ObjectDoesNotExist) as e:
            Article.raw.get(id=valid_article.id)
        assert "Article matching query does not exist." in str(e.value)


@pytest.mark.django_db
class TestArticleUserRoles(object):
    def test_editor_doesnt_see_articles_in_admin_panel(self, editor_user):
        client = Client()
        client.force_login(editor_user)
        response = client.get("/")
        assert response.status_code == 200
        assert '/articles/' not in str(response.content)

    def test_editor_cant_go_to_articles_in_admin_panel(self, editor_user):
        client = Client()
        client.force_login(editor_user)
        response = client.get("/articles/")
        assert response.status_code == 404

    def test_admin_can_see_articles_in_admin_panel(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get("/")
        assert response.status_code == 200
        assert '/articles' in str(response.content)

    def test_admin_can_go_to_articles_in_admin_panel(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get("/articles/")
        assert response.status_code == 200


@pytest.mark.django_db
def test_article_category_translations(valid_article_category):

    valid_article_category.name = 'A'
    valid_article_category.description = 'a opis'
    valid_article_category.name_en = 'B'
    valid_article_category.description_en = 'b description'

    assert valid_article_category.name == 'A'
    assert valid_article_category.description == 'a opis'

    translation.activate('en')
    assert valid_article_category.name_i18n == 'B'
    # Check if fallback lang working
    assert valid_article_category.description_i18n == 'b description'

    translation.activate('pl')
    assert valid_article_category.name_i18n == 'A'
    assert valid_article_category.description_i18n == 'a opis'
