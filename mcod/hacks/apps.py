import importlib

from django.apps import AppConfig

from mcod.hacks.goodtables_spec import spec as gt_spec


def goodtables_spec_hacked():
    return gt_spec


class HacksConfig(AppConfig):
    name = "mcod.hacks"

    @staticmethod
    def hack_goodtables():
        import goodtables.error

        spec_module = importlib.import_module("goodtables.spec")
        spec_module.spec = goodtables_spec_hacked()
        importlib.reload(goodtables.error)

    def ready(self):
        self.hack_goodtables()
