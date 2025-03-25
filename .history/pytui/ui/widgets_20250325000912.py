"""UI widgets module"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque
from datetime import datetimeutton, Label, Static, ScrollView, Header

from textual.widgets import (rom rich.text import Text
    Button, Label, Static, Header
)el
from rich.text import Textss, BarColumn, TextColumn
from rich.spinner import Spinner
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table, boxith a fallback implementation
from rich.layout import Layouttry:

from .widget_utils import (pt ImportError:
    ActiveFunctionHighlighter,r Chart
    SearchableText,
    CollapsibleMixin,ich Chart."""
    SPINNER_STYLES
)
            """Initialize with compatibility args."""
# Types
RenderableType = Any  # Rich's renderable type
ROUNDED = box.ROUNDED
gs, **kwargs):
# Make Chart import optional with a fallback implementation            """Add a series of data (stub implementation)."""
try:
    from rich.chart import Chart
except ImportError:lf):
    # Fallback implementation for Chart            """Return a renderable representation."""
    class Chart:
        """Fallback implementation of Rich Chart."""
art (Rich chart module not installed)",
        def __init__(self, *args, **kwargs):
            """Initialize with compatibility args."""
            self.args = args
            self.kwargs = kwargsclass StatusBar(Static):
    """Status bar for displaying execution info."""
        def add_series(self, *args, **kwargs):
            """Add a series of data (stub implementation)."""
            return self        """Initialize the status bar."""
_("")
        def __rich__(self):
            """Return a renderable representation."""alse
            return Panel(
                "Chart visualization not available","
                title="Chart (Rich chart module not installed)",re execution statistics
            )

        """Render the status bar."""
class StatusBar(Static):
    """Status bar for displaying execution info.""".start_time
psed // 60):02d}:{int(elapsed % 60):02d}"
    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")        if self._is_paused:
        self.start_time = time.time()ED"
        self._is_running = False"bold yellow"
        self._is_paused = False:
        self._status_message = ""
        self._stats = {}  # Store execution statisticsld green"

    def render(self) -> RenderableType:
        """Render the status bar."""tatus_style = "bold red"
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"        text = Text()
s: ", style="bold")
        # Determine statustatus, style=status_style)
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"        if self._status_message:
        elif self._is_running:message})", style="italic")
            status = "RUNNING"
            status_style = "bold green"
        else:        text.append("Elapsed: ", style="bold")
            status = "STOPPED""cyan")
            status_style = "bold red"

        # Build status line        if self._stats:
        text = Text()"dim")
        text.append(" Status: ", style="bold")= " ".join([f"{k}: {v}" for k, v in self._stats.items()])
        text.append(status, style=status_style)green")

        # Add custom status message if set
        if self._status_message:        text.append(" | ", style="dim")
            text.append(f" ({self._status_message})", style="italic")it ", style="bold")
style="bold")
        text.append(" | ", style="dim")d")
        text.append("Elapsed: ", style="bold")
        text.append(elapsed_str, style="cyan"))
d")
        # Add statistics if available
        if self._stats:
            text.append(" | ", style="dim")
            stats_text = " ".join([f"{k}: {v}" for k, v in self._stats.items()])(self, is_running: bool):
            text.append(stats_text, style="green")        """Set the running state."""

        # Add keybindings
        text.append(" | ", style="dim")
        text.append("[Q]uit ", style="bold")f, is_paused: bool):
        text.append("[P]ause/Resume ", style="bold")        """Set the paused state."""
        text.append("[R]estart ", style="bold")
        text.append("[/]Search ", style="bold")
        text.append("[C]ollapse ", style="bold")
        text.append("[V]ar Display", style="bold")lf):
        """Reset the elapsed time counter."""
        return texttime.time()

    def set_running(self, is_running: bool):
        """Set the running state."""sage(self, message: str):
        self._is_running = is_running        """Set a custom status message."""
        self.refresh()

    def set_paused(self, is_paused: bool):
        """Set the paused state."""elf, stats: Dict[str, Any]):
        self._is_paused = is_paused        """Update execution statistics."""
        self.refresh()

    def reset_timer(self):
        """Reset the elapsed time counter."""lf):
        self.start_time = time.time()        """Clear all statistics."""
        self.refresh())

    def set_status_message(self, message: str):
        """Set a custom status message."""ompatibility
        self._status_message = message    @property
        self.refresh()
