"""UI widgets module"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from textual.widgets import Button, Label, Static, ScrollView, Header
from rich.console import Console
from rich.text import Text
from rich.spinner import Spinner
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.layout import Layout

# Make Chart import optional with a fallback implementation
try:
    from rich.chart import Chart
except ImportError:
    # Fallback implementation for Chart
    class Chart:
        """Fallback implementation of Rich Chart."""

        def __init__(self, *args, **kwargs):
            """Initialize with compatibility args."""
            self.args = args
            self.kwargs = kwargs

        def add_series(self, *args, **kwargs):
            """Add a series of data (stub implementation)."""
            return self

        def __rich__(self):
            """Return a renderable representation."""
            return Panel(
                "Chart visualization not available",
                title="Chart (Rich chart module not installed)",
            )


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

    def render(self) -> RenderableType:
        """Render the status bar."""
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        # Determine status
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"
        elif self._is_running:
            status = "RUNNING"
            status_style = "bold green"
        else:
            status = "STOPPED"
            status_style = "bold red"

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

    # Properties for compatibility
    @property
    def is_running(self):
        """Get the running state."""
        return self._is_running

    @property
    def is_paused(self):
        """Get the paused state."""
        return self._is_paused


class SpinnerWidget(Static):
    """A spinner widget for showing progress."""

    SPINNERS = ["dots", "line", "pulse", "dots2", "dots3"]

    def __init__(self, text: str = "Working...", spinner_type: str = "dots"):
        """
        Initialize the spinner widget.

        Args:
            text: Text to display alongside the spinner
            spinner_type: Type of spinner animation to use
        """
        super().__init__("")
        self.text = text
        self.spinner_type = spinner_type if spinner_type in self.SPINNERS else "dots"
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def render(self) -> RenderableType:
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")
        spinner = Spinner(self.spinner_type, text=self.text)
        return spinner

    async def start(self):
        """Start the spinner animation."""
        self._running = True
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()
        # Create a new refresh task
        self._task = asyncio.create_task(self._refresh_spinner())

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()

    async def _refresh_spinner(self):
        """Continuously refresh the spinner while running."""
        try:
            while self._running:
                self.refresh()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


class CollapsiblePanel(Static):
    """A panel that can be collapsed/expanded."""

    def __init__(self, title: str = "", collapsed: bool = False):
        """
        Initialize the collapsible panel.

        Args:
            title: The panel title
            collapsed: Whether the panel starts collapsed
        """
        super().__init__("")
        self.title = title
        self.collapsed = collapsed
        self._content = ""
        self.expand_callback: Optional[Callable] = None
        self.collapse_callback: Optional[Callable] = None

    def render(self) -> RenderableType:
        """Render the panel."""
        if self.collapsed:
            title = f"[+] {self.title} (click to expand)"
            return Panel(Text(""), title=title, border_style="dim")
        else:
            title = f"[-] {self.title} (click to collapse)"
            return Panel(self._content, title=title)

    async def on_click(self):
        """
        Handle click events to toggle collapse state.
        Calls the expand_callback when expanding
        and the collapse_callback when collapsing.
        """
        self.collapsed = not self.collapsed
        if self.collapsed and self.collapse_callback:
            await self.collapse_callback()
        elif not self.collapsed and self.expand_callback:
            await self.expand_callback()
        self.refresh()

    async def update_content(self, content: str):
        """Update the panel content."""
        self._content = content
        self.refresh()


class ProgressBarWidget(Static):
    """Progress bar widget for showing execution progress."""

    def __init__(
        self,
        total: int = 100,
        description: str = "Progress",
        show_percentage: bool = True,
        show_time: bool = True,
    ):
        """Initialize progress bar widget.

        Args:
            total: Total steps for completion
            description: Description of the progress
            show_percentage: Whether to show percentage
            show_time: Whether to show elapsed time
        """
        super().__init__("")
        self.total = total
        self.description = description
        self.show_percentage = show_percentage
        self.show_time = show_time
        self.completed = 0
        self.start_time = time.time()
        self._task: Optional[asyncio.Task] = None

    def render(self) -> RenderableType:
        """Render the progress bar."""
        # Create a new progress bar each time
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            (
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                if self.show_percentage
                else None
            ),
            TimeElapsedColumn() if self.show_time else None,
        )

        # Add the task and update completion
        task_id = progress.add_task(self.description, total=self.total)
        progress.update(task_id, completed=self.completed)

        return progress

    def update(self, completed: int, description: Optional[str] = None):
        """Update progress completion."""
        self.completed = min(completed, self.total)
        if description:
            self.description = description
        self.refresh()

    def increment(self, amount: int = 1):
        """Increment progress by an amount."""
        self.completed = min(self.completed + amount, self.total)
        self.refresh()

    def reset(self, total: Optional[int] = None, description: Optional[str] = None):
        """Reset the progress bar."""
        if total is not None:
            self.total = total
        if description is not None:
            self.description = description
        self.completed = 0
        self.start_time = time.time()
        self.refresh()

    async def auto_pulse(self, interval: float = 0.2, pulse_size: int = 1):
        """Automatically pulse the progress bar for indeterminate progress."""
        if self._task and not self._task.done():
            self._task.cancel()

        async def _pulse():
            try:
                while True:
                    # For indeterminate progress, we'll cycle the progress
                    self.completed = (self.completed + pulse_size) % (self.total + 1)
                    self.refresh()
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                pass

        self._task = asyncio.create_task(_pulse())

    async def stop_pulse(self):
        """Stop the auto-pulse animation."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


