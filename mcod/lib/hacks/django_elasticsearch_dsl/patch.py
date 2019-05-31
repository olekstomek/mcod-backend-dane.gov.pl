import sys
from importlib.machinery import PathFinder, ModuleSpec, SourceFileLoader

from mcod.lib.hacks.django_elasticsearch_dsl import search_index as hacked_search_index


class CustomLoader(SourceFileLoader):
    def exec_module(self, module):
        module.Command = hacked_search_index.Command
        return module


class Finder(PathFinder):
    def __init__(self, module_name):
        self.module_name = module_name

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.module_name:
            spec = super().find_spec(fullname, path, target)
            return ModuleSpec(fullname,
                              CustomLoader(fullname, spec.origin))


def apply():
    sys.meta_path.insert(0, Finder('django_elasticsearch_dsl.management.commands.search_index'))
