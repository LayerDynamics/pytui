"""UI panel components for the TUI."""

from textual.widgets import Static, Tree
from textual.scroll_view import ScrollView
from textual.containers import Container
from rich.console import RenderableType
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from rich.traceback import Traceback

from ..collector import OutputLine, CallEvent, ReturnEvent, ExceptionEvent

class OutputPanel(ScrollView):
    """Panel for displaying script output."""
    
    def __init__(self):
        """Initialize the output panel."""
        super().__init__()
        self.outputs = []
        
    async def add_output(self, output: OutputLine):
        """Add an output line to the panel."""
        # Format based on stream type
        if output.stream == "stderr":
            text = Text(output.content, style="red")
        elif output.stream == "system":
            text = Text(output.content, style="yellow")
        else:
            text = Text(output.content)
            
        self.outputs.append(text)
        await self.update_content()
        
    async def add_message(self, message: str):
        """Add a system message to the panel."""
        text = Text(f"[SYSTEM] {message}", style="bold blue")
        self.outputs.append(text)
        await self.update_content()
        
    async def add_exception(self, exc: ExceptionEvent):
        """Add an exception to the output."""
        text = Text(f"Exception: {exc.exception_type}: {exc.message}", style="bold red")
        self.outputs.append(text)
        await self.update_content()
        
    async def clear(self):
        """Clear the output panel."""
        self.outputs.clear()
        await self.update_content()
        
    async def update_content(self):
        """Update the panel content."""
        renderables = self.outputs.copy()
        content = Panel("\n".join([str(r) for r in renderables]), title="Output")
        # If a testing override is present, use it; otherwise, call update normally.
        if hasattr(self, "_test_display"):
            await self._test_display(content)
        else:
            # Fix: Update method call - ensure we're using update() not display()
            await self.update(content)


class CallGraphPanel(Container):
    """Panel for displaying the call graph."""
    
    def __init__(self):
        """Initialize the call graph panel."""
        super().__init__()
        self._tree = None  # Use underscore to avoid property conflicts
        self.call_nodes = {}
        
    async def on_mount(self):
        """Set up the initial tree."""
        self._tree = Tree("Execution")
        await self.mount(self._tree)
        
    # For testing - allow direct assignment in tests
    def _set_tree_for_test(self, mock_tree):
        """Set tree for testing purposes only."""
        self._tree = mock_tree
        
    async def add_call(self, call: CallEvent):
        """Add a function call to the graph."""
        label = f"{call.function_name}() at {call.filename}:{call.line_no}"
        
        # Format any args if present
        if call.args:
            args_str = ", ".join(f"{k}={v}" for k, v in call.args.items())
            label += f" Args: {args_str}"
            
        # Using Tree API from textual.widgets
        if call.parent_id and call.parent_id in self.call_nodes:
            parent_node = self.call_nodes[call.parent_id]
            node = self._tree.add(label, parent=parent_node.id)
        else:
            node = self._tree.add(label)
            
        self.call_nodes[call.call_id] = node
        
    async def add_return(self, ret: ReturnEvent):
        """Update the call graph with a return value."""
        if ret.call_id in self.call_nodes:
            node = self.call_nodes[ret.call_id]
            # Update node label with return value
            current_label = node.label
            node.label = f"{current_label} -> {ret.return_value}"
            self._tree.refresh()
            
    async def clear(self):
        """Clear the call graph."""
        self.call_nodes.clear()
        # Replace tree with a new one
        await self.remove(self._tree)
        self._tree = Tree("Execution")
        await self.mount(self._tree)
    
    # Add property for test compatibility
    @property
    def tree(self):
        return self._tree

class ExceptionPanel(Static):
    """Panel for displaying exceptions."""
    
    def __init__(self):
        """Initialize the exceptions panel."""
        super().__init__("")
        self.exceptions = []
        
    async def add_exception(self, exc: ExceptionEvent):
        """Add an exception to the panel."""
        self.exceptions.append(exc)
        await self.update_content()
        
    async def clear(self):
        """Clear the exceptions panel."""
        self.exceptions.clear()
        await self.update_content()
        
    async def update_content(self):
        """Update the panel content."""
        if not self.exceptions:
            # Use update_render_str instead of update
            await self.update_render_str(Panel("No exceptions", title="Exceptions"))
            return
            
        # Show the most recent exception
        exc = self.exceptions[-1]
        
        # Create a traceback renderable
        tb_text = "\n".join(exc.traceback)
        
        await self.update_render_str(
            Panel(
                Syntax(
                    tb_text,
                    "python",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                ),
                title=f"Exception: {exc.exception_type}"
            )
        )
