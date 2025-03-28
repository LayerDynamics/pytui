"""Base widget implementations."""

import sys
import asyncio
from typing import Optional

from .style import Style, StyleManager

class Widget:
    """Base class for all UI widgets."""
    
    def __init__(self, name: Optional[str] = None, widget_id: Optional[str] = None):
        self.name = name
        self.id = widget_id or id(self)
        self.parent = None
        self.children = []
        self.styles = StyleManager(self)
        self.visible = True
        self.focused = False
        self.width = None
        self.height = None
        self.classes = set()
        self._event_handlers = {}
        self.content = ""
        self._content = ""
        self._text_parts = []

    # ...rest of Widget implementation...

class Container(Widget):
    """Container for organizing widgets."""
    
    def __init__(self, *widgets, name=None, widget_id=None):
        super().__init__(name=name, widget_id=widget_id)
        self.layout = "vertical"
        self.children = list(widgets)
        for widget in widgets:
            widget.parent = self

    # ...rest of Container implementation...

# Export widgets
__all__ = ["Widget", "Container"]
