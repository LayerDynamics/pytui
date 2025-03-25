"""Metrics and monitoring widgets."""

import time
from typing import Dict, Any, Tuple
from collections import deque
from textual.widgets import Static
from rich.table import Table, box
from rich.panel import Panel

class MetricsWidget(Static):
    """Widget for displaying execution metrics and charts."""
    // ...move MetricsWidget implementation here...

class TimelineWidget(Static):
    """Widget for displaying a timeline of execution events."""
    // ...move TimelineWidget implementation here...
