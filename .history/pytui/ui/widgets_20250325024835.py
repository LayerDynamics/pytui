"""UI widgets module"""

import time
from typing import Dict, List, Optional, Any, Callable, Tuple, TypeVar, Deque
from collections import deque
from datetime import datetime

try:
    from textual.widgets import Static
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
except ImportError:
    # Base class for fallbacks
    class WidgetBase:
        """Base widget with required methods."""
        def __init__(self, *args, **kwargs):
            self.content = ""nit__(self, *args, **kwargs):
            
        def render(self):
            """Render the widget content."""
            return self.content
            
        def update(self, content):
            """Update widget content."""
            self.content = str(content)nel:
            ck Panel."""
    # Fallback implementations        
    class Static(WidgetBase):
        """Fallback Static widget."""
        def set_content(self, content):
            """Set widget content."""ble."""
            self.content = content

    class Box:
        """Fallback Box implementation."""
        ROUNDED = None       """Fallback Layout."""
        
        def get_style(self):
            """Get box style."""
            return None
        """Fallback Box."""
    class Text(WidgetBase):
        """Fallback Text implementation."""
        def append(self, text, style=None):
            """Append text with style."""
            self.content += str(text)port CollapsibleMixin, ensure_callable
            
    class Panel(WidgetBase):pes - use PascalCase as per PEP 8
        """Fallback Panel implementation."""ar("RenderableType")
        def set_title(self, title):
            """Set panel title."""
            self.title = title
Optional[Callable] = None) -> Callable:
    class Table(WidgetBase): or return a no-op function."""
        """Fallback Table implementation."""allback if callable(callback) else lambda *args, **kwargs: None
        def add_row(self, *args):
            """Add a table row."""
            self.content += " ".join(str(arg) for arg in args)
                """Base Static widget with required methods."""
    class Layout(WidgetBase):
        """Fallback Layout implementation."""
        def split(self, *args):t display."""
            """Split layout into sections."""
            self.sections = args

# Local imports"""
from .widget_utils import CollapsibleMixin, ensure_callable

# Type definitions with proper naming
RenderableT = TypeVar("RenderableT")  # Fixed naming convention
ROUNDED = getattr(Box, 'ROUNDED', None) execution info."""

def ensure_callback(callback: Optional[Callable] = None) -> Callable:
    """Ensure a callback is callable or return a no-op function."""        """Initialize the status bar."""
    return callback if callable(callback) else lambda *args, **kwargs: None")
ime.time()
class Static(Static):lse
    """Base Static widget with required methods."""
     ""
    def refresh(self):ore execution statistics
        """Refresh the widget display."""
        passr(self) -> RenderableType:
ar."""
    def update(self, content):
        """Update widget content."""        elapsed = time.time() - self.start_time
        passt(elapsed // 60):02d}:{int(elapsed % 60):02d}"

class StatusBar(Static):
    """Status bar for displaying execution info."""
            status = "PAUSED"
    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")
        self.start_time = time.time()            status_style = "bold green"
        self._is_running = False
        self._is_paused = False
        self._status_message = ""
        self._stats = {}  # Store execution statistics

    def render(self) -> RenderableT:
        """Render the status bar."""d")
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"        # Add custom status message if set
essage:
        # Determine statusus_message})", style="italic")
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"
        elif self._is_running:
            status = "RUNNING"
            status_style = "bold green"
        else:        if self._stats:
            status = "STOPPED"pend(" | ", style="dim")
            status_style = "bold red"            stats_text = " ".join([f"{k}: {v}" for k, v in self._stats.items()])
reen")
        # Build status line
        text = Text()
        text.append(" Status: ", style="bold")| ", style="dim")
        text.append(status, style=status_style)        text.append("[Q]uit ", style="bold")
le="bold")
        # Add custom status message if settyle="bold")
        if self._status_message:tyle="bold")
            text.append(f" ({self._status_message})", style="italic")C]ollapse ", style="bold")
        text.append("[V]ar Display", style="bold")
        text.append(" | ", style="dim")
        text.append("Elapsed: ", style="bold")
        text.append(elapsed_str, style="cyan")
