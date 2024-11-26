from enum import Enum
from typing import Any, Dict, List


class CKANPartialImportError(Enum):
    INVALID_LICENSE_ID = 1
    ORGANIZATION_IN_TRASH = 2
    DATASET_IN_TRASH = 3
    DATASET_ORG_EC_CONFLICT = 4
    DATASET_HVD_CONFLICT = 5
    RES_ORG_EC_CONFLICT = 6
    RES_HVD_CONFLICT = 7


def format_invalid_license_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = "Wartość w polu license_id spoza słownika CC"
    inner_descriptions: List[str] = [
        f"<p><strong>id zbioru danych:</strong> {error['item_id']}</p>"
        f"<p><strong>license_id:</strong> {error['license_id']}</p>"
        for error in errors_data
    ]
    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


def format_organization_in_trash_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = "<p>Instytucja znajduje się w koszu</p>"
    inner_descriptions: List[str] = [
        f"<p><strong>id zbioru danych:</strong> {error['item_id']}</p>"
        f"<p><strong>organization.title:</strong> {error['organization_title']}</p>"
        for error in errors_data
    ]
    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


def format_dataset_in_trash_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = "<p>Zbiór danych znajduje się w koszu</p>"
    inner_descriptions: List[str] = [f"<p><strong>id zbioru danych:</strong> {error['item_id']}</p>" for error in errors_data]
    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


# DATASET HVD
def format_dataset_org_hvd_ec_conflict_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = (
        "<p>Instytucja typu 'prywatna' nie może wybrać wartości true w polu "
        "'has_high_value_data_from_european_commission_list' zbioru danych.</p>"
    )
    inner_descriptions: List[str] = [f"<p><strong>id zbioru danych:</strong> {error['item_id']}</p>" for error in errors_data]
    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


def format_dataset_hvd_conflict_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = (
        "<p>Pole zbioru danych 'has_high_value_data' musi mieć wartość równą true, "
        "jeżeli pole 'has_high_value_data_from_european_commission_list' ma wartość true.</p>"
    )
    inner_descriptions: List[str] = [f"<p><strong>id zbioru danych:</strong> {error['item_id']}</p>" for error in errors_data]
    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


# RESOURCE HVD
def format_res_org_hvd_ec_conflict_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = (
        "<p>Instytucja typu 'prywatna' nie może wybrać wartości true w polu "
        "'has_high_value_data_from_european_commission_list' zasobu.</p>"
    )

    inner_descriptions: List[str] = []
    for error in errors_data:
        item_id: str = error["item_id"]
        resources_ids: List[str] = error["resources_ids"]

        inner_error_desc: str = f"<p><strong>id zbioru danych:</strong> {item_id}</p>"
        resources_desc: List[str] = [f"<p><strong>id zasobu:</strong> {resource_id}</p>" for resource_id in resources_ids]

        inner_descriptions.append(inner_error_desc + "<br>".join(resources_desc))

    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'


def format_res_hvd_conflict_error_details(errors_data: List[Dict[str, Any]]) -> str:
    error_desc = (
        "<p>Pole zasobu 'has_high_value_data' musi mieć wartość równą true, "
        "jeżeli pole 'has_high_value_data_from_european_commission_list' ma wartość true.</p>"
    )
    inner_descriptions: List[str] = []
    for error in errors_data:
        item_id: str = error["item_id"]
        resources_ids: List[str] = error["resources_ids"]

        inner_error_desc: str = f"<p><strong>id zbioru danych:</strong> {item_id}</p>"
        resources_desc: List[str] = [f"<p><strong>id zasobu:</strong> {resource_id}</p>" for resource_id in resources_ids]

        inner_descriptions.append(inner_error_desc + "<br>".join(resources_desc))

    inner_error_desc: str = "<br>".join(inner_descriptions)
    return f'{error_desc}<div class="expandable">{inner_error_desc}</div>'
