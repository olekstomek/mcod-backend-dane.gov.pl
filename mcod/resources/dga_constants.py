from typing import List

from mcod.organizations.models import Organization

DGA_RESOURCE_EXTENSIONS: List[str] = ["xlsx", "xls", "csv"]

# A single DGA resource and the aggregated Main DGA dataset do not have the
# same schema or validation requirements.
#
# DGA_COLUMNS describe the structure of an individual DGA resource.
# MAIN_DGA_REQUIRED_SOURCE_COLUMNS describe the fields required from a source
# resource to participate in Main DGA aggregation.
# MAIN_DGA_COLUMNS describe the structure of the final aggregated Main DGA
# dataset.
#
# The lists currently overlap, but they intentionally remain separate because
# their responsibilities are different.

MAIN_DGA_COLUMNS: List[str] = [
    "Nazwa dysponenta zasobu",
    "Zasób chronionych danych",
    "Format danych",
    "Rozmiar danych",
]

MAIN_DGA_REQUIRED_SOURCE_COLUMNS: List[str] = [
    "Zasób chronionych danych",
    "Format danych",
    "Rozmiar danych",
]


DGA_COLUMNS: List[str] = [
    "Lp.",
    "Zasób chronionych danych",
    "Format danych",
    "Rozmiar danych",
    "Warunki ponownego wykorzystywania",
]
ALLOWED_DGA_INSTITUTIONS: List[str] = [
    Organization.INSTITUTION_TYPE_LOCAL,
    Organization.INSTITUTION_TYPE_STATE,
]
ALLOWED_INSTITUTIONS_TO_USE_HIGH_VALUE_DATA_FROM_EC_LIST: List[str] = [
    Organization.INSTITUTION_TYPE_LOCAL,
    Organization.INSTITUTION_TYPE_STATE,
    Organization.INSTITUTION_TYPE_OTHER,
]
SAVE_CONFIRMATION_FIELD: str = "confirm_save"