lf, is_running: bool):
        # Add statistics if available        """Set the running state."""
        if self._stats:
            text.append(" | ", style="dim")
            stats_text = " ".join([f"{k}: {v}" for k, v in self._stats.items()])
            text.append(stats_text, style="green")f, is_paused: bool):
        """Set the paused state."""
        # Add keybindings
        text.append(" | ", style="dim")
        text.append("[Q]uit ", style="bold")
        text.append("[P]ause/Resume ", style="bold")lf):
        text.append("[R]estart ", style="bold")        """Reset the elapsed time counter."""
        text.append("[/]Search ", style="bold")time.time()
        text.append("[C]ollapse ", style="bold")
        text.append("[V]ar Display", style="bold")
sage(self, message: str):
        return text        """Set a custom status message."""
_status_message = message
    def set_running(self, is_running: bool):
        """Set the running state."""
        self._is_running = is_runnings: Dict[str, Any]):
        self.refresh()        """Update execution statistics."""
_stats.update(stats)
    def set_paused(self, is_paused: bool):
        """Set the paused state."""
        self._is_paused = is_paused
        self.refresh()        """Clear all statistics."""
        self._stats.clear()
    def reset_timer(self):
        """Reset the elapsed time counter."""
        self.start_time = time.time()    @property
        self.refresh()
Get the running state."""
    def set_status_message(self, message: str):
        """Set a custom status message."""
        self._status_message = message
        self.refresh()

    def update_stats(self, stats: Dict[str, Any]):urn self._is_paused
        """Update execution statistics."""
        self._stats.update(stats)
        self.refresh()
 collapsed/expanded."""
    def clear_stats(self):
        """Clear all statistics."""bool = False):
        self._stats.clear()        """
        self.refresh()alize the collapsible panel.

    @property
    def is_running(self):
        """Get the running state."""            collapsed: Whether the panel starts collapsed
        return self._is_running

    @property
    def is_paused(self):
        """Get the paused state."""        self._content = ""
        return self._is_paused_expand_callback = ensure_callable()
lable()

class CollapsiblePanel(Static):
    """A panel that can be collapsed/expanded."""    def expand_callback(self) -> Callable:
k."""
    def __init__(self, title: str = "", collapsed: bool = False):
        """
        Initialize the collapsible panel.
    def expand_callback(self, callback: Optional[Callable]):
        Args:
            title: The panel title ensure_callable(callback)
            collapsed: Whether the panel starts collapsed
        """
        super().__init__("")
        self.title = title
        self.collapsed = collapsed
        self._content = ""
        self._expand_callback = ensure_callable()
        self._collapse_callback = ensure_callable()lapse_callback(self, callback: Optional[Callable]):

    @propertye(callback)
    def expand_callback(self) -> Callable:
        """Get expand callback."""der(self) -> RenderableType:
        return self._expand_callback

    @expand_callback.setterick to expand)"
    def expand_callback(self, callback: Optional[Callable]):yle="dim")
        """Set expand callback."""k to collapse)"
        self._expand_callback = ensure_callable(callback)elf._content, title=title)

    @property
    def collapse_callback(self) -> Callable:
        """Get collapse callback."""toggle collapse state.
        return self._collapse_callbacknd_callback when expanding
        and the collapse_callback when collapsing.
    @collapse_callback.setter
    def collapse_callback(self, callback: Optional[Callable]):
        """Set collapse callback."""
        self._collapse_callback = ensure_callable(callback)    await self.collapse_callback()
