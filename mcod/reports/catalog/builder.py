import logging
from dataclasses import dataclass
from typing import Any, Callable, List, Union

from django.conf import settings
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from mcod.datasets.models import UPDATE_FREQUENCY
from mcod.harvester.models import DataSource
from mcod.resources.models import Resource

from .lookups import DatasetLookups, OrganizationLookups, ResourceLookups

logger = logging.getLogger("mcod")

_UPDATE_FREQUENCY = dict(UPDATE_FREQUENCY)


@dataclass
class RowContext:
    resource: Any
    resource_lookups: ResourceLookups
    dataset_lookups: DatasetLookups
    organization_lookups: OrganizationLookups


CatalogCellValue = Union[str, int, float, bool]


@dataclass
class CatalogColumn:
    header: str
    extractor: Callable[[RowContext], CatalogCellValue]


class CatalogRowBuilder:

    def __init__(self, lang: str) -> None:
        self.lang = lang
        with translation.override(self.lang):
            self.columns = self._define_columns()

    def get_headers(self) -> List[str]:
        with translation.override(self.lang):
            return [str(col.header) for col in self.columns]

    def build_row(
        self,
        resource: Resource,
        resource_lookups: ResourceLookups,
        dataset_lookups: DatasetLookups,
        organization_lookups: OrganizationLookups,
    ) -> List[CatalogCellValue]:
        ctx = RowContext(
            resource=resource,
            resource_lookups=resource_lookups,
            dataset_lookups=dataset_lookups,
            organization_lookups=organization_lookups,
        )
        with translation.override(self.lang):
            return [col.extractor(ctx) for col in self.columns]

    def _define_columns(self) -> List[CatalogColumn]:
        return [
            # --- Dataset fields ---
            CatalogColumn(_("Dataset URL"), lambda ctx: ctx.resource.dataset.frontend_absolute_url),
            CatalogColumn(_("Title"), lambda ctx: ctx.resource.dataset.title_i18n),
            CatalogColumn(_("Notes"), lambda ctx: ctx.resource.dataset.notes_i18n),
            CatalogColumn(_("Tag"), lambda ctx: ctx.dataset_lookups.get_tags(ctx.resource.dataset_id, self.lang)),
            CatalogColumn(_("Category"), lambda ctx: ctx.dataset_lookups.get_categories(ctx.resource.dataset_id, self.lang)),
            CatalogColumn(_("Update frequency"), lambda ctx: _format_frequency(ctx.resource.dataset.update_frequency)),
            CatalogColumn(_("Dataset created"), lambda ctx: _fmt_datetime(ctx.resource.dataset.created)),
            CatalogColumn(_("Dataset verified"), lambda ctx: _fmt_datetime(ctx.resource.dataset.verified)),
            CatalogColumn(_("Dataset views count"), lambda ctx: ctx.dataset_lookups.get_views_count(ctx.resource.dataset_id)),
            CatalogColumn(
                _("Dataset downloads count"), lambda ctx: ctx.dataset_lookups.get_downloads_count(ctx.resource.dataset_id)
            ),
            CatalogColumn(_("Number of data"), lambda ctx: ctx.dataset_lookups.get_resource_counts(ctx.resource.dataset_id)),
            CatalogColumn(_("Terms of use"), lambda ctx: ctx.resource.dataset.formatted_condition_descriptions),
            CatalogColumn(_("License"), lambda ctx: ctx.resource.dataset.license_name or ""),
            CatalogColumn(_("source"), lambda ctx: _format_source(ctx.resource.dataset.source)),
            CatalogColumn(
                _("Dataset has high value data"), lambda ctx: _fmt_nullable_bool(ctx.resource.dataset.has_high_value_data)
            ),
            CatalogColumn(
                _("Dataset has high value data from the EC list"),
                lambda ctx: _fmt_nullable_bool(ctx.resource.dataset.has_high_value_data_from_ec_list),
            ),
            CatalogColumn(_("Dataset has dynamic data"), lambda ctx: _fmt_nullable_bool(ctx.resource.dataset.has_dynamic_data)),
            CatalogColumn(_("Dataset has research data"), lambda ctx: _fmt_nullable_bool(ctx.resource.dataset.has_research_data)),
            CatalogColumn(
                _("Dataset regions"),
                lambda ctx: ctx.dataset_lookups.get_regions(ctx.resource.dataset_id, self.lang),
            ),
            CatalogColumn(
                _("Dataset supplements (name, language, url, file size)"),
                lambda ctx: ctx.dataset_lookups.get_supplements(ctx.resource.dataset_id, self.lang),
            ),
            # --- Organization fields ---
            CatalogColumn(_("Organization URL"), lambda ctx: ctx.resource.dataset.organization.frontend_absolute_url),
            CatalogColumn(_("Institution type"), lambda ctx: ctx.resource.dataset.organization.get_institution_type_display()),
            CatalogColumn(_("Name"), lambda ctx: ctx.resource.dataset.organization.title_i18n),
            CatalogColumn(_("Abbreviation"), lambda ctx: ctx.resource.dataset.organization.abbreviation or ""),
            CatalogColumn(_("Id Institution"), lambda ctx: str(ctx.resource.dataset.organization_id)),
            CatalogColumn(_("REGON"), lambda ctx: ctx.resource.dataset.organization.regon or ""),
            CatalogColumn(_("EPUAP"), lambda ctx: ctx.resource.dataset.organization.epuap or ""),
            CatalogColumn(
                _("Address for electronic delivery"),
                lambda ctx: ctx.resource.dataset.organization.electronic_delivery_address or "",
            ),
            CatalogColumn(_("Website"), lambda ctx: ctx.resource.dataset.organization.website or ""),
            CatalogColumn(_("Organization created"), lambda ctx: _fmt_datetime(ctx.resource.dataset.organization.created)),
            CatalogColumn(_("Organization modified"), lambda ctx: _fmt_datetime(ctx.resource.dataset.organization.modified)),
            CatalogColumn(
                _("Number of datasets"),
                lambda ctx: ctx.organization_lookups.get_dataset_counts(ctx.resource.dataset.organization_id),
            ),
            CatalogColumn(
                _("Number of organization resources"),
                lambda ctx: ctx.organization_lookups.get_resource_counts(ctx.resource.dataset.organization_id),
            ),
            CatalogColumn(_("Postal code"), lambda ctx: ctx.resource.dataset.organization.postal_code or ""),
            CatalogColumn(_("City"), lambda ctx: ctx.resource.dataset.organization.city or ""),
            CatalogColumn(_("Street type"), lambda ctx: ctx.resource.dataset.organization.street_type or ""),
            CatalogColumn(_("Street"), lambda ctx: ctx.resource.dataset.organization.street or ""),
            CatalogColumn(_("Street number"), lambda ctx: ctx.resource.dataset.organization.street_number or ""),
            CatalogColumn(_("Flat number"), lambda ctx: ctx.resource.dataset.organization.flat_number or ""),
            CatalogColumn(_("Email"), lambda ctx: ctx.resource.dataset.organization.email or ""),
            CatalogColumn(_("Phone"), lambda ctx: ctx.resource.dataset.organization.tel or ""),
            # --- Resource fields ---
            CatalogColumn(_("Resource URL"), lambda ctx: ctx.resource.frontend_absolute_url),
            CatalogColumn(_("Resource title"), lambda ctx: strip_tags(ctx.resource.title_i18n)),
            CatalogColumn(_("Resource description"), lambda ctx: strip_tags(ctx.resource.description_i18n)),
            CatalogColumn(_("Resource created"), lambda ctx: _fmt_datetime(ctx.resource.created)),
            CatalogColumn(_("Data date"), lambda ctx: _fmt_date(ctx.resource.data_date)),
            CatalogColumn(_("Openness score"), lambda ctx: ctx.resource.openness_score),
            CatalogColumn(_("Type"), lambda ctx: ctx.resource.get_type_display()),
            CatalogColumn(_("File format"), lambda ctx: ctx.resource.format or ""),
            CatalogColumn(_("File size"), lambda ctx: ctx.resource_lookups.get_file_sizes(ctx.resource.pk)),
            CatalogColumn(_("Resource views count"), lambda ctx: ctx.resource_lookups.get_views_count(ctx.resource.pk)),
            CatalogColumn(_("Resource downloads count"), lambda ctx: ctx.resource_lookups.get_downloads_count(ctx.resource.pk)),
            CatalogColumn(_("Table"), lambda ctx: _fmt_yes_no(ctx.resource.has_table)),
            CatalogColumn(_("Map"), lambda ctx: _fmt_yes_no(ctx.resource.has_chart)),
            CatalogColumn(_("Chart"), lambda ctx: _fmt_yes_no(ctx.resource.has_map)),
            CatalogColumn(_("Resource has high value data"), lambda ctx: _fmt_nullable_bool(ctx.resource.has_high_value_data)),
            CatalogColumn(
                _("Resource has high value data from the EC list"),
                lambda ctx: _fmt_nullable_bool(ctx.resource.has_high_value_data_from_ec_list),
            ),
            CatalogColumn(_("Resource has dynamic data"), lambda ctx: _fmt_nullable_bool(ctx.resource.has_dynamic_data)),
            CatalogColumn(_("Resource has research data"), lambda ctx: _fmt_nullable_bool(ctx.resource.has_research_data)),
            CatalogColumn(
                _("Contains protected data list"), lambda ctx: _fmt_nullable_bool(ctx.resource.contains_protected_data)
            ),
            CatalogColumn(_("Resource regions"), lambda ctx: ctx.resource_lookups.get_regions(ctx.resource.pk, self.lang)),
            CatalogColumn(_("Download URL"), lambda ctx: self._get_download_url(ctx.resource, ctx.resource_lookups)),
            CatalogColumn(_("special signs"), lambda ctx: ctx.resource_lookups.get_signs(ctx.resource.pk, self.lang)),
            CatalogColumn(
                _("Resource supplements (name, language, url, file size)"),
                lambda ctx: ctx.resource_lookups.get_supplements(ctx.resource.pk, self.lang),
            ),
        ]

    def _get_download_url(self, resource: Resource, lookups: ResourceLookups) -> str:
        has_main_file: bool = lookups.has_main_file(resource.pk)
        is_imported: bool = bool(resource.dataset.source_id)
        if has_main_file or is_imported:
            return f"{settings.API_URL}/resources/{resource.ident}/file"
        return ""


def _format_source(source: DataSource) -> str:
    if source is None:
        return ""
    last_import: str = source.last_import_timestamp.isoformat() if source.last_import_timestamp else ""
    return (
        "{title_label}: {title}, {url_label}: {url}," " {last_import_label}: {last_import}, {frequency_label}: {frequency}"
    ).format(
        title_label=_("name"),
        title=source.title or "",
        url_label=_("url"),
        url=source.url or "",
        last_import_label=_("last import timestamp"),
        last_import=last_import,
        frequency_label=_("Update frequency"),
        frequency=source.update_frequency or "",
    )


def _fmt_datetime(dt) -> str:
    return dt.isoformat() if dt else ""


def _fmt_date(d) -> str:
    return d.isoformat() if d else ""


def _fmt_nullable_bool(value) -> str:
    if value is None:
        return _("not specified")
    return _("YES") if value else _("NO")


def _fmt_yes_no(value: bool) -> str:
    return _("YES") if value else _("NO")


def _format_frequency(update_frequency: str) -> str:
    value = _UPDATE_FREQUENCY.get(update_frequency)
    return str(value) if value else ""
