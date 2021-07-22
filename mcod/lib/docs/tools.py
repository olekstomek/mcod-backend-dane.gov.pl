# -*- coding: utf-8 -*-
import yaml
from falcon.routing.compiled import _FIELD_PATTERN
from apispec import utils


def load_yaml_from_docstring(docstring, start_line='---'):
    split_lines = utils.trim_docstring(docstring).split('\n')
    start = 0
    for i, line in enumerate(split_lines):
        line = line.strip()
        if start_line in line:
            start = i + 1
            break

    try:
        doc = (
            yaml.load("\n".join(split_lines[start:]))
        )
    except yaml.YAMLError:
        doc = None
        # doc = {
        #     "description": "Document could not be loaded from docstring",
        #     "tags": ["invalid doc"]
        # }
    return doc


def generate_routes(nodes, path=''):
    for node in nodes:
        node_path = '{}/{}'.format(path, node.raw_segment)
        if node.children:
            for item in generate_routes(node.children, node_path):
                yield item

        if node.method_map:
            yield (node_path, node.method_map)


def path_for_apispec(uri_template):
    segments = []
    path = uri_template.strip('/').split('/')
    for segment in path:
        ns = segment
        for field in _FIELD_PATTERN.finditer(segment):
            name = field.group('fname')
            ns = ns.replace(field.group(0), '{%s}' % name)
        segments.append(ns)
    return '/' + ("/".join(segments))


def generate_apispec(app, spec, start_line='---'):
    roots = app._router._roots
    for path, method_map in generate_routes(roots):
        path = path_for_apispec(path)
        for method in method_map:
            fun = method_map[method]
            if hasattr(fun, '__self__') and \
                    fun.__name__ not in ('method_not_allowed', 'on_options'):
                operations = load_yaml_from_docstring(fun.__doc__, start_line)
                if operations:
                    spec.add_path(path=path, operations=operations)
    return spec
