





class Container(Widget):
    """Container for organizing widgets."""

    def __init__(self, *widgets, name=None, widget_id=None):
        """Initialize container.

        Args:
            *widgets: Initial widgets
            name: Container name
            widget_id: Container ID
        """
        super().__init__(name=name, widget_id=widget_id)
        self.layout = "vertical"  # vertical or horizontal

        # Add initial widgets
        self.children = list(widgets)
        for widget in widgets:
            widget.parent = self

    def render(self):
        """Render the container with children."""
        if not self.visible:
            return ""

        rendered_children = []
        for child in self.children:
            if not getattr(child, "visible", True):
                continue

            rendered = child.render()
            if rendered:
                rendered_children.append(rendered)

        if self.layout == "vertical":
            return "\n".join(rendered_children)

        # Simple horizontal layout - not perfect but workable
        lines = []
        max_lines = max((r.count("\n") + 1 for r in rendered_children), default=0)

        # Split each child's render into lines
        child_lines = []
        for r in rendered_children:
            child_lines.append(r.split("\n"))

        # Combine lines horizontally with padding
        for i in range(max_lines):
            line_parts = []
            for child_render in child_lines:
                if i < len(child_render):
                    line_parts.append(child_render[i])
                else:
                    line_parts.append(" " * 10)  # Padding for empty line
            lines.append("  ".join(line_parts))

        return "\n".join(lines)

    async def dock(self, *widgets, edge="left", size=None):
        """Dock widgets to an edge.

        Args:
            *widgets: Widgets to dock
            edge: Edge to dock to
            size: Size of docked area
        """
        for widget in widgets:
            if hasattr(widget, "styles"):
                widget.styles["dock"] = edge
                if size is not None:
                    if edge in ("left", "right"):
                        widget.styles["width"] = size
                    else:
                        widget.styles["height"] = size

            await self.mount(widget)

        return self
