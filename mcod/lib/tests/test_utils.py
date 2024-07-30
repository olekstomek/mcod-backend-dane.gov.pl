import pytest
from django.utils.html import format_html

from mcod.lib.utils import escape_braces_and_format_html


class TestFormatHTML:
    """
    Tests for HTML formatting functions, specifically examining behavior when
    processing curly braces.

    This test class includes methods to test two different behaviors:
    1. The newly implemented function `escape_braces_and_format_html`,
    which is supposed to correctly escape curly braces to prevent them from
    being treated as placeholders in a formatting string.
    2. The standard Django `format_html` function, which throws exceptions
    or modifies the input text when it contains curly braces that might be
    mistaken for format specifiers.
    """

    @pytest.mark.parametrize(
        "text", ["{text", "{{ text", "test {text}", "}{", "{}", "test }} text", "text}", "<div>{text in braces}</div>"]
    )
    def test_escape_braces_and_format_html(self, text: str):
        formatted_text: str = escape_braces_and_format_html(text)
        assert formatted_text == text

    @pytest.mark.parametrize("text", ["{{ text", "test }} text"])
    def test_format_html_change_text_with_escaped_braces(self, text: str):
        assert format_html(text) != text

    @pytest.mark.parametrize("text", ["{text", "test {text}", "}{", "{}", "text}"])
    def test_format_html_raise_exc_for_unescaped_braces(self, text: str):
        with pytest.raises((KeyError, ValueError, IndexError)):
            format_html(text)
