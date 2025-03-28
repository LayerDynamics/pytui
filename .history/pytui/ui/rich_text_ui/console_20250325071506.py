"""Console widget module for terminal output management.

Provides advanced console functionality including logging, searching, progress indicators and more.
"""

import sys
import asyncio
import json
import re
import contextlib
from datetime import datetime
from typing import Optional, List, Union, TextIO, Dict, Any
from dataclasses import dataclass, field
from contextlib import contextmanager

from .widget import Widget
from .style import Style
from .text import Text
from .progress import ProgressBar


@dataclass
class ConsoleConfig:
    """Configuration options for Console widget."""
    file: TextIO = sys.stdout
    max_lines: int = 1000
    timestamp: bool = False
    style: Optional[str] = None
    scroll: bool = True
    log_file: Optional[str] = None
    log_level: str = "INFO"
    highlight_rules: Optional[Dict[str, str]] = None


@dataclass
class ConsoleState:
    """Internal state for Console widget."""
    buffer: List[tuple] = field(default_factory=list)
    dirty: bool = False
    last_render: str = ""
    log_file_handle: Optional[TextIO] = None
    log_levels: Dict[str, int] = field(default_factory=lambda: {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    })
    current_log_level: int = 20
    search: Dict[str, Any] = field(default_factory=lambda: {
        "text": None, 
        "results": [], 
        "index": -1
    })
    spinner: Dict[str, Any] = field(default_factory=lambda: {
        "chars": {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["-", "\\", "|", "/"],
            "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        },
        "active_index": None,
        "task": None
    })


class Console(Widget):
    """Console output widget with advanced features."""

    def __init__(self, *, config: Optional[ConsoleConfig] = None):
        """Initialize console widget.

        Args:
            config: Configuration options
        """
        super().__init__()

        # Use config if provided, otherwise use defaults
        self._config = config or ConsoleConfig()
        
        # Public properties from config
        self.file = self._config.file
        self.max_lines = self._config.max_lines
        self.show_timestamp = self._config.timestamp
        self.default_style = Style(self._config.style) if self._config.style else None
        self.auto_scroll = self._config.scroll

        # Internal state
        self._state = ConsoleState()
        self._state.current_log_level = self._state.log_levels.get(
            self._config.log_level.upper() if self._config.log_level else "INFO", 20
        )

        # Open log file if specified
        self._setup_log_file()

    def _setup_log_file(self):
        """Set up log file handling."""
        if self._config.log_file:
            try:
                # Use context manager for file operation but store the file handle
                with open(self._config.log_file, "a", encoding="utf-8") as f:
                    # This is just to create the file if it doesn't exist
                    pass
                # Then open it in append mode to keep the handle
                self._state.log_file_handle = open(
                    self._config.log_file, "a", encoding="utf-8"
                )
            except (IOError, OSError) as e:
                self._write_to_stderr(f"Failed to open log file: {e}")

    def __del__(self):
        """Cleanup when destroyed."""
        self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up allocated resources."""
        if self._state.log_file_handle:
            try:
                self._state.log_file_handle.close()
            except (IOError, OSError):
                pass

        if self._state.spinner["task"] and not self._state.spinner["task"].done():
            self._state.spinner["task"].cancel()

    def _write_to_file(self, text: str) -> None:
        """Write text to log file if configured."""
        if self._state.log_file_handle:
            try:
                self._state.log_file_handle.write(f"{text}\n")
                self._state.log_file_handle.flush()
            except (IOError, OSError) as e:
                self._write_to_stderr(f"Failed to write to log file: {e}")

    def _write_to_stderr(self, text: str) -> None:
        """Write text to stderr."""
        try:
            print(text, file=sys.stderr)
        except (IOError, OSError):
            pass

    def write(
        self,
        text: Union[str, Text],
        style: Optional[Union[str, Style]] = None,
        timestamp: bool = None,
        level: str = "INFO",
    ) -> "Console":
        """Write text to console."""
        # Check log level
        message_level = self._state.log_levels.get(level.upper(), 20)
        if message_level < self._state.current_log_level:
            return self

        content = self._prepare_content(text)
        self._write_to_log_file(content)
        self._process_content_lines(content, style, timestamp)
        return self

    def _prepare_content(self, text: Union[str, Text]) -> str:
        """Convert input to string and apply highlighting."""
        if isinstance(text, Text):
            content = text.render()
        else:
            content = str(text)

        # Apply syntax highlighting if rules exist
        if content and self._config.highlight_rules and not isinstance(text, Text):
            content = self._apply_highlighting(content)
        return content

    def _apply_highlighting(self, content: str) -> str:
        """Apply syntax highlighting using regex rules."""
        if not self._config.highlight_rules:
            return content

        for pattern, style_name in self._config.highlight_rules.items():
            # Create a function that captures the style to avoid cell-var-from-loop
            def apply_style(match, style=style_name):
                return Style(style).apply(match.group(0))
                
            try:
                content = re.sub(pattern, apply_style, content)
            except (re.error, ValueError, TypeError):
                pass
        return content

    def _write_to_log_file(self, content: str) -> None:
        """Write clean content to log file."""
        if not self._state.log_file_handle:
            return

        try:
            clean_text = re.sub(r"\x1b\[[0-9;]*m", "", content)
            self._write_to_file(clean_text)
        except (re.error, ValueError, TypeError):
            self._write_to_file(content)

    def _process_content_lines(
        self,
        content: str,
        style: Optional[Union[str, Style]],
        timestamp: Optional[bool],
    ) -> None:
        """Process and store content lines."""
        lines = content.split("\n")
        current_time = datetime.now()
        timestamp_epoch = int(current_time.timestamp())

        # Resolve style priority: passed style > default style
        final_style = None
        if style:
            final_style = Style(style) if isinstance(style, str) else style
        elif self.default_style:
            final_style = self.default_style

        for line in lines:
            if not line:
                continue

            # Add timestamp if requested
            if timestamp or (timestamp is None and self.show_timestamp):
                ts = f"[{current_time.strftime('%H:%M:%S')}] "
                line = ts + line

            # Store line with timestamp (for sorting/filtering)
            self._state.buffer.append((line, final_style, timestamp_epoch))

        # Trim buffer if needed
        if len(self._state.buffer) > self.max_lines:
            self._state.buffer = self._state.buffer[-self.max_lines :]

        self._state.dirty = True

    def clear(self) -> "Console":
        """Clear the console buffer."""
        self._state.buffer.clear()
        self._state.dirty = True
        self._state.search["results"].clear()
        self._state.search["index"] = -1
        return self

    async def update(self, content: Union[str, Text]) -> None:
        """Update console content."""
        self.write(content)
        await self.refresh()

    def render(self) -> str:
        """Render buffered content."""
        if not self._state.dirty and self._state.last_render:
            return self._state.last_render

        lines = []
        highlight_search = self._state.search["text"] is not None

        for i, (text, style, _) in enumerate(self._state.buffer):
            line = text

            # Apply search highlighting
            if highlight_search and i in self._state.search["results"]:
                line = self._highlight_search_match(i, line)

            # Apply line style
            if style:
                line = style.apply(line)

            lines.append(line)

        self._state.last_render = "\n".join(lines)
        self._state.dirty = False
        return self._state.last_render

    def _highlight_search_match(self, index: int, line: str) -> str:
        """Apply highlighting to search matches."""
        if not self._state.search["text"] or not line:
            return line

        try:
            if self._state.search["text"] in line:
                highlighted = Style("reverse").apply(self._state.search["text"])
                line = line.replace(self._state.search["text"], highlighted)
        except (ValueError, TypeError):
            pass

        # Special highlight for current search result - simplified comparison
        current_idx = self._state.search["index"]
        results = self._state.search["results"]
        if 0 <= current_idx < len(results) and index == results[current_idx]:
            line = Style("bright_white on_blue").apply(f"> {line}")

        return line

    async def log(
        self,
        *messages: Union[str, Text],
        sep: str = " ",
        style: Optional[Union[str, Style]] = None,
        level: str = "INFO",
    ) -> None:
        """Log one or more messages with optional styling."""
        text = sep.join(str(m) for m in messages)
        self.write(text, style=style, level=level)
        await self.refresh()

    async def debug(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log debug messages in dim style."""
        await self.log(*messages, sep=sep, style="dim", level="DEBUG")

    async def error(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log error messages in red."""
        await self.log(*messages, sep=sep, style="bold red", level="ERROR")

    async def critical(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log critical messages in bright red."""
        await self.log(
            *messages, sep=sep, style="reverse bold bright_red", level="CRITICAL"
        )

    async def warning(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log warning messages in yellow."""
        await self.log(*messages, sep=sep, style="yellow", level="WARNING")

    async def success(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log success messages in green."""
        await self.log(*messages, sep=sep, style="green", level="INFO")

    async def info(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log info messages in blue."""
        await self.log(*messages, sep=sep, style="blue", level="INFO")

    def get_visible_lines(self, height: Optional[int] = None) -> List[str]:
        """Get visible lines based on height constraint."""
        if not height:
            return [line for line, _, _ in self._state.buffer]

        if self.auto_scroll:
            return [line for line, _, _ in self._state.buffer[-height:]]
        return [line for line, _, _ in self._state.buffer[:height]]

    def set_log_level(self, level: str) -> "Console":
        """Set minimum log level to display."""
        level_upper = level.upper()
        if level_upper in self._state.log_levels:
            self._state.current_log_level = self._state.log_levels[level_upper]
        return self

    def search(self, text: str) -> List[int]:
        """Search for text in the console buffer."""
        if not text:
            self._state.search["text"] = None
            self._state.search["results"] = []
            self._state.search["index"] = -1
            self._state.dirty = True
            return []

        self._state.search["text"] = text
        self._state.search["results"] = [
            i for i, (line, _, _) in enumerate(self._state.buffer) if text in line
        ]

        if self._state.search["results"]:
            self._state.search["index"] = 0
        else:
            self._state.search["index"] = -1

        self._state.dirty = True
        return self._state.search["results"]

    def next_result(self) -> int:
        """Move to next search result."""
        if not self._state.search["results"]:
            return -1

        self._state.search["index"] = (self._state.search["index"] + 1) % len(
            self._state.search["results"]
        )
        self._state.dirty = True
        return self._state.search["index"]

    def prev_result(self) -> int:
        """Move to previous search result."""
        if not self._state.search["results"]:
            return -1

        self._state.search["index"] = (self._state.search["index"] - 1) % len(
            self._state.search["results"]
        )
        self._state.dirty = True
        return self._state.search["index"]

    def export(self, filename: str, output_format: str = "text") -> bool:
        """Export console contents to a file."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                if output_format == "text":
                    self._export_as_text(f)
                elif output_format == "html":
                    self._export_as_html(f)
                elif output_format == "json":
                    self._export_as_json(f)
                else:
                    # Default to plain text
                    self._export_as_text(f)
            return True
        except (IOError, OSError) as e:
            self._write_to_stderr(f"Export failed: {e}")
            return False

    def _export_as_text(self, file_obj: TextIO) -> None:
        """Export as plain text."""
        for line, _, _ in self._state.buffer:
            file_obj.write(f"{line}\n")

    def _export_as_html(self, file_obj: TextIO) -> None:
        """Export as HTML with styling."""
        file_obj.write("<html><head><style>")
        file_obj.write(
            "body { background: #000; color: #fff; font-family: monospace; }"
        )
        file_obj.write(
            ".red { color: #f00; } .green { color: #0f0; } .blue { color: #00f; }"
        )
        file_obj.write(
            ".yellow { color: #ff0; } .magenta { color: #f0f; } .cyan { color: #0ff; }"
        )
        file_obj.write("</style></head><body><pre>")

        for line, style, _ in self._state.buffer:
            css_class = ""
            if style and style.components:
                for comp in style.components:
                    if comp in ["red", "green", "blue", "yellow", "magenta", "cyan"]:
                        css_class = comp
                        break

            if css_class:
                file_obj.write(f'<span class="{css_class}">{line}</span>\n')
            else:
                file_obj.write(f"{line}\n")

        file_obj.write("</pre></body></html>")

    def _export_as_json(self, file_obj: TextIO) -> None:
        """Export as JSON."""
        entries = []
        for line, style, timestamp in self._state.buffer:
            entries.append(
                {
                    "text": line,
                    "style": str(style) if style else None,
                    "timestamp": timestamp,
                }
            )
        json.dump(entries, file_obj, indent=2)

    @contextmanager
    def progress(self, total: int = 100, description: str = ""):
        """Create a progress bar context manager."""
        progress_bar = ProgressBar(total=total)
        self.write(f"{description} [" + " " * 40 + "] 0%")
        index = len(self._state.buffer) - 1

        def update_func(value: int):
            nonlocal index
            if index < len(self._state.buffer):
                ratio = value / total
                filled = int(40 * ratio)
                percent = int(ratio * 100)
                progress_text = "█" * filled + " " * (40 - filled)

                # Update the line in buffer directly
                line = f"{description} [{progress_text}] {percent}%"
                style = self._state.buffer[index][1]
                timestamp = self._state.buffer[index][2]
                self._state.buffer[index] = (line, style, timestamp)
                self._state.dirty = True

        progress_bar.on_update = update_func
        try:
            yield progress_bar
        finally:
            # Ensure final update
            update_func(progress_bar.completed)
            self._state.dirty = True

    async def start_spinner(
        self, message: str = "", style: Optional[str] = None, spinner_type: str = "dots"
    ) -> None:
        """Start an animated spinner."""
        if self._state.spinner["task"] and not self._state.spinner["task"].done():
            self._state.spinner["task"].cancel()

        spinner_chars = self._state.spinner["chars"].get(
            spinner_type, self._state.spinner["chars"]["dots"]
        )
        final_style = Style(style) if style else None
        spinner_index = len(self._state.buffer)
        self.write(f"{spinner_chars[0]} {message}", style=final_style)

        async def animate_spinner():
            i = 0
            while True:
                await asyncio.sleep(0.1)
                char = spinner_chars[i % len(spinner_chars)]
                if spinner_index < len(self._state.buffer):
                    line = f"{char} {message}"
                    style = final_style
                    timestamp = self._state.buffer[spinner_index][2]
                    self._state.buffer[spinner_index] = (line, style, timestamp)
                    self._state.dirty = True
                    await self.refresh()
                i += 1

        self._state.spinner["active_index"] = spinner_index
        self._state.spinner["task"] = asyncio.create_task(animate_spinner())

    async def stop_spinner(
        self, message: Optional[str] = None, style: Optional[str] = None
    ) -> None:
        """Stop the animated spinner."""
        if self._state.spinner["task"] and not self._state.spinner["task"].done():
            self._state.spinner["task"].cancel()
            await asyncio.sleep(0.1)  # Give it time to cancel

            active_idx = self._state.spinner["active_index"]
            if active_idx is not None and active_idx < len(self._state.buffer):
                current_line = self._state.buffer[active_idx][0]
                if message is not None:
                    # Replace the spinner character with a completion character and new message
                    new_line = "✓ " + (message or current_line[2:])
                else:
                    # Replace just the spinner character
                    new_line = "✓ " + current_line[2:]

                final_style = Style(style) if style else self._state.buffer[active_idx][1]
                timestamp = self._state.buffer[active_idx][2]
                self._state.buffer[active_idx] = (new_line, final_style, timestamp)
                self._state.dirty = True
                await self.refresh()

            self._state.spinner["active_index"] = None
            self._state.spinner["task"] = None
