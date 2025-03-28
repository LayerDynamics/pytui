import sys
from .widget import Widget
from .style import Style

class Console(Widget):
    """Console output widget."""

    def __init__(self, *, file=sys.stdout):
        """Initialize console widget.
        
        Args:
            file: File to write output to
        """
        super().__init__()
        self.file = file
        self._buffer = []
        
    def write(self, text, style=None):
        """Write text to console.
        
        Args:
            text: Text to write
            style: Optional style to apply
        """
        if style:
            text = Style(style).apply(text)
        self._buffer.append(text)
        
    def clear(self):
        """Clear the console buffer."""
        self._buffer.clear()
        
    def render(self):
        """Render buffered content."""
        return "\n".join(self._buffer)
