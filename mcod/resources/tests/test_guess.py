from mcod.resources import guess


class TestGuess(object):
    def test_csv(self, file_csv):
        assert guess._csv(file_csv.name, 'utf-8') == 'csv'
        assert guess._csv(file_csv.name, None) == 'csv'
        assert guess._csv(open(file_csv.name, 'rb'), None) == 'csv'

    def test_xml(self, file_xml):
        assert guess._xml(file_xml.name, 'utf-8') == 'xml'
        assert guess._xml(file_xml.name, None) == 'xml'
        assert guess._xml(open(file_xml.name, 'r'), None) == 'xml'

    def test_html(self, file_html):
        assert guess._html(file_html.name, 'utf-8') == 'html'
        assert guess._html(file_html.name, None) == 'html'
        assert guess._html(open(file_html.name, 'r'), None) == 'html'

    # def test_rdf(self, file_rdf):
    #     # TODO
    #     # rdflib.plugin.PluginException: No plugin registered for (rdf, <class 'rdflib.parser.Parser'>)
    #     # co ciekawe file_xml jest rozpoznawany... jako rdf
    #     assert guess._rdf(file_rdf.name, 'utf-8') == 'rdf'
    #     assert guess._rdf(file_rdf.name, None) == 'rdf'
    #     assert guess._rdf(open(file_rdf.name, 'r'), None) == 'rdf'

    def test_json(self, file_json):
        assert guess._json(file_json.name, 'utf-8') == 'json'
        assert guess._json(file_json.name, None) == 'json'
        assert guess._json(open(file_json.name, 'r'), None) == 'json'

    def test_jsonapi(self, file_jsonapi):
        assert guess._jsonapi(file_jsonapi.name, 'utf-8') == 'jsonapi'
        assert guess._jsonapi(file_jsonapi.name, None) == 'jsonapi'
        assert guess._jsonapi(open(file_jsonapi.name, 'r'), None) == 'jsonapi'

    def test_failures(self, file_csv, file_xml, file_html, file_json, file_rdf, file_txt):
        assert guess._csv(file_txt.name, None) is None

        assert guess._xml(file_txt.name, None) is None
        assert guess._xml(file_json.name, None) is None
        assert guess._xml(file_csv.name, None) is None

        assert guess._html(file_json.name, None) is None
        assert guess._html(file_xml.name, None) is None
        assert guess._html(file_txt.name, None) is None
        assert guess._html(file_csv.name, None) is None

        assert guess._rdf(file_json.name, None) is None
        # assert guess._rdf(file_xml.name, None) is None  # FIXME
        assert guess._rdf(file_txt.name, None) is None
        assert guess._rdf(file_csv.name, None) is None

        assert guess._json(file_xml.name, None) is None
        assert guess._json(file_csv.name, None) is None
        assert guess._json(file_txt.name, None) is None

    def test_text_file_format_guess(self, file_csv, file_xml, file_html, file_json, file_rdf, file_txt):
        # assert guess.text_file_format(file_xml.name, 'utf-8') == 'xml'    # FIXME rdf?
        assert guess.text_file_format(file_html.name, 'utf-8') == 'html'
        # assert guess.text_file_format(file_rdf.name, 'utf-8') == 'rdf'  # FIXME test_simple_rdf_guess
        assert guess.text_file_format(file_csv.name, 'utf-8') == 'csv'
        assert guess.text_file_format(file_json.name, 'utf-8') == 'json'
        # assert guess.text_file_format(file_txt.name, 'utf-8') is None

        # assert guess.text_file_format(file_xml.name, None) == 'xml'    # FIXME rdf?
        assert guess.text_file_format(file_html.name, None) == 'html'
        assert guess.text_file_format(file_json.name, None) == 'json'
        # assert guess.text_file_format(file_rdf.name, None) == 'rdf'  # FIXME test_simple_rdf_guess
        assert guess.text_file_format(file_csv.name, None) == 'csv'
        # assert guess.text_file_format(file_txt.name, None) is None

    def test_web_format_guess(self, file_html):
        assert guess.web_format(file_html.name, 'utf-8') == 'html'

    def test_api_format_guess(self, fake_client):
        resp = fake_client.simulate_get('/json')
        assert guess.api_format(resp, None) == 'json'

        resp = fake_client.simulate_get('/jsonapi')
        assert guess.api_format(resp, None) == 'jsonapi'

        resp = fake_client.simulate_get('/xml')
        assert guess.api_format(resp, None) == 'xml'
