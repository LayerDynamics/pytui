"""Application implementation."""

import sys
import asyncio
import signal
from typing import Optional

from .widgets import Container

class App:
    """Base application class."""
    
    def __init__(self, title: str = "TUI Application") -> None:
        self.title = title
        self.view = Container()
        self.is_running = False
        self._bindings = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._refresh_task = None
        self.mounted = False
        self.error = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop."""
        self._loop = loop

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        try:
            self.mounted = True
            if self._loop:
                for sig in (signal.SIGINT, signal.SIGTERM):
                    self._loop.add_signal_handler(sig, self.exit)
        except Exception as e:
            self.error = str(e)

    # ...rest of App implementation...

__all__ = ["App"]
