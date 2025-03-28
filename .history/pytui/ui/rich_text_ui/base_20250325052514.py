"""Base classes for widgets."""

import asyncio
from dataclasses import dataclass
from typing import Optional


@dataclass
class WidgetState:
    """Widget state container to reduce instance attributes."""
    name: Optional[str] = None
    widget_id: Optional[str] = None
    parent: Optional['Widget'] = None
    visible: bool = True
    focused: bool = False
    hover: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    classes: set[str] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.classes is None:
            self.classes = set()


class Widget:
    """Base class for all UI widgets."""
    
    def __init__(self, name: Optional[str] = None, widget_id: Optional[str] = None):
        """Initialize widget."""
        self._state = WidgetState(
            name=name,
            widget_id=widget_id or str(id(self))
        )
        self.children = []
        self.styles = StyleManager(self)
        self._event_handlers = {}

    # ...rest of Widget class...
