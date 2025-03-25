"""Progress related widgets."""

import time
import asyncio
from typing import Optional, Any
from textual.widgets import Static
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

class ProgressBarWidget(Static):
    """Progress bar widget for showing execution progress."""
    // ...move ProgressBarWidget implementation here...

class SpinnerWidget(Static):
    """A spinner widget for showing progress."""
    // ...move SpinnerWidget implementation here...

class AnimatedSpinnerWidget(Static):
    """Enhanced spinner widget with richer animation options."""
    // ...move AnimatedSpinnerWidget implementation here...
