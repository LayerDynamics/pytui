"""Application module for rich text UI framework."""

import asyncio
import sys
from typing import Callable

from .app_config import AppConfig
from .container import Container
from .panel import Panel
from .text import Text


class Application:
    """Main application class."""

    def __init__(self, title="TUI Application"):
        """Initialize application."""
        self.config = AppConfig(title)
        self.view = Container()
        self.bindings = {}
        self.is_running = False
        self.error = None
        self._handlers = {"key": None, "mouse": None, "resize": None}

    async def on_mount(self):
        """Called when application is mounted.

        Override this method to initialize your application.
        """
        # Create default layout
        header = Panel(self.config.title, border_style="bold")
        content = Container(name="main")
        footer = Text("Press 'q' to quit", style="dim")
        await self.view.mount(header, content, footer)

    async def refresh(self):
        """Refresh the application display."""
        if self.view:
            await self.view.refresh()

    async def exit(self):
        """Exit the application."""
        self.is_running = False
        await self.on_unmount()

    async def on_unmount(self):
        """Called when application is unmounting.

        Override this method to clean up resources.
        """
        # Reset terminal
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write("\033[0m")  # Reset colors
        sys.stdout.write("\033[2J")  # Clear screen
        sys.stdout.write("\033[H")  # Move to home
        sys.stdout.flush()

        # Clean up handlers
        if self.view:
            self.view.children.clear()

    async def mount(self):
        """Mount the application."""
        try:
            await self.on_mount()
            self.is_running = True
            await self._setup_handlers()
            await self.refresh()
        except (RuntimeError, IOError) as e:
            self.error = str(e)
            await self.exit()

    async def _setup_handlers(self):
        """Set up event handlers."""
        if self._handlers["key"]:
            self.view.on("key", self._handlers["key"])
        if self._handlers["mouse"]:
            self.view.on("mouse", self._handlers["mouse"])
        if self._handlers["resize"]:
            self.view.on("resize", self._handlers["resize"])

    def bind(self, key: str, handler: Callable) -> "Application":
        """Bind a key to a handler function."""
        self.bindings[key] = handler
        return self

    async def run_async(self):
        """Run the application asynchronously."""
        try:
            await self.mount()
            while self.is_running:
                await asyncio.sleep(0.1)
        finally:
            await self.on_unmount()

    def run(self):
        """Run the application synchronously."""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.run_async())
        finally:
            loop.close()
