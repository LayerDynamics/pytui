import sys
import asyncio
from typing import Optional, List, Union, TextIO
from datetime import datetime

from .widget import Widget
from .style import Style
from .text import Text


class Console(Widget):
    """Console output widget with advanced features."""

    def __init__(
        self,
        *,
        file: TextIO = sys.stdout,
        max_lines: int = 1000,
        timestamp: bool = False,
        style: Optional[str] = None,
        scroll: bool = True,
    ):
        """Initialize console widget.

        Args:
            file: File to write output to
            max_lines: Maximum number of lines to keep in buffer
            timestamp: Whether to show timestamps
            style: Default style for output
            scroll: Whether to auto-scroll to bottom
        """
        super().__init__()
        self.file = file
        self.max_lines = max_lines
        self.show_timestamp = timestamp
        self.default_style = Style(style) if style else None
        self.auto_scroll = scroll
        self._buffer: List[tuple[str, Optional[Style]]] = []
        self._dirty = False
        self._last_render = ""

    def write(
        self,
        text: Union[str, Text],
        style: Optional[Union[str, Style]] = None,
        timestamp: bool = None,
    ) -> "Console":
        """Write text to console.

        Args:
            text: Text to write
            style: Optional style to apply
            timestamp: Override default timestamp setting

        Returns:
            Self for chaining
        """
        if isinstance(text, Text):
            content = text.render()
        else:
            content = str(text)

        # Handle multiline input
        lines = content.split("\n")
        for line in lines:
            if not line:
                continue

            if timestamp or (timestamp is None and self.show_timestamp):
                ts = f"[{datetime.now().strftime('%H:%M:%S')}] "
                line = ts + line

            # Resolve style priority: passed style > default style
            final_style = None
            if style:
                final_style = Style(style) if isinstance(style, str) else style
            elif self.default_style:
                final_style = self.default_style

            self._buffer.append((line, final_style))

        # Trim buffer if needed
        if len(self._buffer) > self.max_lines:
            self._buffer = self._buffer[-self.max_lines :]

        self._dirty = True
        return self

    def clear(self) -> "Console":
        """Clear the console buffer.

        Returns:
            Self for chaining
        """
        self._buffer.clear()
        self._dirty = True
        return self

    async def update(self, content: Union[str, Text]) -> None:
        """Update console content.

        Args:
            content: New content to display
        """
        self.write(content)
        await self.refresh()

    def render(self) -> str:
        """Render buffered content."""
        if not self._dirty and self._last_render:
            return self._last_render

        lines = []
        for text, style in self._buffer:
            if style:
                lines.append(style.apply(text))
            else:
                lines.append(text)

        self._last_render = "\n".join(lines)
        self._dirty = False
        return self._last_render

    async def log(
        self,
        *messages: Union[str, Text],
        sep: str = " ",
        style: Optional[Union[str, Style]] = None,
    ) -> None:
        """Log one or more messages with optional styling.

        Args:
            *messages: Messages to log
            sep: Separator between messages
            style: Optional style to apply
        """
        text = sep.join(str(m) for m in messages)
        self.write(text, style=style)
        await self.refresh()

    async def error(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log error messages in red.

        Args:
            *messages: Error messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="bold red")

    async def warning(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log warning messages in yellow.

        Args:
            *messages: Warning messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="yellow")

    async def success(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log success messages in green.

        Args:
            *messages: Success messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="green")

    async def info(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log info messages in blue.

        Args:
            *messages: Info messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="blue")

    def get_visible_lines(self, height: Optional[int] = None) -> List[str]:
        """Get visible lines based on height constraint.

        Args:
            height: Maximum number of lines to return

        Returns:
            List of visible lines
        """
        if not height:
            return [line for line, _ in self._buffer]

        if self.auto_scroll:
            return [line for line, _ in self._buffer[-height:]]
        return [line for line, _ in self._buffer[:height]]
