






class Widget:
    """Base class for all UI widgets."""

    def __init__(self, name=None, widget_id=None):
        """Initialize widget with standard attributes.

        Args:
            name: Widget name
            widget_id: Widget ID
        """
        self.name = name
        self.id = widget_id or id(self)
        self.parent = None
        self.children = []
        self.styles = StyleManager(self)
        self.visible = True
        self.focused = False
        self.hover = False
        self.width = None
        self.height = None
        self.classes = set()
        self._event_handlers = {}
        self.content = ""
        self._content = ""
        self._text_parts = []

    def render(self) -> str:
        """Render the widget to a string representation."""
        return ""

    def __str__(self):
        """Convert widget to string."""
        return self.render()

    async def mount(self, *widgets):
        """Mount child widgets.

        Args:
            *widgets: Child widgets to mount
        """
        for widget in widgets:
            if widget.parent:
                widget.parent.children.remove(widget)
            widget.parent = self
            self.children.append(widget)
        await self.refresh()
        return self

    def remove_widget(self, widget):
        """Remove a child widget.

        Args:
            widget: Widget to remove
        """
        if widget in self.children:
            self.children.remove(widget)
            widget.parent = None

    async def update(self, content):
        """Update widget content.

        Args:
            content: New content to update the widget with
        """
        if hasattr(self, "content"):
            if isinstance(content, (str, int, float)):
                self.content = str(content)
            elif hasattr(content, "render"):
                self.content = content
            else:
                self.content = str(content)

        if hasattr(self, "_content"):
            has_style = hasattr(self, "style")
            text_content = str(content)
            style_value = self.style if has_style else None
            self._text_parts = [(text_content, style_value)]

        if hasattr(self, "_text_parts"):
            self._text_parts = (
                [(str(content), self.style)]
                if hasattr(self, "style")
                else [(str(content), None)]
            )

        if self.children and isinstance(content, (list, tuple)):
            # Update children if content is a sequence
            for child, child_content in zip(self.children, content):
                await child.update(child_content)

        await self.refresh()

    async def refresh(self):
        """Refresh the widget display."""
        # Clear screen and move cursor to top
        sys.stdout.write("\033[2J\033[H")

        # Render and display the widget
        rendered = self.render()
        if rendered:
            # Use write() to avoid extra newlines from print()
            sys.stdout.write(rendered)
            sys.stdout.write("\n")

        # Force flush the output
        sys.stdout.flush()

    def focus(self):
        """Focus this widget."""
        if self.parent:
            self.parent.set_focus(self)
        self.focused = True

    def set_focus(self, widget):
        """Set focus to a child widget.

        Args:
            widget: Widget to focus
        """
        for child in self.children:
            child.focused = child == widget

    def add_class(self, class_name):
        """Add a CSS-like class to the widget.

        Args:
            class_name: Class to add
        """
        self.classes.add(class_name)

    def remove_class(self, class_name):
        """Remove a CSS-like class from the widget.

        Args:
            class_name: Class to remove
        """
        if class_name in self.classes:
            self.classes.remove(class_name)

    def on(self, event_name, callback):
        """Register an event handler.

        Args:
            event_name: Event to handle
            callback: Handler function
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(callback)

    async def emit(self, event_name, *args, **kwargs):
        """Emit an event to registered handlers.

        Args:
            event_name: Event to emit
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        handlers = self._event_handlers.get(event_name, [])
        results = []
        for handler in handlers:
            result = handler(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            results.append(result)
        return results

