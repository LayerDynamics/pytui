from .widget import Widget
from .style import Style


class Text(Widget):
    """Text content with styling."""

    def __init__(self, content="", style=None, justify="left"):
        """Initialize text widget.

        Args:
            content: Initial text content
            style: Text style
            justify: Text justification
        """
        super().__init__()
        self.content = str(content)
        self.style = Style(style) if isinstance(style, str) else style
        self.justify = justify
        self._text_parts = []

        # Add initial content as a part if provided
        if content:
            self._text_parts.append((str(content), self.style))

    def render(self):
        """Render text with styling."""
        if not self._text_parts:
            return ""

        # Apply styling to each part and combine
        result = ""
        for text, style in self._text_parts:
            if style:
                result += Style(style).apply(text)
            else:
                result += text

        return result

    def append(self, text, style=None):
        """Append text with optional style.

        Args:
            text: Text to append
            style: Style to apply

        Returns:
            Self for chaining
        """
        self._text_parts.append((str(text), style))
        self.content += str(text)
        return self

    def clear(self):
        """Clear text content."""
        self._text_parts = []
        self.content = ""
        return self

    def __add__(self, other):
        """Add two Text objects or a Text and a string."""
        result = Text()

        # Add parts from this Text
        result._text_parts.extend(self._text_parts)

        # Add parts from other
        if isinstance(other, Text):
            result._text_parts.extend(other._text_parts)
            result.content = self.content + other.content
        else:
            other_str = str(other)
            result._text_parts.append((other_str, None))
            result.content = self.content + other_str

        return result

    def __iadd__(self, other):
        """In-place addition."""
        if isinstance(other, Text):
            self._text_parts.extend(other._text_parts)
            self.content += other.content
        else:
            other_str = str(other)
            self._text_parts.append((other_str, None))
            self.content += other_str

        return self
