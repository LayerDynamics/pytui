"""Console widget module for terminal output management."""

import sys
import asyncio
import json
import re
import contextlib
from datetime import datetime
from typing import Optional, List, Union, TextIO, Dict, Any, Tuple, Generator
from dataclasses import dataclass, field
from enum import Enum

from .widget import Widget
from .style import Style
from .text import Text
from .progress import ProgressBar
from .events import Event


class LogLevel(Enum):
    """Log levels with integer values."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class ConsoleConfig:
    """Configuration options for Console widget."""

    # Group I/O related settings
    io: Dict[str, Any] = field(
        default_factory=lambda: {
            "file": sys.stdout,
            "log_file": None,
        }
    )

    # Group display settings
    display: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_lines": 1000,
            "timestamp": False,
            "style": None,
            "scroll": True,
        }
    )

    # Log settings
    log_level: LogLevel = LogLevel.INFO
    highlight_rules: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConsoleState:
    """Internal state for Console widget."""

    # Content state
    buffer: List[Tuple[str, Optional["Style"], int]] = field(default_factory=list)
    dirty: bool = False
    last_render: str = ""

    # Resources
    log_file_handle: Optional[TextIO] = None

    # Search state
    search: Dict[str, Any] = field(
        default_factory=lambda: {"text": None, "results": [], "index": -1}
    )

    # Animation state
    animation: Dict[str, Any] = field(
        default_factory=lambda: {
            "spinner_chars": {
                "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
                "line": ["-", "\\", "|", "/"],
                "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            },
            "active_index": None,
            "task": None,
        }
    )


class ConsoleBase(Widget):
    """Base class for console to reduce public method count."""

    def __init__(self):
        """Initialize base console."""
        super().__init__()
        self._events = {}  # Store event handlers
        self._write_handlers = []
        self._state = ConsoleState()
        self._last_event = None  # Initialize _last_event
        self._setup_default_events()

    def _setup_default_events(self):
        """Setup default event handlers."""
        self._events["write"] = []
        self._events["console_init"] = []

    def _emit_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Emit an event to registered handlers."""
        event = Event(event_name, data)
        if event_name in self._events:
            for handler in self._events[event_name]:
                handler(event)
        return event

    def write(
        self,
        text: Union[str, Text],
        style: Optional[Union[str, Style]] = None,
        timestamp: Optional[bool] = None,
        level: Optional[Union[str, LogLevel]] = None,
    ) -> "ConsoleBase":
        """Write content to console with optional styling."""
        # Create and emit write event
        event = self._emit_event(
            "write",
            {"text": text, "style": style, "timestamp": timestamp, "level": level},
        )

        # Only process if event not prevented
        if not event.prevented:
            # Process text with style
            content = str(text)
            if style:
                content = (
                    Style(style).apply(content)
                    if isinstance(style, str)
                    else style.apply(content)
                )

            # Add timestamp if requested
            if timestamp:
                ts = f"[{datetime.now().strftime('%H:%M:%S')}] "
                content = ts + content

            # Handle log level
            if level:
                level_name = level if isinstance(level, str) else level.name
                content = f"[{level_name}] {content}"

            # Store last event
            self._last_event = event

        return self

    def _highlight_search_match(self, index: int, line: str) -> str:
        """Apply highlighting to search matches."""
        if not hasattr(self, "_state"):
            return line

        if not self._state.search["text"] or not line:
            return line

        try:
            if self._state.search["text"] in line:
                highlighted = Style("reverse").apply(self._state.search["text"])
                line = line.replace(self._state.search["text"], highlighted)
        except (ValueError, TypeError):
            return line

        current_idx = self._state.search["index"]
        results = self._state.search["results"]
        if 0 <= current_idx < len(results) and index == results[current_idx]:
            line = Style("bright_white on_blue").apply(f"> {line}")

        return line

    def handle_search(self, action: str, text: str = "") -> Union[List[int], int]:
        """Handle search-related actions."""
        # Move _handle_search implementation here
        if action == "search":
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
            self._state.search["index"] = 0 if self._state.search["results"] else -1
            self._state.dirty = True
            return self._state.search["results"]

        if not self._state.search["results"]:
            return -1

        if action == "next":
            self._state.search["index"] = (self._state.search["index"] + 1) % len(
                self._state.search["results"]
            )
        elif action == "prev":
            self._state.search["index"] = (self._state.search["index"] - 1) % len(
                self._state.search["results"]
            )

        self._state.dirty = True
        return self._state.search["index"]

    def _write_to_stderr(self, text: str) -> None:
        """Write text to stderr."""
        try:
            print(text, file=sys.stderr)
        except (IOError, OSError):
            pass

    def _export_as_text(self, file_obj: TextIO) -> None:
        """Export as plain text."""
        for line, _, _ in self._state.buffer:
            file_obj.write(f"{line}\n")

    def _export_as_html(self, file_obj: TextIO) -> None:
        """Export as HTML with styling."""
        file_obj.write("<html><head><style>")
        file_obj.write("body { background: #000; color: #fff; font-family: monospace; }")
        file_obj.write(".red { color: #f00; } .green { color: #0f0; } .blue { color: #00f; }")
        file_obj.write(".yellow { color: #ff0; } .magenta { color: #f0f; } .cyan { color: #0ff; }")
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
            entries.append({
                "text": line,
                "style": str(style) if style else None,
                "timestamp": timestamp,
            })
        json.dump(entries, file_obj, indent=2)

    def handle_export(self, filename: str, fmt: str = "text") -> bool:
        """Handle export operations."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                if fmt == "text":
                    self._export_as_text(f)
                elif fmt == "html":
                    self._export_as_html(f)
                elif fmt == "json":
                    self._export_as_json(f)
                else:
                    self._export_as_text(f)
            return True
        except (IOError, OSError) as e:
            self._write_to_stderr(f"Export failed: {e}")
            return False


class ConsoleLogging:
    """Mixin class for console logging functionality."""

    async def log(self, *messages: Union[str, Text], sep: str = " ", 
                 style: Optional[Union[str, Style]] = None, level: str = "INFO") -> None:
        """Log one or more messages with optional styling."""
        text = sep.join(str(m) for m in messages)
        self.write(text, style=style, level=level)
        await self.refresh()

    async def debug(self, *messages, sep=" "):
        """Log debug messages."""
        await self.log_message(LogLevel.DEBUG, *messages, sep=sep, style="dim")

    async def info(self, *messages, sep=" "):
        """Log info messages."""
        await self.log_message(LogLevel.INFO, *messages, sep=sep, style="blue")

    async def warning(self, *messages, sep=" "):
        """Log messages at WARNING level."""
        await self.log_message(LogLevel.WARNING, *messages, sep=sep, style="yellow")

    async def error(self, *messages, sep=" "):
        """Log messages at ERROR level."""
        await self.log_message(LogLevel.ERROR, *messages, sep=sep, style="bold red")

    async def critical(self, *messages, sep=" "):
        """Log messages at CRITICAL level."""
        await self.log_message(LogLevel.CRITICAL, *messages, sep=sep, 
                             style="reverse bold bright_red")

    async def success(self, *messages, sep=" "):
        """Log success message at INFO level with green styling."""
        await self.log_message(LogLevel.INFO, *messages, sep=sep, style="green")


class Console(ConsoleBase, ConsoleLogging):
    """Console output widget with advanced features."""

    def __init__(self, *, config: Optional[ConsoleConfig] = None):
        """Initialize console widget."""
        super().__init__()

        # Use config if provided, otherwise use defaults
        self._config = config or ConsoleConfig()

        # Set up log file if specified
        self._setup_log_file()
        self._setup_log_file()

    def _setup_log_file(self):
        """Set up log file handling."""
        log_file = self._config.io["log_file"]
        if not log_file:
            return

        try:
            # Use context manager for file operations
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"--- Console log started at {datetime.now().isoformat()} ---\n"
                )
                # Keep file handle open for logging
                self._state.log_file_handle = f

        except (IOError, OSError) as e:
            self._write_to_stderr(f"Failed to open log file: {e}")

    # Property accessors
    @property
    def file(self) -> TextIO:
        """Get output file."""
        return self._config.io["file"]

    @property
    def max_lines(self) -> int:
        """Get maximum lines."""
        return self._config.display["max_lines"]

    @property
    def show_timestamp(self) -> bool:
        """Get timestamp setting."""
        return self._config.display["timestamp"]

    @property
    def default_style(self) -> Optional[Style]:
        """Get default style."""
        style_str = self._config.display["style"]
        return Style(style_str) if style_str else None

    @property
    def auto_scroll(self) -> bool:
        """Get auto-scroll setting."""
        return self._config.display["scroll"]

    def __del__(self):
        """Cleanup when destroyed."""
        self._cleanup_resources()

    # Setup and resource handling methods
    def _cleanup_resources(self):
        """Clean up allocated resources."""
        if self._state.log_file_handle:
            try:
                self._state.log_file_handle.close()
            except (IOError, OSError):
                pass

        spinner_task = self._state.animation["task"]
        if spinner_task and not spinner_task.done():
            spinner_task.cancel()

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

    # Content handling methods
    def write(self, text, style=None, timestamp=None, level=None):
        """Write content to console with optional styling.

        Acts as a unified entry point for logging methods.
        """
        # Check log level
        msg_level = LogLevel.INFO
        if level:
            if isinstance(level, str):
                try:
                    msg_level = LogLevel[level.upper()]
                except KeyError:
                    msg_level = LogLevel.INFO
            else:
                msg_level = level

        if msg_level.value < self._config.log_level.value:
            return self

        # Process and store content
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

    async def _log_with_level(
        self,
        level: LogLevel,
        *messages: Union[str, Text],
        sep: str = " ",
        style: Optional[Union[str, Style]] = None,
    ) -> None:
        """Internal method to handle logging with different levels."""
        text = sep.join(str(m) for m in messages)
        self.write(text, style=style, level=level)
        await self.refresh()

    # Public logging interface
    async def log_message(
        self,\
        level: LogLevel,\
        *messages: Union[str, Text],\
        sep: str = " ",\
        style: Optional[Union[str, Style]] = None,
    ) -> None:
        """Log messages with specified level."""
        await self._log_with_level(level, *messages, sep=sep, style=style)

    async def debug(self, *messages, sep=" "):
        """Log debug messages."""
        await self.log_message(LogLevel.DEBUG, *messages, sep=sep, style="dim")

    async def info(self, *messages, sep=" "):
        """Log info messages."""
        await self.log_message(LogLevel.INFO, *messages, sep=sep, style="blue")

    async def warning(self, *messages, sep=" "):
        """Log messages at WARNING level."""
        await self.log_message(LogLevel.WARNING, *messages, sep=sep, style="yellow")

    async def error(self, *messages, sep=" "):
        """Log messages at ERROR level."""
        await self.log_message(LogLevel.ERROR, *messages, sep=sep, style="bold red")

    async def critical(self, *messages, sep=" "):
        """Log messages at CRITICAL level."""
        await self.log_message(
            LogLevel.CRITICAL, *messages, sep=sep, style="reverse bold bright_red"
        )

    async def success(self, *messages, sep=" "):
        """Log success message at INFO level with green styling."""
        await self.log_message(LogLevel.INFO, *messages, sep=sep, style="green")

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
        if level_upper in LogLevel.__members__:
            self._config.log_level = LogLevel[level_upper]
        return self

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

    @contextlib.contextmanager
    def progress(
        self, total: int = 100, description: str = ""
    ) -> Generator["ProgressBar", None, None]:
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

                line = f"{description} [{progress_text}] {percent}%"
                style = self._state.buffer[index][1]
                timestamp = self._state.buffer[index][2]
                self._state.buffer[index] = (line, style, timestamp)
                self._state.dirty = True

        progress_bar.on_update = update_func
        try:
            yield progress_bar
        finally:
            update_func(progress_bar.completed)
            self._state.dirty = True

    # Move some public methods to private implementations
    _action_handlers = {
        "search": lambda self, text: self.handle_search("search", text),
        "next": lambda self: self.handle_search("next"),
        "prev": lambda self: self.handle_search("prev"),
        "export": lambda self, filename, fmt="text": self.handle_export(filename, fmt),
    }

    def handle(self, action: str, *args, **kwargs) -> Any:
        """Handle various actions through a single unified method."""
        if action in self._action_handlers:
            return self._action_handlers[action](self, *args, **kwargs)
        return None

    async def start_spinner(
        self, message: str = "", style: Optional[str] = None, spinner_type: str = "dots"
    ) -> None:
        """Start an animated spinner."""
        if self._state.animation["task"] and not self._state.animation["task"].done():
            self._state.animation["task"].cancel()

        spinner_chars = self._state.animation["spinner_chars"].get(
            spinner_type, self._state.animation["spinner_chars"]["dots"]
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

        self._state.animation["active_index"] = spinner_index
        self._state.animation["task"] = asyncio.create_task(animate_spinner())

    async def stop_spinner(
        self, message: Optional[str] = None, style: Optional[str] = None
    ) -> None:
        """Stop the animated spinner."""
        if self._state.animation["task"] and not self._state.animation["task"].done():
            self._state.animation["task"].cancel()
            await asyncio.sleep(0.1)  # Give it time to cancel

            active_idx = self._state.animation["active_index"]
            if active_idx is not None and active_idx < len(self._state.buffer):
                current_line = self._state.buffer[active_idx][0]
                if message is not None:
                    # Replace the spinner character with a completion character and new message
                    new_line = "✓ " + (message or current_line[2:])
                else:
                    # Replace just the spinner character
                    new_line = "✓ " + current_line[2:]

                final_style = (
                    Style(style) if style else self._state.buffer[active_idx][1]
                )
                timestamp = self._state.buffer[active_idx][2]
                self._state.buffer[active_idx] = (new_line, final_style, timestamp)
                self._state.dirty = True
                await self.refresh()

            self._state.animation["active_index"] = None
            self._state.animation["task"] = None
