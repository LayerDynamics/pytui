"""Rich and textual UI components implementation.

This module provides alternative implementations of rich and textual widgets
that can be used when the actual packages are not available. These implementations
provide similar interfaces but with simplified functionality.
"""

import sys
import re
import os
import asyncio
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Set, Iterable
import signal

# ============================
# Color and Style Handling
# ============================


class Style:
    """Style representation for text formatting."""

    COLORS = {
        # Basic colors
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        # Bright colors
        "bright_black": "\033[90m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
        # Others
        "reset": "\033[0m",
        "dim": "\033[2m",
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
    }

    # Check if terminal supports color
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        SUPPORTS_COLOR = True
    else:
        SUPPORTS_COLOR = False

    def __init__(self, style_string=""):
        """Initialize style from string.

        Args:
            style_string: Space-separated style components (e.g., "bold red")
        """
        self.components = set()
        if style_string:
            for component in style_string.split():
                self.components.add(component)

    def __add__(self, other):
        """Combine two styles."""
        if not other:
            return self
        result = Style()
        result.components = self.components.copy()
        if isinstance(other, Style):
            result.components.update(other.components)
        elif isinstance(other, str):
            result.components.update(Style(other).components)
        return result

    def __str__(self):
        """Return the string representation."""
        return " ".join(self.components)

    def apply(self, text):
        """Apply this style to text."""
        if not self.SUPPORTS_COLOR or not self.components:
            return text

        codes = []
        for comp in self.components:
            if comp in self.COLORS:
                codes.append(self.COLORS[comp])

        if not codes:
            return text

        return f"{''.join(codes)}{text}{self.COLORS['reset']}"


# ============================
# Base Widget Classes
# ============================


