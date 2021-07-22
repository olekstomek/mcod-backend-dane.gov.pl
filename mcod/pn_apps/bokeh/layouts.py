from bokeh.models.layouts import Column
from bokeh.core.properties import Bool


class ExtendedColumn(Column):
    aria_hidden = Bool(False)
