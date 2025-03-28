"""Base components for rich text UI."""

import sys
import asyncio
from dataclasses import dataclass

@dataclass
class WidgetConfig:
    """Configuration for widget instances."""
    name: str = None
    widget_id: str = None
    visible: bool = True
    focused: bool = False
    hover: bool = False
    width: int = None
    height: int = None

class Widget:
    """Base class for all UI widgets."""
    
    def __init__(self, name=None, widget_id=None):
        """Initialize widget with standard attributes."""
        self._config = WidgetConfig(name=name, widget_id=widget_id)
        self.parent = None
        self.children = []
        self.styles = StyleManager(self)
        self.classes = set()
        self._event_handlers = {}
        self.content = ""
        self._content = ""
        self._text_parts = []

    # ...rest of Widget class implementation...

class StyleManager:
    """Manages widget styles."""
    
    def __init__(self, widget):
        self.widget = widget
        self._styles = {}

    # ...rest of StyleManager implementation...
