from django import VERSION
from django.utils.html import format_html


def is_django_ver_lt(major=2, minor=2):
    return VERSION[0] < major or (VERSION[0] == major and VERSION[1] < minor)


def escape_braces_and_format_html(text: str) -> str:
    """
    Escapes curly braces in the given text and formats it for safe HTML
    display.

    This function ensures that any literal curly braces in the `text` are not
    treated as placeholders in string formatting operations, which could
    otherwise lead to errors if `format_html` tries to insert values where
    none are intended.

    Parameters:
    - text (str): The text to be formatted.

    Returns:
    - str: The HTML-safe formatted text with escaped braces.
    """
    return format_html(text.replace("{", "{{").replace("}", "}}"))
