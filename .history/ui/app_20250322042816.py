"""Main Textual UI application."""

from textual.app import App
from textual.widgets import Header, Footer
from textual.binding import Binding
import asyncio

from ..executor import ScriptExecutor
from .panels import OutputPanel, CallGraphPanel, ExceptionPanel
from .widgets import StatusBar

class PyTUIApp(App):
    """PyTUI Application for visualizing Python execution."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("r", "restart", "Restart"),
        Binding("/", "search", "Search"),
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)
        self.executor = None
        self.is_paused = False
        
    def set_executor(self, executor: ScriptExecutor):
        """Set the script executor."""
        self.executor = executor
        
    async def on_mount(self):
        """Set up the UI layout."""
        # Dock header, footer, and status bar on the view container instead.
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(StatusBar(), edge="bottom", size=1, z=1)
        
        # Create panels
        self.output_panel = OutputPanel()
        self.call_graph_panel = CallGraphPanel()
        self.exception_panel = ExceptionPanel()
        
        # Dock panels in a grid (all docked at top)
        await self.view.dock(
            self.call_graph_panel,
            self.output_panel,
            self.exception_panel,
            edge="top"
        )
        
        # Start the executor if available
        if self.executor:
            self.executor.start()
            asyncio.create_task(self.process_events())
            
    async def process_events(self):
        """Process events from the executor."""
        if not self.executor:
            return
            
        collector = self.executor.collector
        
        while self.executor.is_running:
            try:
                event_type, event = await collector.get_event()
                
                if self.is_paused:
                    continue
                    
                if event_type == 'output':
                    await self.output_panel.add_output(event)
                elif event_type == 'call':
                    await self.call_graph_panel.add_call(event)
                elif event_type == 'return':
                    await self.call_graph_panel.add_return(event)
                elif event_type == 'exception':
                    await self.exception_panel.add_exception(event)
                    await self.output_panel.add_exception(event)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                
    async def action_toggle_pause(self):
        """Toggle pause/resume execution updates."""
        if not self.executor:
            return
            
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.executor.pause()
            await self.output_panel.add_message("Execution updates paused")
        else:
            self.executor.resume()
            await self.output_panel.add_message("Execution updates resumed")
            
    async def action_restart(self):
        """Restart the script execution."""
        if not self.executor:
            return
            
        await self.output_panel.clear()
        await self.call_graph_panel.clear()
        await self.exception_panel.clear()
        
        self.executor.restart()
        await self.output_panel.add_message("Restarting execution...")
        
    async def action_search(self):
        """Open search in the output panel."""
        await self.output_panel.focus()
        await self.output_panel.action_search()
