from typing import Dict, List, Type

import pytest
from django.db.models import Model, QuerySet
from factory.django import DjangoModelFactory

from mcod.core.db.querysets import QuerySetDTO
from mcod.datasets.factories import DatasetFactory
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.factories import ResourceFactory
from mcod.schedules.factories import UserScheduleItemFactory
from mcod.showcases.factories import ShowcaseProposalFactory
from mcod.suggestions.factories import DatasetSubmissionFactory
from mcod.users.factories import UserFactory


class TestQuerySetDTO:
    @pytest.mark.parametrize(
        "factory_class",
        (
            ResourceFactory,
            DatasetFactory,
            UserFactory,
            OrganizationFactory,
            DatasetSubmissionFactory,
            UserScheduleItemFactory,
            DatasetSubmissionFactory,
            ShowcaseProposalFactory,
        ),
    )
    def test_queryset_serialization_roundtrip(self, factory_class: Type[DjangoModelFactory]):
        # GIVEN
        db_model_class: Type[Model] = factory_class._meta.model
        assert db_model_class.objects.all().count() == 0
        factory_class.create_batch(10)
        assert db_model_class.objects.all().count() == 10
        qs: QuerySet = db_model_class.objects.filter(pk__gt=2).order_by("-pk")
        original_query_str: str = str(qs.query)
        original_qs_items: List[Model] = list(qs)

        # WHEN
        qs_dto = QuerySetDTO.from_queryset(qs)
        restored_qs: QuerySet = qs_dto.to_queryset()
        qs_dto_dict: Dict = qs_dto.asdict()
        restored_from_dict: QuerySet = QuerySetDTO(**qs_dto_dict).to_queryset()

        # THEN
        assert str(restored_qs.query) == original_query_str
        assert str(restored_from_dict.query) == original_query_str
        assert list(restored_qs) == original_qs_items
        assert list(restored_from_dict) == original_qs_items
