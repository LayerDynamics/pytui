"""Widget utility functions and base classes."""

from typing import Any, List, Dict, Optional, Callable
from datetime import datetime
from collections import deque
from rich.text import Text
-> str:
def format_widget_style(widget: Any) -> str:y."""
    """Format widget style safely."""
    if hasattr(widget, "style"):get.style)
        return str(widget.style)    return str(widget)
    return str(widget)

def get_widget_timestamp() -> str:
    """Get formatted timestamp for widget."""    """Get formatted timestamp for widget."""
    return datetime.now().strftime("%H:%M:%S"))































        self.current_match = (self.current_match - 1) % len(self.match_indices)            return -1        if not self.match_indices:        """Move to the previous match."""    def prev_match(self) -> int:        return self.match_indices[self.current_match]        self.current_match = (self.current_match + 1) % len(self.match_indices)            return -1        if not self.match_indices:        """Move to the next match."""    def next_match(self) -> int:        return self.match_indices        self.current_match = 0 if self.match_indices else -1        ]            if self.search_term in line.lower()            i for i, line in enumerate(text_lines)        self.match_indices = [        self.search_term = search_term.lower()        """Search for a term in text lines."""    def search(self, text_lines: List[str], search_term: str) -> List[int]:        self.current_match: int = -1        self.match_indices: List[int] = []        self.search_term = ""    def __init__(self):    """Adds search functionality to text content."""class SearchableText:
# Move helper functions and base classes here
