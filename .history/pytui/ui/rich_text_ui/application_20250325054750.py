import asyncio
import signal
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
        self._key_handler = None
        self._mouse_handler = None
        self._resize_handler = None
        
    async def mount(self):
        """Mount the application."""
        try:
            await self.on_mount()
            self.is_running = True
            await self._setup_handlers()
            await self.refresh()
        except Exception as e:
            self.error = str(e)
            await self.exit()
            
    async def _setup_handlers(self):
        """Set up event handlers."""
        if self._key_handler:
            self.view.on("key", self._key_handler)
        if self._mouse_handler:
            self.view.on("mouse", self._mouse_handler)
        if self._resize_handler:
            self.view.on("resize", self._resize_handler)
            
    def bind(self, key, handler):
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
