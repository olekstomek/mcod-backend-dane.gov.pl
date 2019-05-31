import pytest
from django.utils import translation

from mcod.categories.models import Category


@pytest.mark.django_db
class TestCategoryModel:

    def test_create_category(self):
        category = Category()
        category.slug = 'slug-kategorii'
        category.title = 'Tytuł'
        category.title_en = 'Title'
        category.description = 'Opis'
        assert category.full_clean() is None
        assert category.id is None
        category.save()
        assert category.id is not None
        assert Category.objects.last().slug == category.slug

    # def test_category_name_uniqnes(self, valid_category):
    #     category = Category(slug='slug-kategorii', title='Tytuł kategorii')
    #     category.slug = valid_category.slug
    #     with pytest.raises(ValidationError) as e:
    #         category.full_clean()
    #     assert "'slug':" in str(e.value)

    def test_category_translations(self, valid_category):
        assert valid_category.title == 'Tytuł kategorii'
        assert valid_category.slug == 'slug-kategorii'
        assert valid_category.description == 'Opis kategorii'

        translation.activate('en')
        assert valid_category.title_i18n == 'Category title'
        # Check if fallback lang working
        assert valid_category.description_i18n == 'Opis kategorii'

        translation.activate('pl')
        assert valid_category.title_i18n == 'Tytuł kategorii'
        assert valid_category.description_i18n == 'Opis kategorii'

    def test_category_str(self, valid_category):
        assert str(valid_category) == valid_category.title
