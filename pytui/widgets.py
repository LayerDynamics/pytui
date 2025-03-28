"""UI widgets module for PyTUI that re-exports and extends rich_text_ui components."""

import time
from typing import Dict, Optional, Any, Callable, List, Tuple

# Re-export the components from rich_text_ui
from .rich_text_ui.widget import Widget
from .rich_text_ui.static import Static
from .rich_text_ui.text import Text
from .rich_text_ui.panel import Panel
from .rich_text_ui.table import Table
from .rich_text_ui.layout import Layout
from .rich_text_ui.box import Box
from .rich_text_ui.scroll_view import ScrollView
from .rich_text_ui.container import Container
from .rich_text_ui.colors import Color
from .rich_text_ui.progress import (
    ProgressBarWidget,
    AnimatedSpinnerWidget,
    SpinnerWidget,
)
from .rich_text_ui.metrics import MetricsWidget, TimelineWidget

# Import utility functions
from .widget_utils import CollapsibleMixin, ensure_callable

# Define constants
ROUNDED = Box.get_box_style("rounded")


# Define utility functions
def ensure_callback(callback: Optional[Callable] = None) -> Callable:
    """Ensure a callback is callable or return a no-op function."""
    return callback if callable(callback) else lambda *args, **kwargs: None


# Only implement classes that extend or adapt the rich_text_ui components
class StatusBar(Static):
    """Status bar for displaying execution info."""

    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")
        self.start_time = time.time()
        self._is_running = False
        self._is_paused = False
        self._status_message = ""
        self._stats = {}  # Store execution statistics

    def render(self):
        """Render the status bar."""
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        # Determine status
        status_style = "bold red"
        status = "STOPPED"
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"
        elif self._is_running:
            status = "RUNNING"
            status_style = "bold green"

        # Build status line
        text = Text()
        text.append(" Status: ", style="bold")
        text.append(status, style=status_style)

        # Add custom status message if set
        if self._status_message:
            text.append(f" ({self._status_message})", style="italic")

        text.append(" | ", style="dim")
        text.append("Elapsed: ", style="bold")
        text.append(elapsed_str, style="cyan")

        # Add statistics if available
        if self._stats:
            text.append(" | ", style="dim")
            stats_text = " ".join([f"{k}: {v}" for k, v in self._stats.items()])
            text.append(stats_text, style="green")

        # Add keybindings
        text.append(" | ", style="dim")
        text.append("[Q]uit ", style="bold")
        text.append("[P]ause/Resume ", style="bold")
        text.append("[R]estart ", style="bold")
        text.append("[/]Search ", style="bold")
        text.append("[C]ollapse ", style="bold")
        text.append("[V]ar Display", style="bold")

        return text

    def set_running(self, is_running: bool):
        """Set the running state."""
        self._is_running = is_running
        self.refresh()

    def set_paused(self, is_paused: bool):
        """Set the paused state."""
        self._is_paused = is_paused
        self.refresh()

    def reset_timer(self):
        """Reset the elapsed time counter."""
        self.start_time = time.time()
        self.refresh()

    def set_status_message(self, message: str):
        """Set a custom status message."""
        self._status_message = message
        self.refresh()

    def update_stats(self, stats: Dict[str, Any]):
        """Update execution statistics."""
        self._stats.update(stats)
        self.refresh()

    def clear_stats(self):
        """Clear all statistics."""
        self._stats.clear()
        self.refresh()

    @property
    def is_running(self):
        """Get the running state."""
        return self._is_running

    @property
    def is_paused(self):
        """Get the paused state."""
        return self._is_paused


# Extend CollapsibleMixin with Widget to create a useful base class
class CollapsibleWidget(Widget, CollapsibleMixin):
    """A widget that can be collapsed/expanded."""

    def __init__(
        self, collapse_callback: Callable = None, expand_callback: Callable = None
    ):
        """Initialize collapsible widget."""
        Widget.__init__(self)
        CollapsibleMixin.__init__(self, collapse_callback, expand_callback)

    def update(self, state: bool):
        """Update collapsed state."""
        self.is_collapsed = state
        if state and self.collapse_callback:
            self.collapse_callback()
        elif not state and self.expand_callback:
            self.expand_callback()


# Create a search widget using components from rich_text_ui
class SearchWidget(Static):
    """Widget for search functionality."""

    def __init__(self, search_callback: Optional[Callable[[str], None]] = None):
        """Initialize search widget."""
        super().__init__("")
        self._search_callback = ensure_callback(search_callback)
        self._search_term = ""

    def on_search_change(self, value: str) -> None:
        """Handle search text changes."""
        self._search_term = value
        self._search_callback(value)
        self.refresh()

    def clear(self) -> None:
        """Clear search state."""
        self._search_term = ""
        self.on_search_change("")

    def render(self):
        """Render the search widget."""
        return Text(f"🔍 {self._search_term or 'Search...'}")


