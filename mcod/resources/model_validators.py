from xml.dom.minidom import parseString

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pyexpat import ExpatError

from mcod.unleash import is_enabled


def illegal_character_validator(value: str) -> None:
    """
    Validate whether the input contains illegal characters within a specific format.
    Basically it's a validator for xml creation files. When illegal characters
    occurs, then task create_xml_metadata_files will fail.

    Args:
    - value (str): The string to be validated for illegal characters.

    Raises:
    - ValidationError: If the input contains illegal characters.

    Note:
    This function wraps the input string in a specified format
    (for example "<description>...</description>") and checks if it can be parsed without
    raising an exception due to illegal characters.
    """
    data = f"<data>{value}</data>"
    if is_enabled("S60_fix_for_task_creating_xml_and_csv_metadata_files.be"):
        try:
            parseString(data)
        except ExpatError:
            raise ValidationError(
                _(
                    "Given text contains illegal character. "
                    "Please revalidate provided data."
                )
            )
