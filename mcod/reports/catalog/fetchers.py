from collections import defaultdict, namedtuple
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, List, Optional, Set

from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Count, F, Q, Sum
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from mcod.categories.models import Category
from mcod.core import storages
from mcod.core.storages import BaseFileSystemStorage
from mcod.core.utils import sizeof_fmt
from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.datasets.models import Dataset, Supplement as DatasetSupplement
from mcod.regions.models import Region, ResourceRegion
from mcod.resources.models import Resource, ResourceFile, Supplement as ResourceSupplement
from mcod.special_signs.models import SpecialSign
from mcod.tags.models import Tag

from .lookups import (
    DatasetLookups,
    OrganizationLookups,
    RegionGlobalCache,
    ResourceLookups,
    SpecialSignGlobalCache,
)

_DATASET_PUBLISHED_FILTER_Q = Q(
    dataset__status="published",
    dataset__is_removed=False,
    dataset__is_permanently_removed=False,
)

_RESOURCE_PUBLISHED_FILTER_Q = Q(
    resource__status="published",
    resource__is_removed=False,
    resource__is_permanently_removed=False,
)


def build_organization_lookups() -> OrganizationLookups:
    return OrganizationLookups(
        dataset_counts=fetch_organizations_datasets_count(),
        resource_counts=fetch_organizations_resources_count(),
    )


def build_dataset_lookups(
    languages: List[str],
    regions_cache: RegionGlobalCache,
) -> DatasetLookups:
    return DatasetLookups(
        views=fetch_datasets_views(),
        downloads=fetch_datasets_downloads(),
        resource_counts=fetch_datasets_resources_count(),
        tags=fetch_datasets_tags(languages),
        categories=fetch_datasets_categories(languages),
        region_cache=regions_cache,
        region_mapping=fetch_datasets_regions_mapping(),
        supplements=fetch_datasets_supplements(languages),
    )


def build_resource_lookups(
    languages: List[str],
    regions_cache: RegionGlobalCache,
    special_signs_cache: SpecialSignGlobalCache,
    resource_ids: Optional[List[int]] = None,
) -> ResourceLookups:
    return ResourceLookups(
        views=fetch_resources_views(resource_ids),
        downloads=fetch_resources_downloads(resource_ids),
        file_sizes=fetch_resources_files_sizes(resource_ids),
        supplements=fetch_resources_supplements(languages, resource_ids),
        signs=fetch_resources_special_signs(languages, special_signs_cache, resource_ids),
        region_mapping=fetch_resources_regions_mapping(resource_ids),
        region_cache=regions_cache,
    )


def fetch_organizations_datasets_count():
    return dict(
        Dataset.objects.filter(status="published")
        .values("organization_id")
        .annotate(count=Count("id"))
        .values_list("organization_id", "count")
    )


def fetch_organizations_resources_count():
    return dict(
        Resource.objects.published()
        .filter(_DATASET_PUBLISHED_FILTER_Q)
        .values("dataset__organization_id")
        .annotate(count=Count("id"))
        .values_list("dataset__organization_id", "count")
    )


def fetch_datasets_views():
    return dict(
        ResourceViewCounter.objects.values("resource__dataset_id")
        .annotate(total=Sum("count"))
        .values_list("resource__dataset_id", "total")
    )


def fetch_datasets_downloads():
    return dict(
        ResourceDownloadCounter.objects.values("resource__dataset_id")
        .annotate(total=Sum("count"))
        .values_list("resource__dataset_id", "total")
    )


def fetch_datasets_resources_count():
    return dict(Resource.objects.published().values("dataset_id").annotate(count=Count("id")).values_list("dataset_id", "count"))


def fetch_datasets_tags(languages: List[str]) -> Dict[str, Dict[int, str]]:
    dataset_tags = {lang: {} for lang in languages}
    results = (
        Tag.objects.filter(_DATASET_PUBLISHED_FILTER_Q)
        .filter(language__in=languages)
        .values("language", ds_id=F("dataset__id"))
        .annotate(tag_list=StringAgg("name", delimiter=", ", ordering="name"))
    )
    for item in results:
        dataset_tags[item["language"]][item["ds_id"]] = item["tag_list"]
    return dataset_tags


def fetch_datasets_categories(languages: List[str]) -> Dict[str, Dict[int, str]]:
    cat_titles: Dict[int, Dict[str, str]] = {
        cat.pk: {lang: (getattr(cat, f"title_{lang}") or "") for lang in languages} for cat in Category.objects.all()
    }
    entries = Dataset.objects.filter(status="published").values_list("pk", "categories__pk").order_by("pk", "categories__pk")
    result = {lang: {} for lang in languages}
    for ds_id, group in groupby(entries, key=itemgetter(0)):
        category_ids = [item[1] for item in group if item[1] is not None]
        if not category_ids:
            continue
        for lang in languages:
            labels = [cat_titles[cid][lang] for cid in category_ids if cid in cat_titles]
            result[lang][ds_id] = ", ".join(filter(None, labels))

    return result