d and self.expand_callback:
    def render(self) -> RenderableT:)
        """Render the panel."""
        if self.collapsed:
            title = f"[+] {self.title} (click to expand)"    async def update_content(self, content: str):
            return Panel(Text(""), title=title, border_style="dim")        """Update the panel content."""
        title = f"[-] {self.title} (click to collapse)"ent
        return Panel(self._content, title=title)

    async def on_click(self):
        """rning by implementing bool."""
        Handle click events to toggle collapse state.        return bool(not self.collapsed)  # Fix constant test warning
        Calls the expand_callback when expanding
        and the collapse_callback when collapsing.
        """Add second public method."""
        self.collapsed = not self.collapsedcontent)
        if self.collapsed and self.collapse_callback:
            await self.collapse_callback()
        elif not self.collapsed and self.expand_callback:
            await self.expand_callback()
        self.refresh() metrics and charts."""

    async def update_content(self, content: str)::
        """Update the panel content."""t.
        self._content = content
        self.refresh()
Maximum number of data points to store
    def __bool__(self) -> bool:
        """Fix missing parentheses warning by implementing bool."""er().__init__("")
        return bool(not self.collapsed)  # Fix constant test warningmax_data_points
        e[Tuple[float, float]]] = (
    def update(self, content):
        """Add second public method."""
        self._content = str(content)()
        self.refresh()
    def add_metric(self, name: str, value: float):
 point.
class MetricsWidget(Static):
    """Widget for displaying execution metrics and charts."""
ic name
    def __init__(self, max_data_points: int = 100):            value: Metric value
        """Initialize metrics widget.

        Args:metrics:
            max_data_points: Maximum number of data points to stores)
        """        self.metrics[name].append((timestamp, value))
        super().__init__("")
        self.max_data_points = max_data_points
        self.metrics: Dict[str, Deque[Tuple[float, float]]] = (
            {}
        )  # name -> [(timestamp, value)]        """Clear all metrics data."""
        self.last_update = time.time()

    def add_metric(self, name: str, value: float):
        """Add a metric data point.    def render(self) -> RenderableType:
t."""
        Args:rics:
            name: Metric name            return Panel("No metrics collected", title="Metrics")
            value: Metric value
        """ Metrics", box=ROUNDED)
        timestamp = time.time()
        if name not in self.metrics:lue")
            self.metrics[name] = deque(maxlen=self.max_data_points)
        self.metrics[name].append((timestamp, value))
        self.last_update = timestamp
        self.refresh()lues:

    def clear_metrics(self):
        """Clear all metrics data."""
        self.metrics.clear()            change = ""
        self.refresh()
            if len(values) > 1:
    def render(self) -> RenderableT:                prev = values[-2][1]
        """Render the metrics widget.""" prev
        if not self.metrics:
            return Panel("No metrics collected", title="Metrics")                    change = f"↑ {diff:.2f}"
                elif diff < 0:
                    change = f"↓ {abs(diff):.2f}"
                else:
                    change = "−"

            table.add_row(name, f"{current:.2f}", change)

        return Panel(table, title="Execution Metrics")


class KeyBindingsWidget(Static):
    """Widget for displaying available key bindings."""

    def __init__(self):
        """Initialize key bindings widget."""
        super().__init__("")
        self.bindings: Dict[str, str] = {}

    def set_bindings(self, bindings: Dict[str, str]):
        """Set the key bindings to display.

        Args:
            bindings: Mapping of key to description
        """
        self.bindings = bindings
        self.refresh()

    def add_binding(self, key: str, description: str):
        """Add a key binding.

        Args:
            key: Key shortcut
            description: Description of what the key does
        """
        self.bindings[key] = description
        self.refresh()

    def render(self) -> RenderableType:
        """Render the key bindings widget."""
        text = Text()

        for i, (key, description) in enumerate(self.bindings.items()):
            if i > 0:
                text.append(" | ", style="dim")
            text.append(f"[{key}]", style="bold cyan")
            text.append(f" {description}", style="white")

        return Panel(text, title="Key Bindings")


