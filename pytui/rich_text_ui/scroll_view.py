import asyncio
from .container import Container


class ScrollView(Container):
    """Container that supports scrolling."""

    def __init__(self, *widgets, name=None, widget_id=None):
        """Initialize scroll view.

        Args:
            *widgets: Initial widgets
            name: Widget name
            widget_id: Widget ID
        """
        super().__init__(*widgets, name=name, widget_id=widget_id)
        self.scroll_x = 0
        self.scroll_y = 0
        self.content_width = 0
        self.content_height = 0
        self.viewport_width = 80
        self.viewport_height = 24

    async def scroll_to(self, x=None, y=None, animate=False):
        """Scroll to a position.

        Args:
            x: Horizontal position (0-1)
            y: Vertical position (0-1)
            animate: Whether to animate the scroll
        """
        if animate:
            # Animate scrolling with small steps
            if x is not None:
                start_x = self.scroll_x
                for step in range(10):
                    self.scroll_x = start_x + (x - start_x) * (step + 1) / 10
                    self.scroll_x = max(0, min(1, self.scroll_x))
                    await self.refresh()
                    await asyncio.sleep(0.01)
            if y is not None:
                start_y = self.scroll_y
                for step in range(10):
                    self.scroll_y = start_y + (y - start_y) * (step + 1) / 10
                    self.scroll_y = max(0, min(1, self.scroll_y))
                    await self.refresh()
                    await asyncio.sleep(0.01)
        else:
            if x is not None:
                self.scroll_x = max(0, min(1, x))
            if y is not None:
                self.scroll_y = max(0, min(1, y))
            await self.refresh()
