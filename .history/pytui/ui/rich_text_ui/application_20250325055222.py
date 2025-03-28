"""Application class for managing TUI applications."""

import asyncio
import signal
from typing import Optional, Dict, Any, Callable
from .app_config import AppConfig
from .container import Container
from .panel import Panel
from .text import Text
from .events import Event"""Main application class."""

class Application:lication"):
    """Main application class."""
    (title)
    def __init__(self, title: str = "TUI Application"):ner()
        """Initialize application."""
        self.config = AppConfig(title)
        self.view = Container()
        self.bindings: Dict[str, Callable] = {}
        self.is_running = Falseself._resize_handler = None
        self._key_handler = None
        self._mouse_handler = None
        self._resize_handler = Noneount the application."""
        self.error: Optional[str] = None
        self.title = title

    async def on_mount(self):ndlers()
        """Called when application is mounted."""()
        try:
            # Initialize base application statee)
            self.is_running = Trueawait self.exit()

            # Set up default key bindings
            self.bindings.update({ers."""
                "q": self.exit,
                "ctrl+c": self.exit, self._key_handler)
                "r": self.refresh
            }), self._mouse_handler)

            # Create default layout if view is emptyself.view.on("resize", self._resize_handler)
            if not self.view.children:
                header = Panel(self.title, border_style="bold")
                content = Container(name="main")unction."""
                footer = Text("Press 'q' to quit", style="dim")gs[key] = handler
                await self.view.mount(header, content, footer)return self

        except Exception as e:
            self.error = str(e)un the application asynchronously."""
            await self.exit()

    async def refresh(self):
        """Refresh the application display."""await asyncio.sleep(0.1)
        if self.view:
            await self.view.refresh()await self.on_unmount()

    async def exit(self):
        """Exit the application."""ously."""
        self.is_running = False = asyncio.get_event_loop()
        await self.on_unmount()
.run_until_complete(self.run_async())
    async def on_unmount(self):
        """Called when application is unmounted."""            loop.close()







































































            loop.close()        finally:            loop.run_until_complete(self.run_async())        try:        loop = asyncio.get_event_loop()        """Run the application synchronously."""    def run(self):                        await self.on_unmount()        finally:                await asyncio.sleep(0.1)            while self.is_running:            await self.mount()        try:        """Run the application asynchronously."""    async def run_async(self):                return self        self.bindings[key] = handler        """Bind a key to a handler function."""    def bind(self, key, handler):                        self.view.on("resize", self._resize_handler)        if self._resize_handler:            self.view.on("mouse", self._mouse_handler)        if self._mouse_handler:            self.view.on("key", self._key_handler)        if self._key_handler:        """Set up event handlers."""    async def _setup_handlers(self):                        await self.exit()            self.error = str(e)        except Exception as e:            await self.refresh()            await self._setup_handlers()            self.is_running = True            await self.on_mount()        try:        """Mount the application."""    async def mount(self):        sys.stdout.flush()        sys.stdout.write("\033[H")     # Move to home position        sys.stdout.write("\033[2J")    # Clear screen        sys.stdout.write("\033[0m")    # Reset colors        sys.stdout.write("\033[?25h")  # Show cursor        import sys        """Reset terminal to initial state."""    def _reset_terminal(self):            print(f"Error during unmount: {e}", file=sys.stderr)        except Exception as e:            self._reset_terminal()            # Reset terminal state                    self.view.remove_widget(child)                for child in self.view.children[:]:            if self.view:            # Clear widget tree                    pass                except (NotImplementedError, ValueError):                    self.config._loop.remove_signal_handler(signal.SIGTERM)                    self.config._loop.remove_signal_handler(signal.SIGINT)                try:            if hasattr(self.config, "_loop"):            # Remove signal handlers        try: