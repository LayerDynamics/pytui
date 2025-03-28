"""List component for rich text UI."""

from .widget import Widget
from .colors import Color

class List(Widget):
    """List widget for displaying items with optional styling."""

    def __init__(self):
        """Initialize an empty list."""
        super().__init__()
        self.items = []
        self._styles = []

    def add_item(self, item: str, style: str = None) -> None:
        """Add an item to the list with optional style."""
        self.items.append(str(item))
        self._styles.append(style or "")

    def clear(self) -> None:
        """Clear all items from the list."""
        self.items.clear()
        self._styles.clear()

    def remove_item(self, index: int) -> None:
        """Remove item at specified index."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._styles.pop(index)

    def render(self) -> str:
        """Render the list items."""
        if not self.items:
            return "[Empty List]"

        rendered_items = []
        for item, style in zip(self.items, self._styles):
            if style:
                rendered_items.append(f"[{style}]{item}[/]")
            else:
                rendered_items.append(f"• {item}")

        return "\n".join(rendered_items)
