
import re

from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_text

from mcod.articles.models import Article
from mcod.unleash import is_enabled


def test_save_model_auto_create_slug(admin, article_category):
    obj = {
        'title': "Test with article title",
        'notes': "Tresc",
        'status': 'published',
        'category': article_category.id
    }

    client = Client()
    client.force_login(admin)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200
    assert Article.objects.last().slug == "test-with-article-title"


def test_save_model_manual_create_name(admin, article_category):
    obj = {
        'title': "Test with dataset title",
        'slug': 'manual-name',
        'notes': 'tresc',
        'status': 'published',
        'category': article_category.id
    }

    client = Client()
    client.force_login(admin)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200

    assert Article.objects.last().slug == "manual-name"


def test_save_model_given_creator_user(admin, another_admin, article_category):
    obj = {
        'title': "Test with dataset title 1",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'status': 'published',
        'category': article_category.id
    }
    obj2 = {
        'title': "Test with dataset title 2",
        'slug': 'manual-name-2',
        'notes': 'tresc',
        'app_url': "http://2.test.pl",
        'status': 'published',
        'category': article_category.id
    }

    obj3 = {
        'title': "Test with dataset title 3",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'app_url': "http://1.test.pl",
        'status': 'published',
        'category': article_category.id
    }
    # add 1 article
    client = Client()
    client.force_login(admin)
    response = client.post(reverse('admin:articles_article_add'), obj, follow=True)
    assert response.status_code == 200
    ap1 = Article.objects.last()
    assert ap1.created_by_id == admin.id

    # add 2 article
    client = Client()
    client.force_login(another_admin)
    response = client.post(reverse('admin:articles_article_add'), obj2, follow=True)
    assert response.status_code == 200
    ap2 = Article.objects.last()
    assert ap2.created_by_id == another_admin.id
    assert ap1.id != ap2.id

    # change 1 article
    client = Client()
    client.force_login(another_admin)
    response = client.post(reverse('admin:articles_article_change', args=[ap1.id]), obj3, follow=True)
    assert response.status_code == 200

    # creator of app2 should be still admin
    assert Article.objects.get(id=ap1.id).created_by_id == admin.id


def test_add_tags_to_article(admin, tag, tag_en, article, article_category):
    data = {
        'title': "Test with dataset title",
        'slug': 'test-name',
        'notes': 'tresc',
        'status': 'published',
        'category': article_category.id
    }
    if is_enabled('S18_new_tags.be'):
        data['tags_en'] = [tag_en.id]
        assert tag_en not in article.tags.all()
    else:
        data['tags'] = [tag.id]
        assert tag not in article.tags.all()

    assert article.slug != "test-name"
    client = Client()
    client.force_login(admin)
    client.post(reverse('admin:articles_article_change', args=[article.id]), data, follow=True)
    app = Article.objects.get(id=article.id)
    assert app.slug == "test-name"
    if is_enabled('S18_new_tags.be'):
        assert tag_en in article.tags.all()
    else:
        assert tag in article.tags.all()


def test_removed_articles_are_not_in_applicaiton_list(admin, article, article_category):
    client = Client()
    client.force_login(admin)
    response = client.get(reverse("admin:articles_article_changelist"))
    pattern = re.compile(r"/articles/article/\d+/change")
    result = pattern.findall(smart_text(response.content))
    assert result == [f'/articles/article/{article.id}/change']
    article.delete()
    response = client.get(reverse("admin:articles_article_changelist"))
    result = pattern.findall(smart_text(response.content))
    assert not result
