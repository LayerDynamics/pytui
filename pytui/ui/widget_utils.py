"""Widget utility functions and base classes."""

from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from collections import deque

def ensure_callable(callback: Optional[Callable] = None) -> Callable:
    """Return the provided callback if callable, otherwise return a no-op function."""
    return callback if callable(callback) else lambda *args, **kwargs: None

def format_widget_style(widget: Any) -> str:
    """Format widget style safely."""
    if hasattr(widget, "style"):
        return str(widget.style)
    return str(widget)


def get_widget_timestamp() -> str:
    """Get formatted timestamp for widget."""
    return datetime.now().strftime("%H:%M:%S")


class ActiveFunctionHighlighter:
    """Tracks and highlights the active function in the call graph."""

    def __init__(self):
        """Initialize the highlighter."""
        self.current_call_id: Optional[int] = None
        self.previous_call_ids: List[int] = []
        self.tree = None

    def set_tree(self, tree: Any):
        """Set the tree widget to highlight nodes in."""
        self.tree = tree

    def highlight_function(self, call_id: int):
        """Highlight a function by call ID."""
        if not self.tree or not hasattr(self.tree, "nodes"):
            return

        self._reset_highlights()
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
        self.previous_call_ids.append(self.current_call_id)
        if len(self.previous_call_ids) > 10:
            self.previous_call_ids = self.previous_call_ids[-10:]
        self.current_call_id = None

    def _apply_highlight(self, call_id: int, style: str):
        """Apply a style to a node."""
        if call_id in self.tree.nodes:
            node = self.tree.nodes[call_id]
            if hasattr(node, "set_style"):
                node.set_style(style)
            elif hasattr(node, "style"):
                node.style = style


class SearchableText:
    """Adds search functionality to text content."""

    def __init__(self):
        """Initialize the search functionality."""
        self.search_term = ""
        self.match_indices: List[int] = []
        self.current_match: int = -1

    def search(self, text_lines: List[str], search_term: str) -> List[int]:
        """Search for a term in text lines."""
        self.search_term = search_term.lower()
        self.match_indices = []
        for i, line in enumerate(text_lines):
            if self.search_term in line.lower():
                self.match_indices.append(i)
        self.current_match = 0 if self.match_indices else -1
        return self.match_indices

    def next_match(self) -> int:
        """Move to the next match."""
        if not self.match_indices:
            return -1
        self.current_match = (self.current_match + 1) % len(self.match_indices)
        return self.match_indices[self.current_match]

    def prev_match(self) -> int:
        """Move to the previous match."""
        if not self.match_indices:
            return -1
        self.current_match = (self.current_match - 1) % len(self.match_indices)
        return self.match_indices[self.current_match]


class CollapsibleMixin:
    """Mixin for adding collapse/expand functionality."""

    def __init__(
        self,
        collapse_callback: Optional[Callable] = None,
        expand_callback: Optional[Callable] = None,
    ):
        """Initialize collapse functionality."""
        self.collapse_callback = collapse_callback or (lambda: None)
        self.expand_callback = expand_callback or (lambda: None)
        self.is_collapsed = False

    def toggle_collapse(self) -> None:
        """Toggle collapsed state."""
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self) -> None:
        """Collapse the widget."""
        self.is_collapsed = True
        self.collapse_callback()

    def expand(self) -> None:
        """Expand the widget."""
        self.is_collapsed = False
        self.expand_callback()


SPINNER_STYLES = {
    "dots": {
        "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "interval": 0.08,
    },
    "line": {"frames": ["-", "\\", "|", "/"], "interval": 0.1},
    # Add more spinner styles as needed
}
