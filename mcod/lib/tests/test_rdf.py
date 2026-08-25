from django.test import SimpleTestCase

from mcod.lib.rdf.store import get_sparql_store


class SparqlStoreTest(SimpleTestCase):

    def test_update_and_select(self):
        """Check if a triple can be added and read from the sparql store."""

        # Given
        update_store = get_sparql_store()
        query_store = get_sparql_store(readonly=True)

        # When
        update_store.update("DROP GRAPH <urn:test:graph>")
        update_store.update("INSERT DATA { GRAPH <urn:test:graph> { <urn:x> <urn:y> <urn:z> } }")

        # Then
        rows = list(
            query_store.query(
                """
                SELECT ?s ?p ?o
                FROM NAMED <urn:test:graph>
                WHERE { GRAPH <urn:test:graph> { ?s ?p ?o } }
            """
            )
        )
        self.assertEqual(len(rows), 1)
        s, p, o = rows[0]
        self.assertEqual(s.n3(), "<urn:x>")
        self.assertEqual(p.n3(), "<urn:y>")
        self.assertEqual(o.n3(), "<urn:z>")