def fetch_datasets_regions(languages: List[str]) -> Dict[str, Any]:
    default_lang = getattr(settings, "LANGUAGE_CODE", "pl")
    raw_default_id = getattr(settings, "DEFAULT_REGION_ID", None)
    default_region_str_id = str(raw_default_id) if raw_default_id is not None else None

    needed_langs = list(set(languages) | {default_lang})
    label_fields = [f"hierarchy_label_{lang}" for lang in needed_langs]
    regions_query = Region.objects.values("pk", "region_id", *label_fields)

    region_labels = {lang: {} for lang in languages}
    default_pk = None

    for row in regions_query:
        pk = row["pk"]
        if str(row["region_id"]) == default_region_str_id:
            default_pk = pk

        for lang in languages:
            col = f"hierarchy_label_{lang}"
            fallback_col = f"hierarchy_label_{default_lang}"
            region_labels[lang][pk] = row.get(col) or row.get(fallback_col) or ""

    ds_entries = (
        ResourceRegion.objects.filter(_RESOURCE_PUBLISHED_FILTER_Q).values_list("resource__dataset_id", "region_id").distinct()
    )

    ds_region_sets: Dict[int, Set[int]] = defaultdict(set)
    for ds_id, region_id_fk in ds_entries:
        ds_region_sets[ds_id].add(region_id_fk)

    return {
        "labels": region_labels,
        "dataset_ids": {ds_id: sorted(list(rids)) for ds_id, rids in ds_region_sets.items()},
        "default_pk": default_pk,
    }


def fetch_datasets_supplements(languages: List[str]) -> Dict[str, Dict[int, str]]:
    ds_qs = DatasetSupplement.objects.filter(_DATASET_PUBLISHED_FILTER_Q)
    dataset_to_supplements: Dict[str, Dict[int, str]] = defaultdict(dict)
    for lang in languages:
        with translation.override(lang):
            for supplement in ds_qs.iterator(chunk_size=20_000):
                dataset_to_supplements[lang][supplement.dataset_id] = supplement.name_csv
    return dataset_to_supplements


def fetch_resources_views(resource_ids: Optional[List[int]] = None) -> Dict[int, int]:
    views_qs = ResourceViewCounter.objects.all()
    if resource_ids is not None:
        views_qs = views_qs.filter(resource_id__in=resource_ids)
    return dict(views_qs.values("resource_id").annotate(total=Sum("count")).values_list("resource_id", "total"))


def fetch_resources_downloads(resource_ids: Optional[List[int]] = None) -> Dict[int, int]:
    downloads_qs = ResourceDownloadCounter.objects.all()
    if resource_ids is not None:
        downloads_qs = downloads_qs.filter(resource_id__in=resource_ids)
    return dict(downloads_qs.values("resource_id").annotate(total=Sum("count")).values_list("resource_id", "total"))


def fetch_resources_files_sizes(resource_ids: Optional[List[int]] = None) -> Dict[int, str]:
    storage: BaseFileSystemStorage = storages.get_storage("resources")
    main_files_qs = ResourceFile.objects.filter(is_main=True)
    if resource_ids is not None:
        main_files_qs = main_files_qs.filter(resource_id__in=resource_ids)

    main_files_qs = main_files_qs.values_list("resource_id", "file")

    def get_file_size(res_file_name: str) -> str:
        try:
            size: int = storage.size(res_file_name)
        except Exception:
            return ""
        return sizeof_fmt(size) if size else ""

    res_id_to_file_size: Dict[int, str] = {resource_id: get_file_size(file_name) for resource_id, file_name in main_files_qs}
    return res_id_to_file_size


def fetch_resources_supplements(
    languages: List[str],
    resource_ids: Optional[List[int]] = None,
) -> Dict[str, Dict[int, str]]:
    rs_qs = ResourceSupplement.objects.all()
    if resource_ids is not None:
        rs_qs = rs_qs.filter(resource_id__in=resource_ids)
    rs_qs = rs_qs.filter(_RESOURCE_PUBLISHED_FILTER_Q)
    resources_to_supplements: Dict[str, Dict[int, str]] = defaultdict(dict)
    for lang in languages:
        with translation.override(lang):
            for supplement in rs_qs.iterator(chunk_size=20_000):
                resources_to_supplements[lang][supplement.resource_id] = supplement.name_csv
    return resources_to_supplements


def fetch_global_region_cache(languages: List[str]) -> RegionGlobalCache:
    default_lang: str = settings.LANGUAGE_CODE
    raw_default_id: int = settings.DEFAULT_REGION_ID
    default_region_str_id = str(raw_default_id) if raw_default_id is not None else None

    needed_langs = list(set(languages) | {default_lang})
    label_fields = [f"hierarchy_label_{lang}" for lang in needed_langs]
    regions_query = Region.objects.values("pk", "region_id", *label_fields)

    region_labels = {lang: {} for lang in languages}
    default_pk = None

    for row in regions_query:
        pk = row["pk"]
        if str(row.get("region_id")) == default_region_str_id:
            default_pk = pk

        for lang in languages:
            col = f"hierarchy_label_{lang}"
            fallback_col = f"hierarchy_label_{default_lang}"
            region_labels[lang][pk] = row.get(col) or row.get(fallback_col) or ""

    return RegionGlobalCache(labels=region_labels, default_pk=default_pk)