class Widget:
    """Base class for all UI widgets."""

    def __init__(self, name=None, widget_id=None):
        """Initialize widget with standard attributes.

        Args:
            name: Widget name
            widget_id: Widget ID
        """
        self.name = name
        self.id = widget_id or id(self)
        self.parent = None
        self.children = []
        self.styles = StyleManager(self)
        self.visible = True
        self.focused = False
        self.hover = False
        self.width = None
        self.height = None
        self.classes = set()
        self._event_handlers = {}
        self.content = ""
        self._content = ""
        self._text_parts = []

    def render(self) -> str:
        """Render the widget to a string representation."""
        return ""

    def __str__(self):
        """Convert widget to string."""
        return self.render()

    async def mount(self, *widgets):
        """Mount child widgets.

        Args:
            *widgets: Child widgets to mount
        """
        for widget in widgets:
            if widget.parent:
                widget.parent.children.remove(widget)
            widget.parent = self
            self.children.append(widget)
        await self.refresh()
        return self

    def remove_widget(self, widget):
        """Remove a child widget.

        Args:
            widget: Widget to remove
        """
        if widget in self.children:
            self.children.remove(widget)
            widget.parent = None

    async def update(self, content):
        """Update widget content.

        Args:
            content: New content to update the widget with
        """
        if hasattr(self, "content"):
            if isinstance(content, (str, int, float)):
                self.content = str(content)
            elif hasattr(content, "render"):
                self.content = content
            else:
                self.content = str(content)

        if hasattr(self, "_content"):
            has_style = hasattr(self, "style")
            text_content = str(content)
            style_value = self.style if has_style else None
            self._text_parts = [(text_content, style_value)]

        if hasattr(self, "_text_parts"):
            self._text_parts = (
                [(str(content), self.style)]
                if hasattr(self, "style")
                else [(str(content), None)]
            )

        if self.children and isinstance(content, (list, tuple)):
            # Update children if content is a sequence
            for child, child_content in zip(self.children, content):
                await child.update(child_content)

        await self.refresh()

    async def refresh(self):
        """Refresh the widget display."""
        # Clear screen and move cursor to top
        sys.stdout.write("\033[2J\033[H")

        # Render and display the widget
        rendered = self.render()
        if rendered:
            # Use write() to avoid extra newlines from print()
            sys.stdout.write(rendered)
            sys.stdout.write("\n")

        # Force flush the output
        sys.stdout.flush()

    def focus(self):
        """Focus this widget."""
        if self.parent:
            self.parent.set_focus(self)
        self.focused = True

    def set_focus(self, widget):
        """Set focus to a child widget.

        Args:
            widget: Widget to focus
        """
        for child in self.children:
            child.focused = child == widget

    def add_class(self, class_name):
        """Add a CSS-like class to the widget.

        Args:
            class_name: Class to add
        """
        self.classes.add(class_name)

    def remove_class(self, class_name):
        """Remove a CSS-like class from the widget.

        Args:
            class_name: Class to remove
        """
        if class_name in self.classes:
            self.classes.remove(class_name)

    def on(self, event_name, callback):
        """Register an event handler.

        Args:
            event_name: Event to handle
            callback: Handler function
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(callback)

    async def emit(self, event_name, *args, **kwargs):
        """Emit an event to registered handlers.

        Args:
            event_name: Event to emit
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        handlers = self._event_handlers.get(event_name, [])
        results = []
        for handler in handlers:
            result = handler(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            results.append(result)
        return results


class StyleManager:
    """Manages widget styles."""

    def __init__(self, widget):
        """Initialize style manager.

        Args:
            widget: Widget to manage styles for
        """
        self.widget = widget
        self._styles = {}

    def __getitem__(self, key):
        """Get a style property.

        Args:
            key: Property name

        Returns:
            Property value
        """
        return self._styles.get(key)

    def __setitem__(self, key, value):
        """Set a style property.

        Args:
            key: Property name
            value: Property value
        """
        self._styles[key] = value

    def get(self, key, default=None):
        """Get a style property with default.

        Args:
            key: Property name
            default: Default value

        Returns:
            Property value or default
        """
        return self._styles.get(key, default)

    @staticmethod
    def _linear(t):
        return t

    @staticmethod
    def _ease_in(t):
        return t * t

    @staticmethod
    def _ease_out(t):
        return 1 - (1 - t) * (1 - t)

    async def animate(self, property_name, target_value, duration=0.3, easing="linear"):
        """Animate a style property change.

        Args:
            property_name: Property to animate
            target_value: Target value
            duration: Animation duration in seconds (must be positive)
            easing: Easing function ('linear', 'ease-in', 'ease-out')

        Examples:
            await widget.styles.animate('opacity', 0.5, duration=1.0)
            await widget.styles.animate('width', 100, easing='ease-in')
        """
        duration = max(0.0, float(duration))
        if easing not in {"linear", "ease-in", "ease-out"}:
            easing = "linear"

        try:
            start = float(self._styles.get(property_name, 0))
            target = float(target_value)
            frame_count = int(duration * 60)

            if frame_count < 1:
                self._styles[property_name] = target
                await self.widget.refresh()
                return

            easing_map = {
                "linear": self._linear,
                "ease-in": self._ease_in,
                "ease-out": self._ease_out,
            }
            ease_func = easing_map[easing]
            frame_time = duration / frame_count

            async def update_frame(step):
                progress = step / frame_count
                current = start + (target - start) * ease_func(progress)
                self._styles[property_name] = current
                await self.widget.refresh()
                await asyncio.sleep(frame_time)

            for step in range(frame_count + 1):
                await update_frame(step)

            self._styles[property_name] = target
            await self.widget.refresh()

        except (ValueError, AttributeError):
            self._styles[property_name] = target_value
            await self.widget.refresh()


# ============================
# Layout Components
# ============================


class Container(Widget):
    """Container for organizing widgets."""

    def __init__(self, *widgets, name=None, widget_id=None):
        """Initialize container.

        Args:
            *widgets: Initial widgets
            name: Container name
            widget_id: Container ID
        """
        super().__init__(name=name, widget_id=widget_id)
        self.layout = "vertical"  # vertical or horizontal

        # Add initial widgets
        self.children = list(widgets)
        for widget in widgets:
            widget.parent = self

    def render(self):
        """Render the container with children."""
        if not self.visible:
            return ""

        rendered_children = []
        for child in self.children:
            if not getattr(child, "visible", True):
                continue

            rendered = child.render()
            if rendered:
                rendered_children.append(rendered)

        if self.layout == "vertical":
            return "\n".join(rendered_children)

        # Simple horizontal layout - not perfect but workable
        lines = []
        max_lines = max((r.count("\n") + 1 for r in rendered_children), default=0)

        # Split each child's render into lines
        child_lines = []
        for r in rendered_children:
            child_lines.append(r.split("\n"))

        # Combine lines horizontally with padding
        for i in range(max_lines):
            line_parts = []
            for child_render in child_lines:
                if i < len(child_render):
                    line_parts.append(child_render[i])
                else:
                    line_parts.append(" " * 10)  # Padding for empty line
            lines.append("  ".join(line_parts))

        return "\n".join(lines)

    async def dock(self, *widgets, edge="left", size=None):
        """Dock widgets to an edge.

        Args:
            *widgets: Widgets to dock
            edge: Edge to dock to
            size: Size of docked area
        """
        for widget in widgets:
            if hasattr(widget, "styles"):
                widget.styles["dock"] = edge
                if size is not None:
                    if edge in ("left", "right"):
                        widget.styles["width"] = size
                    else:
                        widget.styles["height"] = size

            await self.mount(widget)

        return self


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


# ============================
# Rich Components
# ============================


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


class Static(Widget):
    """Static content display widget."""

    def __init__(self, content="", *, name=None, widget_id=None):
        """Initialize static widget.

        Args:
            content: Initial content
            name: Widget name
            widget_id: Widget ID
        """
        super().__init__(name=name, widget_id=widget_id)
        self._content = str(content) if content else ""

    def render(self):
        """Render the content."""
        return self._content

    async def update(self, content):
        """Update the widget content.

        Args:
            content: New content
        """
        self._content = str(content) if content else ""
        await self.refresh()


class Panel(Widget):
    """Panel with a border and optional title."""

    def __init__(self, content="", *, title="", border_style=None, box=None):
        """Initialize panel.

        Args:
            content: Panel content
            title: Panel title
            border_style: Style for the border
            box: Box drawing characters
        """
        super().__init__()
        self.content = content
        self.title = title
        self.border_style = (
            Style(border_style) if isinstance(border_style, str) else border_style
        )
        self.box = box or Box.get_box_style("rounded")
        self.padding = (1, 1)  # (horizontal, vertical)

    def _create_borders(self, width):
        """Create border lines for the panel."""
        box_chars = {
            "tl": self.box.get("tl", "┌"),
            "tr": self.box.get("tr", "┐"),
            "bl": self.box.get("bl", "└"),
            "br": self.box.get("br", "┘"),
            "h": self.box.get("h", "─"),
            "v": self.box.get("v", "│"),
        }

        title_str = ""
        if self.title:
            max_title_width = width - 4
            title = self.title[:max_title_width]
            title_str = f" {title} "

        # Create borders
        if title_str:
            padding = width - len(title_str) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            top = (
                box_chars["tl"]
                + box_chars["h"] * left_pad
                + title_str
                + box_chars["h"] * right_pad
                + box_chars["tr"]
            )
        else:
            top = box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"]

        bottom = box_chars["bl"] + box_chars["h"] * (width - 2) + box_chars["br"]

        return top, bottom, box_chars["v"]

    def render(self):
        """Render panel with border and content."""
        # Convert content to string
        content_str = (
            self.content.render()
            if hasattr(self.content, "render")
            else str(self.content)
        )
        content_lines = content_str.split("\n")

        # Calculate width
        content_width = max(
            [len(line) for line in content_lines] + [len(self.title)], default=0
        )
        width = content_width + self.padding[0] * 2 + 2

        # Get borders
        top_border, bottom_border, v = self._create_borders(width)
        lines = [top_border]

        # Add padding and content
        empty_line = v + " " * (width - 2) + v
        lines.extend([empty_line] * self.padding[1])

        for line in content_lines:
            padding_width = max(0, width - 2 - len(line) - self.padding[0] * 2)
            padded = line + " " * padding_width
            lines.append(v + " " * self.padding[0] + padded + " " * self.padding[0] + v)

        lines.extend([empty_line] * self.padding[1])
        lines.append(bottom_border)

        # Apply border style
        if self.border_style:
            lines = [
                (
                    self.border_style.apply(line)
                    if i == 0 or i == len(lines) - 1 or line.startswith(v)
                    else line
                )
                for i, line in enumerate(lines)
            ]

        return "\n".join(lines)


class Box:
    """Box drawing characters for borders."""

    _STYLES = {
        "ascii": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
        "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
        "square": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
        "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    }

    @staticmethod
    def get_box_style(name="rounded") -> dict:
        """Get a box style by name.

        Args:
            name: Style name (ascii, rounded, square, double)

        Returns:
            Box style dictionary
        """
        return Box._STYLES.get(name.lower(), Box._STYLES["rounded"])

    @staticmethod
    def create_box(width: int, height: int, style="rounded") -> str:
        """Create a box with given dimensions and style.

        Args:
            width: Width of the box
            height: Height of the box
            style: Box style name

        Returns:
            String representation of the box
        """
        box_chars = Box.get_box_style(style)
        lines = []
        lines.append(box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"])
        for _ in range(height - 2):
            lines.append(box_chars["v"] + " " * (width - 2) + box_chars["v"])
        lines.append(box_chars["bl"] + box_chars["h"] * (width - 2) + box_chars["br"])
        return "\n".join(lines)

    @staticmethod
    def create_header(width: int, style="rounded", text="") -> str:
        """Create a header line with optional text.

        Args:
            width: Width of the header
            style: Box style name
            text: Optional text to include in header

        Returns:
            String representation of the header
        """
        box_chars = Box.get_box_style(style)
        if text:
            text_space = width - 4
            text = text[:text_space] if len(text) > text_space else text
            padding = width - len(text) - 4
            left_pad = padding // 2
            right_pad = padding - left_pad
            return (
                box_chars["tl"]
                + box_chars["h"] * left_pad
                + " "
                + text
                + " "
                + box_chars["h"] * right_pad
                + box_chars["tr"]
            )
        return box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"]


class TableData:
    """Data container for table content."""

    def __init__(self):
        self.columns = []
        self.column_styles = []
        self.column_widths = []
        self.rows = []
        self.row_styles = []

    def clear(self):
        """Clear all table data."""
        self.columns.clear()
        self.column_styles.clear()
        self.column_widths.clear()
        self.rows.clear()
        self.row_styles.clear()

    def get_column_count(self) -> int:
        """Get the number of columns in the table.

        Returns:
            int: Number of columns
        """
        return len(self.columns)


class Table(Widget):
    """Table widget for displaying tabular data."""

    def __init__(self, title=None, box=None, show_header=True, show_footer=False):
        """Initialize table.

        Args:
            title: Table title
            box: Box style
            show_header: Whether to show column headers
            show_footer: Whether to show footer
        """
        super().__init__()
        self.title = title
        self.box = box or Box.get_box_style("rounded")
        self.show_header = show_header
        self.show_footer = show_footer
        self._data = TableData()

    def add_column(self, title, **kwargs):
        """Add a column to the table."""
        self._data.columns.append(title)
        self._data.column_styles.append(kwargs.get("style"))
        width = kwargs.get("width", 0) or len(title)
        self._data.column_widths.append(width)
        return self

    def add_row(self, *values, style=None):
        """Add a row to the table."""
        row = []
        for i, value in enumerate(values):
            value_str = str(value)
            if i < len(self._data.column_widths):
                self._data.column_widths[i] = max(
                    self._data.column_widths[i], len(value_str)
                )
            row.append(value_str)

        self._data.rows.append(row)
        self._data.row_styles.append(style)
        return self

    def _render_header(self, box_chars, separator):
        """Render table header."""
        lines = []
        if self.show_header:
            header = box_chars["v"] + "  "
            for i, col in enumerate(self._data.columns):
                width = self._data.column_widths[i]
                header += f" {col:<{width}} " + box_chars["v"]
            lines.extend(
                [
                    box_chars["tl"] + separator + box_chars["tr"],
                    header,
                    box_chars["v"] + box_chars["h"] * len(separator) + box_chars["v"],
                ]
            )
        return lines

    def _render_rows(self, box_chars, num_columns):
        """Render table rows."""
        lines = []
        for i, row in enumerate(self._data.rows):
            row_text = box_chars["v"] + "  "
            for j, cell in enumerate(row[:num_columns]):
                width = self._data.column_widths[j]
                row_text += f" {str(cell):<{width}} " + box_chars["v"]

            if self._data.row_styles[i]:
                row_text = Style(self._data.row_styles[i]).apply(row_text)
            lines.append(row_text)
        return lines

    def render(self):
        """Render the table."""
        if not self._data.columns or not self._data.rows:
            return Panel(
                f"Table: {self.title or 'No data'} (no data)", border_style="dim"
            ).render()

        # Normalize data
        num_columns = len(self._data.columns)
        for i, row in enumerate(self._data.rows):
            if len(row) < num_columns:
                self._data.rows[i] = row + [""] * (num_columns - len(row))

        # Setup box characters and separator
        box_chars = {
            k: self.box.get(k, v)
            for k, v in {
                "tl": "┌",
                "tr": "┐",
                "bl": "└",
                "br": "┘",
                "h": "─",
                "v": "│",
            }.items()
        }

        separator = box_chars["h"] * 3
        for width in self._data.column_widths:
            separator += box_chars["h"] * (width + 2) + box_chars["h"] * 3

        # Build table
        lines = []
        if self.title:
            lines.extend([f" {self.title} ", ""])

        lines.extend(self._render_header(box_chars, separator))
        lines.extend(self._render_rows(box_chars, num_columns))

        if self.show_footer:
            lines.extend(self._render_footer(box_chars, separator))

        # Add bottom border
        lines.append(
            box_chars["bl"] + box_chars["h"] * len(separator) + box_chars["br"]
        )

        return "\n".join(lines)

    def _render_footer(self, box_chars, separator):
        """Render table footer."""
        lines = [box_chars["v"] + box_chars["h"] * len(separator) + box_chars["v"]]
        footer = box_chars["v"] + "  "
        for i, width in enumerate(self._data.column_widths):
            text = "Total" if i == 0 else ""
            footer += f" {text:<{width}} " + box_chars["v"]
        lines.append(footer)
        return lines


class Layout(Widget):
    """Layout manager for arranging widgets."""

    def __init__(self, content=None, *, size=None, name=None):
        """Initialize layout.

        Args:
            content: Initial content
            size: Layout size
            name: Layout name
        """
        super().__init__(name=name)
        self.content = content
        self.size = size
        self.children = []
        self.layout_type = "vertical"  # vertical, horizontal, grid

    def render(self):
        """Render the layout with content."""
        # If we have direct content, render it
        if self.content:
            if hasattr(self.content, "render"):
                return self.content.render()
            return str(self.content)

        # Return empty string if no children
        if not self.children:
            return ""

        # Handle vertical layout
        if self.layout_type == "vertical":
            return "\n".join(child.render() for child in self.children)

        # Handle horizontal layout
        if self.layout_type == "horizontal":
            # Simple side-by-side layout - not perfect but workable
            child_renders = [child.render().split("\n") for child in self.children]
            max_height = max([len(r) for r in child_renders], default=0)

            # Pad each render to the same height
            for i, render in enumerate(child_renders):
                if len(render) < max_height:
                    child_renders[i] = render + [""] * (max_height - len(render))

            # Combine side by side
            combined = [
                "  ".join(r[i] for r in child_renders) for i in range(max_height)
            ]
            return "\n".join(combined)

        # Default to vertical layout for unknown types
        return "\n".join(child.render() for child in self.children)

    def split(self, *layouts):
        """Split the layout into multiple sections.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.children.extend(layouts)
        return self

    def split_column(self, *layouts):
        """Split into vertical columns.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.layout_type = "vertical"
        return self.split(*layouts)

    def split_row(self, *layouts):
        """Split into horizontal rows.

        Args:
            *layouts: Child layouts

        Returns:
            Self for chaining
        """
        self.layout_type = "horizontal"
        return self.split(*layouts)


# ============================
# Application Components
# ============================


class App:
    """Base application class."""

    def __init__(self, title="TUI Application"):
        """Initialize application.

        Args:
            title: Application title
        """
        self.title = title
        self.view = Container()
        self.is_running = False
        self._bindings = {}
        self._loop = None

    def set_event_loop(self, loop):
        """Set the event loop.

        Args:
            loop: Asyncio event loop
        """
        self._loop = loop

    async def on_mount(self):
        """Called when the app is mounted. Initializes the application state and UI.

        This method should be overridden by subclasses to:
        - Set up initial application state
        - Create and mount widgets
        - Register event handlers
        - Initialize resources
        - Set up background tasks

        Returns:
            None

        Examples:
            class MyApp(App):
                async def on_mount(self):
                    await super().on_mount() # Call parent implementation first

                    # Set up app state
                    self.counter = 0

                    # Create widgets
                    self.header = Panel("My App")
                    self.content = Container()
                    self.status = Text("Ready")

                    # Mount widgets
                    await self.view.mount(
                        self.header,
                        self.content,
                        self.status
                    )

                    # Register handlers
                    self.view.on("key", self.handle_key)

                    # Start background tasks
                    asyncio.create_task(self.update_loop())
        """
        try:
            # Initialize base application state
            self.mounted = True
            self.error = None

            # Set up default key bindings
            self._bindings.update(
                {
                    "q": self.exit,
                    "ctrl+c": self.exit,
                    "r": self.refresh,
                }
            )

            # Create default layout if view is empty
            if not self.view.children:
                header = Panel(self.title, border_style="bold")
                content = Container(name="main")
                footer = Text("Press 'q' to quit", style="dim")
                await self.view.mount(header, content, footer)

            # Initial render
            await self.view.refresh()

            # Set up signal handlers
            try:
                for sig in (signal.SIGINT, signal.SIGTERM):
                    self._loop.add_signal_handler(sig, lambda s=sig: self.exit())
            except (ImportError, NotImplementedError):
                # Signal handlers not supported on this platform
                pass

            # Create background task for periodic refresh
            async def refresh_loop():
                while self.is_running:
                    await asyncio.sleep(0.1)
                    if self.view.children:
                        await self.view.refresh()

            self._refresh_task = asyncio.create_task(refresh_loop())

        except Exception as e:
            self.error = e
            raise

    async def refresh(self):
        """Force a refresh of the display."""
        if self.view:
            await self.view.refresh()

    def __init__(self, title="TUI Application"):
        """Initialize application."""
        super().__init__(title=title)
        self.mounted = False
        self.error = None

    async def on_unmount(self):
        """Called when the app is unmounted. Performs cleanup and disposal.

        This method handles:
        - Canceling background tasks
        - Cleaning up widget tree
        - Closing connections/files
        - Resetting terminal state
        - Stopping running processes"""
        try:
            # Cancel refresh task if running
            if hasattr(self, "_refresh_task"):
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass

            # Remove signal handlers
            if self._loop:
                try:
                    self._loop.remove_signal_handler(signal.SIGINT)
                    self._loop.remove_signal_handler(signal.SIGTERM)
                except (NotImplementedError, ValueError):
                    pass

            # Clear widget tree
            if self.view:
                await self._unmount_widget_tree(self.view)
                self.view.children.clear()

            # Reset terminal state
            self._reset_terminal()

            # Clear application state
            self.mounted = False
            self._bindings.clear()
            self.error = None

        except (RuntimeError, IOError) as err:
            # Log specific cleanup errors but don't raise
            print(f"Error during unmount: {err}", file=sys.stderr)

    async def _unmount_widget_tree(self, widget):
        """Recursively unmount all widgets in the tree."""
        if hasattr(widget, "children"):
            # Make a copy of children list to avoid modification
            # during iteration
            children = widget.children[:]
            for child in children:
                await self._unmount_widget_tree(child)
                widget.remove_widget(child)

        # Clear widget state
        widget.parent = None
        widget.focused = False
        if hasattr(widget, "event_handlers"):
            widget.event_handlers.clear()

    def _reset_terminal(self):
        """Reset terminal to initial state."""
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write("\033[0m")  # Reset colors
        sys.stdout.write("\033[2J")  # Clear screen
        sys.stdout.write("\033[H")  # Move to home position
        sys.stdout.flush()

    def exit(self, result=None):
        """Exit the application.
        
        Args:
            result: Optional exit result
        """
        self.is_running = False
    def action(self, action_name):
        """Handle an action.

        Args:
            action_name: Action to perform
        """
        method_name = f"action_{action_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        print(f"Action not found: {action_name}")

    def run(self):
        """Run the application."""
        self.is_running = True

        # Create and set event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.set_event_loop(loop)

        # Run the application
        try:
            # Mount the application
            loop.run_until_complete(self.on_mount())

            # In fallback mode, render the initial state and exit
            print(f"\n{self.title}\n{'=' * len(self.title)}\n")
            print(self.view.render())
            print("\nPress Ctrl+C to exit\n")

            # Keep the app running until exit() is called
            while self.is_running:
                try:
                    loop.run_until_complete(asyncio.sleep(0.1))
                except KeyboardInterrupt:
                    print("\nExiting...")
                    self.is_running = False

        finally:
            # Unmount the application
            loop.run_until_complete(self.on_unmount())
            if not loop.is_closed():
                loop.close()


# ============================
# Export symbols
# ============================

__all__ = [
    # Basic components
    "Widget",
    "Container",
    "ScrollView",
    "StyleManager",
    "Style",
    # Rich components
    "Text",
    "Static",
    "Panel",
    "Table",
    "Layout",
    "Box",
    # Application
    "App",
]