t the running state."""
    def update_stats(self, stats: Dict[str, Any]):unning
        """Update execution statistics."""
        self._stats.update(stats)
        self.refresh()    def is_paused(self):
t the paused state."""
    def clear_stats(self):paused
        """Clear all statistics."""
        self._stats.clear()
        self.refresh()class SpinnerWidget(Static):
    """A spinner widget for showing progress."""
    # Properties for compatibility
    @property, "dots3"]
    def is_running(self):
        """Get the running state."""ype: str = "dots"):
        return self._is_running        """

    @property
    def is_paused(self):
        """Get the paused state."""            text: Text to display alongside the spinner
        return self._is_pausedpinner_type: Type of spinner animation to use


class SpinnerWidget(Static):f.text = text
    """A spinner widget for showing progress."""spinner_type if spinner_type in self.SPINNERS else "dots"
False
    SPINNERS = ["dots", "line", "pulse", "dots2", "dots3"]

    def __init__(self, text: str = "Working...", spinner_type: str = "dots"):
        """        """Render the spinner."""
        Initialize the spinner widget.
ext} (stopped)")
        Args:f.spinner_type, text=self.text)
            text: Text to display alongside the spinner
            spinner_type: Type of spinner animation to use
        """lf):
        super().__init__("")        """Start the spinner animation."""
        self.text = textue
        self.spinner_type = spinner_type if spinner_type in self.SPINNERS else "dots"
        self._running = Falset self._task.done():
        self._task: Optional[asyncio.Task] = None.cancel()

    def render(self) -> RenderableType:eate_task(self._refresh_spinner())
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")        """Stop the spinner animation."""
        spinner = Spinner(self.spinner_type, text=self.text)alse
        return spinner
 self._task.done():
    async def start(self):.cancel()
        """Start the spinner animation."""
        self._running = Trueself):
        self.refresh()        """Continuously refresh the spinner while running."""
        if self._task and not self._task.done():
            self._task.cancel()
        # Create a new refresh task    self.refresh()
        self._task = asyncio.create_task(self._refresh_spinner())eep(0.1)
edError:
    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        self.refresh()class CollapsiblePanel(Static):
        if self._task and not self._task.done():    """A panel that can be collapsed/expanded."""
            self._task.cancel()
: bool = False):
    async def _refresh_spinner(self):        """
        """Continuously refresh the spinner while running."""
        try:
            while self._running:
                self.refresh()            title: The panel title
                await asyncio.sleep(0.1)ollapsed: Whether the panel starts collapsed
        except asyncio.CancelledError:
            pass
f.title = title
lapsed
class CollapsiblePanel(Static):
    """A panel that can be collapsed/expanded."""onal[Callable] = None
