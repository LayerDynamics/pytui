"""Rich text UI implementation.

Provides alternative implementations of rich and textual widgets when
the actual packages are not available.
"""

from .style import Style
from .base import Widget, Container, ScrollView, StyleManager
from .components import Text, Static, Panel, Table, Box, Layout

__all__ = [
    # Basic components
    "Widget", "Container", "ScrollView", "StyleManager", "Style",
    # Rich components
    "Text", "Static", "Panel", "Table", "Layout", "Box",
]
