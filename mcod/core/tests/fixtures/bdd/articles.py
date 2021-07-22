from pytest_bdd import given, then
from pytest_bdd import parsers

from mcod.articles.factories import ArticleFactory, ArticleCategoryFactory
from mcod.datasets.factories import DatasetFactory


@given(parsers.parse('add dataset with id {dataset_id:d} to article with id {article_id:d}'))
def add_dataset_to_article(dataset_id, article_id):
    instance = ArticleFactory._meta.model.objects.get(pk=article_id)
    dataset_instance = DatasetFactory(pk=dataset_id)
    instance.datasets.add(dataset_instance)


@given(parsers.parse('remove dataset with id {dataset_id:d} from article with id {article_id:d}'))
def remove_dataset_from_article_with_id(dataset_id, article_id):
    dataset_instance = DatasetFactory._meta.model.objects.get(pk=dataset_id)
    instance = ArticleFactory._meta.model.objects.get(pk=article_id)
    instance.datasets.remove(dataset_instance)


@given(parsers.parse('clear datasets from article with id {article_id:d}'))
def clear_dataset_from_article_with_id(article_id):
    instance = ArticleFactory._meta.model.objects.get(pk=article_id)
    instance.datasets.clear()


# Depricated fixtures:
@given(parsers.parse('article category'))
def article_category():
    _cat = ArticleCategoryFactory.create()
    return _cat


@given(parsers.parse('article category with id {category_id:d}'))
def article_category_with_id(category_id):
    return ArticleCategoryFactory.create(
        id=category_id,
        name='Article Category {}'.format(category_id),
    )


@given(parsers.parse('article'))
def article():
    _article = ArticleFactory.create()
    return _article


@given(parsers.parse('article with datasets'))
def article_with_datasets():
    _article = ArticleFactory.create(title='Article with datasets')
    DatasetFactory.create_batch(2, articles=(_article,))
    return _article


@given(parsers.parse('removed article'))
def removed_article():
    _article = ArticleFactory.create(is_removed=True, title='Removed article')
    return _article


@given(parsers.parse('second article with id {article_id:d}'))
def second_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Second Article {}'.format(article_id))
    return _article


@given(parsers.parse('another article with id {article_id:d}'))
def another_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Another Article {}'.format(article_id))
    return _article


@given(parsers.parse('third article with id {article_id:d}'))
def third_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Another Article {}'.format(article_id))
    return _article


@given(parsers.parse('fourth article with id {article_id:d}'))
def fourth_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Another Article {}'.format(article_id))
    return _article


@given(parsers.parse('article with id {article_id:d} with {num:d} datasets'))
def article_with_id_with_datasets(article_id, num):
    _article = ArticleFactory.create(id=article_id, title='Article {} with datasets'.format(article_id))
    DatasetFactory.create_batch(num, articles=(_article,))
    return _article


@given(parsers.parse('draft article with id {article_id:d}'))
def draft_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Draft article {}'.format(article_id), status='draft')
    return _article


@given(parsers.parse('removed article with id {article_id:d}'))
def removed_article_with_id(article_id):
    _article = ArticleFactory.create(id=article_id, title='Removed article {}'.format(article_id), is_removed=True)
    return _article


@given(parsers.parse('3 articles'))
def articles():
    return ArticleFactory.create_batch(3)


@given(parsers.parse('{article_count:d} articles'))
def x_articles(article_count):
    _num = article_count or 3
    return ArticleFactory.create_batch(_num)


@then(parsers.parse('article with title {article_title} has tag with id {tag_id:d}'))
def article_with_title_has_tag_with_id(article_title, tag_id):
    article = ArticleFactory._meta.model.objects.get(title=article_title)
    assert tag_id in article.tags.values_list('id', flat=True)