back: Optional[Callable] = None
    def __init__(self, title: str = "", collapsed: bool = False):
        """
        Initialize the collapsible panel.        """Render the panel."""

        Args:.title} (click to expand)"
            title: The panel titleext(""), title=title, border_style="dim")
            collapsed: Whether the panel starts collapsed
        """
        super().__init__("")eturn Panel(self._content, title=title)
        self.title = title
        self.collapsed = collapsed
        self._content = ""        """
        self._expand_callback: Callable = lambda: Noneo toggle collapse state.
        self._collapse_callback: Callable = lambda: Nonels the expand_callback when expanding

    @property
    def expand_callback(self) -> Callable:
        """Get the expand callback."""self.collapsed and self.collapse_callback:
        return self._expand_callback
ack:
    @expand_callback.setter
    def expand_callback(self, callback: Optional[Callable]):
        """Set the expand callback."""
        self._expand_callback = ensure_callable(callback)ontent(self, content: str):
        """Update the panel content."""
    @property
    def collapse_callback(self) -> Callable:
        """Get the collapse callback."""
        return self._collapse_callback
class ProgressBarWidget(Static):
    @collapse_callback.setter    """Progress bar widget for showing execution progress."""
    def collapse_callback(self, callback: Optional[Callable]):
        """Set the collapse callback."""
        self._collapse_callback = ensure_callable(callback)        self,
t = 100,
    def render(self) -> RenderableType:iption: str = "Progress",
        """Render the panel."""bool = True,
        if self.collapsed:
            title = f"[+] {self.title} (click to expand)"
            return Panel(Text(""), title=title, border_style="dim")bar widget.
        else:
            title = f"[-] {self.title} (click to collapse)"
            return Panel(self._content, title=title)            total: Total steps for completion
escription: Description of the progress
    async def on_click(self):percentage
        """
        Handle click events to toggle collapse state.
        Calls the expand_callback when expanding
        and the collapse_callback when collapsing.f.total = total
        """escription
        self.collapsed = not self.collapsedge = show_percentage
        if self.collapsed and self.collapse_callback:
            await self.collapse_callback()
        elif not self.collapsed and self.expand_callback:e()
            await self.expand_callback()al[asyncio.Task] = None
        self.refresh()

    async def update_content(self, content: str):        """Render the progress bar."""
        """Update the panel content."""h time
        self._content = content
        self.refresh()ription}"),
dth=None),

class ProgressBarWidget(Static):percentage]{task.percentage:>3.0f}%")
    """Progress bar widget for showing execution progress."""   if self.show_percentage

    def __init__(
        self,lumn() if self.show_time else None,
        total: int = 100,
        description: str = "Progress",
        show_percentage: bool = True, Add the task and update completion
        show_time: bool = True,        task_id = progress.add_task(self.description, total=self.total)
    ):elf.completed)
        """Initialize progress bar widget.

        Args:
            total: Total steps for completionmpleted: int, description: Optional[str] = None):
            description: Description of the progress        """Update progress completion."""
            show_percentage: Whether to show percentage
            show_time: Whether to show elapsed time
        """
        super().__init__("")
        self.total = total
        self.description = description, amount: int = 1):
        self.show_percentage = show_percentage        """Increment progress by an amount."""
        self.show_time = show_timeed + amount, self.total)
        self.completed = 0
        self.start_time = time.time()
        self._task: Optional[asyncio.Task] = Nonetal: Optional[int] = None, description: Optional[str] = None):
        """Reset the progress bar."""
    def render(self) -> RenderableType:
        """Render the progress bar."""
        # Create a new progress bar each time None:
        progress = Progress( description
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            (
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                if self.show_percentagese(self, interval: float = 0.2, pulse_size: int = 1):
                else None        """Automatically pulse the progress bar for indeterminate progress."""
            ),
            TimeElapsedColumn() if self.show_time else None,
        )

        # Add the task and update completion            try:
        task_id = progress.add_task(self.description, total=self.total)
        progress.update(task_id, completed=self.completed)    # For indeterminate progress, we'll cycle the progress
mpleted = (self.completed + pulse_size) % (self.total + 1)
        return progress

    def update(self, completed: int, description: Optional[str] = None):edError:
        """Update progress completion."""
        self.completed = min(completed, self.total)
        if description: asyncio.create_task(_pulse())
            self.description = description
        self.refresh()
        """Stop the auto-pulse animation."""
    def increment(self, amount: int = 1):elf._task.done():
        """Increment progress by an amount."""
        self.completed = min(self.completed + amount, self.total)
        self.refresh()k
pt asyncio.CancelledError:
    def reset(self, total: Optional[int] = None, description: Optional[str] = None):
        """Reset the progress bar."""
        if total is not None:
            self.total = totalclass MetricsWidget(Static):
        if description is not None:    """Widget for displaying execution metrics and charts."""
            self.description = description
        self.completed = 0
        self.start_time = time.time()        """Initialize metrics widget.
        self.refresh()

    async def auto_pulse(self, interval: float = 0.2, pulse_size: int = 1):            max_data_points: Maximum number of data points to store
        """Automatically pulse the progress bar for indeterminate progress."""
        if self._task and not self._task.done():
            self._task.cancel()f.max_data_points = max_data_points
