"""
Generates a report of discrepancies between XML DataSource and Resources.
"""

import csv
import sys
from contextlib import contextmanager
from datetime import date
from functools import lru_cache
from logging import getLogger
from pathlib import Path
from typing import IO, Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

from django.core.management import BaseCommand
from django.db.models import BooleanField, Case, F, QuerySet, Value, When

from mcod.harvester.utils import fetch_xml_data
from mcod.resources.models import Resource

DASH = "-"

logger = getLogger("mcod")

_field_names_common = (
    "organization_id",
    "organization_title",
    "organization_type",
    "dataset_id",
    "dataset_title",
    "dataset_is_active",
    "resource_id",
    "resource_title",
    "resource_ext_ident",
    "resource_data_date",
)
FIELD_NAMES_DB = (
    *_field_names_common,
    # non report
    "xml_url",
    "dataset_ext_ident",
)
FIELD_NAMES_REPORT = (
    *_field_names_common,
    "remote_data_date",
    "comment",
    "dates_differ",
)


def find_resources(
    not_newer_than: date,
    offset: int = 0,
    limit: int = 0,
    include_trashed: bool = True,
    include_inactive: bool = True,
    field_names: Iterable[str] = FIELD_NAMES_DB,
) -> QuerySet:
    if offset < 0 or (limit < 0 and limit != -1):
        raise ValueError("unsupported offset and limit")
    if include_trashed:
        query = Resource.raw
    else:
        query = Resource.objects
    query = query.filter(
        created__lte=not_newer_than,
        dataset__source__source_type="xml",
    ).exclude(dataset__source__xml_url="")
    if not include_inactive:
        query = query.filter(dataset__source__status="active")
    query = query.order_by(
        "dataset__source_id",
        "dataset_id",
        "id",
    )
    dataset_is_active_expr = Case(
        When(dataset__source__status="active", then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    )
    query = query.annotate(
        organization_id=F("dataset__organization__id"),
        organization_title=F("dataset__organization__title"),
        organization_type=F("dataset__organization__institution_type"),
        dataset_title=F("dataset__title"),
        dataset_is_active=dataset_is_active_expr,
        resource_id=F("id"),
        resource_title=F("title"),
        resource_ext_ident=F("ext_ident"),
        resource_data_date=F("data_date"),
        xml_url=F("dataset__source__xml_url"),
        dataset_ext_ident=F("dataset__ext_ident"),
    ).values(*field_names)
    if offset > 0:
        query = query[offset:]
    if limit > 0:
        query = query[:limit]
    return query


@lru_cache(maxsize=100)
def fetch_remote_data_date(
    xml_url: str,
) -> Union[List[Tuple[str, str, Optional[date]]], Exception]:
    """
    Returns:
        dataset_ext_ident, resource_ext_ident, data_date
        or Exception
    Raises: Nothing
    """
    try:
        remote_data = fetch_xml_data(xml_url)
    except Exception as e:
        logger.error(f"Can't get {xml_url}", exc_info=True)
        return e
    try:
        result = list(_unpack_xml_data(remote_data))
    except Exception as e:
        logger.error(f"Can't parse data from {xml_url}")
        return e
    return result


def _unpack_xml_data(
    xml_as_dict: List[Dict],
) -> Generator[Tuple[str, str, Optional[date]], None, None]:
    """Yields a tuple of (dataset's extident, resource extident, data date)"""
    for dataset in xml_as_dict:
        dataset_ext_ident = dataset["extIdent"]
        for resource in dataset["resources"]["resource"]:
            resource_ext_ident = resource["extIdent"]
            resource_data_date = resource.get("dataDate")
            yield (
                dataset_ext_ident,
                resource_ext_ident,
                date.fromisoformat(resource_data_date) if resource_data_date else None,
            )


class FlushingDictWriter(csv.DictWriter):
    """Wrapper over CSV to force flushing to file after each row.
    The goal is to prevent data loss if a Pod dies.
    """

    _flushable: Optional[IO] = None

    def __init__(self, f, *args, **kwargs):
        if hasattr(f, "flush"):  # hack: csv interface is untyped here and so is this class
            self._flushable = f
        super().__init__(f, *args, **kwargs)

    def writerow(self, rowdict: dict):
        rv = super().writerow(rowdict)
        if self._flushable:
            self._flushable.flush()
        return rv


@contextmanager
def open_csv(
    report_location: Union[str, Path],
) -> Generator[csv.DictWriter, None, None]:
    if report_location == "-":
        filelike = sys.stdout
        closing = False
    else:
        filelike = open(report_location, "w")
        closing = True
    writer = FlushingDictWriter(
        filelike,
        FIELD_NAMES_REPORT,
        extrasaction="ignore",
    )
    writer.writeheader()
    yield writer
    if closing:
        filelike.close()


def main(
    report_location: str,
    dry_run: bool,
    resources_not_newer_than: date,
    offset: int,
    limit: int,
):
    """
    Open CSV, write header, iterate over resources getting the xml.
    xml results are cached.
    """
    resources = find_resources(resources_not_newer_than, offset, limit)
    with open_csv(report_location) as writer:
        for resource in resources:
            resource: dict
            xml_url = resource["xml_url"]
            if dry_run:
                comment = "dry run"
                remote_data_date = None
            else:
                comment, remote_data_date = _fetch_single_row(resource, xml_url)
            resource["comment"] = comment
            resource["remote_data_date"] = remote_data_date
            resource["dates_differ"] = not (remote_data_date == resource["resource_data_date"])
            writer.writerow(resource)


def _fetch_single_row(
    resource: dict,
    xml_url: str,
) -> Tuple[str, str]:
    remote_result = fetch_remote_data_date(xml_url)
    if isinstance(remote_result, Exception):
        comment = "Error " + repr(remote_result)
        remote_data_date = None
    else:
        comment, remote_data_date = _match_single_row(remote_result, resource)
    return comment, remote_data_date


def _match_single_row(
    remote_result: List[Tuple[str, str, Optional[date]]],
    resource: Dict[str, Any],
) -> Tuple[str, Union[str, Optional[date]]]:
    """
    Args:
        remote_result: list of datafields from remote xml
        resource: Row from the queryset on Resources, dict
    Returns: comment, remote_data_date (in ISO-8601)
    """
    comment = "extIdent not found"
    remote_data_date = None
    for dataset_ext_ident, resource_ext_ident, data_date in remote_result:
        dm = dataset_ext_ident == resource["dataset_ext_ident"]
        rm = resource_ext_ident == resource["resource_ext_ident"]
        if dm and rm:
            comment = DASH
            remote_data_date = data_date
            return comment, remote_data_date
    return comment, remote_data_date


class Command(BaseCommand):
    help = "Generate report for Resource.data_date for XML-Harvested resources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--report-location",
            type=str,
            help="Path to the resulting report, special value of `-` means stdout.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Do not fetch remote XMLs - remote data will be blanked out.",
        )
        parser.add_argument(
            "--resources-not-newer-than",
            default=date.today().isoformat(),
            type=str,
            help="Cutoff date, include resources with created lower than of equal to this value.",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Add offset to the queryset. Notice - we query Resources so this may cross Datasets or Organization boundaries.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Number of resources to process. By default will process all of them. n<0 ignored.",
        )

    def handle(self, *args, **options):
        report_location: str = options["report_location"]
        dry_run: bool = options["dry_run"]
        resources_not_newer_than: date = date.fromisoformat(options["resources_not_newer_than"])
        offset: int = options["offset"]
        limit: int = options["limit"]
        main(report_location, dry_run, resources_not_newer_than, offset, limit)
