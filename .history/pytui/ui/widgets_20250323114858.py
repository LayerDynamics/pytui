"""Custom UI widgets for pytui."""

import time
import asyncio
from typing import Optional, List, Callable, Any

from textual.widgets import Static
from rich.console import RenderableType
from rich.text import Text
from rich.style import Style
from rich.spinner import Spinner
from rich.panel import Panel

class StatusBar(Static):
    """Status bar for displaying execution info."""
    
    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")
        self.start_time = time.time()
        self._is_running = False
        self._is_paused = False
        
    def render(self) -> RenderableType:
        """Render the status bar."""
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        # Determine status
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"
        elif self._is_running:
            status = "RUNNING"
            status_style = "bold green"
        else:
            status = "STOPPED"
            status_style = "bold red"

        # Build status line
        text = Text()
        text.append(" Status: ", style="bold")
        text.append(status, style=status_style)
        text.append(" | ", style="dim")
        text.append("Elapsed: ", style="bold")
        text.append(elapsed_str, style="cyan")
        text.append(" | ", style="dim")
        text.append("[Q]uit ", style="bold")
        text.append("[P]ause/Resume ", style="bold")
        text.append("[R]estart ", style="bold")
        text.append("[/]Search", style="bold")
        
        return text

    def set_running(self, is_running: bool):
        """Set the running state."""
        self._is_running = is_running
        self.refresh()

    def set_paused(self, is_paused: bool):
        """Set the paused state."""
        self._is_paused = is_paused
        self.refresh()

    def reset_timer(self):
        """Reset the elapsed time counter."""
        self.start_time = time.time()
        self.refresh()

    @property
    def is_running(self):
        """Get the running state."""
        return self._is_running

    @property
    def is_paused(self):
        """Get the paused state."""
        return self._is_paused
        return result                                result.append(Text(line))            else:                result.append(text)                                    start = pos + len(self.search_term)                    # Update start position                                        text.append(line[pos:pos+len(self.search_term)], style=highlight_style)                    highlight_style = "reverse yellow" if i == self.match_indices[self.current_match] else "yellow"                    # Add highlighted match                                        text.append(line[start:pos])                    # Add text before match                                                break                        text.append(line[start:])                        # Add the rest of the line                    if pos == -1:                    pos = line_lower.find(self.search_term, start)                while True:                                line_lower = line.lower()                start = 0                text = Text()                # Create a Text object with highlighted matches            if i in self.match_indices:        for i, line in enumerate(text_lines):        result = []        """            List of Text objects with highlights        Returns:                        text_lines: List of text lines to highlight        Args:                """Highlight matches in text lines.    def highlight_matches(self, text_lines: List[str]) -> List[Text]:                return self.match_indices[self.current_match]        self.current_match = (self.current_match - 1) % len(self.match_indices)                        return -1        if not self.match_indices:        """            Index of the previous match or -1 if no matches        Returns:                """Move to the previous match.    def prev_match(self) -> int:                return self.match_indices[self.current_match]        self.current_match = (self.current_match + 1) % len(self.match_indices)                        return -1        if not self.match_indices:        """            Index of the next match or -1 if no matches        Returns:                """Move to the next match.    def next_match(self) -> int:                return self.match_indices        self.current_match = 0 if self.match_indices else -1                                self.match_indices.append(i)            if self.search_term in line.lower():        for i, line in enumerate(text_lines):                self.match_indices = []        self.search_term = search_term.lower()        """            List of indices where matches were found        Returns:                        search_term: Term to search for            text_lines: List of text lines to search        Args:                """Search for a term in text lines.    def search(self, text_lines: List[str], search_term: str) -> List[int]:                self.current_match = -1        self.match_indices: List[int] = []        self.search_term = ""        """Initialize the search functionality."""    def __init__(self):        """Adds search functionality to text content."""class SearchableText:                node._style = style            elif hasattr(node, "_style"):                node.set_style(style)            if hasattr(node, "set_style"):            node = self.tree.nodes[call_id]        if call_id in self.tree.nodes:        """Apply a style to a node."""    def _apply_highlight(self, call_id: int, style: str):                    self.previous_call_ids = self.previous_call_ids[-10:]        if len(self.previous_call_ids) > 10:        # Limit history length                self.current_call_id = None        self.previous_call_ids.append(self.current_call_id)        # Clear tracking lists                                self._apply_highlight(call_id, "")            if call_id in self.tree.nodes:        for call_id in self.previous_call_ids:        # Reset all previous highlights                        self._apply_highlight(self.current_call_id, "")        if self.current_call_id and self.current_call_id in self.tree.nodes:        # Reset current highlight                        return        if not self.tree:        """Reset all highlighted nodes to normal style."""    def _reset_highlights(self):                self._apply_highlight(call_id, "bold reverse green")        self.current_call_id = call_id        # Add the new highlight                self._reset_highlights()        # Reset previous highlights                        return        if not self.tree or not hasattr(self.tree, "nodes"):        """Highlight a function by call ID."""    def highlight_function(self, call_id: int):                self.tree = tree        """Set the tree widget to highlight nodes in."""    def set_tree(self, tree):                self.tree = None        self.previous_call_ids: List[int] = []        self.current_call_id: Optional[int] = None        """Initialize the highlighter."""    def __init__(self):        """Tracks and highlights the active function in the call graph."""class ActiveFunctionHighlighter:            pass        except asyncio.CancelledError:                await asyncio.sleep(0.1)                self.refresh()            while self._running:        try:        """Continuously refresh the spinner while running."""    async def _refresh_spinner(self):                self.refresh()            self._task.cancel()        if self._task and not self._task.done():        self._running = False        """Stop the spinner animation."""    async def stop(self):                self._task = asyncio.create_task(self._refresh_spinner())        # Create a new refresh task                        self._task.cancel()        if self._task and not self._task.done():        # Cancel existing task if running                self.refresh()        self._running = True        """Start the spinner animation."""    async def start(self):                return spinner        spinner = Spinner(self.spinner_type, text=self.text)                        return Text(f"{self.text} (stopped)")        if not self._running:        """Render the spinner."""    def render(self) -> RenderableType:                self._task: Optional[asyncio.Task] = None        self._running = False        self.spinner_type = spinner_type if spinner_type in self.SPINNERS else "dots"        self.text = text        super().__init__("")        """            spinner_type: Type of spinner animation to use            text: Text to display alongside the spinner        Args:                """Initialize the spinner widget.    def __init__(self, text: str = "Working...", spinner_type: str = "dots"):        SPINNERS = ["dots", "line", "pulse", "dots2", "dots3"]        """A spinner widget for showing progress."""class SpinnerWidget(Static):        self.refresh()        self._content = content        """Update the panel content."""    async def update_content(self, content):                        await self.expand_callback()        elif not self.collapsed and self.expand_callback:            await self.collapse_callback()        if self.collapsed and self.collapse_callback:        # Call the appropriate callback                self.refresh()        self.collapsed = not self.collapsed        """Handle click events to toggle collapse state."""    async def on_click(self):                        return Panel(self._content, title=title)            title = f"[-] {self.title} (click to collapse)"        else:            return Panel(Text(""), title=title, border_style="dim")            title = f"[+] {self.title} (click to expand)"        if self.collapsed:        """Render the panel."""    def render(self) -> RenderableType:                self.collapse_callback: Optional[Callable] = None        self.expand_callback: Optional[Callable] = None        self._content = ""        self.collapsed = collapsed        self.title = title        super().__init__("")        """            collapsed: Whether the panel starts collapsed            title: The panel title        Args:                """Initialize the collapsible panel.    def __init__(self, title: str = "", collapsed: bool = False):        """A panel that can be collapsed/expanded."""class CollapsiblePanel(Static):        return self._is_paused    def is_paused(self):    @property        