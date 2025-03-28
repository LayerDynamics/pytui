"""Layout containers for PyTUI."""

class Container:
    """Base class for layout containers."""
    
    def __init__(self):
        """Initialize a container."""
        self.children = []
        self.align = "left"
    
    def add(self, widget):
        """Add a widget to this container.
        
        Args:
            widget: The widget to add
        """
        self.children.append(widget)
        widget.parent = self
    
    def set_align(self, align):
        """Set the alignment of this container.
        
        Args:
            align: One of "left", "center", "right"
        """
        self.align = align
    
    def render(self):
        """Render this container and all its children."""
        for child in self.children:
            child.render()


class VBox(Container):
    """A vertical box container that stacks widgets vertically."""
    
    def render(self):
        """Render this vertical box and its children."""
        print(f"VBox (align: {self.align}):")
        super().render()


class HBox(Container):
    """A horizontal box container that arranges widgets horizontally."""
    
    def render(self):
        """Render this horizontal box and its children."""
        print(f"HBox (align: {self.align}):")
        super().render()
