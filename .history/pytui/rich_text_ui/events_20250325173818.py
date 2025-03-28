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

    name: str  # This is required by Event
    key: str   # Required non-default argument
    target: Any = None  # Default argument from Event
    prevented: bool = False  # Default argument from Event
    ctrl: bool = False    # Default arguments specific to KeyEvent
    alt: bool = False
    shift: bool = False


@dataclass
class MouseEvent(Event):
    """Mouse event."""

    name: str  # Required by Event
    x: int     # Required non-default arguments specific to MouseEvent
    y: int
    button: int
    action: str  # click, double_click, drag, etc.
    target: Any = None  # Default argument from Event
    prevented: bool = False  # Default argument from Event


@dataclass
class ResizeEvent(Event):
    """Terminal resize event."""

    name: str  # Required by Event
    width: int  # Required non-default arguments specific to ResizeEvent
    height: int
    target: Any = None  # Default argument from Event
    prevented: bool = False  # Default argument from Event
