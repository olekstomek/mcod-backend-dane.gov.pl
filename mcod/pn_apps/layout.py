from mcod.pn_apps.bokeh.layouts import ExtendedColumn as BkExtendedColumn
from panel.layout import ListPanel
import param


class ExtendedColumn(ListPanel):
    _bokeh_model = BkExtendedColumn
    aria_hidden = param.Boolean(default=False)