tr, Deque[Tuple[float, float]]] = (
        async def _pulse():
            try:
                while True:ast_update = time.time()
                    # For indeterminate progress, we'll cycle the progress
                    self.completed = (self.completed + pulse_size) % (self.total + 1)lue: float):
                    self.refresh()        """Add a metric data point.
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                pass            name: Metric name
alue: Metric value
        self._task = asyncio.create_task(_pulse())

    async def stop_pulse(self):
        """Stop the auto-pulse animation."""rics:
        if self._task and not self._task.done():            self.metrics[name] = deque(maxlen=self.max_data_points)
            self._task.cancel()
            try:
                await self._task        self.last_update = timestamp
            except asyncio.CancelledError:
                pass
self):
        """Clear all metrics data."""
class MetricsWidget(Static):
    """Widget for displaying execution metrics and charts."""

    def __init__(self, max_data_points: int = 100):> RenderableType:
        """Initialize metrics widget.        """Render the metrics widget."""

        Args:lected", title="Metrics")
            max_data_points: Maximum number of data points to store
        """
        super().__init__("")        table = Table(title="Current Metrics", box=ROUNDED)
        self.max_data_points = max_data_points
        self.metrics: Dict[str, Deque[Tuple[float, float]]] = (
            {}
        )  # name -> [(timestamp, value)]
        self.last_update = time.time()
        for name, values in self.metrics.items():
    def add_metric(self, name: str, value: float):
        """Add a metric data point.

        Args:lues[-1][1]
            name: Metric name            change = ""
            value: Metric value
        """es) > 1:
        timestamp = time.time()                prev = values[-2][1]
- prev
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_data_points)f:.2f}"
0:
        self.metrics[name].append((timestamp, value)).2f}"
        self.last_update = timestamp
        self.refresh()

    def clear_metrics(self):f"{current:.2f}", change)
        """Clear all metrics data."""
        self.metrics.clear()ow
        self.refresh()        # In a real implementation, we would add a chart of recent values

    def render(self) -> RenderableType:
        """Render the metrics widget."""
        if not self.metrics:class KeyBindingsWidget(Static):
            return Panel("No metrics collected", title="Metrics")    """Widget for displaying available key bindings."""

        # Create a table for current values
        table = Table(title="Current Metrics", box=ROUNDED)        """Initialize key bindings widget."""
        table.add_column("Metric")_("")
        table.add_column("Value")
        table.add_column("Change")
str, str]):
        # Add metrics to table        """Set the key bindings to display.
        for name, values in self.metrics.items():
            if not values:
                continue            bindings: Mapping of key to description

            current = values[-1][1]
            change = ""f.refresh()

            if len(values) > 1:lf, key: str, description: str):
                prev = values[-2][1]        """Add a key binding.
                diff = current - prev
                if diff > 0:
                    change = f"↑ {diff:.2f}"            key: Key shortcut
                elif diff < 0:escription: Description of what the key does
                    change = f"↓ {abs(diff):.2f}"
                else:
                    change = "−"f.refresh()

            table.add_row(name, f"{current:.2f}", change)> RenderableType:
        """Render the key bindings widget."""
        # For simplicity, we'll just show the table for now
        # In a real implementation, we would add a chart of recent values
        return Panel(table, title="Execution Metrics")description) in enumerate(self.bindings.items()):
            if i > 0:

class KeyBindingsWidget(Static):nd(f"[{key}]", style="bold cyan")
    """Widget for displaying available key bindings."""e="white")

    def __init__(self):
        """Initialize key bindings widget."""
        super().__init__("")
        self.bindings: Dict[str, str] = {}class TimelineWidget(Static):
    """Widget for displaying a timeline of execution events."""
    def set_bindings(self, bindings: Dict[str, str]):
        """Set the key bindings to display.
        """Initialize timeline widget.
        Args:
            bindings: Mapping of key to description
        """            max_events: Maximum number of events to display
        self.bindings = bindings
        self.refresh()
