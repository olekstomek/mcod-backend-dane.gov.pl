from django.utils.translation import override

from mcod.organizations.factories import OrganizationFactory


def test_translated_slug_is_i18n_field():
    organisation = OrganizationFactory.build(slug="slug-in-polish", slug_en="slug-in-english")

    assert hasattr(organisation, "slug_en")
    assert organisation.slug == "slug-in-polish"
    assert organisation.slug_en == "slug-in-english"
    assert organisation.slug_i18n == "slug-in-polish"

    with override("en"):
        assert organisation.slug_i18n == "slug-in-english"
