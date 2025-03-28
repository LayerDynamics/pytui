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
class KeyEvent:
    """Keyboard event."""

    name: str
    key: str
    target: Any = None
    prevented: bool = False
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    def prevent_default(self):
        """Prevent default event handling."""
        self.prevented = True


@dataclass
class MouseEvent:
    """Mouse event."""

    name: str
    x: int
    y: int
    button: int
    action: str  # click, double_click, drag, etc.
    target: Any = None
    prevented: bool = False

    def prevent_default(self):
        """Prevent default event handling."""
        self.prevented = True


@dataclass
class ResizeEvent:
    """Terminal resize event."""

    name: str
    width: int
    height: int
    target: Any = None
    prevented: bool = False

    def prevent_default(self):
        """Prevent default event handling."""
        self.prevented = True
