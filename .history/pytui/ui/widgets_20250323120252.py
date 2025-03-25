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


class SearchableText:
    """
    Adds search functionality to text content.

    This class keeps track of a search term, the matched line indices,
    and a 'current match' pointer to allow highlighting the currently
    active match differently from the others.
    """

    def __init__(self):
        """Initialize the search functionality."""
        self.search_term = ""
        self.match_indices: List[int] = []
        self.current_match: int = -1

    def search(self, text_lines: List[str], search_term: str) -> List[int]:
        """
        Search for a term in text lines.

        Args:
            text_lines: List of text lines to search.
            search_term: Term to search for.

        Returns:
            List of indices where matches were found.
        """
        self.search_term = search_term.lower()
        self.match_indices = []
        for i, line in enumerate(text_lines):
            if self.search_term in line.lower():
                self.match_indices.append(i)
        self.current_match = 0 if self.match_indices else -1
        return self.match_indices

    def next_match(self) -> int:
        """
        Move to the next match.

        Returns:
            Index of the next match or -1 if no matches
        """
        if not self.match_indices:
            return -1
        self.current_match = (self.current_match + 1) % len(self.match_indices)
        return self.match_indices[self.current_match]

    def prev_match(self) -> int:
        """
        Move to the previous match.

        Returns:
            Index of the previous match or -1 if no matches
        """
        if not self.match_indices:
            return -1
        self.current_match = (self.current_match - 1) % len(self.match_indices)
        return self.match_indices[self.current_match]

    def highlight_matches(self, text_lines: List[str]) -> List[Text]:
        """
        Highlight matches in text lines.

        Returns:
            List of Text objects with highlights
        """
        result: List[Text] = []

        # We'll use a special style for the active match vs. other matches
        for i, line in enumerate(text_lines):
            line_lower = line.lower()
            start = 0
            text = Text()

            # Search for all occurrences of self.search_term in line
            while True:
                pos = line_lower.find(self.search_term, start)
                if pos == -1:
                    # No more matches in this line
                    text.append(line[start:])
                    break

                # Add the text before the match
                text.append(line[start:pos])

                # Determine highlight style
                if (
                    self.match_indices
                    and i == self.match_indices[self.current_match]
                ):
                    highlight_style = "reverse yellow"
                else:
                    highlight_style = "yellow"

                # Add highlighted match
                text.append(
                    line[pos : pos + len(self.search_term)],
                    style=highlight_style
                )

                start = pos + len(self.search_term)

            result.append(text)

        return result


class ActiveFunctionHighlighter:
    """
    Tracks and highlights the active function in the call graph.

    This class assumes there's some kind of 'tree' structure with nodes
    accessible by ID, and that each node can have its style changed.
    """

    def __init__(self):
        """Initialize the highlighter."""
        self.current_call_id: Optional[int] = None
        self.previous_call_ids: List[int] = []
        self.tree = None

    def set_tree(self, tree: Any):
        """
        Set the tree widget to highlight nodes in.

        Args:
            tree: The tree-like structure containing nodes
        """
        self.tree = tree

    def highlight_function(self, call_id: int):
        """
        Highlight a function by call ID.
        
        Args:
            call_id: The ID of the node (function call) to highlight
        """
        if not self.tree or not hasattr(self.tree, "nodes"):
            return

        # Reset previous highlights
        self._reset_highlights()

        # Add the new highlight
        self.current_call_id = call_id
        self._apply_highlight(call_id, "bold reverse green")

    def _reset_highlights(self):
        """Reset all highlighted nodes to normal style."""
        if not self.tree:
            return
        if self.current_call_id and self.current_call_id in self.tree.nodes:
            self._apply_highlight(self.current_call_id, "")
        for call_id in self.previous_call_ids:
            if call_id in self.tree.nodes:
                self._apply_highlight(call_id, "")
        # Clear tracking lists
        self.previous_call_ids.append(self.current_call_id)
        if len(self.previous_call_ids) > 10:
            # Limit history length
            self.previous_call_ids = self.previous_call_ids[-10:]
        self.current_call_id = None

    def _apply_highlight(self, call_id: int, style: str):
        """Apply a style to a node."""
        if call_id in self.tree.nodes:
            node = self.tree.nodes[call_id]
            if hasattr(node, "set_style"):
                node.set_style(style)
            elif hasattr(node, "_style"):
                node._style = style


class SpinnerWidget(Static):
    """A spinner widget for showing progress."""

    SPINNERS = ["dots", "line", "pulse", "dots2", "dots3"]

    def __init__(self, text: str = "Working...", spinner_type: str = "dots"):
        """
        Initialize the spinner widget.

        Args:
            text: Text to display alongside the spinner
            spinner_type: Type of spinner animation to use
        """
        super().__init__("")
        self.text = text
        self.spinner_type = spinner_type if spinner_type in self.SPINNERS else "dots"
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def render(self) -> RenderableType:
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")
        spinner = Spinner(self.spinner_type, text=self.text)
        return spinner

    async def start(self):
        """Start the spinner animation."""
        self._running = True
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()
        # Create a new refresh task
        self._task = asyncio.create_task(self._refresh_spinner())

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()

    async def _refresh_spinner(self):
        """Continuously refresh the spinner while running."""
        try:
            while self._running:
                self.refresh()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


class CollapsiblePanel(Static):
    """A panel that can be collapsed/expanded."""

    def __init__(self, title: str = "", collapsed: bool = False):
        """
        Initialize the collapsible panel.

        Args:
            title: The panel title
            collapsed: Whether the panel starts collapsed
        """
        super().__init__("")
        self.title = title
        self.collapsed = collapsed
        self._content = ""
        self.expand_callback: Optional[Callable] = None
        self.collapse_callback: Optional[Callable] = None

    def render(self) -> RenderableType:
        """Render the panel."""
        if self.collapsed:
            title = f"[+] {self.title} (click to expand)"
            return Panel(Text(""), title=title, border_style="dim")
        else:
            title = f"[-] {self.title} (click to collapse)"
            return Panel(self._content, title=title)

    async def on_click(self):
        """
        Handle click events to toggle collapse state.
        Calls the expand_callback when expanding
        and the collapse_callback when collapsing.
        """
        self.collapsed = not self.collapsed
        if self.collapsed and self.collapse_callback:
            await self.collapse_callback()
        elif not self.collapsed and self.expand_callback:
            await self.expand_callback()
        self.refresh()

    async def update_content(self, content: str):
        """Update the panel content."""
        self._content = content
        self.refresh()
