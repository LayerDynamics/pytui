"""Application components for rich text UI."""

import sys
import asyncio
import signal
from .containers import Container

class AppConfig:
    """Configuration class for App."""
    
    def __init__(self, title="TUI Application"):
        self.title = title
        self.mounted = False
        self.error = None
        self.is_running = False
        self._bindings = {}
        self._loop = None
        self._refresh_task = None
        self.view = Container()

class App:
    """Base application class."""
    
    def __init__(self, title="TUI Application"):
        self.config = AppConfig(title)
        self.view = self.config.view
        self.is_running = False

    # ...rest of App implementation...

    def _handle_signal(self, _):
        """Handle exit signals directly instead of using lambda."""
        self.exit()

    async def on_mount(self):
        """Mount the application."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            self.config._loop.add_signal_handler(sig, self._handle_signal)
        # ...rest of mount implementation...
