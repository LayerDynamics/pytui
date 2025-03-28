"""Metrics and monitoring widgets."""

import time
from typing import Dict, List, Tuple
from collections import deque
from datetime import datetime

from textual.widgets import Static
from rich.table import Table, box
from rich.panel import Panel
from rich.text import Text

from .types import RenderableType


class MetricsWidget(Static):
    """Widget for displaying execution metrics and charts."""

    def __init__(self, max_data_points: int = 100):
        """Initialize metrics widget."""
        super().__init__("")
        self.max_data_points = max_data_points
        self.metrics: Dict[str, deque[Tuple[float, float]]] = {}
        self.last_update = time.time()

    def add_metric(self, name: str, value: float) -> None:
        """Add a metric data point."""
        timestamp = time.time()
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_data_points)
        self.metrics[name].append((timestamp, value))
        self.last_update = timestamp
        self.refresh()

    def clear_metrics(self) -> None:
        """Clear all metrics data."""
        self.metrics.clear()
        self.refresh()

    def render(self) -> RenderableType:
        """Render the metrics widget."""
        if not self.metrics:
            return Panel("No metrics collected", title="Metrics")

        table = Table(title="Current Metrics", box=box.ROUNDED)
        table.add_column("Metric")
        table.add_column("Value")
        table.add_column("Change")

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

        return Panel(table, title="Execution Metrics")


class TimelineWidget(Static):
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
