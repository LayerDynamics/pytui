"""Container components for rich text UI."""

from .base import Widget

class Container(Widget):
    """Container for organizing widgets."""
    
    def __init__(self, *widgets, name=None, widget_id=None):
        super().__init__(name=name, widget_id=widget_id)
        self.layout = "vertical"
        self.children = list(widgets)
        for widget in widgets:
            widget.parent = self

    # ...rest of Container implementation...

class ScrollView(Container):
    """Container that supports scrolling."""
    
    def __init__(self, *widgets, name=None, widget_id=None):
        super().__init__(*widgets, name=name, widget_id=widget_id)
        self._scroll = {"x": 0, "y": 0}
        self._viewport = {"width": 80, "height": 24}

    # ...rest of ScrollView implementation...
