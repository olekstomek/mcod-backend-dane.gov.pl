import pytest
from django.test import override_settings
from marshmallow import ValidationError

from mcod.search.deserializers import SparqlRequestAttrs


@pytest.mark.parametrize(
    "valid_query",
    [
        # Basic SELECT
        "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }",
        # Case-insensitivity check
        "select ?s where {?s ?p ?o}",
        # Basic ASK
        "ASK WHERE { ?s ?p ?o . }",
        # Basic DESCRIBE
        "DESCRIBE <http://example.org/book/book1>",
        # Basic CONSTRUCT
        "CONSTRUCT { ?s <http://xmlns.com/foaf/0.1/name> ?name } WHERE { ?s <http://example.org/schema#name> ?name . }",
        # More complex query with filters and unions
        """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT ?name ?mbox
    WHERE {
      { ?x foaf:name ?name . }
      UNION
      { ?x foaf:mbox ?mbox . }
    }
    """,
    ],
)
def test_valid_read_only_queries_should_pass(valid_query: str):
    """
    Tests that valid, read-only SPARQL queries (SELECT, ASK, DESCRIBE, CONSTRUCT)
    pass the validation without raising an error.
    """
    # This should not raise any exception
    SparqlRequestAttrs().validate_q(valid_query)


@pytest.mark.parametrize(
    "invalid_syntax_query",
    [
        "",  # Empty string
        "   ",  # Whitespace only
        "INVALID SYNTAX",  # Not a valid query keyword
        "SELECT ?s WHERE { ?s ?p ?o ",  # Missing closing brace
        "SELEC ?s ?p ?o WHERE { ?s ?p ?o . }",  # Typo in keyword
        "SELECT ?s ?p o WHERE { ?s ?p o . }",  # Missing '?' for variable 'o'
    ],
)
def test_queries_with_invalid_syntax_should_raise_error(invalid_syntax_query: str):
    """
    Tests that malformed or syntactically incorrect SPARQL queries raise a ValidationError.
    """
    with pytest.raises(ValidationError, match="Invalid or disallowed query"):
        SparqlRequestAttrs().validate_q(invalid_syntax_query)


@pytest.mark.parametrize(
    "disallowed_query",
    [
        # Update queries
        "INSERT DATA { <urn:a> <urn:b> <urn:c> . }",
        "DELETE DATA { <urn:a> <urn:b> <urn:c> . }",
        "LOAD <http://example.org/data> INTO GRAPH <urn:g1>",
        # Graph management queries
        "CREATE SILENT GRAPH <urn:g1>",
        "DROP GRAPH <urn:g2>",
        "CLEAR DEFAULT",
    ],
)
def test_disallowed_update_queries_should_raise_error(disallowed_query: str):
    """
    Tests that disallowed SPARQL update and graph management queries
    (e.g., INSERT, DELETE, CREATE) raise a ValidationError.
    """
    with pytest.raises(ValidationError, match="Invalid or disallowed query"):
        SparqlRequestAttrs().validate_q(disallowed_query)


@override_settings(ALLOWED_SPARQL_EXTERNAL_DOMAINS=["http://allowed1.com", "allowed2.pl"])
@pytest.mark.parametrize(
    "allowed_service_query",
    [
        # Basic allowed services
        "SELECT * WHERE { SERVICE <https://allowed1.com/data> { ?s ?p ?o } }",
        "SELECT * WHERE { SERVICE <https://allowed2.pl/data> { ?s ?p ?o } }",
        # Case-insensitivity and SILENT keyword
        "select * where { service silent <https://allowed1.com/data> { ?s ?p ?o } }",
        # Multiple allowed services
        """
        SELECT * WHERE {
            SERVICE <https://allowed1.com/data> { ?s ?p ?o }
            SERVICE <https://allowed2.pl/data> { ?a ?b ?c }
        }
        """,
    ],
)
def test_queries_with_allowed_service_endpoints_should_pass(allowed_service_query: str):
    """
    Tests that queries containing SERVICE clauses with whitelisted external
    endpoints pass validation.
    """
    # This should not raise any exception
    SparqlRequestAttrs().validate_q(allowed_service_query)


@override_settings(ALLOWED_SPARQL_EXTERNAL_DOMAINS=["http://allowed1.com", "allowed2.pl"])
@pytest.mark.parametrize(
    "disallowed_site, expected_full_message",
    [
        ("https://disallowed.example.org/q", "Query references a disallowed external site: https://disallowed.example.org/q"),
        ("https://google.com", "Query references a disallowed external site: https://google.com"),
        ("http://allowed2.pl.fake.com/data", "Query references a disallowed external site: http://allowed2.pl.fake.com/data"),
        ("dev.dane.gov.pl", "Query references a disallowed external site: dev.dane.gov.pl"),
        ("this-is-not-a-valid-url", "Query references a disallowed external site: this-is-not-a-valid-url"),
        ("www-google-com", "Query references a disallowed external site: www-google-com"),
        ("dane/gov/pl", "Query references a disallowed external site: dane/gov/pl"),
    ],
)
def test_queries_with_disallowed_service_endpoints_should_raise_exact_error(disallowed_site: str, expected_full_message: str):
    """
    Tests that queries containing SERVICE clauses raise a ValidationError
    with an EXACT message match.
    """
    query = f"SELECT * WHERE {{ SERVICE <{disallowed_site}> {{ ?s ?p ?o }} }}"

    # Capture the exception object
    with pytest.raises(ValidationError) as exc_info:
        SparqlRequestAttrs().validate_q(query)

    # Assert exact string equality.
    # Django ValidationError stores messages in a list (.messages).
    assert exc_info.value.messages[0] == expected_full_message
