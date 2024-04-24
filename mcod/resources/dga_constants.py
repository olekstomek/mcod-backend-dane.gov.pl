from typing import List

from mcod.organizations.models import Organization

DGA_RESOURCE_EXTENSIONS: List[str] = ["xlsx", "xls", "csv"]
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
NOT_ALLOWED_DGA_INSTITUTIONS: List[str] = [
    Organization.INSTITUTION_TYPE_PRIVATE,
    Organization.INSTITUTION_TYPE_OTHER,
]
SAVE_CONFIRMATION_FIELD: str = "confirm_save"
