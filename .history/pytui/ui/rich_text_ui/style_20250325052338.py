"""Style handling for rich text UI."""

import sys
import asyncio
from typing import Any, Dict, Optional

class Style:
    """Style representation for text formatting."""
    
    COLORS = {
        # Basic colors
        "black": "\033[30m",
        "red": "\033[31m",
        # ...rest of color definitions...
    }

    SUPPORTS_COLOR = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    def __init__(self, style_string: str = "") -> None:
        self.components = set(style_string.split()) if style_string else set()

    # ...rest of Style implementation...

class StyleManager:
    """Manages widget styles."""
    
    def __init__(self, widget: Any) -> None:
        self.widget = widget
        self._styles: Dict[str, Any] = {}

    # ...rest of StyleManager implementation...

__all__ = ["Style", "StyleManager"]
