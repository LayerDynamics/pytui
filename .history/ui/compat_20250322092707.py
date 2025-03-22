"""Minimal Textual-compatible UI components."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio

@dataclass
class TreeNode:
    """Tree node data structure."""
    id: str
    label: str
    parent_id: Optional[str] = None
    children: Dict[str, 'TreeNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = {}

class Tree:
    """Basic tree widget implementation."""
    def __init__(self, label: str = "Root"):
        self.root = TreeNode(id="root", label=label)
        self.nodes: Dict[str, TreeNode] = {"root": self.root}
        self._next_id = 1
    
    def add(self, label: str, *, parent: Optional[str] = None) -> TreeNode:
        """Add a node to the tree."""
        node_id = f"node_{self._next_id}"
        self._next_id += 1
        
        node = TreeNode(id=node_id, label=label, parent_id=parent or "root")
        self.nodes[node_id] = node
        
        parent_node = self.nodes[parent] if parent else self.root
        parent_node.children[node_id] = node
        return node
    
    def refresh(self):
        """Update the tree display."""
        # No-op for now, would be implemented by UI framework

class ScrollView:
    """Basic scrollable view."""
    def __init__(self):
        self._content = None
    
    async def update(self, content: Any):
        """Update the view content."""
        self._content = content
        # Would trigger actual display update in UI framework

class Static:
    """Static content display."""
    def __init__(self, content: str = ""):
        self._content = content
    
    async def update(self, content: Any):
        """Update the content."""
        self._content = content
        # Would trigger actual display update in UI framework

class Container:
    """Container for other widgets."""
    def __init__(self):
        self.widgets = []
    
    async def mount(self, widget: Any):
        """Mount a widget in the container."""
        self.widgets.append(widget)
    
    async def remove_widget(self, widget: Any):
        """Remove a widget from the container."""
        if widget in self.widgets:
            self.widgets.remove(widget)