class TimelineWidget(Static):
    """Widget for displaying a timeline of execution events."""

    def __init__(self, max_events: int = 50):
        """Initialize timeline widget.

        Args:
            max_events: Maximum number of events to display
        """
        super().__init__("")
        self.max_events = max_events
        self.events: List[Tuple[datetime, str, str]] = (
            []
        )  # (timestamp, event_type, description)

    def add_event(self, event_type: str, description: str):
        """Add an event to the timeline.

        Args:
            event_type: Type of event (e.g., "call", "return", "exception")
            description: Description of the event
        """
        timestamp = datetime.now()
        self.events.append((timestamp, event_type, description))

        # Trim if we have too many events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        self.refresh()

    def clear(self):
        """Clear all timeline events."""
        self.events.clear()
        self.refresh()

    def render(self) -> RenderableType:
        """Render the timeline widget."""
        if not self.events:
            return Panel("No events recorded", title="Timeline")

        table = Table(box=ROUNDED)
        table.add_column("Time")
        table.add_column("Event")
        table.add_column("Description")

        for timestamp, event_type, description in self.events:
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]

            # Determine style based on event type
            if event_type == "call":
                event_style = "green"
            elif event_type == "return":
                event_style = "blue"
            elif event_type == "exception":
                event_style = "red"
            else:
                event_style = "white"

            table.add_row(time_str, Text(event_type, style=event_style), description)

        return Panel(table, title="Event Timeline")


class SearchBar(Static):
    """Search bar widget with additional search options."""

    def __init__(self, placeholder: str = "Search..."):
        """Initialize search bar widget.

        Args:
            placeholder: Placeholder text when empty
        """
        super().__init__("")
        self.placeholder = placeholder
        self.query = ""
        self.active = False
        self.case_sensitive = False
        self.regex_mode = False
        self.match_count = 0
        self.current_match = 0
        self.search_callback = ensure_callable()

    def activate(self):
        """Activate the search bar."""
        self.active = True
        self.refresh()

    def deactivate(self):
        """Deactivate the search bar."""
        self.active = False
        self.refresh()

    def toggle_case_sensitivity(self):
        """Toggle case sensitivity."""
        self.case_sensitive = not self.case_sensitive
        self._trigger_search()
        self.refresh()

    def toggle_regex(self):
        """Toggle regex search mode."""
        self.regex_mode = not self.regex_mode
        self._trigger_search()
        self.refresh()

    def set_query(self, query: str):
        """Set the search query.

        Args:
            query: Search query
        """
        self.query = query
        self._trigger_search()
        self.refresh()

    def append_char(self, char: str):
        """Append a character to the search query.

        Args:
            char: Character to append
        """
        self.query += char
        self._trigger_search()
        self.refresh()

    def backspace(self):
        """Remove the last character from the query."""
        if self.query:
            self.query = self.query[:-1]
            self._trigger_search()
            self.refresh()

    def clear(self):
        """Clear the search query."""
        self.query = ""
        self._trigger_search()
        self.refresh()

    def set_match_info(self, current: int, total: int):
        """Set match information.

        Args:
            current: Current match index (1-based)
            total: Total number of matches
        """
        self.current_match = current
        self.match_count = total
        self.refresh()

    def _trigger_search(self):
        """Trigger the search callback if set."""
        if self.search_callback:
            self.search_callback(self.query, self.case_sensitive, self.regex_mode)

    def render(self) -> RenderableType:
        """Render the search bar."""
        if not self.active:
            return Text("")

        text = Text()
        text.append("Search: ", style="bold")

        # Show search query with cursor
        if self.query:
            text.append(self.query)
        else:
            text.append(self.placeholder, style="dim italic")

        text.append("█", style="blink")

        # Show search options
        options_text = []
        if self.case_sensitive:
            options_text.append("Case-sensitive")
        if self.regex_mode:
            options_text.append("Regex")

        if options_text:
            text.append(" [")
            text.append(", ".join(options_text), style="italic")
            text.append("]")

        # Show match information if we have any
        if self.match_count > 0:
            text.append(
                f" ({self.current_match}/{self.match_count} matches)", style="green"
            )
        elif self.query and not self.match_count:
            text.append(" (No matches)", style="red")

        return Panel(text, title="Search", border_style="blue")


