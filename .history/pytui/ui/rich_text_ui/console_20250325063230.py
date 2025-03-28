"""Console widget module for terminal output management.

Provides advanced console functionality including logging, searching, progress indicators and more.
"""

import sys
import asyncio
import json
import re
from datetime import datetime
from typing import Optional, List, Union, TextIO, Dict
from contextlib import contextmanager
from dataclasses import dataclass

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


class Console(Widget):
    """Console output widget with advanced features."""

    def __init__(
        self,
        *,
        config: Optional[ConsoleConfig] = None,
        file: TextIO = sys.stdout,
        max_lines: int = 1000,
        timestamp: bool = False,
        style: Optional[str] = None,
        scroll: bool = True,
    ):
        """Initialize console widget.

        Args:
            config: Configuration options (overrides individual parameters)
            file: File to write output to
            max_lines: Maximum number of lines to keep in buffer
            timestamp: Whether to show timestamps
            style: Default style for output
            scroll: Whether to auto-scroll to bottom
        """
        super().__init__()

        # Use config if provided, otherwise build from parameters
        self._config = config or ConsoleConfig(
            file=file,
            max_lines=max_lines,
            timestamp=timestamp,
            style=style,
            scroll=scroll,
        )

        # Public properties
        self.file = self._config.file
        self.max_lines = self._config.max_lines
        self.show_timestamp = self._config.timestamp
        self.default_style = Style(self._config.style) if self._config.style else None
        self.auto_scroll = self._config.scroll

        # Private state
        self._buffer = []  # [(text, style, timestamp)]
        self._dirty = False
        self._last_render = ""
        self._log_file_handle = None
        self._log_levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        self._current_log_level = self._log_levels.get(
            self._config.log_level.upper() if self._config.log_level else "INFO", 20
        )
        self._search_state = {"text": None, "results": [], "index": -1}
        self._spinner_state = {
            "chars": {
                "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
                "line": ["-", "\\", "|", "/"],
                "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            },
            "active_index": None,
            "task": None,
        }

        # Open log file if specified
        self._setup_log_file()

    def _setup_log_file(self):
        """Set up log file handling."""
        if self._config.log_file:
            try:
                self._log_file_handle = open(
                    self._config.log_file, "a", encoding="utf-8"
                )
            except (IOError, OSError) as e:
                self._write_to_stderr(f"Failed to open log file: {e}")

    def __del__(self):
        """Cleanup when destroyed."""
        self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up allocated resources."""
        if self._log_file_handle:
            try:
                self._log_file_handle.close()
            except (IOError, OSError):
                pass

        if self._spinner_state["task"] and not self._spinner_state["task"].done():
            self._spinner_state["task"].cancel()

    def _write_to_file(self, text: str) -> None:
        """Write text to log file if configured."""
        if self._log_file_handle:
            try:
                self._log_file_handle.write(f"{text}\n")
                self._log_file_handle.flush()
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
        message_level = self._log_levels.get(level.upper(), 20)
        if message_level < self._current_log_level:
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

        for pattern, highlight_style in self._config.highlight_rules.items():
            # Create a copy of the style for each match to avoid cell-var-from-loop issue
            style_str = highlight_style
            try:
                content = re.sub(
                    pattern, lambda m: Style(style_str).apply(m.group(0)), content
                )
            except (re.error, ValueError, TypeError):
                pass
        return content

    def _write_to_log_file(self, content: str) -> None:
        """Write clean content to log file."""
        if not self._log_file_handle:
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
            self._buffer.append((line, final_style, timestamp_epoch))

        # Trim buffer if needed
        if len(self._buffer) > self.max_lines:
            self._buffer = self._buffer[-self.max_lines :]

        self._dirty = True

    def clear(self) -> "Console":
        """Clear the console buffer."""
        self._buffer.clear()
        self._dirty = True
        self._search_state["results"].clear()
        self._search_state["index"] = -1
        return self

    async def update(self, content: Union[str, Text]) -> None:
        """Update console content."""
        self.write(content)
        await self.refresh()

    def render(self) -> str:
        """Render buffered content."""
        if not self._dirty and self._last_render:
            return self._last_render

        lines = []
        highlight_search = self._search_state["text"] is not None

        for i, (text, style, _) in enumerate(self._buffer):
            line = text

            # Apply search highlighting
            if highlight_search and i in self._search_state["results"]:
                line = self._highlight_search_match(i, line)

            # Apply line style
            if style:
                line = style.apply(line)

            lines.append(line)

        self._last_render = "\n".join(lines)
        self._dirty = False
        return self._last_render

    def _highlight_search_match(self, index: int, line: str) -> str:
        """Apply highlighting to search matches."""
        if not self._search_state["text"] or not line:
            return line

        try:
            if self._search_state["text"] in line:
                highlighted = Style("reverse").apply(self._search_state["text"])
                line = line.replace(self._search_state["text"], highlighted)
        except (ValueError, TypeError):
            pass

        # Special highlight for current search result
        current_idx = self._search_state["index"]
        if (
            current_idx >= 0
            and current_idx < len(self._search_state["results"])
            and index == self._search_state["results"][current_idx]
        ):
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
            return [line for line, _, _ in self._buffer]

        if self.auto_scroll:
            return [line for line, _, _ in self._buffer[-height:]]
        return [line for line, _, _ in self._buffer[:height]]

    def set_log_level(self, level: str) -> "Console":
        """Set minimum log level to display."""
        level_upper = level.upper()
        if level_upper in self._log_levels:
            self._current_log_level = self._log_levels[level_upper]
        return self

    def search(self, text: str) -> List[int]:
        """Search for text in the console buffer."""
        if not text:
            self._search_state["text"] = None
            self._search_state["results"] = []
            self._search_state["index"] = -1
            self._dirty = True
            return []

        self._search_state["text"] = text
        self._search_state["results"] = [
            i for i, (line, _, _) in enumerate(self._buffer) if text in line
        ]

        if self._search_state["results"]:
            self._search_state["index"] = 0
        else:
            self._search_state["index"] = -1

        self._dirty = True
        return self._search_state["results"]

    def next_result(self) -> int:
        """Move to next search result."""
        if not self._search_state["results"]:
            return -1

        self._search_state["index"] = (self._search_state["index"] + 1) % len(
            self._search_state["results"]
        )
        self._dirty = True
        return self._search_state["index"]

    def prev_result(self) -> int:
        """Move to previous search result."""
        if not self._search_state["results"]:
            return -1

        self._search_state["index"] = (self._search_state["index"] - 1) % len(
            self._search_state["results"]
        )
        self._dirty = True
        return self._search_state["index"]

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
        for line, _, _ in self._buffer:
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

        for line, style, _ in self._buffer:
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
        for line, style, timestamp in self._buffer:
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
        index = len(self._buffer) - 1

        def update_func(value: int):
            nonlocal index
            if index < len(self._buffer):
                ratio = value / total
                filled = int(40 * ratio)
                percent = int(ratio * 100)
                progress_text = "█" * filled + " " * (40 - filled)

                # Update the line in buffer directly
                line = f"{description} [{progress_text}] {percent}%"
                style = self._buffer[index][1]
                timestamp = self._buffer[index][2]
                self._buffer[index] = (line, style, timestamp)
                self._dirty = True

        progress_bar.on_update = update_func
        try:
            yield progress_bar
        finally:
            # Ensure final update
            update_func(progress_bar.completed)
            self._dirty = True

    async def start_spinner(
        self, message: str = "", style: Optional[str] = None, spinner_type: str = "dots"
    ) -> None:
        """Start an animated spinner."""
        if self._spinner_state["task"] and not self._spinner_state["task"].done():
            self._spinner_state["task"].cancel()

        spinner_chars = self._spinner_state["chars"].get(
            spinner_type, self._spinner_state["chars"]["dots"]
        )
        final_style = Style(style) if style else None
        spinner_index = len(self._buffer)
        self.write(f"{spinner_chars[0]} {message}", style=final_style)

        async def animate_spinner():
            i = 0
            while True:
                await asyncio.sleep(0.1)
                char = spinner_chars[i % len(spinner_chars)]
                if spinner_index < len(self._buffer):
                    line = f"{char} {message}"
                    style = final_style
                    timestamp = self._buffer[spinner_index][2]
                    self._buffer[spinner_index] = (line, style, timestamp)
                    self._dirty = True
                    await self.refresh()
                i += 1

        self._spinner_state["active_index"] = spinner_index
        self._spinner_state["task"] = asyncio.create_task(animate_spinner())

    async def stop_spinner(
        self, message: Optional[str] = None, style: Optional[str] = None
    ) -> None:
        """Stop the animated spinner."""
        if self._spinner_state["task"] and not self._spinner_state["task"].done():
            self._spinner_state["task"].cancel()
            await asyncio.sleep(0.1)  # Give it time to cancel

            active_idx = self._spinner_state["active_index"]
            if active_idx is not None and active_idx < len(self._buffer):
                current_line = self._buffer[active_idx][0]
                if message is not None:
                    # Replace the spinner character with a completion character and new message
                    new_line = "✓ " + (message or current_line[2:])
                else:
                    # Replace just the spinner character
                    new_line = "✓ " + current_line[2:]

                final_style = Style(style) if style else self._buffer[active_idx][1]
                timestamp = self._buffer[active_idx][2]
                self._buffer[active_idx] = (new_line, final_style, timestamp)
                self._dirty = True
                await self.refresh()

            self._spinner_state["active_index"] = None
            self._spinner_state["task"] = None
