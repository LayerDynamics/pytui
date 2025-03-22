"""Compatibility layer for UI components.

This module provides real implementations of UI components when Textual
is not available, enabling pytui to run in reduced functionality mode
when dependencies are missing.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, List, Any, Callable, Union
from dataclasses import dataclass

# Track if we're using fallback mode
USING_FALLBACKS = False

try:
    # Attempt to import from textual
    from textual.widgets import Static, Tree
    from textual.scroll_view import ScrollView
    from textual.containers import Container
    from textual.app import App
except ImportError:
    USING_FALLBACKS = True
    
    # Provide actual fallback implementations
    class Widget:
        """Base class for all UI widgets."""
        
        def __init__(self, *args, **kwargs):
            self.parent = None
            self.children = []
            self.id = id(self)
            self.styles = {}
            self._content = ""
            self._visible = True
        
        async def mount(self, *args, **kwargs):
            """Mount a child widget."""
            for child in args:
                child.parent = self
                self.children.append(child)
            return self
            
        async def update(self, content):
            """Update widget content."""
            self._content = str(content)
            await self.refresh()
            
        async def refresh(self):
            """Refresh the widget."""
            if hasattr(self, "_test_display") and callable(self._test_display):
                await self._test_display(self._content)
            elif hasattr(self, "render") and callable(self.render):
                rendered = self.render()
                print(f"[{self.__class__.__name__}] {rendered}")
        
        def remove_widget(self, widget):
            """Remove a child widget."""
            if widget in self.children:
                self.children.remove(widget)
                widget.parent = None
                
    class Container(Widget):
        """Container for other widgets."""
        
        async def dock(self, *widgets, edge="left", size=None, z=0):
            """Dock widgets to an edge."""
            for widget in widgets:
                await self.mount(widget)
                
    class ScrollView(Widget):
        """Scrollable view widget."""
        
        async def scroll_to(self, y=None):
            """Scroll to a position."""
            pass
            
    class Static(Widget):
        """Static content widget."""
        
        def __init__(self, content="", **kwargs):
            super().__init__(**kwargs)
            self._content = str(content)
            
        def render(self):
            """Render the widget."""
            return self._content
            
    class TreeNode:
        """Node in a tree widget."""
        
        def __init__(self, label, parent=None, expanded=True, id=None):
            self.label = label
            self.parent_id = parent
            self.expanded = expanded
            self.id = id or id(self)
            self.children = []
            
    class Tree(Widget):
        """Tree widget for hierarchical data."""
        
        def __init__(self, label, **kwargs):
            super().__init__(**kwargs)
            self.root = TreeNode(label)
            self.nodes = {self.root.id: self.root}
            
        def add(self, label, parent=None):
            """Add a node to the tree."""
            parent_node = self.nodes.get(parent, self.root)
            node = TreeNode(label, parent=parent_node.id)
            parent_node.children.append(node)
            self.nodes[node.id] = node
            return node
            
        def remove(self, node_id):
            """Remove a node from the tree."""
            if node_id in self.nodes:
                node = self.nodes.pop(node_id)
                if node.parent_id and node.parent_id in self.nodes:
                    parent = self.nodes[node.parent_id]
                    parent.children = [c for c in parent.children if c.id != node_id]
        
        async def refresh(self):
            """Refresh the tree widget."""
            await super().refresh()
            
    class App:
        """Base application class."""
        
        def __init__(self, **kwargs):
            self.view = Container()
            self.is_running = False
            
        def set_event_loop(self, loop):
            """Set the event loop."""
            self._loop = loop
            
        async def on_mount(self):
            """Called when the app is mounted."""
            pass
            
        async def on_unmount(self):
            """Called when the app is unmounted."""
            pass
            
        def exit(self, result=None):
            """Exit the application."""
            self.is_running = False
            
        def run(self):
            """Run the application."""
            self.is_running = True
            
            # Create an event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.set_event_loop(loop)
            
            # Mount and start application
            try:
                loop.run_until_complete(self.on_mount())
                # In fallback mode, we just run until on_mount completes
                # rather than starting a UI event loop
                loop.run_until_complete(self.on_unmount())
            finally:
                loop.close()
                
# Export classes with consistent naming regardless of backend
__all__ = ["USING_FALLBACKS", "App", "Container", "ScrollView", "Static", "Tree"]
