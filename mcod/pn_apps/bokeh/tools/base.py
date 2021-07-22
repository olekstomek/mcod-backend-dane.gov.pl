from bokeh.models import HoverTool, WheelZoomTool, PanTool, SaveTool, ResetTool
from bokeh.core.properties import String


class LocalizedHoverTool(HoverTool):
    localized_tool_name = String(default='')


class LocalizedWheelZoomTool(WheelZoomTool):
    localized_tool_name = String(default='')


class LocalizedPanTool(PanTool):
    localized_tool_name = String(default='')


class LocalizedSaveTool(SaveTool):
    localized_tool_name = String(default='')


class LocalizedResetTool(ResetTool):
    localized_tool_name = String(default='')
