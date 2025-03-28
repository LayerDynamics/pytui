"""UI widgets module for PyTUI that re-exports and extends rich_text_ui components."""

import time
from typing import Dict, Optional, Any, Callable

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
from .rich_text_ui.progress import ProgressBarWidget, AnimatedSpinnerWidget

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

# Re-export everything for easy imports
__all__ = [
    'Widget', 'Static', 'Text', 'Panel', 'Table', 'Layout', 'Box',
    'ScrollView', 'Container', 'Color', 'ProgressBarWidget', 'AnimatedSpinnerWidget',
    'StatusBar', 'CollapsibleWidget', 'SearchWidget', 'ROUNDED',
    'async_methods',
]
