"""PyTUI Application module."""

import asyncio
from typing import Dict, Any, Optional

# Use internal rich_text_ui components instead of textual
from .rich_text_ui.application import Application
from .rich_text_ui.container import Container
from .rich_text_ui.panel import Panel
from .rich_text_ui.text import Text
from .rich_text_ui.static import Static
from .rich_text_ui.widget import Widget
from .rich_text_ui.colors import Color

# Local imports
from .executor import ScriptExecutor
from .panels import OutputPanel, CallGraphPanel, ExceptionPanel
from .widgets import (
    StatusBar,
    AnimatedSpinnerWidget,
    ProgressBarWidget,
    MetricsWidget,
    TimelineWidget,
    SearchBar,
    VariableInspectorWidget,
    KeyBindingsWidget,
)


def maybe_await(result):
    """Await a coroutine if necessary, otherwise return the result."""
    if asyncio.iscoroutine(result):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(result)
    return result


class PyTUIApp(Application):
    """PyTUI Application for visualizing Python execution."""

    def __init__(self, *args, **kwargs):
        """Initialize the PyTUI application."""
        super().__init__(*args, **kwargs)
        self._executor = None
        self._panels = {}
        self._focused = None
        self._bindings = {
            "q": self.exit,
            "p": self.toggle_pause,
            "r": self.restart,
            "/": self.search,
            "c": self.toggle_collapse,
            "v": self.toggle_vars,
            "m": self.toggle_metrics,
            "t": self.toggle_timeline,
            "h": self.toggle_help,
        }
        
    @property
    def executor(self):
        """Get the script executor."""
        return self._executor
        
    @executor.setter
    def executor(self, executor):
        """Set the script executor."""
        self._executor = executor
        
    @property
    def focused(self):
        """Get the currently focused panel."""
        return self._focused
        
    @focused.setter
    def focused(self, panel):
        """Set the focused panel."""
        self._focused = panel
        
    def set_executor(self, executor):
        """Set the script executor."""
        self.executor = executor
        
    async def on_mount(self):
        """Initialize the UI when the application is mounted."""
        await super().on_mount()
        # Initialize UI panels
        
    def toggle_pause(self):
        """Toggle execution pause state."""
        if self.executor:
            if self.executor.is_paused:
                self.executor.resume()
            else:
                self.executor.pause()
                
    def restart(self):
        """Restart script execution."""
        if self.executor:
            self.executor.restart()
            
    def search(self):
        """Activate search mode."""
        if self.focused:
            maybe_await(self.focused.action_search())
            
    def toggle_collapse(self):
        """Toggle collapse state of the focused panel."""
        if self.focused:
            maybe_await(self.focused.toggle_collapse())
            
    def toggle_vars(self):
        """Toggle variable inspector visibility."""
        if self._panels.get("call_graph"):
            maybe_await(self._panels["call_graph"].toggle_var_display())
            
    def toggle_metrics(self):
        """Toggle metrics panel visibility."""
        pass  # Implement as needed
        
    def toggle_timeline(self):
        """Toggle timeline panel visibility."""
        pass  # Implement as needed
        
    def toggle_help(self):
        """Toggle help panel visibility."""
        pass  # Implement as needed
