import pytest
import re
from django.test import Client
from django.urls import reverse

from mcod.articles.models import Article


@pytest.mark.django_db
def test_save_model_auto_create_slug(admin_user, valid_article_category):
    obj = {
        'title': "Test with article title",
        'notes': "Tresc",
        'status': 'published',
        'category': valid_article_category.id
    }

    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200
    assert Article.objects.last().slug == "test-with-article-title"


@pytest.mark.django_db
def test_save_model_manual_create_name(admin_user, valid_article_category):
    obj = {
        'title': "Test with dataset title",
        'slug': 'manual-name',
        'notes': 'tresc',
        'status': 'published',
        'category': valid_article_category.id
    }

    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200

    assert Article.objects.last().slug == "manual-name"


@pytest.mark.django_db
def test_save_model_given_creator_user(admin_user, admin_user2, valid_article_category):
    obj = {
        'title': "Test with dataset title 1",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'status': 'published',
        'category': valid_article_category.id
    }
    obj2 = {
        'title': "Test with dataset title 2",
        'slug': 'manual-name-2',
        'notes': 'tresc',
        'app_url': "http://2.test.pl",
        'status': 'published',
        'category': valid_article_category.id
    }

    obj3 = {
        'title': "Test with dataset title 3",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'app_url': "http://1.test.pl",
        'status': 'published',
        'category': valid_article_category.id
    }
    # add 1 article
    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200
    ap1 = Article.objects.last()
    assert ap1.created_by_id == admin_user.id

    # add 2 article
    client = Client()
    client.force_login(admin_user2)
    response = client.post(reverse('admin:articles_article_add'), obj2, follow=True)
    assert response.status_code == 200
    ap2 = Article.objects.last()
    assert ap2.created_by_id == admin_user2.id
    assert ap1.id != ap2.id

    # change 1 article
    client = Client()
    client.force_login(admin_user2)
    response = client.post(reverse('admin:articles_article_change', args=[ap1.id]), obj3, follow=True)
    assert response.status_code == 200

    # creator of app2 should be still admin_user
    assert Article.objects.get(id=ap1.id).created_by_id == admin_user.id


@pytest.mark.django_db
def test_add_tags_to_article(admin_user, valid_tag, valid_article, valid_article_category):
    obj = {
        'title': "Test with dataset title",
        'slug': 'test-name',
        'notes': 'tresc',
        'status': 'published',
        'tags': [valid_tag.id],
        'category': valid_article_category.id

    }

    assert valid_article.slug == "test-name"
    assert valid_tag not in valid_article.tags.all()
    client = Client()
    client.force_login(admin_user)
    client.post(reverse('admin:articles_article_change', args=[valid_article.id]), obj, follow=True)
    app = Article.objects.get(id=valid_article.id)
    assert app.slug == "test-name"
    assert valid_tag in app.tags.all()


@pytest.mark.django_db
def test_removed_articles_are_not_in_applicaiton_list(admin_user, valid_article, valid_article_category):
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:articles_article_changelist"))
    pattern = re.compile(r"/articles/article/\d+/change")
    result = pattern.findall(str(response.content))
    assert result == [f'/articles/article/{valid_article.id}/change']
    valid_article.delete()
    response = client.get(reverse("admin:articles_article_changelist"))
    result = pattern.findall(str(response.content))
    assert not result