def fetch_resources_regions_mapping(
    resource_ids: Optional[List[int]] = None,
) -> Dict[int, List[int]]:
    res_entries_qs = ResourceRegion.objects.filter(_RESOURCE_PUBLISHED_FILTER_Q)

    if resource_ids is not None:
        res_entries_qs = res_entries_qs.filter(resource_id__in=resource_ids)

    res_entries = res_entries_qs.values_list("resource_id", "region_id").distinct()

    res_region_sets: Dict[int, Set[int]] = defaultdict(set)
    for res_id, region_id_fk in res_entries:
        if res_id is not None:
            res_region_sets[res_id].add(region_id_fk)

    return {res_id: sorted(list(rids)) for res_id, rids in res_region_sets.items()}


def fetch_datasets_regions_mapping() -> Dict[int, List[int]]:
    ds_entries = (
        ResourceRegion.objects.filter(_RESOURCE_PUBLISHED_FILTER_Q).values_list("resource__dataset_id", "region_id").distinct()
    )

    ds_region_sets: Dict[int, Set[int]] = defaultdict(set)
    for ds_id, region_id_fk in ds_entries:
        ds_region_sets[ds_id].add(region_id_fk)

    return {ds_id: sorted(list(rids)) for ds_id, rids in ds_region_sets.items()}


LocalizedLabels = namedtuple("LocalizedLabels", ["name", "symbol", "desc"])


def _get_labels_for_lang(lang: str) -> LocalizedLabels:
    with translation.override(lang):
        return LocalizedLabels(
            name=str(_("name")),
            symbol=str(_("symbol")),
            desc=str(_("description")),
        )


def _get_localized_labels_map(languages: List[str]) -> Dict[str, LocalizedLabels]:
    """
    Build a mapping of language codes to their respective LocalizedLabels.
    """
    return {lang: _get_labels_for_lang(lang) for lang in languages}


def _format_sign_line(sign_data: Dict[str, Any], lang: str, labels: LocalizedLabels) -> str:
    """
    Combine raw database data with localized labels into a single formatted string.
    """
    name = sign_data.get(f"name_{lang}") or ""
    symbol = sign_data.get("symbol") or ""
    desc = sign_data.get(f"description_{lang}") or ""

    return f'{labels.name}: {name}, {labels.symbol}: "{symbol}", {labels.desc}: {desc}'


def fetch_global_special_signs_cache(languages: List[str]) -> SpecialSignGlobalCache:
    """
    Pre-format all special signs for all supported languages and store them in a cache object.
    """
    labels_map = _get_localized_labels_map(languages)

    # Prepare list of fields to fetch from the database
    fields = ["id", "symbol"]
    for lang in languages:
        fields.extend([f"name_{lang}", f"description_{lang}"])

    formatted_signs: Dict[str, Dict[int, str]] = defaultdict(dict)

    # Fetch all signs and process them into the cache structure
    for sign in SpecialSign.objects.values(*fields):
        sign_id = sign["id"]
        for lang in languages:
            formatted_signs[lang][sign_id] = _format_sign_line(sign, lang, labels_map[lang])

    return SpecialSignGlobalCache(formatted_signs=formatted_signs)


def fetch_resources_special_signs(
    languages: List[str],
    special_signs_cache: SpecialSignGlobalCache,
    resource_ids: Optional[List[int]] = None,
) -> Dict[str, Dict[int, str]]:
    """
    Map resources to their assigned special signs and return joined formatted strings per language.
    Only resources that actually have special signs are included in the result to optimize memory.
    """
    # 1. Fetch relations from the through-table for the requested batch of resources
    entries_qs = Resource.special_signs.through.objects.all()
    if resource_ids is not None:
        entries_qs = entries_qs.filter(resource_id__in=resource_ids)

    # 2. Group sign IDs by resource ID
    res_to_sign_ids = defaultdict(list)
    ordered_entries = entries_qs.values_list("resource_id", "specialsign_id").order_by("resource_id", "specialsign_id")
    for res_id, sign_id in ordered_entries:
        res_to_sign_ids[res_id].append(sign_id)

    # 3. Build the final dictionary ONLY for resources that have associated signs
    result: Dict[str, Dict[int, str]] = defaultdict(dict)
    cache: Dict[str, Dict[int, str]] = special_signs_cache.formatted_signs

    for res_id, sign_ids in res_to_sign_ids.items():
        for lang in languages:
            # Retrieve pre-formatted strings from the global cache
            lines = [cache[lang][sid] for sid in sign_ids if sid in cache[lang]]

            # Populate the result only if there are actual signs for this language
            if lines:
                result[lang][res_id] = ", ".join(lines)

    return result