# Add a SearchBar widget that extends SearchWidget with more functionality
class SearchBar(SearchWidget):
    """Enhanced search widget with input handling and styling."""

    def __init__(
        self,
        placeholder: str = "Search...",
        search_callback: Optional[Callable[[str], None]] = None,
        clear_callback: Optional[Callable[[], None]] = None,
        style: str = "cyan",
    ):
        """Initialize search bar.

        Args:
            placeholder: Text to show when empty
            search_callback: Callback when search text changes
            clear_callback: Callback when search is cleared
            style: Style for the search bar
        """
        super().__init__(search_callback)
        self.placeholder = placeholder
        self._clear_callback = ensure_callback(clear_callback)
        self.style = Style(style) if isinstance(style, str) else style
        self._active = False

    def render(self):
        """Render the search bar."""
        text = Text()

        if self._active:
            text.append("🔍 ", style="bright_cyan")
            if self._search_term:
                text.append(self._search_term, style="bold cyan")
            else:
                text.append(self.placeholder, style="dim")
            text.append(" (Esc to close)", style="dim")
        else:
            text.append("🔍 Press / to search", style="dim")

        return text

    def activate(self):
        """Activate the search bar."""
        self._active = True
        self.refresh()

    def deactivate(self):
        """Deactivate the search bar."""
        self._active = False
        self.refresh()

    def toggle(self):
        """Toggle search bar active state."""
        self._active = not self._active
        self.refresh()

    def on_key(self, key: str) -> bool:
        """Handle key input.

        Args:
            key: Key pressed

        Returns:
            True if key was handled, False otherwise
        """
        if not self._active:
            return False

        if key == "escape":
            self.deactivate()
            return True

        if key == "backspace":
            if self._search_term:
                self._search_term = self._search_term[:-1]
                self._search_callback(self._search_term)
            elif self._clear_callback:
                self._clear_callback()
            self.refresh()
            return True

        if key == "enter":
            self._search_callback(self._search_term)
            return True

        # Handle normal character input
        if len(key) == 1:
            self._search_term += key
            self._search_callback(self._search_term)
            self.refresh()
            return True

        return False

    def clear(self) -> None:
        """Clear search term and call callbacks."""
        self._search_term = ""
        self._search_callback("")
        if self._clear_callback:
            self._clear_callback()
        self.refresh()


# Add async compatibility to widgets from rich_text_ui
async def async_refresh(self):
    """Async refresh method for widgets."""
    self.refresh()
    return self


async def async_update(self, *args, **kwargs):
    """Async update method for widgets."""
    self.update(*args, **kwargs)
    return self


async def async_start(self):
    """Async start method for spinner widgets."""
    self._running = True
    self.start_time = time.time()
    self.refresh()
    return self


async def async_stop(self):
    """Async stop method for spinner widgets."""
    self._running = False
    self.refresh()
    return self


# Attach async methods to core rich_text_ui widgets
Widget.async_refresh = async_refresh
Static.async_update = async_update
Panel.async_update = async_update
ProgressBarWidget.async_update = async_update
AnimatedSpinnerWidget.async_start = async_start
AnimatedSpinnerWidget.async_stop = async_stop

# Define async_methods container for easy access
async_methods = {
    "refresh": async_refresh,
    "update": async_update,
    "start": async_start,
    "stop": async_stop,
}


