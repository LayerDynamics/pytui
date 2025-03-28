"""Metrics display components for the UI."""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from textual.widget import Widget  # Changed from Static to Widget
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED as box  # Add missing import for box
from rich.console import RenderableType


class MetricsWidget(Widget):  # Changed from Static to Widget
    """Widget for displaying execution metrics."""

    def __init__(self):
        """Initialize the metrics widget."""
        super().__init__("")
        self.metrics: Dict[str, Any] = {
            "start_time": None,
            "execution_time": 0,
            "memory_usage": 0,
            "cpu_usage": 0,
        }

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update the metrics with new values."""
        self.metrics.update(metrics)
        self.refresh()

    def render(self) -> RenderableType:
        """Render the metrics display."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric")
        table.add_column("Value")

        if self.metrics["start_time"]:
            table.add_row(
                "Start Time",
                datetime.fromtimestamp(self.metrics["start_time"]).strftime("%H:%M:%S"),
            )

        table.add_row("Execution Time", f"{self.metrics['execution_time']:.2f}s")
        table.add_row("Memory Usage", f"{self.metrics['memory_usage']:.1f} MB")
        table.add_row("CPU Usage", f"{self.metrics['cpu_usage']:.1f}%")

        return Panel(table, title="Execution Metrics", border_style="blue")


class TimelineWidget(Widget):  # Changed from Static to Widget
    """Widget for displaying a timeline of execution events."""

    def __init__(self, max_events: int = 50):
        """Initialize timeline widget."""
        super().__init__("")
        self.max_events = max_events
        self.events: List[Tuple[datetime, str, str]] = []

    def add_event(self, event_type: str, description: str) -> None:
        """Add an event to the timeline."""
        timestamp = datetime.now()
        self.events.append((timestamp, event_type, description))

        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        self.refresh()

    def clear(self) -> None:
        """Clear all timeline events."""
        self.events.clear()
        self.refresh()

    def render(self) -> RenderableType:
        """Render the timeline widget."""
        if not self.events:
            return Panel("No events recorded", title="Timeline")

        table = Table(box=box.ROUNDED)
        table.add_column("Time")
        table.add_column("Event")
        table.add_column("Description")

        styles = {"call": "green", "return": "blue", "exception": "red"}

        for timestamp, event_type, description in self.events:
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
            event_style = styles.get(event_type, "white")
            table.add_row(time_str, Text(event_type, style=event_style), description)

        return Panel(table, title="Event Timeline")
