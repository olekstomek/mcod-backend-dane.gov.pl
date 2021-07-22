import csv
import json
from io import BytesIO
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
from requests.exceptions import RequestException
from csvwlib import CSVWConverter
from rdflib import URIRef, ConjunctiveGraph

from mcod import settings
from mcod.resources.link_validation import content_type_from_file_format
from mcod.unleash import is_enabled


class ScoreValidationError(Exception):
    pass


DEFAULT_OPENNESS_SCORE = {_type: os for _, _type, _, os, *other in settings.SUPPORTED_CONTENT_TYPES}
OPENNESS_SCORES = {_type: {os} | set(*other) for _, _type, _, os, *other in settings.SUPPORTED_CONTENT_TYPES}

format_to_score_calculator = {}


def register_score_calculator(format_):
    def inner(class_):
        assert issubclass(class_, OpennessScoreCalculator)
        format_to_score_calculator[format_] = class_
        return class_
    return inner


def get_score(resource, format_):
    calculator = format_to_score_calculator.get(format_, OpennessScoreCalculator)()
    return calculator.get_score(resource, format_)


class OpennessScoreCalculator:

    default_score = 1

    def get_score(self, resource, format_):
        _, content = content_type_from_file_format(format_.lower())
        return DEFAULT_OPENNESS_SCORE.get(content, 0)

    def get_context(self, resource):
        context = {}
        if resource.link and not resource.file:
            try:
                response = requests.get(resource.link, stream=True, allow_redirects=True, verify=False, timeout=180)
                context['res_link'] = resource.link
                context['link_header'] = response.headers.get('Link')
                context['data'] = response.content
            except RequestException:
                context['data'] = None
        else:
            with open(resource.file.path, 'rb') as outfile:
                context['data'] = outfile.read()
        return context

    def calculate_score(self, context):
        score = self.default_score
        try:
            for score_num in range(self.default_score + 1, 6):
                getattr(self, f'validate_score_level_{score_num}')(context)
                score = score_num
        except (ScoreValidationError, AttributeError):
            pass
        return score

    def contains_linked_data(self, graph):
        # TODO zastanowić się kiedy plik zawiera dane zlinkowane
        for subject, predicate, object_ in graph:
            if isinstance(object_, URIRef) and not str(predicate).startswith(
                    'http://www.w3.org/1999/02/22-rdf-syntax-ns#'):
                return True
        return False


@register_score_calculator('csv')
class CSVScoreCalculator(OpennessScoreCalculator):
    default_score = 3

    def get_score(self, resource, format_):
        if not is_enabled('S29_new_csv_openness_score.be'):
            return super().get_score(resource, format_)

        is_originally_csv = resource.file and resource.format == 'csv'

        csv_file = resource.file if is_originally_csv else resource.csv_file
        csv_url = resource.file_url if is_originally_csv else resource.csv_file_url
        if csv_url:
            csv_url = resource._get_absolute_url(urlparse(csv_url).path, base_url=settings.API_URL_INTERNAL, use_lang=False)

        metadata_url = getattr(resource, 'csv_file_metadata_url', None)
        if is_originally_csv:
            metadata_url = getattr(resource, 'file_metadata_url', None)
        if metadata_url:
            metadata_url = resource._get_absolute_url(
                urlparse(metadata_url).path, base_url=settings.API_URL_INTERNAL, use_lang=False)

        score = self.default_score
        if csv_file and self.is_compatible_to_rfc_4180(csv_file.path) and self.is_convertable_to_json_ld(csv_url, metadata_url):
            score = 4
            graph = CSVWConverter.to_rdf(csv_url, metadata_url)
            if self.contains_linked_data(graph):
                score = 5

        return score

    def is_convertable_to_json_ld(self, csv_url, metadata_url):
        try:
            CSVWConverter.to_rdf(csv_url, metadata_url, format='json-ld')
            return True
        except Exception:
            return False

    def is_compatible_to_rfc_4180(self, file_path):
        try:
            with open(file_path, newline='') as file:
                sample = file.read(10000)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)

                conditions = [
                    dialect.lineterminator == '\r\n',
                    dialect.delimiter == ',',
                    dialect.quotechar == '"',
                    sniffer.has_header(sample),
                ]

                if not all(conditions):
                    return False

                file.seek(0)
                reader = csv.reader(file, dialect)
                row = next(reader)

                headers = [cell.strip() for cell in row]
                are_all_headers_nonempty = all(headers)
                are_all_headers_unique = len(headers) == len(set(headers))

                return are_all_headers_nonempty and are_all_headers_unique

        except Exception:
            return False


@register_score_calculator('json')
class JSONScoreCalculator(OpennessScoreCalculator):

    default_score = 3

    def validate_score_level_4(self, context):
        try:
            json.loads(context['data'])
            graph = ConjunctiveGraph()
            link_header = context.get('link_header')
            if link_header and 'application/ld+json' in link_header:
                json_ctx_uri = link_header.split(';')[0]
                json_ctx_path = json_ctx_uri.rstrip('>').lstrip('<')
                if not json_ctx_path.startswith('http'):
                    url_details = urlparse(context['res_link'])
                    base_url = f'{url_details.scheme}://{url_details.netloc}'
                    ctx_rel_has_slash = json_ctx_path.startswith('/')
                    if ctx_rel_has_slash:
                        full_ctx_url = base_url + json_ctx_path
                    else:
                        full_ctx_url = f'{base_url}/{json_ctx_path}'
                else:
                    full_ctx_url = json_ctx_path
                json_data = json.loads(context['data'])
                json_data['@context'] = full_ctx_url
                json_bts = BytesIO()
                json_bts.write(json.dumps(json_data).encode())
                json_bts.seek(0)
                json_str = json_bts.read()
            else:
                json_str = context['data']
            graph.parse(data=json_str, format='json-ld')
            if not graph:
                raise ScoreValidationError
            context['rdf_graph'] = graph
        except Exception:
            raise ScoreValidationError

    def validate_score_level_5(self, context):
        rdf_graph = context['rdf_graph']
        q = 'ASK WHERE {?s ?p ?o . FILTER(isURI(?o) && str(?p)' \
            ' != "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" )}'
        res = rdf_graph.query(q)
        if not res.askAnswer:
            raise ScoreValidationError

    def get_score(self, resource, format_):
        if is_enabled('S29_new_json_openness_score'):
            context = self.get_context(resource)
            return self.calculate_score(context)
        return super().get_score(resource, format_)


@register_score_calculator('xml')
class XMLScoreCalculator(OpennessScoreCalculator):

    default_score = 3

    def get_score(self, resource, format_):
        if is_enabled('S29_new_xml_openness_score.be'):
            context = self.get_context(resource)
            return self.calculate_score(context)
        return super().get_score(resource, format_)

    def validate_score_level_4(self, context):
        data = context['data']
        try:
            namespaces = dict([node for _, node in ElementTree.iterparse(BytesIO(data), events=['start-ns'])])
            if not namespaces:
                raise ScoreValidationError
            tree = ElementTree.ElementTree(ElementTree.fromstring(data))
            root = tree.getroot()
            if not root:
                raise ScoreValidationError
        except Exception:
            raise ScoreValidationError

        items_tags = [item.tag for item in root.iter()]
        for item_tag in items_tags:
            if not any([ns in item_tag for ns in namespaces.values()]):
                raise ScoreValidationError

    def validate_score_level_5(self, context):
        graph = ConjunctiveGraph()
        try:
            graph = graph.parse(data=context['data'])
            if not len(graph) or not self.contains_linked_data(graph):
                raise ScoreValidationError
        except Exception:
            raise ScoreValidationError
