from webargs import core
from webargs.falconparser import FalconParser


class Parser(FalconParser):
    def parse_querystring(self, req, name, field):
        data = field.prepare_data(name, req.params)
        return core.get_value(data, name, field)
