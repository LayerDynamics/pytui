"""Rich text UI components."""

from dataclasses import dataclass, field
from typing import Optional, List

from .base import Widget
from .style import Style

@dataclass
class BoxStyle:
    """Box drawing characters."""
    tl: str = "+"  # top left
    tr: str = "+"  # top right
    bl: str = "+"  # bottom left
    br: str = "+"  # bottom right
    h: str = "-"   # horizontal
    v: str = "|"   # vertical

class Box:
    """Box drawing characters for borders."""
    
    ASCII = BoxStyle()
    ROUNDED = BoxStyle(tl="╭", tr="╮", bl="╰", br="╯", h="─", v="│")
    SQUARE = BoxStyle(tl="┌", tr="┐", bl="└", br="┘", h="─", v="│")
    DOUBLE = BoxStyle(tl="╔", tr="╗", bl="╚", br="╝", h="═", v="║")

    @staticmethod
    def get_box_style(name: str = "rounded") -> BoxStyle:
        """Get box style by name."""
        styles = {
            "ascii": Box.ASCII,
            "rounded": Box.ROUNDED,
            "square": Box.SQUARE,
            "double": Box.DOUBLE
        }
        return styles.get(name.lower(), Box.ROUNDED)

# ...rest of component classes...
