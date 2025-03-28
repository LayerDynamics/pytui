from .widget import Widget
from .style import Style
from typing import Optional

class Static(Widget):
    """Static content display widget."""

    def __init__(self, content="", *, style=None, width=None, justify="left", name=None, widget_id=None):
        """Initialize static widget.

        Args:
            content: Initial content
            style: Text style 
            width: Maximum width for text wrapping
            justify: Text alignment (left, center, right)
            name: Widget name
            widget_id: Widget ID
        """
        super().__init__(name=name, widget_id=widget_id)
        self._content = str(content) if content else ""
        self.style = Style(style) if isinstance(style, str) else style
        self.width = width
        self.justify = justify

    def render(self):
        """Render the content."""
        if not self._content:
            return ""

        lines = self._content.split('\n')
        if self.width:
            # Wrap text at width
            wrapped_lines = []
            for line in lines:
                while len(line) > self.width:
                    # Find last space before width
                    space_idx = line[:self.width].rfind(' ')
                    if space_idx == -1:
                        # No space found, hard break
                        wrapped_lines.append(line[:self.width])
                        line = line[self.width:]
                    else:
                        wrapped_lines.append(line[:space_idx])
                        line = line[space_idx+1:]
                if line:
                    wrapped_lines.append(line)
            lines = wrapped_lines

        # Apply justification
        if self.width:
            if self.justify == "center":
                lines = [line.center(self.width) for line in lines]
            elif self.justify == "right":
                lines = [line.rjust(self.width) for line in lines]
            else:  # left
                lines = [line.ljust(self.width) for line in lines]

        result = '\n'.join(lines)
        
        # Apply style if set
        if self.style:
            result = self.style.apply(result)
            
        return result

    async def update(self, content):
        """Update the widget content.

        Args:
            content: New content
        """
        self._content = str(content) if content else ""
        await self.refresh()

    def align(self, justify: str) -> 'Static':
        """Set text alignment.
        
        Args:
            justify: Alignment (left, center, right)
            
        Returns:
            Self for chaining
        """
        self.justify = justify
        return self

    def set_style(self, style: Optional[str]) -> 'Static':
        """Set text style.
        
        Args:
            style: Style string or None
            
        Returns:
            Self for chaining
        """
        self.style = Style(style) if style else None
        return self

