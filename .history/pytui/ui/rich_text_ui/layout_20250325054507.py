from .widget import Widget

class Layout(Widget):
    """Layout manager for arranging widgets."""

    def __init__(self, content=None, *, size=None, name=None):
        """Initialize layout.

        Args:
            content: Initial content
            size: Layout size
            name: Layout name
        """
        super().__init__(name=name)
        self.content = content
        self.size = size
        self.children = []
        self.layout_type = "vertical"  # vertical, horizontal, grid

    def render(self):
        """Render the layout with content."""
        # If we have direct content, render it
        if self.content:
            if hasattr(self.content, "render"):
                return self.content.render()
            return str(self.content)

        # Return empty string if no children
        if not self.children:
            return ""

        # Handle vertical layout
        if self.layout_type == "vertical":
            return "\n".join(child.render() for child in self.children)

        # Handle horizontal layout
        if self.layout_type == "horizontal":
            # Simple side-by-side layout - not perfect but workable
            child_renders = [child.render().split("\n") for child in self.children]
            max_height = max([len(r) for r in child_renders], default=0)

            # Pad each render to the same height
            for i, render in enumerate(child_renders):
                if len(render) < max_height:
                    child_renders[i] = render + [""] * (max_height - len(render))

            # Combine side by side
            combined = [
                "  ".join(r[i] for r in child_renders) for i in range(max_height)
            ]
            return "\n".join(combined)

        # Default to vertical layout for unknown types
        return "\n".join(child.render() for child in self.children)

    def split(self, *layouts):
        """Split the layout into multiple sections.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.children.extend(layouts)
        return self

    def split_column(self, *layouts):
        """Split into vertical columns.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.layout_type = "vertical"
        return self.split(*layouts)

    def split_row(self, *layouts):
        """Split into horizontal rows.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.layout_type = "horizontal"
        return self.split(*layouts)
