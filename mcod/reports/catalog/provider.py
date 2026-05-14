import logging
from dataclasses import dataclass
from typing import Dict, Iterator, List

from django.db.models import QuerySet
from more_itertools import chunked

from mcod.resources.models import Resource

from .builder import CatalogCellValue, CatalogRowBuilder
from .fetchers import (
    build_dataset_lookups,
    build_organization_lookups,
    build_resource_lookups,
    fetch_global_region_cache,
    fetch_global_special_signs_cache,
)
from .lookups import (
    DatasetLookups,
    OrganizationLookups,
    RegionGlobalCache,
    ResourceLookups,
    SpecialSignGlobalCache,
)

logger = logging.getLogger("mcod")

# Minimum size to prevent excessive database round-trips and overhead.
_MIN_CHUNK_SIZE = 1_000
# Maximum size to avoid database query limits (e.g., IN clause length) and memory issues.
_MAX_CHUNK_SIZE = 10_000
# Balanced default for optimal performance and stability.
_DEFAULT_CHUNK_SIZE = 5_000


@dataclass(frozen=True)
class TranslatedCatalogRow:
    translations: Dict[str, List[CatalogCellValue]]

    def get_for_language(self, lang: str) -> List[CatalogCellValue]:
        return self.translations.get(lang, [])


class CatalogDataProvider:

    def __init__(self, languages: List[str], chunk_size: int = _DEFAULT_CHUNK_SIZE):
        self.languages = languages

        if chunk_size < _MIN_CHUNK_SIZE:
            logger.warning(f"Catalog report | Chunk size to small. Setting chunk_size={_MIN_CHUNK_SIZE}.")
            chunk_size = _MIN_CHUNK_SIZE
        if chunk_size > _MAX_CHUNK_SIZE:
            logger.warning(f"Catalog report | Chunk size to big. Setting chunk_size={_MAX_CHUNK_SIZE}.")
            chunk_size = _MAX_CHUNK_SIZE
        self.chunk_size = chunk_size

        self.region_global_cache: RegionGlobalCache = fetch_global_region_cache(languages)
        self.special_signs_global_cache: SpecialSignGlobalCache = fetch_global_special_signs_cache(languages)
        self.dataset_lookups: DatasetLookups = build_dataset_lookups(
            languages,
            self.region_global_cache,
        )
        self.organization_lookups: OrganizationLookups = build_organization_lookups()
        self.builders: Dict[str, CatalogRowBuilder] = {lang: CatalogRowBuilder(lang) for lang in languages}

    def get_headers(self) -> Dict[str, List[str]]:
        return {lang: builder.get_headers() for lang, builder in self.builders.items()}

    def __iter__(self) -> Iterator[TranslatedCatalogRow]:
        db_stream = self.queryset.iterator(chunk_size=self.chunk_size)
        for chunk in chunked(db_stream, self.chunk_size):
            res_ids: List[int] = [r.id for r in chunk]
            resource_chunk_lookups: ResourceLookups = build_resource_lookups(
                self.languages,
                self.region_global_cache,
                self.special_signs_global_cache,
                res_ids,
            )
            for resource in chunk:
                row_data = {
                    lang: builder.build_row(resource, resource_chunk_lookups, self.dataset_lookups, self.organization_lookups)
                    for lang, builder in self.builders.items()
                }
                yield TranslatedCatalogRow(translations=row_data)

    queryset: QuerySet = (
        Resource.objects.published()
        .select_related(
            "dataset",
            "dataset__organization",
            "dataset__source",
        )
        .order_by("dataset_id", "id")
    )
