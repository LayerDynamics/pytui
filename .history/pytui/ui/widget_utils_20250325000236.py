"""Widget utility functions and base classes."""

from typing import Any
from datetime import datetime


def format_widget_style(widget: Any) -> str:
    """Format widget style safely."""
    if hasattr(widget, "style"):
        return str(widget.style)
    return str(widget)


def get_widget_timestamp() -> str:
    """Get formatted timestamp for widget."""
    return datetime.now().strftime("%H:%M:%S")


# Move helper functions and base classes here
