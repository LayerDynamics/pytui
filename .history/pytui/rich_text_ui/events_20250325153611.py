from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class Event:
    """Base event class."""

    name: str
    target: Any = None
    prevented: bool = False

    def prevent_default(self):
        """Prevent default event handling."""
        self.prevented = True


@dataclass
class KeyEvent(Event):
    """Keyboard event."""

    key: str
    ctrl: bool = False
    alt: bool = False
    shift: bool = False


@dataclass
class MouseEvent(Event):
    """Mouse event."""

    x: int
    y: int
    button: int
    action: str  # click, double_click, drag, etc.


@dataclass
class ResizeEvent(Event):
    """Terminal resize event."""

    width: int
    height: int
