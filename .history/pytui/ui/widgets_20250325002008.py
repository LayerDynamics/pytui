"""UI widgets module"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple, TypeVar
from collections import deque
from datetime import datetime

from textual.widgets import (
    Button, Label, Static, Header
)
from rich.text import Text
from rich.spinner import Spinner
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table, box
from rich.layout import Layout

from .widget_utils import (
    ActiveFunctionHighlighter,
    SearchableText,
    CollapsibleMixin,
    SPINNER_STYLES,
    ensure_callable
)

// ...existing imports...

# Types
RenderableType = TypeVar('RenderableType')
ROUNDED = box.ROUNDED

// ...existing Chart fallback implementation...

class StatusBar(Static):
    // ...existing code...

class SpinnerWidget(Static):
    // ...existing code...

class CollapsiblePanel(Static):
    // ...existing code...

class ProgressBarWidget(Static):
    // ...existing code...

class KeyBindingsWidget(Static):
    // ...existing code...

class SearchBar(Static):
    // ...existing code...

class VariableInspectorWidget(Static):
    // ...existing code...

class AnimatedSpinnerWidget(Static):
    // ...existing code...

class CollapsibleWidget(CollapsibleMixin):
    // ...existing code...

class SearchWidget:
    // ...existing code...
