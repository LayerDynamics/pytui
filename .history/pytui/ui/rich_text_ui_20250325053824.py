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





# ============================
# Rich Components
# ============================















# ============================
# Application Components
# ============================





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