f.max_events = max_events
    def add_binding(self, key: str, description: str):ple[datetime, str, str]] = (
        """Add a key binding.

        Args:
            key: Key shortcution: str):
            description: Description of what the key does        """Add an event to the timeline.
        """
        self.bindings[key] = description
        self.refresh()            event_type: Type of event (e.g., "call", "return", "exception")
escription: Description of the event
    def render(self) -> RenderableType:
        """Render the key bindings widget."""
        text = Text()f.events.append((timestamp, event_type, description))

        for i, (key, description) in enumerate(self.bindings.items()):
            if i > 0:        if len(self.events) > self.max_events:
                text.append(" | ", style="dim")lf.max_events :]
            text.append(f"[{key}]", style="bold cyan")
            text.append(f" {description}", style="white")

        return Panel(text, title="Key Bindings")
        """Clear all timeline events."""
clear()
class TimelineWidget(Static):
    """Widget for displaying a timeline of execution events."""
> RenderableType:
    def __init__(self, max_events: int = 50):        """Render the timeline widget."""
        """Initialize timeline widget.
ded", title="Timeline")
        Args:
            max_events: Maximum number of events to display
        """        table.add_column("Time")
        super().__init__("")
        self.max_events = max_eventsption")
        self.events: List[Tuple[datetime, str, str]] = (
            []ription in self.events:
        )  # (timestamp, event_type, description)            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]

    def add_event(self, event_type: str, description: str):
        """Add an event to the timeline.            if event_type == "call":

        Args:rn":
            event_type: Type of event (e.g., "call", "return", "exception")
            description: Description of the eventn":
        """
        timestamp = datetime.now()
        self.events.append((timestamp, event_type, description))e"

        # Trim if we have too many eventsext(event_type, style=event_style), description)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        self.refresh()
class SearchBar(Static):
    def clear(self):    """Search bar widget with additional search options."""
        """Clear all timeline events."""
        self.events.clear()
        self.refresh()        """Initialize search bar widget.

    def render(self) -> RenderableType:
        """Render the timeline widget."""            placeholder: Placeholder text when empty
        if not self.events:
            return Panel("No events recorded", title="Timeline")
f.placeholder = placeholder
        table = Table(box=ROUNDED)
        table.add_column("Time")
        table.add_column("Event")tive = False
        table.add_column("Description")alse

        for timestamp, event_type, description in self.events:
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]: Optional[Callable[[str, bool, bool], None]] = None

            # Determine style based on event type
            if event_type == "call":        """Activate the search bar."""
                event_style = "green"rue
            elif event_type == "return":
                event_style = "blue"
            elif event_type == "exception":f):
                event_style = "red"        """Deactivate the search bar."""
            else:se
                event_style = "white"

            table.add_row(time_str, Text(event_type, style=event_style), description)nsitivity(self):
        """Toggle case sensitivity."""
        return Panel(table, title="Event Timeline").case_sensitive


class SearchBar(Static):
    """Search bar widget with additional search options."""elf):
        """Toggle regex search mode."""
    def __init__(self, placeholder: str = "Search..."):ot self.regex_mode
        """Initialize search bar widget.

        Args:
            placeholder: Placeholder text when empty, query: str):
        """        """Set the search query.
        super().__init__("")
        self.placeholder = placeholder
        self.query = ""            query: Search query
        self.active = False
        self.case_sensitive = False
        self.regex_mode = Falsef._trigger_search()
        self.match_count = 0
        self.current_match = 0
        self.search_callback: Optional[Callable[[str, bool, bool], None]] = Nonelf, char: str):
        """Append a character to the search query.
    def activate(self):
        """Activate the search bar."""
        self.active = True            char: Character to append
        self.refresh()

    def deactivate(self):f._trigger_search()
        """Deactivate the search bar."""
        self.active = False
        self.refresh()):
        """Remove the last character from the query."""
    def toggle_case_sensitivity(self):
        """Toggle case sensitivity."""
        self.case_sensitive = not self.case_sensitiveger_search()
        self._trigger_search()
        self.refresh()

    def toggle_regex(self):        """Clear the search query."""
        """Toggle regex search mode.""" ""
        self.regex_mode = not self.regex_mode
        self._trigger_search()
        self.refresh()
