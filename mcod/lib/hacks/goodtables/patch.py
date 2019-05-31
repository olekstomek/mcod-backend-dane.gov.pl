import importlib
import goodtables.error
from mcod.lib.hacks.goodtables.spec import _load_spec as hacked_spec


def apply():
    spec_module = importlib.import_module('goodtables.spec')
    spec_module.spec = hacked_spec()
    importlib.reload(goodtables.error)