class VariableInspectorWidget(Static):
    """Widget for inspecting variable values in the call graph."""

    def __init__(self):
        """Initialize variable inspector widget."""
        super().__init__("")
        self._config = {
            "variables": {},  # function_name -> {var_name: var_value}
            "selected_function": None,
            "expanded": True,
            "display_options": {"max_value_length": 50, "show_types": True},
        }

    @property
    def variables(self) -> Dict[str, Dict[str, Any]]:
        """Get variables dict."""
        return self._config["variables"]

    @property
    def selected_function(self) -> Optional[str]:
        """Get selected function."""
        return self._config["selected_function"]

    @selected_function.setter
    def selected_function(self, value: Optional[str]):
        """Set selected function."""
        self._config["selected_function"] = value

    def set_variables(self, function_name: str, variables: Dict[str, Any]):
        """Set variables for a function.

        Args:
            function_name: Function name
            variables: Variable name to value mapping
        """
        self.variables[function_name] = variables

        # Auto-select if this is the first function
        if self.selected_function is None:
            self.selected_function = function_name
        self.refresh()

    def select_function(self, function_name: str):
        """Select a function to display variables for.

        Args:
            function_name: Function name to select
        """
        if function_name in self.variables:
            self.selected_function = function_name
            self.refresh()

    def toggle_expansion(self):
        """Toggle expanded/collapsed state."""
        self._config["expanded"] = not self._config["expanded"]
        self.refresh()

    def clear(self):
        """Clear all variable data."""
        self.variables.clear()
        self.selected_function = None
        self.refresh()

    def render(self) -> RenderableType:
        """Render the variable inspector widget."""
        if not self.variables or self.selected_function is None:
            return Panel("No variables to inspect", title="Variable Inspector")

        selected_vars = self.variables.get(self.selected_function, {})

        if not selected_vars:
            return Panel(
                f"No variables for {self.selected_function}()",
                title="Variable Inspector",
            )

        if not self._config["expanded"]:
            return Panel(
                f"{len(selected_vars)} variables available for {self.selected_function}()",
                title="Variable Inspector [+]",
            )

        table = Table(box=ROUNDED)
        table.add_column("Variable")
        table.add_column("Value")
        table.add_column("Type")

        for var_name, var_value in selected_vars.items():
            var_type = type(var_value).__name__
            value_str = str(var_value)

            if len(value_str) > self._config["display_options"]["max_value_length"]:
                value_str = value_str[:47] + "..."

            table.add_row(var_name, value_str, var_type)

        function_selector = Text("Function: ")

        for i, func_name in enumerate(self.variables.keys()):
            if i > 0:
                function_selector.append(" | ")

            if func_name == self.selected_function:
                function_selector.append(func_name, style="bold reverse")
            else:
                function_selector.append(func_name)

        layout = Layout()
        layout.split(Layout(function_selector, size=3), Layout(table))

        return Panel(layout, title="Variable Inspector [-]")


class CollapsibleWidget(CollapsibleMixin):
    """A widget that can be collapsed/expanded."""

    def __init__(
        self, collapse_callback: Callable = None, expand_callback: Callable = None
    ):
        super().__init__(collapse_callback, expand_callback)


class SearchWidget:
    """Widget for search functionality."""

    def __init__(self, search_callback: Optional[Callable[[str], None]] = None):
        self.search_callback = ensure_callback(search_callback)

    def on_search_change(self, value: str) -> None:
        """Handle search text changes."""
        self.search_callback(value)
