"""Metrics display components."""

from typing import Dict, Any, Optional
from datetime import datetime

from textual.widgets import Static
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import RenderableType

class MetricsPanel(Static):
    """Panel for displaying execution metrics."""
    
    def __init__(self) -> None:
        """Initialize metrics panel."""
        super().__init__("")
        self.metrics: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update the metrics data."""
        self.metrics = metrics
        self.last_update = datetime.now()
        self.refresh()

    def render(self) -> RenderableType:
        """Render the metrics panel."""
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Metric")
        table.add_column("Value")

        for key, value in self.metrics.items():
            table.add_row(str(key), str(value))

        last_update_text = ""
        if self.last_update:
            last_update_text = f"\nLast updated: {self.last_update.strftime('%H:%M:%S')}"

        return Panel(
            table,
            title="Execution Metrics",
            subtitle=last_update_text,
            border_style="blue"
        )