class MetricsWidget(Static):
    """Widget for displaying execution metrics and charts."""

    def __init__(self, max_data_points: int = 100):
        """Initialize metrics widget.

        Args:
            max_data_points: Maximum number of data points to store
        """
        super().__init__("")
        self.max_data_points = max_data_points
        self.metrics: Dict[str, Deque[Tuple[float, float]]] = (
            {}
        )  # name -> [(timestamp, value)]
        self.last_update = time.time()

    def add_metric(self, name: str, value: float):
        """Add a metric data point.

        Args:
            name: Metric name
            value: Metric value
        """
        timestamp = time.time()

        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_data_points)

        self.metrics[name].append((timestamp, value))
        self.last_update = timestamp
        self.refresh()

    def clear_metrics(self):
        """Clear all metrics data."""
        self.metrics.clear()
        self.refresh()

    def render(self) -> RenderableType:
        """Render the metrics widget."""
        if not self.metrics:
            return Panel("No metrics collected", title="Metrics")

        # Create a table for current values
        table = Table(title="Current Metrics", box=ROUNDED)
        table.add_column("Metric")
        table.add_column("Value")
        table.add_column("Change")

        # Add metrics to table
        for name, values in self.metrics.items():
            if not values:
                continue

            current = values[-1][1]
            change = ""

            if len(values) > 1:
                prev = values[-2][1]
                diff = current - prev
                if diff > 0:
                    change = f"↑ {diff:.2f}"
                elif diff < 0:
                    change = f"↓ {abs(diff):.2f}"
                else:
                    change = "−"

            table.add_row(name, f"{current:.2f}", change)

        # For simplicity, we'll just show the table for now
        # In a real implementation, we would add a chart of recent values
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
        self.search_callback: Optional[Callable[[str, bool, bool], None]] = None

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
        self.variables: Dict[str, Dict[str, Any]] = (
            {}
        )  # function_name -> {var_name: var_value}
        self.selected_function: Optional[str] = None
        self.expanded = True

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
        self.expanded = not self.expanded
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

        if not self.expanded:
            return Panel(
                f"{len(selected_vars)} variables available for {self.selected_function}()",
                title="Variable Inspector [+]",
            )

        # Render variables in a table
        table = Table(box=ROUNDED)
        table.add_column("Variable")
        table.add_column("Value")
        table.add_column("Type")

        for var_name, var_value in selected_vars.items():
            var_type = type(var_value).__name__
            value_str = str(var_value)

            # Truncate long values
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."

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

        layout = Layout()
        layout.split(Layout(function_selector, size=3), Layout(table))

        return Panel(layout, title="Variable Inspector [-]")


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
                "[=   ]",
                "[==  ]",
                "[=== ]",
                "[ ===]",
                "[  ==]",
                "[   =]",
                "[    ]",
                "[   =]",
                "[  ==]",
                "[ ===]",
                "[====]",
                "[=== ]",
                "[==  ]",
                "[=   ]",
            ],
            "interval": 0.1,
        },
        "dots2": {"frames": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"], "interval": 0.08},
        "dots3": {"frames": ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"], "interval": 0.08},
        "clock": {
            "frames": [
                "🕛",
                "🕐",
                "🕑",
                "🕒",
                "🕓",
                "🕔",
                "🕕",
                "🕖",
                "🕗",
                "🕘",
                "🕙",
                "🕚",
            ],
            "interval": 0.1,
        },
        "moon": {
            "frames": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
            "interval": 0.1,
        },
        "bounce": {"frames": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"], "interval": 0.1},
    }

    def __init__(
        self,
        text: str = "Working...",
        spinner_type: str = "dots",
        show_elapsed: bool = True,
    ):
        """Initialize the animated spinner widget.

        Args:
            text: Text to display alongside the spinner
            spinner_type: Type of spinner animation to use
            show_elapsed: Whether to show elapsed time
        """
        super().__init__("")
        self.text = text
        self.show_elapsed = show_elapsed

        # Get spinner configuration
        if spinner_type in self.SPINNERS:
            self.spinner_config = self.SPINNERS[spinner_type]
        else:
            self.spinner_config = self.SPINNERS["dots"]

        self.current_frame = 0
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.start_time = time.time()

    def render(self) -> RenderableType:
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")

        # Get the current frame character
        frames = self.spinner_config["frames"]
        frame_char = frames[self.current_frame % len(frames)]

        text = Text()
        text.append(frame_char, style="bold cyan")
        text.append(" ")
        text.append(self.text)

        # Add elapsed time if enabled
        if self.show_elapsed:
            elapsed = time.time() - self.start_time
            elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            text.append(" (")
            text.append(elapsed_str, style="dim")
            text.append(")")

        return text

    async def start(self):
        """Start the spinner animation."""
        self._running = True
        self.start_time = time.time()
        self.refresh()

        # Cancel existing task if running
        if self._task and not self._task.done():
            self._task.cancel()

        # Create a new refresh task
        self._task = asyncio.create_task(self._animate_spinner())

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self.refresh()

    def set_text(self, text: str):
        """Update the spinner text.

        Args:
            text: New text to display
        """
        self.text = text
        self.refresh()

    async def _animate_spinner(self):
        """Continuously animate the spinner while running."""
        try:
            while self._running:
                # Update frame and refresh
                self.current_frame += 1
                self.refresh()

                # Wait for next frame using spinner interval
                interval = self.spinner_config.get("interval", 0.1)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass


class CollapsibleWidget(CollapsibleMixin):
    """A widget that can be collapsed/expanded."""

    def __init__(
        self, collapse_callback: Callable = None, expand_callback: Callable = None
    ):
        super().__init__(collapse_callback, expand_callback)


class SearchWidget:
    """Widget for search functionality."""

    def __init__(self, search_callback: Callable = None):
        self.search_callback = search_callback or (lambda x: None)

    def on_search_change(self, value: str) -> None:
        """Handle search text changes."""
        self.search_callback(value)
