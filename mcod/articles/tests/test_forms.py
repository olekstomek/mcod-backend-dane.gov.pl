import pytest

from mcod.articles.forms import ArticleForm
from mcod.articles.models import Article


class TestArticleFormValidity:
    def test_article_form_add_tag(self, tag, tag_pl, article_category):
        data = {
            'title': "Article with tag",
            'slug': "article-with-tag",
            'app_url': "http://test.pl",
            'notes': 'tresc',
            'status': 'published',
            'category': article_category.id,
            'tags_pl': [tag_pl.id],
        }
        form = ArticleForm(data=data)
        assert form.is_valid() is True
        form.save()
        assert tag_pl in Article.objects.last().tags.all()

    @pytest.mark.parametrize(
        'title, slug, notes, author, license_id, status, category, validity',
        [
            # correct scenarios
            ("Article published", "slug", "content", None, None, "published", 1, True),
            ("Article draft", "slug", "content", None, None, "draft", 1, True),
            # incorrect scenarios
            (None, "withot-title", "content", None, None, "published", 1, False),
            ("Without slug", None, None, None, None, "published", 1, False),
            ("Without notes", "article-title", None, None, None, "published", 1, False),
            ("Wrong", "article", "status", None, None, "value", 1, False),
            ("Wrong", "article", "author", "a" * 51, None, "length", 1, False),
        ])
    def test_article_form_validity(self, title, slug, notes, author, license_id, status, category, validity,
                                   article_category):
        form = ArticleForm(data={
            'title': title,
            'slug': slug,
            'notes': notes,
            'author': author,
            'license_id': license_id,
            'status': status,
            'category': article_category.id
        })
        assert form.is_valid() is validity
        if validity:
            form.save()
            assert Article.objects.last().slug == slug
