import sys
import asyncio
import time
import os
import json
from datetime import datetime
from typing import Optional, List, Union, TextIO, Dict, Callable, Any, Tuple
from contextlib import contextmanager

from .widget import Widget
from .style import Style
from .text import Text
from .progress import ProgressBar


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
        log_file: Optional[str] = None,
        log_level: str = "INFO",
        highlight_rules: Optional[Dict[str, str]] = None,
    ):
        """Initialize console widget.

        Args:
            file: File to write output to
            max_lines: Maximum number of lines to keep in buffer
            timestamp: Whether to show timestamps
            style: Default style for output
            scroll: Whether to auto-scroll to bottom
            log_file: Optional file path to write logs to
            log_level: Minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            highlight_rules: Dictionary of regex patterns to style names for syntax highlighting
        """
        super().__init__()
        self.file = file
        self.max_lines = max_lines
        self.show_timestamp = timestamp
        self.default_style = Style(style) if style else None
        self.auto_scroll = scroll
        self._buffer: List[tuple[str, Optional[Style], int]] = []  # text, style, timestamp
        self._dirty = False
        self._last_render = ""
        self._log_file = log_file
        self._log_file_handle = None
        self._log_levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }
        self._current_log_level = self._log_levels.get(log_level.upper(), 20)
        self._highlight_rules = highlight_rules or {}
        self._search_text = None
        self._search_results = []
        self._search_index = -1
        self._spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["-", "\\", "|", "/"],
            "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        }
        self._active_spinner = None
        self._spinner_task = None
        
        # Open log file if specified
        if self._log_file:
            try:
                self._log_file_handle = open(self._log_file, "a", encoding="utf-8")
            except (IOError, OSError) as e:
                self._write_to_stderr(f"Failed to open log file: {e}")

    def __del__(self):
        """Cleanup when destroyed."""
        if self._log_file_handle:
            try:
                self._log_file_handle.close()
            except:
                pass
        
        if self._spinner_task and not self._spinner_task.done():
            self._spinner_task.cancel()

    def _write_to_file(self, text: str) -> None:
        """Write text to log file if configured.
        
        Args:
            text: Text to write
        """
        if self._log_file_handle:
            try:
                self._log_file_handle.write(f"{text}\n")
                self._log_file_handle.flush()
            except (IOError, OSError) as e:
                self._write_to_stderr(f"Failed to write to log file: {e}")

    def _write_to_stderr(self, text: str) -> None:
        """Write text to stderr.
        
        Args:
            text: Text to write
        """
        try:
            print(text, file=sys.stderr)
        except:
            pass
            
    def write(
        self,
        text: Union[str, Text],
        style: Optional[Union[str, Style]] = None,
        timestamp: bool = None,
        level: str = "INFO",
    ) -> "Console":
        """Write text to console.

        Args:
            text: Text to write
            style: Optional style to apply
            timestamp: Override default timestamp setting
            level: Log level for this message

        Returns:
            Self for chaining
        """
        # Check log level
        message_level = self._log_levels.get(level.upper(), 20)
        if message_level < self._current_log_level:
            return self
            
        if isinstance(text, Text):
            content = text.render()
        else:
            content = str(text)
            
        # Apply syntax highlighting if rules exist
        if content and self._highlight_rules and not style:
            for pattern, highlight_style in self._highlight_rules.items():
                try:
                    import re
                    content = re.sub(
                        pattern,
                        lambda m: Style(highlight_style).apply(m.group(0)),
                        content
                    )
                except:
                    pass

        # Write to log file (without ANSI codes)
        try:
            import re
            clean_text = re.sub(r'\x1b\[[0-9;]*m', '', content)
            self._write_to_file(clean_text)
        except:
            self._write_to_file(content)

        # Handle multiline input
        lines = content.split("\n")
        current_time = datetime.now()
        for line in lines:
            if not line:
                continue

            if timestamp or (timestamp is None and self.show_timestamp):
                ts = f"[{current_time.strftime('%H:%M:%S')}] "
                line = ts + line

            # Resolve style priority: passed style > default style
            final_style = None
            if style:
                final_style = Style(style) if isinstance(style, str) else style
            elif self.default_style:
                final_style = self.default_style

            # Store line with timestamp (for sorting/filtering)
            timestamp_epoch = int(current_time.timestamp())
            self._buffer.append((line, final_style, timestamp_epoch))

        # Trim buffer if needed
        if len(self._buffer) > self.max_lines:
            self._buffer = self._buffer[-self.max_lines:]

        self._dirty = True
        return self
        
    def clear(self) -> "Console":
        """Clear the console buffer.

        Returns:
            Self for chaining
        """
        self._buffer.clear()
        self._dirty = True
        self._search_results.clear()
        self._search_index = -1
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
        highlight_search = self._search_text is not None
        
        for i, (text, style, _) in enumerate(self._buffer):
            line = text
            
            # Apply search highlighting
            if highlight_search and i in self._search_results:
                # Highlight the search term within the line
                try:
                    import re
                    if self._search_text in line:
                        highlighted = Style("reverse").apply(self._search_text)
                        line = line.replace(self._search_text, highlighted)
                except:
                    pass
                    
                # Special highlight for current search result
                if i == self._search_results[self._search_index]:
                    line = Style("bright_white on_blue").apply(f"> {line}")
            
            # Apply line style
            if style:
                line = style.apply(line)
                
            lines.append(line)
                
        self._last_render = "\n".join(lines)
        self._dirty = False
        return self._last_render
        
    async def log(
        self,
        *messages: Union[str, Text],
        sep: str = " ",
        style: Optional[Union[str, Style]] = None,
        level: str = "INFO",
    ) -> None:
        """Log one or more messages with optional styling.

        Args:
            *messages: Messages to log
            sep: Separator between messages
            style: Optional style to apply
            level: Log level for this message
        """
        text = sep.join(str(m) for m in messages)
        self.write(text, style=style, level=level)
        await self.refresh()
        
    async def debug(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log debug messages in dim style.
        
        Args:
            *messages: Debug messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="dim", level="DEBUG")
        
    async def error(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log error messages in red.

        Args:
            *messages: Error messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="bold red", level="ERROR")
        
    async def critical(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log critical messages in bright red.
        
        Args:
            *messages: Critical messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="reverse bold bright_red", level="CRITICAL")
        
    async def warning(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log warning messages in yellow.

        Args:
            *messages: Warning messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="yellow", level="WARNING")
        
    async def success(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log success messages in green.

        Args:
            *messages: Success messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="green", level="INFO")
        
    async def info(self, *messages: Union[str, Text], sep: str = " ") -> None:
        """Log info messages in blue.

        Args:
            *messages: Info messages to log
            sep: Separator between messages
        """
        await self.log(*messages, sep=sep, style="blue", level="INFO")

    def get_visible_lines(self, height: Optional[int] = None) -> List[str]:
        """Get visible lines based on height constraint.
        
        Args:
            height: Maximum number of lines to return
            
        Returns:
            List of visible lines
        """
        if not height:
            return [line for line, _, _ in self._buffer]
            
        if self.auto_scroll:
            return [line for line, _, _ in self._buffer[-height:]]
        return [line for line, _, _ in self._buffer[:height]]
        
    def set_log_level(self, level: str) -> "Console":
        """Set minimum log level to display.
        
        Args:
            level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Self for chaining
        """
        level_upper = level.upper()
        if level_upper in self._log_levels:
            self._current_log_level = self._log_levels[level_upper]
        return self
        
    def search(self, text: str) -> List[int]:
        """Search for text in the console buffer.
        
        Args:
            text: Text to search for
            
        Returns:
            List of line indices containing the search text
        """
        if not text:
            self._search_text = None
            self._search_results = []
            self._search_index = -1
            self._dirty = True
            return []
            
        self._search_text = text
        self._search_results = [
            i for i, (line, _, _) in enumerate(self._buffer)
            if text in line
        ]
        
        if self._search_results:
            self._search_index = 0
        else:
            self._search_index = -1
            
        self._dirty = True
        return self._search_results
        
    def next_result(self) -> int:
        """Move to next search result.
        
        Returns:
            Current search result index or -1 if no results
        """
        if not self._search_results:
            return -1
            
        self._search_index = (self._search_index + 1) % len(self._search_results)
        self._dirty = True
        return self._search_index
        
    def prev_result(self) -> int:
        """Move to previous search result.
        
        Returns:
            Current search result index or -1 if no results
        """
        if not self._search_results:
            return -1
            
        self._search_index = (self._search_index - 1) % len(self._search_results)
        self._dirty = True
        return self._search_index
        
    def export(self, filename: str, format: str = "text") -> bool:
        """Export console contents to a file.
        
        Args:
            filename: File to export to
            format: Export format ("text", "html", "json")
            
        Returns:
            True if export was successful
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                if format == "text":
                    # Export plain text (no styling)
                    for line, _, _ in self._buffer:
                        f.write(f"{line}\n")
                        
                elif format == "html":
                    # Export as HTML with styling
                    f.write("<html><head><style>")
                    f.write("body { background: #000; color: #fff; font-family: monospace; }")
                    f.write(".red { color: #f00; } .green { color: #0f0; } .blue { color: #00f; }")
                    f.write(".yellow { color: #ff0; } .magenta { color: #f0f; } .cyan { color: #0ff; }")
                    f.write("</style></head><body><pre>")
                    
                    for line, style, _ in self._buffer:
                        css_class = ""
                        if style and style.components:
                            for comp in style.components:
                                if comp in ["red", "green", "blue", "yellow", "magenta", "cyan"]:
                                    css_class = comp
                                    break
                        
                        if css_class:
                            f.write(f'<span class="{css_class}">{line}</span>\n')
                        else:
                            f.write(f"{line}\n")
                            
                    f.write("</pre></body></html>")
                    
                elif format == "json":
                    # Export as JSON
                    entries = []
                    for line, style, timestamp in self._buffer:
                        entries.append({
                            "text": line,
                            "style": str(style) if style else None,
                            "timestamp": timestamp
                        })
                    json.dump(entries, f, indent=2)
                    
                else:
                    # Default to plain text
                    for line, _, _ in self._buffer:
                        f.write(f"{line}\n")
            return True
            
        except Exception as e:
            self._write_to_stderr(f"Export failed: {e}")
            return False
    
    @contextmanager
    def progress(self, total: int = 100, description: str = "") -> ProgressBar:
        """Create a progress bar context manager.
        
        Args:
            total: Total steps
            description: Progress description
            
        Yields:
            ProgressBar object
        """
        progress = ProgressBar(total=total)
        self.write(f"{description} [" + " " * 40 + "] 0%")
        index = len(self._buffer) - 1
        
        def update_func(value: int):
            nonlocal index
            if index < len(self._buffer):
                ratio = value / total
                filled = int(40 * ratio)
                percent = int(ratio * 100)
                bar = "█" * filled + " " * (40 - filled)
                
                # Update the line in buffer directly
                line = f"{description} [{bar}] {percent}%"
                style = self._buffer[index][1]
                timestamp = self._buffer[index][2]
                self._buffer[index] = (line, style, timestamp)
                self._dirty = True
                
        progress.on_update = update_func
        try:
            yield progress
        finally:
            # Ensure final update
            update_func(progress.completed)
            self._dirty = True
    
    async def start_spinner(self, message: str = "", style: Optional[str] = None, spinner_type: str = "dots") -> None:
        """Start an animated spinner.
        
        Args:
            message: Message to display with spinner
            style: Style for the spinner
            spinner_type: Type of spinner animation (dots, line, braille)
        """
        if self._spinner_task and not self._spinner_task.done():
            self._spinner_task.cancel()
            
        spinner_chars = self._spinners.get(spinner_type, self._spinners["dots"])
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
                
        self._active_spinner = spinner_index
        self._spinner_task = asyncio.create_task(animate_spinner())
        
    async def stop_spinner(self, message: Optional[str] = None, style: Optional[str] = None) -> None:
        """Stop the animated spinner.
        
        Args:
            message: Final message to display (or None to keep last message)
            style: Style for the final message
        """
        if self._spinner_task and not self._spinner_task.done():
            self._spinner_task.cancel()
            await asyncio.sleep(0.1)  # Give it time to cancel
            
            if self._active_spinner is not None and self._active_spinner < len(self._buffer):
                current_line = self._buffer[self._active_spinner][0]
                if message is not None:
                    # Replace the spinner character with a completion character and new message
                    new_line = "✓ " + (message or current_line[2:])
                else:
                    # Replace just the spinner character
                    new_line = "✓ " + current_line[2:]
                    
                final_style = Style(style) if style else self._buffer[self._active_spinner][1]
                timestamp = self._buffer[self._active_spinner][2]
                self._buffer[self._active_spinner] = (new_line, final_style, timestamp)
                self._dirty = True
                await self.refresh()
                
            self._active_spinner = None
            self._spinner_task = None
