import sys
import asyncio
import re
import json
import time
from typing import Optional, List, Union, TextIO, Dict, Callable, Pattern, Tuple, Any
from pathlib import Path
from datetime import datetime

from .widget import Widget
from .style import Style
from .text import Text    """Console output widget with advanced features."""

class LogLevel:__(
    """Log level constants."""lf,
    DEBUG = "debug"
    INFO = "info"out,
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"] = None,
    CRITICAL = "critical"  scroll: bool = True,

    @staticmethod"""Initialize console widget.
    def get_style(level: str) -> str:
        """Get style for log level."""
        styles = {
            LogLevel.DEBUG: "dim", keep in buffer
            LogLevel.INFO: "blue",stamps
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red", scroll: Whether to auto-scroll to bottom
            LogLevel.SUCCESS: "green",
            LogLevel.CRITICAL: "bold red"()
        }
        return styles.get(level.lower(), "")

class Console(Widget):e(style) if style else None
    """Console output widget with advanced features."""
tuple[str, Optional[Style]]] = []
    def __init__(
        self, self._last_render = ""
        *,
        file: TextIO = sys.stdout,
        max_lines: int = 1000,
        timestamp: bool = False,
        style: Optional[str] = None,str, Style]] = None,
        scroll: bool = True,bool = None,
        log_level: str = LogLevel.INFO,
        highlight_patterns: Optional[Dict[str, str]] = None,"""Write text to console.
        record_history: bool = False
    ):
        """Initialize console widget.
        
        Args:            timestamp: Override default timestamp setting
            file: File to write output to
            max_lines: Maximum number of lines to keep in buffer
            timestamp: Whether to show timestamps Self for chaining
            style: Default style for output
            scroll: Whether to auto-scroll to bottom
            log_level: Minimum log level to displayontent = text.render()
            highlight_patterns: Dictionary of regex patterns and styles to highlight
            record_history: Whether to save console history            content = str(text)
        """
        super().__init__()
        self.file = filelit("\n")
        self.max_lines = max_liness:
        self.show_timestamp = timestamp
        self.default_style = Style(style) if style else Nonecontinue
        self.auto_scroll = scroll
        self.log_level = log_levelestamp):
        self._buffer: List[Tuple[str, Optional[Style], str]] = []  # text, style, levele.now().strftime('%H:%M:%S')}] "
        self._dirty = False                line = ts + line
        self._last_render = ""
        self._search_results: List[int] = []  # Indices in buffer where search matchesiority: passed style > default style
        self._search_index = -1le = None
        self._current_position = 0
        self._filters: List[Tuple[Pattern, bool]] = []  # regex, include/excludestyle) if isinstance(style, str) else style
        self._highlight_patterns = {}
        self._history_file = None                final_style = self.default_style
        
        # Initialize highlight patternsself._buffer.append((line, final_style))
        if highlight_patterns:
            for pattern, style in highlight_patterns.items():
                self.add_highlight(pattern, style)
                self._buffer = self._buffer[-self.max_lines :]
        # Setup history recording
        if record_history: = True
            self._setup_history()return self
        
    def _setup_history(self, directory: Optional[str] = None) -> None:
        """Set up console history recording."""Clear the console buffer.
        
        Args:
            directory: Optional directory to store history Self for chaining
        """
        try:()
            dir_path = Path(directory) if directory else Path.home() / ".pytui" / "history" = True
            dir_path.mkdir(parents=True, exist_ok=True)return self
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._history_file = dir_path / f"console_{timestamp}.log": Union[str, Text]) -> None:
        except (OSError, PermissionError) as e:"""Update console content.
            print(f"Warning: Could not setup history recording: {e}", file=sys.stderr)
            self._history_file = None
     content: New content to display
    def add_highlight(self, pattern: str, style: str) -> None:
        """Add a highlight pattern.
        await self.refresh()
        Args:
            pattern: Regex pattern to match
            style: Style to apply to matches
        """_last_render:
        try:return self._last_render
            compiled = re.compile(pattern)
            self._highlight_patterns[compiled] = Style(style)
        except re.error:le in self._buffer:
            pass  # Invalid regex pattern
            ines.append(style.apply(text))
    def add_filter(self, pattern: str, include: bool = True) -> None:
        """Add a filter for console output.lines.append(text)
        
        Args: "\n".join(lines)
            pattern: Regex pattern to match
            include: Whether to include (True) or exclude (False) matchesreturn self._last_render
        """
        try:log(
            compiled = re.compile(pattern)
            self._filters.append((compiled, include))n[str, Text],
            self._dirty = True  # Force re-render with new filters
        except re.error: Optional[Union[str, Style]] = None,
            pass  # Invalid regex pattern
            """Log one or more messages with optional styling.
    def clear_filters(self) -> None:
        """Clear all filters."""
        self._filters.clear()
        self._dirty = Trues
         style: Optional style to apply
    def search(self, query: str) -> int:
        """Search for text in console buffer.in messages)
        le=style)
        Args:await self.refresh()
            query: Text to search for
            Union[str, Text], sep: str = " ") -> None:
        Returns:"""Log error messages in red.
            Number of matches found
        """
        if not query:g
            self._search_results.clear() sep: Separator between messages
            return 0
            await self.log(*messages, sep=sep, style="bold red")
        self._search_results.clear()
        pattern = re.compile(re.escape(query), re.IGNORECASE)on[str, Text], sep: str = " ") -> None:
        """Log warning messages in yellow.
        for i, (text, _, _) in enumerate(self._buffer):
            if pattern.search(text):
                self._search_results.append(i)log
                 sep: Separator between messages
        self._search_index = 0 if self._search_results else -1
        self._dirty = Trueawait self.log(*messages, sep=sep, style="yellow")
        return len(self._search_results)
        ion[str, Text], sep: str = " ") -> None:
    def next_search_result(self) -> Optional[int]:"""Log success messages in green.
        """Move to next search result.
        
        Returns:log
            Line number or None if no more results sep: Separator between messages
        """
        if not self._search_results:await self.log(*messages, sep=sep, style="green")
            return None
            nion[str, Text], sep: str = " ") -> None:
        if self._search_index < len(self._search_results) - 1:"""Log info messages in blue.
            self._search_index += 1
        else:
            self._search_index = 0
             sep: Separator between messages
        result_line = self._search_results[self._search_index]
        self._current_position = result_line        await self.log(*messages, sep=sep, style="blue")
        self._dirty = True
        return result_lineNone) -> List[str]:
        """Get visible lines based on height constraint.
    def previous_search_result(self) -> Optional[int]:
        """Move to previous search result.
        height: Maximum number of lines to return
        Returns:
            Line number or None if no more results
        """ List of visible lines
        if not self._search_results:
            return None
            return [line for line, _ in self._buffer]
        if self._search_index > 0:
            self._search_index -= 1
        else:ht:]]
            self._search_index = len(self._search_results) - 1        return [line for line, _ in self._buffer[:height]]

















            text: Text to write        Args:                """Write text to console.    ) -> 'Console':        level: str = LogLevel.INFO        timestamp: bool = None,        style: Optional[Union[str, Style]] = None,        text: Union[str, Text],         self,     def write(            return result_line        self._dirty = True        self._current_position = result_line        result_line = self._search_results[self._search_index]            