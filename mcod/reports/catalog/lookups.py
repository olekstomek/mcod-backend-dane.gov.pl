import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger("mcod")


@dataclass(frozen=True)
class RegionGlobalCache:
    labels: Dict[str, Dict[int, str]]
    default_pk: Optional[int]


@dataclass(frozen=True)
class SpecialSignGlobalCache:
    formatted_signs: Dict[str, Dict[int, str]]


@dataclass(frozen=True)
class OrganizationLookups:
    dataset_counts: Dict[int, int]
    resource_counts: Dict[int, int]

    def get_dataset_counts(self, organization_id: int) -> int:
        return self.dataset_counts.get(organization_id, 0)

    def get_resource_counts(self, organization_id: int) -> int:
        return self.resource_counts.get(organization_id, 0)


@dataclass(frozen=True)
class BaseLookups:
    views: Dict[int, int]
    downloads: Dict[int, int]
    supplements: Dict[str, Dict[int, str]]
    region_mapping: Dict[int, List[int]]
    region_cache: RegionGlobalCache

    def get_views_count(self, obj_id: int) -> int:
        return self.views.get(obj_id, 0)

    def get_downloads_count(self, obj_id: int) -> int:
        return self.downloads.get(obj_id, 0)

    def get_supplements(self, obj_id: int, language: str) -> str:
        return self.supplements.get(language, {}).get(obj_id, "")

    def get_regions(self, obj_id: int, language: str) -> str:
        region_ids = self.region_mapping.get(obj_id, [])
        default_pk = self.region_cache.default_pk

        combined_ids = set(region_ids)
        if default_pk is not None:
            combined_ids.add(default_pk)

        final_ids = sorted(list(combined_ids))
        lang_labels = self.region_cache.labels.get(language, {})
        names = [str(lang_labels.get(rid)) for rid in final_ids if lang_labels.get(rid)]

        return "; ".join(names)


@dataclass(frozen=True)
class DatasetLookups(BaseLookups):
    resource_counts: Dict[int, int]
    tags: Dict[str, Dict[int, str]]
    categories: Dict[str, Dict[int, str]]

    def get_resource_counts(self, dataset_id: int) -> int:
        return self.resource_counts.get(dataset_id, 0)

    def get_tags(self, dataset_id: int, language: str) -> str:
        return self.tags[language].get(dataset_id, "")

    def get_categories(self, dataset_id: int, language: str) -> str:
        return self.categories[language].get(dataset_id, "")


@dataclass(frozen=True)
class ResourceLookups(BaseLookups):
    file_sizes: Dict[int, str]
    signs: Dict[str, Dict[int, str]]

    def get_file_sizes(self, resource_id: int) -> str:
        return self.file_sizes.get(resource_id, "")

    def get_signs(self, resource_id: int, language: str) -> str:
        return self.signs.get(language, {}).get(resource_id, "")

    def has_main_file(self, resource_id: int) -> bool:
        return resource_id in self.file_sizes.keys()
