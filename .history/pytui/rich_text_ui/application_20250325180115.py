"""Application module for rich text UI framework."""

import asyncio
import sys
import traceback
from typing import Callable, Dict, Any

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
        self.bindings = {"q": self.exit, "Q": self.exit}  # Add default quit bindings
        self.is_running = False
        self.error = None
        self._handlers = {"key": self._handle_key, "mouse": None, "resize": None}

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
            await self._safe_refresh()  # Use safer refresh method
        except (RuntimeError, IOError) as e:
            self.error = str(e)
            print(f"Error during mount: {e}", file=sys.stderr)
            await self.exit()
        except Exception as e:
            self.error = str(e)
            print(f"Unexpected error during mount: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            await self.exit()

    async def _safe_refresh(self):
        """Safely refresh the application, catching and reporting errors."""
        try:
            if self.view:
                # Just mark as needing refresh instead of full render
                self.view._needs_refresh = True
        except Exception as e:
            print(f"Error during refresh: {e}", file=sys.stderr)

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

    def _handle_key(self, event):
        """Handle key events."""
        key = event.get("key", "")
        if key in self.bindings:
            handler = self.bindings[key]
            if callable(handler):
                return handler()
        return None

    async def run_async(self):
        """Run the application asynchronously."""
        try:
            await self.mount()
            
            # Simple main loop with safe error handling
            while self.is_running:
                try:
                    # Process any key input here if needed
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error in application loop: {e}", file=sys.stderr)
                    
        except asyncio.CancelledError:
            # Handle graceful cancellation
            self.is_running = False
        except Exception as e:
            print(f"Unexpected error in run_async: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        finally:
            await self.on_unmount()

    def run(self):
        """Run the application synchronously."""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.run_async())
        finally:
            loop.close()