(self, current: int, total: int):
    def set_query(self, query: str):        """Set match information.
        """Set the search query.

        Args:            current: Current match index (1-based)
            query: Search queryotal: Total number of matches
        """
        self.query = query
        self._trigger_search()f.match_count = total
        self.refresh()

    def append_char(self, char: str):h(self):
        """Append a character to the search query.        """Trigger the search callback if set."""
k:
        Args:.case_sensitive, self.regex_mode)
            char: Character to append
        """
        self.query += char        """Render the search bar."""
        self._trigger_search()
        self.refresh()

    def backspace(self):
        """Remove the last character from the query."""        text.append("Search: ", style="bold")
        if self.query:
            self.query = self.query[:-1]
            self._trigger_search()        if self.query:
            self.refresh()

    def clear(self):older, style="dim italic")
        """Clear the search query."""
        self.query = ""
        self._trigger_search()
        self.refresh()
        options_text = []
    def set_match_info(self, current: int, total: int):e:
        """Set match information.append("Case-sensitive")

        Args:
            current: Current match index (1-based)
            total: Total number of matches
        """            text.append(" [")
        self.current_match = current", ".join(options_text), style="italic")
        self.match_count = total
        self.refresh()
tion if we have any
    def _trigger_search(self):        if self.match_count > 0:
        """Trigger the search callback if set."""
        if self.search_callback:t_match}/{self.match_count} matches)", style="green"
            self.search_callback(self.query, self.case_sensitive, self.regex_mode)

    def render(self) -> RenderableType:ext.append(" (No matches)", style="red")
        """Render the search bar."""
        if not self.active:le="blue")
            return Text("")

        text = Text()class VariableInspectorWidget(Static):
        text.append("Search: ", style="bold")    """Widget for inspecting variable values in the call graph."""

        # Show search query with cursor
        if self.query:        """Initialize variable inspector widget."""
            text.append(self.query)_("")
        else: (
            text.append(self.placeholder, style="dim italic")

        text.append("█", style="blink")elected_function: Optional[str] = None

        # Show search options
        options_text = []function_name: str, variables: Dict[str, Any]):
        if self.case_sensitive:        """Set variables for a function.
            options_text.append("Case-sensitive")
        if self.regex_mode:
            options_text.append("Regex")            function_name: Function name
ariables: Variable name to value mapping
        if options_text:
            text.append(" [")
            text.append(", ".join(options_text), style="italic")
            text.append("]")on
        if self.selected_function is None:
        # Show match information if we have any
        if self.match_count > 0:
            text.append(
                f" ({self.current_match}/{self.match_count} matches)", style="green"
            )n(self, function_name: str):
        elif self.query and not self.match_count:        """Select a function to display variables for.
            text.append(" (No matches)", style="red")

        return Panel(text, title="Search", border_style="blue")            function_name: Function name to select


class VariableInspectorWidget(Static): self.selected_function = function_name
    """Widget for inspecting variable values in the call graph."""

    def __init__(self):elf):
        """Initialize variable inspector widget."""        """Toggle expanded/collapsed state."""
        super().__init__("")f.expanded
        self.variables: Dict[str, Dict[str, Any]] = (
            {}
        )  # function_name -> {var_name: var_value}
        self.selected_function: Optional[str] = None        """Clear all variable data."""
        self.expanded = Truees.clear()

    def set_variables(self, function_name: str, variables: Dict[str, Any]):
        """Set variables for a function.
