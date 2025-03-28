



class Static(Widget):
    """Static content display widget."""

    def __init__(self, content="", *, name=None, widget_id=None):
        """Initialize static widget.

        Args:
            content: Initial content
            name: Widget name
            widget_id: Widget ID
        """
        super().__init__(name=name, widget_id=widget_id)
        self._content = str(content) if content else ""

    def render(self):
        """Render the content."""
        return self._content

    async def update(self, content):
        """Update the widget content.

        Args:
            content: New content
        """
        self._content = str(content) if content else ""
        await self.refresh()