class VariableInspectorWidget(Widget):
    """Widget for inspecting variables and their values."""

    def __init__(
        self,
        title: str = "Variable Inspector",
        max_depth: int = 3,
        max_string_length: int = 100,
        name: Optional[str] = None,
    ):
        """Initialize the variable inspector widget.

        Args:
            title: Title for the widget panel
            max_depth: Maximum depth for nested object inspection
            max_string_length: Maximum length for string representation
            name: Widget name
        """
        super().__init__(name=name)
        self.title = title
        self.max_depth = max_depth
        self.max_string_length = max_string_length
        self.variables: Dict[str, Any] = {}
        self._filter_text = ""
        self._selected_var = None
        self._expanded_vars = set()

    def update_variables(self, variables: Dict[str, Any]) -> None:
        """Update the variables to display.

        Args:
            variables: Dictionary of variable names and values
        """
        self.variables = variables
        self.refresh()

    def set_filter(self, filter_text: str) -> None:
        """Set a filter for variable names.

        Args:
            filter_text: Text to filter variable names by
        """
        self._filter_text = filter_text
        self.refresh()

    def toggle_expand(self, var_name: str) -> None:
        """Toggle expansion state of a variable.

        Args:
            var_name: Variable name to toggle
        """
        if var_name in self._expanded_vars:
            self._expanded_vars.remove(var_name)
        else:
            self._expanded_vars.add(var_name)
        self.refresh()

    def _format_value(self, value: Any, depth: int = 0) -> str:
        """Format a value for display, handling various types.

        Args:
            value: Value to format
            depth: Current recursion depth

        Returns:
            Formatted string representation
        """
        if depth >= self.max_depth:
            return "..."

        if value is None:
            return "None"

        if isinstance(value, (int, float, bool)):
            return str(value)

        if isinstance(value, str):
            if len(value) > self.max_string_length:
                return f'"{value[:self.max_string_length]}..."'
            return f'"{value}"'

        if isinstance(value, (list, tuple)):
            if not value:
                return "[]" if isinstance(value, list) else "()"
            if depth == self.max_depth - 1:
                return (
                    f"[{len(value)} items]"
                    if isinstance(value, list)
                    else f"({len(value)} items)"
                )

            items = []
            for i, item in enumerate(value):
                if i >= 5:  # Limit to first 5 items
                    items.append("...")
                    break
                items.append(self._format_value(item, depth + 1))

            sep = ", "
            return (
                f"[{sep.join(items)}]"
                if isinstance(value, list)
                else f"({sep.join(items)})"
            )

        if isinstance(value, dict):
            if not value:
                return "{}"
            if depth == self.max_depth - 1:
                return f"{{{len(value)} keys}}"

            items = []
            for i, (k, v) in enumerate(value.items()):
                if i >= 5:  # Limit to first 5 keys
                    items.append("...")
                    break
                items.append(f"{k}: {self._format_value(v, depth + 1)}")

            return f"{{{', '.join(items)}}}"

        # For other objects, return their type and string representation
        type_name = type(value).__name__
        try:
            str_val = str(value)
            if len(str_val) > self.max_string_length:
                str_val = str_val[: self.max_string_length] + "..."
            return f"<{type_name}: {str_val}>"
        except Exception:
            return f"<{type_name}: [error formatting]>"

    def render(self) -> str:
        """Render the variable inspector.

        Returns:
            String representation of the inspector
        """
        if not self.variables:
            return Panel(f"No variables to display", title=self.title).render()

        # Filter variables if needed
        variables = self.variables
        if self._filter_text:
            variables = {
                k: v
                for k, v in variables.items()
                if self._filter_text.lower() in k.lower()
            }

        if not variables:
            return Panel(
                f"No variables match filter: '{self._filter_text}'", title=self.title
            ).render()

        # Create table to display variables
        table = Table(title=None, box=Box.get_box_style("rounded"), show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Value", style="white")

        # Sort variables by name
        for name in sorted(variables.keys()):
            value = variables[name]
            type_name = type(value).__name__

            # Format the value
            value_str = self._format_value(value)

            # Add to table
            table.add_row(name, type_name, value_str)

        # Wrap table in a panel
        return Panel(table, title=self.title, border_style="blue").render()

    async def inspect_variable(self, var_name: str) -> None:
        """Show detailed information about a variable.

        Args:
            var_name: Name of variable to inspect
        """
        if var_name not in self.variables:
            return

        self._selected_var = var_name
        self.refresh()


class KeyBindingsWidget(Widget):
    """Widget for displaying key bindings help."""

    def __init__(
        self,
        title: str = "Key Bindings",
        name: Optional[str] = None,
        border_style: str = "blue",
    ):
        """Initialize key bindings widget.

        Args:
            title: Title for the widget panel
            name: Widget name
            border_style: Style for the panel border
        """
        super().__init__(name=name)
        self.title = title
        self.border_style = border_style
        self.bindings: List[Tuple[str, str]] = []

    def add_binding(self, key: str, description: str) -> None:
        """Add a key binding to the display.

        Args:
            key: Key combination (e.g., "Ctrl+C")
            description: Description of the action
        """
        self.bindings.append((key, description))
        self.refresh()

    def add_bindings(self, bindings: Dict[str, str]) -> None:
        """Add multiple key bindings at once.

        Args:
            bindings: Dictionary of key bindings {key: description}
        """
        for key, description in bindings.items():
            self.bindings.append((key, description))
        self.refresh()

    def clear_bindings(self) -> None:
        """Clear all key bindings."""
        self.bindings.clear()
        self.refresh()

    def render(self) -> str:
        """Render the key bindings widget.

        Returns:
            String representation of the widget
        """
        if not self.bindings:
            return Panel(
                "No key bindings defined",
                title=self.title,
                border_style=self.border_style,
            ).render()

        # Create a table to display bindings
        table = Table(box=Box.get_box_style("rounded"), show_header=True)
        table.add_column("Key", style="cyan bold")
        table.add_column("Action", style="white")

        # Add bindings to table
        for key, description in sorted(self.bindings, key=lambda x: x[0]):
            formatted_key = Text(key, style="bold cyan")
            table.add_row(formatted_key, description)

        # Wrap table in panel
        return Panel(table, title=self.title, border_style=self.border_style).render()


# Re-export everything for easy imports
__all__ = [
    "Widget",
    "Static",
    "Text",
    "Panel",
    "Table",
    "Layout",
    "Box",
    "ScrollView",
    "Container",
    "Color",
    "ProgressBarWidget",
    "AnimatedSpinnerWidget",
    "SpinnerWidget",
    "StatusBar",
    "CollapsibleWidget",
    "SearchWidget",
    "SearchBar",
    "KeyBindingsWidget",
    "MetricsWidget",
    "TimelineWidget",
    "ROUNDED",
    "async_methods",
    "VariableInspectorWidget",
]