> RenderableType:
        Args:        """Render the variable inspector widget."""
            function_name: Function nameelected_function is None:
            variables: Variable name to value mapping title="Variable Inspector")
        """
        self.variables[function_name] = variables

        # Auto-select if this is the first function
        if self.selected_function is None:            return Panel(
            self.selected_function = function_names for {self.selected_function}()",
riable Inspector",
        self.refresh()

    def select_function(self, function_name: str):t self.expanded:
        """Select a function to display variables for.            return Panel(
ed_vars)} variables available for {self.selected_function}()",
        Args:riable Inspector [+]",
            function_name: Function name to select
        """
        if function_name in self.variables:der variables in a table
            self.selected_function = function_name        table = Table(box=ROUNDED)
            self.refresh()

    def toggle_expansion(self):
        """Toggle expanded/collapsed state."""
        self.expanded = not self.expandedin selected_vars.items():
        self.refresh()            var_type = type(var_value).__name__

    def clear(self):
        """Clear all variable data."""
        self.variables.clear()            if len(value_str) > 50:
        self.selected_function = Nonestr[:47] + "..."
        self.refresh()
_type)
    def render(self) -> RenderableType:
        """Render the variable inspector widget."""ables
        if not self.variables or self.selected_function is None:        function_selector = Text("Function: ")
            return Panel("No variables to inspect", title="Variable Inspector")
one highlighted
        selected_vars = self.variables.get(self.selected_function, {})        for i, func_name in enumerate(self.variables.keys()):

        if not selected_vars:
            return Panel(
                f"No variables for {self.selected_function}()",ion:
                title="Variable Inspector",                function_selector.append(func_name, style="bold reverse")
            )

        if not self.expanded:
            return Panel(
                f"{len(selected_vars)} variables available for {self.selected_function}()",        layout.split(Layout(function_selector, size=3), Layout(table))
                title="Variable Inspector [+]",
            )

        # Render variables in a table
        table = Table(box=ROUNDED)class AnimatedSpinnerWidget(Static):
        table.add_column("Variable")    """Enhanced spinner widget with richer animation options."""
        table.add_column("Value")
        table.add_column("Type")
        "dots": {
        for var_name, var_value in selected_vars.items():mes": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            var_type = type(var_value).__name__rval": 0.08,
            value_str = str(var_value)
-", "\\", "|", "/"], "interval": 0.1},
            # Truncate long valuesulse": {
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."    ]",
",
            table.add_row(var_name, value_str, var_type)

        # Create a panel with function selector and variables
        function_selector = Text("Function: ")

        # Add all functions with the selected one highlighted
        for i, func_name in enumerate(self.variables.keys()):
            if i > 0:
                function_selector.append(" | ")

            if func_name == self.selected_function:
                function_selector.append(func_name, style="bold reverse")
            else:
                function_selector.append(func_name)
.1,
        layout = Layout()
        layout.split(Layout(function_selector, size=3), Layout(table))["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"], "interval": 0.08},
ots3": {"frames": ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"], "interval": 0.08},
        return Panel(layout, title="Variable Inspector [-]")

",
class AnimatedSpinnerWidget(Static):
    """Enhanced spinner widget with richer animation options."""

    SPINNERS = {
        "dots": {
            "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "interval": 0.08,
        },
        "line": {"frames": ["-", "\\", "|", "/"], "interval": 0.1},
        "pulse": {
            "frames": [
                "[    ]",
                "[=   ]",": 0.1,
                "[==  ]",
                "[=== ]",
                "[ ===]",  "frames": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
                "[  ==]",rval": 0.1,
                "[   =]",
                "[    ]", ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"], "interval": 0.1},
                "[   =]",
                "[  ==]",
                "[ ===]",ef __init__(
                "[====]",        self,
                "[=== ]", = "Working...",
                "[==  ]",er_type: str = "dots",
                "[=   ]",,
            ],
            "interval": 0.1, spinner widget.
        },
        "dots2": {"frames": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"], "interval": 0.08},
        "dots3": {"frames": ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"], "interval": 0.08},            text: Text to display alongside the spinner
        "clock": {pinner_type: Type of spinner animation to use
            "frames": [
                "🕛",
                "🕐",
                "🕑",f.text = text
                "🕒",show_elapsed
                "🕓",
                "🕔",
                "🕕",        if spinner_type in self.SPINNERS:
                "🕖",elf.SPINNERS[spinner_type]
                "🕗",
                "🕘",
                "🕙",
                "🕚",
            ],        self._running = False
            "interval": 0.1,syncio.Task] = None
        },e.time()
        "moon": {
            "frames": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],e:
            "interval": 0.1,        """Render the spinner."""
        },
        "bounce": {"frames": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"], "interval": 0.1},ext} (stopped)")
    }

    def __init__(        frames = self.spinner_config["frames"]
        self,frame % len(frames)]
        text: str = "Working...",
        spinner_type: str = "dots",
        show_elapsed: bool = True,        text.append(frame_char, style="bold cyan")
    ): ")
        """Initialize the animated spinner widget.

        Args:enabled
            text: Text to display alongside the spinner        if self.show_elapsed:
            spinner_type: Type of spinner animation to useelf.start_time
            show_elapsed: Whether to show elapsed timeint(elapsed // 60):02d}:{int(elapsed % 60):02d}"
        """
        super().__init__("")
        self.text = text
        self.show_elapsed = show_elapsed

        # Get spinner configuration
        if spinner_type in self.SPINNERS:(self):
            self.spinner_config = self.SPINNERS[spinner_type]        """Start the spinner animation."""
        else:ue
            self.spinner_config = self.SPINNERS["dots"]

        self.current_frame = 0
        self._running = Falseing task if running
        self._task: Optional[asyncio.Task] = None        if self._task and not self._task.done():
        self.start_time = time.time()

    def render(self) -> RenderableType:task
        """Render the spinner."""        self._task = asyncio.create_task(self._animate_spinner())
        if not self._running:
            return Text(f"{self.text} (stopped)")
        """Stop the spinner animation."""
        # Get the current frame characteralse
        frames = self.spinner_config["frames"]done():
        frame_char = frames[self.current_frame % len(frames)]()

        text = Text()
        text.append(frame_char, style="bold cyan") text: str):
        text.append(" ")        """Update the spinner text.
        text.append(self.text)

        # Add elapsed time if enabled            text: New text to display
        if self.show_elapsed:
            elapsed = time.time() - self.start_time
            elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"f.refresh()
            text.append(" (")
            text.append(elapsed_str, style="dim")_spinner(self):
            text.append(")")        """Continuously animate the spinner while running."""

        return text
    # Update frame and refresh
    async def start(self):me += 1
        """Start the spinner animation."""
        self._running = True
        self.start_time = time.time()t frame using spinner interval
        self.refresh()                interval = self.spinner_config.get("interval", 0.1)

        # Cancel existing task if running
        if self._task and not self._task.done():
            self._task.cancel()

        # Create a new refresh taskclass CollapsibleWidget(CollapsibleMixin):
        self._task = asyncio.create_task(self._animate_spinner())    """A widget that can be collapsed/expanded."""

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        if self._task and not self._task.done():        super().__init__(collapse_callback, expand_callback)
            self._task.cancel()
        self.refresh()

    def set_text(self, text: str):
        """Update the spinner text.
    def __init__(self, search_callback: Callable = None):
        Args:lambda x: None)
            text: New text to display
        """e: str) -> None:
        self.text = text        """Handle search text changes."""
































        self.search_callback(value)        """Handle search text changes."""    def on_search_change(self, value: str) -> None:        self.search_callback = search_callback or (lambda x: None)    def __init__(self, search_callback: Callable = None):    """Widget for search functionality."""class SearchWidget:        super().__init__(collapse_callback, expand_callback)    def __init__(self, collapse_callback: Callable = None, expand_callback: Callable = None):    """A widget that can be collapsed/expanded."""class CollapsibleWidget(CollapsibleMixin):            pass        except asyncio.CancelledError:                await asyncio.sleep(interval)                interval = self.spinner_config.get("interval", 0.1)                # Wait for next frame using spinner interval                self.refresh()                self.current_frame += 1                # Update frame and refresh            while self._running:        try:        """Continuously animate the spinner while running."""    async def _animate_spinner(self):        self.refresh()        self.search_callback(value)
